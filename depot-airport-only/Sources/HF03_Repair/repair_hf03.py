"""Additive HF03 repair against sealed HF02. Never writes installed scenery."""
import pathlib,sys,pickle,json,ast,math,copy,hashlib,subprocess,importlib.util,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
sys.path.insert(0,str(PREV/'work'))
from sign_groups import *
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
from layout_plan import heading_vec,aircraft_outline
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
from route_common import smooth_pavement
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03';LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
plan,d,apt,oldscene=pickle.loads((ROOT/'work/current.pkl').read_bytes())
scene=json.loads((ROOT/'work/scene-hf03.json').read_text());newjets,jshapes,planes=pickle.loads((ROOT/'work/jetways.pkl').read_bytes())
spec=importlib.util.spec_from_file_location('mesh_hf03',STAGE/'Sources/Build/native_mesh.py');nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(nm)
tree=ast.parse((PREV/'work/repair_airport_details.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('emit_area','apt_area','sampled_apt_segments','emit_apt_line','dsf_path','emit_dsf_line')],type_ignores=[]),'helpers','exec'))
solids=unary_union([v['geom'] for v in plan['models'].values()])
primary=[r for r in plan['new'] if not r.get('alternative')]+plan['details']
# Full new aprons plus removed stand pockets, excluding the retained C pier.
apron=unary_union([box(-660,350,-125,700),box(150,390,430,700),plan['zones']['D_West']]+[g.buffer(10) for g in planes])
core=plan['models']['B_Lobby_Closed']['geom'];icp=plan['models']['International_Processor']['geom']
landside=unary_union([box(*core.bounds).buffer(7,join_style=2),icp.buffer(4,join_style=2)])
cleanup=unary_union([apron,solids.buffer(3),landside])
stats=collections.Counter();deleted=[];replaced={};discard=set();removed_signs=[]

def uv_clip(e,mask):
 rows=[];dim=int(e['lines'][0].split()[3])
 if dim==2 and e['param']!=65535:return emit_area(e['index'],e['param'],e['geom'].difference(mask))
 if dim==4 and e['param']!=65535:
  rings=[];ring=[]
  for row in e['lines']:
   if row.startswith('POLYGON_POINT'):ring.append(list(map(float,row.split()[1:])))
   elif row=='END_WINDING':
    points=[]
    for a,b in zip(ring,ring[1:]+ring[:1]):
     p=np.array(xy(*a[:2]));q=np.array(xy(*b[:2]));h=np.array(xy(*a[2:]));k=np.array(xy(*b[2:]))
     count=max(2,math.ceil(np.linalg.norm(q-p)/2))
     for t in np.linspace(0,1,count,endpoint=False):points.append((1-t)**3*p+3*(1-t)**2*t*h+3*(1-t)*t*t*(2*q-k)+t**3*q)
    rings.append(safe_poly(points));ring=[]
  g=rings[0].difference(unary_union(rings[1:]))
  return emit_area(e['index'],e['param'],g.difference(mask))
 if dim!=4 or e['param']!=65535:raise ValueError('Unsupported UV polygon '+e['resource'])
 points=np.array([list(map(float,l.split()[1:])) for l in e['lines'] if l.startswith('POLYGON_POINT')])
 pts=np.array([xy(*p[:2]) for p in points]);uv=points[:,2:]
 # Clip per source triangle to preserve non-affine atlas coordinates.
 g=safe_poly(pts);src_tris=constrained_delaunay_triangles(g)
 for tri in src_tris.geoms:
  t=np.array(list(tri.exterior.coords)[:3]);ids=[np.argmin(np.linalg.norm(pts-v,axis=1)) for v in t]
  fit=np.linalg.solve(np.column_stack([t,np.ones(3)]),uv[ids])
  for part in polygon_parts(polys_only(tri.difference(mask))):
   if part.area<.001:continue
   for cut in constrained_delaunay_triangles(part).geoms:
    rows += [f'BEGIN_POLYGON {e["index"]} 65535 4','BEGIN_WINDING']
    for x,y in list(orient(cut,sign=1).exterior.coords)[:-1]:
     lon,lat=ll(x,y);u,v=np.array([x,y,1])@fit
     rows.append(f'POLYGON_POINT {lon:.9f} {lat:.9f} {u:.8f} {v:.8f}')
    rows+=['END_WINDING','END_POLYGON']
 return rows

# Remove entire old glyph groups in the new aprons, including partial remnants.
# The independent current label OBJ remains untouched.
for g in groups(d):
 if g['geom'].intersects(apron) and (g['text'].startswith(('B','C')) or len(g['text'])<=3):
  discard.update(g['indices']);removed_signs.append(dict(text=g['text'],center=list(g['geom'].centroid.coords[0])))
# Old apron zones can contain disconnected glyph fragments after the R02 cut.
for i,e in enumerate(d['entities']):
 res=e['resource'];g=e['geom'];reason=None
 if i in discard:continue
 if any(t in res for t in ('DrapedLocSigns.pol','DrapedDirSigns.pol')) and apron.intersects(g):reason='obsolete apron identifier or fragment'
 elif e['kind']=='object' and not res.startswith('objects/'):
  if landside.buffer(4).contains(g) and any(t in res.lower() for t in ('car','vehicle','parking','light','ramp_equipment','barrier')):reason='old landside object within replacement building/core'
  elif apron.contains(g) and any(t in res.lower() for t in ('barrier','fuel_hydrant')):reason='obsolete apron furnishing'
 elif e['kind']=='polygon' and res.endswith('.fac') and 'Jetways/' not in res:
  if 'Garage' in res and g.intersects(landside):reason='clipped garage fragment at replacement processor'
  elif 'term_building' in res and box(*core.bounds).buffer(7).covers(g):reason='old B processor facade fragment'
  elif 'term_bridge' in res and g.intersects(core.buffer(5)) and g.area<110:reason='small disconnected B walkway fragment'
  elif ('term_building' in res or 'term_roof' in res) and g.area<200 and g.distance(solids)<3:reason='small disconnected terminal fragment'
  elif 'fence' in res.lower() and g.intersects(landside):reason='old fence passing into rebuilt processor'
 elif res.endswith('.pol') and g.intersects(cleanup) and any(t in res.lower() for t in ('pavement/','terrain_fx/','safety_area','markings/')):
  # Trim inherited dirty/apron overlays and safety paint, including explicit UV artwork.
  changed=g.intersection(cleanup).area
  if changed>.01:
   replaced[i]=uv_clip(e,cleanup);stats['trimmed inherited ground polygons']+=1
 elif res.endswith(('.lin','.str')) and g.intersects(cleanup):
  path=dsf_path(e);remain=path.difference(cleanup)
  if path.length-remain.length>.05:
   replaced[i]=emit_dsf_line(e,remain);stats['trimmed inherited strings']+=1
 if reason:discard.add(i);stats[reason]+=1;deleted.append(dict(index=i,resource=res,reason=reason,center=list(g.centroid.coords[0])))

# Additional old C labels outside the main new apron: replace only shifted C12/14/15.
for g in groups(d):
 if g['text'] in ('C12','C14','C14W','C15') and g['geom'].distance(Point(-130,485))<55:
  discard.update(g['indices']);removed_signs.append(dict(text=g['text'],center=list(g['geom'].centroid.coords[0])))

# Remove old paint while preserving authored lead-ins and service/aircraft routes.
servicefix=json.loads((ROOT/'work/service-repair.json').read_text())
airnodes={n for a in apt if a['code']==1202 for n in a['parts'][1:3]}
assert not airnodes.intersection(servicefix['moved_nodes'])
rows=[];jet_index=0;paint=[];added_service_nodes=False
for a in apt:
 if a['code']==99:continue
 if a['code']==1201 and a['parts'][4] in servicefix['moved_nodes']:
  s=a['parts'].copy();lon,lat=ll(*servicefix['moved_nodes'][s[4]]);s[1]=f'{lat:.9f}';s[2]=f'{lon:.9f}';rows.append(' '.join(s));continue
 if a['code']==1206:
  if not added_service_nodes:rows+=servicefix['new_nodes'];added_service_nodes=True
  rows+=servicefix['replacements'].get(a['lines'][0],a['lines']);continue
 if a['code']==1500:
  rows+=newjets[jet_index]['lines'] if jet_index<32 else a['lines'];jet_index+=1;continue
 if a['code']==120 and a.get('geom') is not None:
  authored=a['lines'][0].startswith(('120 Stand ','120 GSE equipment bay ','120 R03 aircraft circulation'))
  mask=solids.buffer(.15) if authored else cleanup
  if a['geom'].intersects(mask):
   out=[];n=0
   for line,style in sampled_apt_segments(a):
    rem=line.difference(mask);n+=line.length-rem.length;out+=emit_apt_line(rem,style,'HF03 retained '+a['lines'][0][4:])
   if n>.05:rows+=out;paint.append(dict(name=a['lines'][0][4:],removed_m=n));continue
 rows+=a['lines']
rows+=['99'];(STAGE/'Earth nav data/apt.dat').write_text('\n'.join(rows)+'\n')

# Network exclusions are contained in this add-on. Remove lower-priority roads
# crossing aircraft pavement or the rebuilt processor walls; keep landside roads.
roads=pickle.loads((ROOT/'work/roads.pkl').read_bytes())
movement=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and int(a['parts'][1]) not in (3,4,5,15)])
airside=movement.intersection(unary_union([box(-1600,350,1400,850),box(-1600,-500,-1050,350)]))
bridgepave=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and 'bridge' in a['lines'][0].lower()])
airside=unary_union([airside,bridgepave])
roadmask=unary_union([solids.buffer(4),airside])
badroads=[s for s in roads if s['geom'].intersection(roadmask).length>3]
exclusions=[]
for seg in badroads:
 # Node-containing buffers ensure DSF's primitive containment rule catches
 # the selected full road segment, including elevated approaches.
 g=seg['geom'].buffer(8,cap_style=1,join_style=2,quad_segs=3).simplify(.5)
 for part in polygon_parts(g):
  ring=list(part.exterior.coords)[:-1];w,s,e,n=unproject(part).bounds
  exclusions.append(f'PROPERTY sim/exclude_net {w:.9f}/{s:.9f}/{e:.9f}/{n:.9f};'+','.join(f'{v:.9f}' for p in ring for v in ll(*p)))
# Prevent lower-priority parking/objects from growing through new building walls.
for part in polygon_parts(solids.buffer(5)):
 w,s,e,n=unproject(part).bounds;coords=','.join(f'{v:.9f}' for p in list(part.exterior.coords)[:-1] for v in ll(*p))
 for kind in ('obj','fac','str'):exclusions.append(f'PROPERTY sim/exclude_{kind} {w:.9f}/{s:.9f}/{e:.9f}/{n:.9f};'+coords)

# AEP supplies separate old gate glyph objects, grunge and paint without an
# airport-ID filter. Exclude these lower layers locally, leaving AEP installed.
aep=pickle.loads((ROOT/'work/aep.pkl').read_bytes())
overlaymask=cleanup.buffer(2,join_style=2)
renamezones=unary_union([box(-620,-70,-170,170),box(350,370,1000,610),box(-170,360,0,505)])
overlayex={k:[overlaymask] for k in ('obj','lin','pol')};overlayhits=[]
for i,e in enumerate(aep['entities']):
 res=e['resource'];g=e['geom']
 kind='obj' if e['kind']=='object' else 'lin' if res.endswith('.lin') else 'pol' if res.endswith('.pol') else None
 if not kind:continue
 selected=g.intersects(overlaymask)
 if '/Draped_Signs/Taxi_Small/' in res and g.intersects(renamezones):selected=True
 if not selected:continue
 points=[g] if kind=='obj' else [Point(p[:2]) for loop in e.get('loops',[]) for p in loop]
 if not points:continue
 # DSF excludes entire primitives by contained vertices, not by crossing.
 if not any(overlaymask.covers(p) for p in points):
  p=min(points,key=lambda p:p.distance(overlaymask))
  overlayex[kind].append(p.buffer(1.0))
 overlayhits.append(dict(index=i,resource=res,kind=kind,center=list(g.centroid.coords[0]),bounds=list(g.bounds)))
for kind,gs in overlayex.items():
 for part in polygon_parts(unary_union(gs)):
  # Exclusion rings have no holes; filling a hole only affects this local zone.
  poly=Polygon(part.exterior).simplify(.10,preserve_topology=True)
  w,s,e,n=unproject(poly).bounds;coords=','.join(f'{v:.9f}' for p in list(poly.exterior.coords)[:-1] for v in ll(*p))
  exclusions.append(f'PROPERTY sim/exclude_{kind} {w:.9f}/{s:.9f}/{e:.9f}/{n:.9f};'+coords)
(ROOT/'work/aep-exclusion-audit.json').write_text(json.dumps(overlayhits,indent=2))

# DSFTool's text reader truncates long property values. Partition long rings
# into triangles so each exclusion property survives compilation in full.
short_exclusions=[]
for entry in exclusions:
 if len(entry)<470:short_exclusions.append(entry);continue
 _,kind,data=entry.split(' ',2);extent,ring=data.split(';');nums=list(map(float,ring.split(',')))
 poly=Polygon([xy(*nums[i:i+2]) for i in range(0,len(nums),2)])
 for tri in constrained_delaunay_triangles(poly).geoms:
  if tri.area<.02:continue
  w,s,e,n=unproject(tri).bounds;coords=','.join(f'{v:.9f}' for p in list(tri.exterior.coords)[:-1] for v in ll(*p))
  row=f'PROPERTY {kind} {w:.9f}/{s:.9f}/{e:.9f}/{n:.9f};'+coords
  assert len(row)<470;short_exclusions.append(row)
exclusions=short_exclusions

# Hangar: retain the correct open side and interior, add modest structural detail.
interior=next(e for e in d['entities'] if e['resource']=='lib/airport/hangars/flat/parts/interior_01.fac')
ig=interior['geom'];origin=list(ig.centroid.coords[0]);shell=nm.Mesh('United_Maintenance_Exterior')
pts=[np.array(p) for p in list(orient(ig,sign=1).exterior.coords)[:-1]]
for a,b in zip(pts,pts[1:]+pts[:1]):
 length=np.linalg.norm(b-a);unit=(b-a)/length;normal=np.array([unit[1],-unit[0]])
 east=(a[0]+b[0])/2>ig.bounds[2]-2
 if east:
  shell.face([(*a,20.8),(*b,20.8),(*b,22),(*a,22)],'metal')
  for t in (0,length):shell.box(*(a+unit*t),0,.7,.7,22,'hvac')
 else:
  shell.face([(*a,0),(*b,0),(*b,22),(*a,22)],'metal')
  # Vertical metal battens and low concrete plinth, no invented logo/windows.
  shell.link(a,b,.18,0,1.0,'concrete')
  for t in np.arange(.7,length,.9):
   p=a+unit*t+normal*.065;shell.link(p-unit*.075,p+unit*.075,.10,1,21.7,'hvac')
  shell.link(a+normal*.06,b+normal*.06,.14,21.5,21.8,'hvac')
shell.flat(ig,22,'roof')
for x in np.arange(ig.bounds[0]+2,ig.bounds[2]-1,3):
 shell.extrude(ig.intersection(box(x-.04,ig.bounds[1],x+.04,ig.bounds[3])),22,22.07,'white','white')
newmodel=shell.write(STAGE/'objects/United_Maintenance_Exterior.obj',origin)
scene['models']=[newmodel if pathlib.Path(m['path']).stem=='United_Maintenance_Exterior' else dict(m,path=str(STAGE/'objects'/pathlib.Path(m['path']).name)) for m in scene['models']]
(ROOT/'work/scene-hf03.json').write_text(json.dumps(scene,indent=2))

head=[l for l in d['head'] if l.strip() and not l.startswith(('#','FILTER','DIVISIONS','HEIGHTS'))]
head+=exclusions;body=[]
for i,e in enumerate(d['entities']):
 if i not in discard:body+=replaced.get(i,e['lines'])
source=STAGE/'Sources/modified-south-scenery.txt';source.write_text('\n'.join(head+['DIVISIONS 32','FILTER 0']+body)+'\n')
tool=W/'xptools-24-5/tools/DSFTool.exe';dst=STAGE/'Earth nav data/+20-100/+29-096.dsf'
for args in [('--text2dsf',source,dst),('--dsf2text',dst,ROOT/'work/roundtrip-south.txt')]:
 p=subprocess.run([str(tool),*map(str,args)],capture_output=True,text=True);print(p.stdout,p.stderr);p.check_returncode()
stats['removed old glyph polygons']=len(discard)-len(deleted)
report=dict(status='STAGED - NOT INSTALLED',jetway_count=116,new_parked_jetways=32,cleanup=dict(stats),removed_identifiers=removed_signs,deleted=deleted,paint_changes=paint,road_segments_excluded=len(badroads),road_segments=[dict(head=s['head'],points=s['points']) for s in badroads],exclusion_count=len(exclusions),hangar_detail='Interpreted metal battens, plinth, edge trim and roof seams; east doorway retained',ea_barriers='Unchanged; remaining red row at -95.313975,29.99105 is EA, east side, not the reopened 15L west corridor')
report['conflicting_aep_primitives']=dict(collections.Counter(e['kind'] for e in overlayhits))
report['service_paths']=dict(rerouted_original_edges=servicefix['affected_original_edges'],new_nodes=len(servicefix['new_nodes']),moved_existing_nodes=servicefix['moved_nodes'],total_service_edges=588+len(servicefix['new_nodes']))
(ROOT/'HF03_Changes.json').write_text(json.dumps(report,indent=2))
(ROOT/'work/cleanup-mask.json').write_text(json.dumps(dict(apron=mapping(apron),landside=mapping(landside),roadmask=mapping(roadmask))))
print(json.dumps({k:v for k,v in report.items() if k not in ('deleted','paint_changes','road_segments','removed_identifiers')},indent=2))
