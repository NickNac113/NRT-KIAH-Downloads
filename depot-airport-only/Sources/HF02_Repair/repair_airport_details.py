"""R03 HF02: repair retained facades, jetways, apron overlays and identifiers.
This only writes to the HF02 stage, never the installed airport.
"""
from sign_groups import *
import importlib.util, hashlib, math, copy, subprocess, csv
from shapely.geometry.polygon import orient
from PIL import Image,ImageDraw,ImageFont
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF02'
LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
spec=importlib.util.spec_from_file_location('repaired_mesh',STAGE/'Sources/Build/native_mesh.py')
nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(nm)
from layout_plan import heading_vec,aircraft_outline,bearing
plan,dsf,apt=pickle.loads((ROOT/'work/context.pkl').read_bytes())
scene=json.loads((W/'generated/scene.json').read_text())
solids=unary_union([m['geom'] for m in plan['models'].values()])
primary=[r for r in plan['new'] if not r.get('alternative')]+plan['details']
apron=unary_union([plan['zones'][n] for n in ('B_North','D_West')]+
                 [aircraft_outline(r['pos'],r['heading'],r['size']).buffer(7) for r in primary])
# Include the full new B apron: the earlier deletion rectangle stopped short of
# the northern taxiway and eastern side of the new fanned stands.
apron=unary_union([apron,box(-650,350,-125,700)])
cleanup=unary_union([apron,solids.buffer(1)])
stats={};changes=[];discard=set();replace={};ground_labels=[]

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit_area(index,param,g):
    """DSF areas require CCW exterior / CW holes, unlike OBJ8 triangles."""
    rows=[]
    for part in polygon_parts(polys_only(make_valid(g))):
        if part.area<.05:continue
        q=orient(part,sign=1);rows += [f'BEGIN_POLYGON {index} {param} 2']
        for ring in [q.exterior,*q.interiors]:
            rows.append('BEGIN_WINDING')
            for x,y in list(ring.coords)[:-1]:
                lon,lat=ll(x,y);rows.append(f'POLYGON_POINT {lon:.9f} {lat:.9f}')
            rows.append('END_WINDING')
        rows.append('END_POLYGON')
    return rows

def apt_area(g,name,surface=50):
    rows=[]
    for part in polygon_parts(polys_only(make_valid(g))):
        if part.area<.05:continue
        p=orient(part,sign=1);rows.append(f'110 {surface} 0.25 0.0 {name}')
        for ring in [p.exterior,*p.interiors]:
            coords=list(ring.coords)[:-1]
            for j,(x,y) in enumerate(coords):
                lon,lat=ll(x,y);rows.append(f'{113 if j==len(coords)-1 else 111} {lat:.8f} {lon:.8f}')
    return rows

def sampled_apt_segments(a):
    """Preserve each edge's paint/light codes while flattening Bezier curves."""
    ring=[];out=[]
    for row in a['lines'][1:]:
        s=row.split();code=int(s[0]);p=np.array(xy(float(s[2]),float(s[1])))
        curved=code in (112,114,116);h=np.array(xy(float(s[4]),float(s[3]))) if curved else p
        ring.append((p,h,s[5:] if curved else s[3:]))
        if code in (113,114,115,116):
            closed=code in (113,114);pairs=zip(ring,ring[1:]+(ring[:1] if closed else []))
            for (p,h,style),(q,k,_) in pairs:
                if not style:continue
                steps=max(1,min(100,math.ceil((np.linalg.norm(h-p)+np.linalg.norm(q-h)+np.linalg.norm(k-q))/2)))
                ps=[(1-t)**3*p+3*(1-t)**2*t*h+3*(1-t)*t*t*(2*q-k)+t**3*q for t in np.linspace(0,1,steps+1)]
                if math.dist(ps[0],ps[-1])>.001:out.append((LineString(ps),style))
            ring=[]
    return out

def emit_apt_line(g,style,name):
    rows=[]
    for line in ([g] if g.geom_type=='LineString' else getattr(g,'geoms',[])):
        if line.geom_type!='LineString' or line.length<.05:continue
        coords=list(line.coords);rows.append('120 '+name)
        for i,(x,y) in enumerate(coords):
            lon,lat=ll(x,y);last=i==len(coords)-1
            rows.append(f'{115 if last else 111} {lat:.8f} {lon:.8f}'+('' if last else ' '+' '.join(style)))
    return rows

def dsf_path(e):
    a=[list(map(float,l.split()[1:])) for l in e['lines'] if l.startswith('POLYGON_POINT')]
    points=[];closed=e['resource'].endswith('.lin') and e['param']==1
    for i in range(len(a) if closed else len(a)-1):
        v=a[i];u=a[(i+1)%len(a)];p=np.array(xy(*v[:2]));q=np.array(xy(*u[:2]))
        h=np.array(xy(*v[2:4])) if len(v)==4 else p;k=np.array(xy(*u[2:4])) if len(u)==4 else q
        for t in np.linspace(0,1,max(2,math.ceil(np.linalg.norm(q-p)/2)),endpoint=False):
            points.append((1-t)**3*p+3*(1-t)**2*t*h+3*(1-t)*t*t*(2*q-k)+t**3*q)
    if a:points.append(np.array(xy(*(a[0] if closed else a[-1])[:2])))
    return LineString(points) if len(points)>1 else LineString()

def emit_dsf_line(e,g):
    rows=[];param=0 if e['resource'].endswith('.lin') else e['param']
    for line in ([g] if g.geom_type=='LineString' else getattr(g,'geoms',[])):
        if line.geom_type!='LineString' or line.length<.05:continue
        rows += [f'BEGIN_POLYGON {e["index"]} {param} 2','BEGIN_WINDING']
        for x,y in line.coords:
            lon,lat=ll(x,y);rows.append(f'POLYGON_POINT {lon:.9f} {lat:.9f}')
        rows += ['END_WINDING','END_POLYGON']
    return rows

# Replace obsolete, decoded gate identifiers at their existing paint locations.
# Taxiway/direction signs are not selected merely by proximity.
renamed=[r for r in plan['ramps'] if r.get('old_name') and r['old_name']!=r['name'] and r['name'].startswith(('Gate B','Gate D'))]
label_positions={};label_replacements=[]
for g in groups(dsf):
    matches=[r for r in renamed if r['old_name'].removeprefix('Gate ')==g['text'] and r['geom'].distance(g['geom'])<160]
    if matches:
        r=min(matches,key=lambda r:r['geom'].distance(g['geom']));new=r['name'].removeprefix('Gate ').replace(' wide','W').replace(' A380','A380')
        discard.update(g['indices']);label_replacements.append(dict(old=g['text'],new=new,center=list(g['geom'].centroid.coords[0])))
        # Several old wide positions have duplicate labels; use the nearest one.
        if r['name'] not in label_positions or r['geom'].distance(g['geom'])<label_positions[r['name']][1]:
            label_positions[r['name']]=(g['geom'].centroid.coords[0],r['geom'].distance(g['geom']))
    elif g['text']=='3' and g['geom'].centroid.distance(Point(461.1,454.1))<2:
        discard.update(g['indices']);label_positions['Gate D9']=(g['geom'].centroid.coords[0],67)
        label_replacements.append(dict(old='orphan D3 digit',new='D9',center=list(g['geom'].centroid.coords[0])))
    elif g['text']=='D9B' and g['geom'].centroid.distance(Point(815,481))<3:
        discard.update(g['indices']);label_replacements.append(dict(old='D9B retired alternative',new=None,center=list(g['geom'].centroid.coords[0])))

# Fix only newly reversed facades, not deliberately directed open fences/jetways.
original_lines={tuple(e['lines']) for e in plan['dsf']['entities']}
facade_fixes=[]
for i,e in enumerate(dsf['entities']):
    if not e['resource'].endswith('.fac') or tuple(e['lines']) in original_lines:continue
    if not any(t in e['resource'] for t in ('term_building','term_bridge','Garage','term_roof')):continue
    points=[l for l in e['lines'] if l.startswith('POLYGON_POINT')]
    if len(points)<3:continue
    xypts=[xy(*map(float,l.split()[1:3])) for l in points]
    area=sum(x*v-u*y for (x,y),(u,v) in zip(xypts,xypts[1:]+xypts[:1]))/2
    if area>=0:continue
    # All generated clip nodes have selector 0; retain it on the reversed edge.
    assert all(len(l.split())==4 and float(l.split()[3])==0 for l in points)
    replace[i]=[e['lines'][0],'BEGIN_WINDING',*reversed(points),'END_WINDING','END_POLYGON']
    facade_fixes.append(dict(resource=e['resource'],area_m2=abs(area),center=list(e['geom'].centroid.coords[0])))

# Keep authored new equipment, remove inherited details inside rebuilt aprons.
new_item_points=[Point(x['pos']) for x in scene['equipment']]
cleanup_counts={};remaining=[]
for i,e in enumerate(dsf['entities']):
    if i in discard:continue
    g=e['geom'];res=e['resource'];reason=None
    if e['kind']=='object' and not res.startswith('objects/') and cleanup.contains(g):
        protected=any(g.distance(p)<.05 for p in new_item_points)
        if not protected and any(k in res.lower() for k in ('ramp_equipment','fuel_hydrant','vehicles/','parking_items','parking/','barriers/','lawn_tracks')):reason='obsolete apron equipment'
    elif e['kind']=='polygon' and res.endswith(('.lin','.str')):
        if g.intersects(cleanup):
            path=dsf_path(e);clipped=path.difference(cleanup)
            if path.length-clipped.length>.1:
                replace[i]=emit_dsf_line(e,clipped);cleanup_counts['clipped inherited painted/object strings']=cleanup_counts.get('clipped inherited painted/object strings',0)+1
    elif res.endswith('.pol') and g.intersects(cleanup) and ('pavement/' in res or 'terrain_FX/' in res or 'safety_area_' in res):
        # Existing pavement overlays were retained on top of the replacement
        # apron. Trim only the simple XY/heading placements; keep explicit-UV
        # artwork intact for individual review rather than corrupt its UVs.
        dim=int(e['lines'][0].split()[3]);param=e['param']
        if dim==2 and param!=65535:
            replace[i]=emit_area(e['index'],param,g.difference(cleanup));cleanup_counts['trimmed old apron surface polygons']=cleanup_counts.get('trimmed old apron surface polygons',0)+1
    if reason:cleanup_counts[reason]=cleanup_counts.get(reason,0)+1;discard.add(i)
    else:remaining.append(e)

# Restore the animated portions stripped from the Gateway's compiled scenery.
compiled_apt=parse_apt(W/'KIAH-99761/compiled/KIAH_Scenery_Pack/Earth nav data/apt.dat')
# The downloaded compiled source still uses an older 1-based tunnel enum.
# Use the same placements from this X-Plane installation's current Global
# Airports, whose emitted size codes are 0-based and match installed artwork.
global_rows=[];in_kiah=False
with (LIVE.parents[1]/'Global Scenery/Global Airports/Earth nav data/apt.dat').open(encoding='utf-8',errors='replace') as f:
    for line in f:
        s=line.split()
        if s and s[0] in ('1','16','17'):
            if in_kiah:break
            in_kiah=len(s)>4 and s[4]=='KIAH'
        if in_kiah:global_rows.append(line.rstrip())
global_source=ROOT/'work/current-global-KIAH-apt.dat'
global_source.write_text('I\n1200 Version\n'+'\n'.join(global_rows)+'\n99\n')
current_jets=[a for a in parse_apt(global_source) if a['code']==1500]
fixed_facades=[e for e in remaining if 'Jetways/' in e['resource']]
restored=[];rejected=[];enum_updates=[]
for a in compiled_apt:
    if a['code']!=1500:continue
    s=a['parts'];point=Point(xy(float(s[2]),float(s[1])))
    nearest=min(fixed_facades,key=lambda e:e['geom'].distance(point));dist=nearest['geom'].distance(point)
    if dist<1:
        modern=min(current_jets,key=lambda j:Point(xy(float(j['parts'][2]),float(j['parts'][1]))).distance(point))
        matched=Point(xy(float(modern['parts'][2]),float(modern['parts'][1]))).distance(point)<.02
        if matched:
            assert all(abs(float(s[k])-float(modern['parts'][k]))<.02 for k in (3,4,6,7,8))
            restored.append(modern)
        else:
            # Seven additional source arms are absent from the optimized global
            # airport. Keep their placements, applying the same 1-based ->
            # 0-based size conversion confirmed by 100 of the 104 matches.
            # The other four current records explicitly use smaller models.
            modern=copy.deepcopy(a);modern['parts'][5]=str(int(s[5])-1)
            modern['lines']=[' '.join(modern['parts'])];restored.append(modern)
        enum_updates.append(dict(old=s[5],current=modern['parts'][5],location=s[1:3],matched_current_global=matched))
    else:rejected.append(dict(record=a['lines'][0],nearest_surviving_base_m=dist))
assert len(restored)==84

# Repair custom ground labels without moving the existing texture tiles.
nm.SIGN_TILES.update(json.loads((W/'generated/sign_tiles.json').read_text()))
label_specs=[]
for r in primary:
    label_specs.append(dict(name=r['name'],pos=(np.array(r['pos'])-heading_vec(r['heading'])*24).tolist(),heading=r['heading'],width=6,height=2.6,source='new stand lead-in'))
for r in renamed:
    name=r['name'].removeprefix('Gate ').replace(' wide','W').replace(' A380','A380')
    point=label_positions.get(r['name'],((np.array(r['geom'].coords[0])-heading_vec(r['heading'])*40).tolist(),0))[0]
    label_specs.append(dict(name=name,pos=list(point),heading=r['heading'],width=6 if len(name)>3 else 4.5,height=2.0,source='retained stand renumbering'))
for r in [r for r in plan['new'] if r.get('alternative')]:
    label_specs.append(dict(name=r['name'],pos=(np.array(r['pos'])-heading_vec(r['heading'])*24).tolist(),heading=r['heading'],width=5,height=2.0,source='manual MARS alternative'))
for item in label_specs:
    if item['name']=='D16A380':
        item['pos']=(np.array(item['pos'])-heading_vec(item['heading'])*4).tolist()
missing=sorted({s['name'] for s in label_specs}-nm.SIGN_TILES.keys())
im=Image.open(LIVE/'textures/terminal_atlas.png').copy();lit=Image.open(LIVE/'textures/terminal_atlas_LIT.png').copy();draw=ImageDraw.Draw(im);ld=ImageDraw.Draw(lit)
occupied={(int(v[0])//128,(int(v[1])-1024)//64) for v in nm.SIGN_TILES.values()}
for name in missing:
    col,row=next((c,r) for r in range(16) for c in range(16) if (c,r) not in occupied);occupied.add((col,row));x=col*128;y=1024+row*64
    tile=(x+2,y+2,x+126,y+62);nm.SIGN_TILES[name]=tile
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30 if len(name)>3 else 44)
    draw.rectangle(tile,fill=(23,30,34),outline=(236,186,61),width=3);draw.text((x+64,y+32),name,fill=(246,207,95),font=font,anchor='mm');ld.text((x+64,y+32),name,fill=(142,123,72),font=font,anchor='mm')
im.save(STAGE/'textures/terminal_atlas.png');lit.save(STAGE/'textures/terminal_atlas_LIT.png')
mesh=nm.Mesh('Current_Stand_Labels')
for item in label_specs:nm.ground_sign(mesh,item['pos'],item['heading'],item['name'],item['width'],item['height'])
mesh.write(STAGE/'objects/Current_Stand_Labels.obj',(0,0),True)

# United Maintenance: the source contains an interior-only facade, including in
# the locally installed Global Airports. Add an exterior shell around that exact
# footprint, retaining the open east doorway and existing interior framework.
interior=next(e for e in dsf['entities'] if e['resource']=='lib/airport/hangars/flat/parts/interior_01.fac')
ig=interior['geom'];origin=list(ig.centroid.coords[0]);shell=nm.Mesh('United_Maintenance_Exterior')
pts=[np.array(p) for p in list(orient(ig,sign=1).exterior.coords)[:-1]]
for a,b in zip(pts,pts[1:]+pts[:1]):
    if (a[0]+b[0])/2>ig.bounds[2]-2:
        shell.face([(*a,20.8),(*b,20.8),(*b,22),(*a,22)],'metal')
    else:shell.face([(*a,0),(*b,0),(*b,22),(*a,22)],'metal')
shell.flat(ig,22,'roof')
hangar_model=shell.write(STAGE/'objects/United_Maintenance_Exterior.obj',origin)
scene['models'].append(hangar_model)

# Update native apt paint and add a solid base under custom buildings/tunnels.
paint_removed=0;paint_clipped=0;out=[];paint_delta=[]
new_foundation=unary_union([solids.buffer(.6)]+[LineString([j['door'],j['base']]).buffer(1.7,cap_style=2) for j in scene['jetways']])
for a in apt:
    if a['code']==99:continue
    if a['code']==1500:
        s=list(a['parts']);s[6]=s[3] # parked tunnel heading is ABSOLUTE, not relative
        out.append(' '.join(s));continue
    if a['code']==120 and a.get('geom') is not None:
        authored=a['lines'][0].startswith(('120 Stand ','120 GSE equipment bay ','120 R03 aircraft circulation'))
        mask=solids.buffer(.15) if authored else cleanup
        if a['geom'].intersects(mask):
            rebuilt=[];old_len=0;new_len=0
            for path,style in sampled_apt_segments(a):
                cut=path.difference(mask);old_len+=path.length;new_len+=cut.length
                rebuilt+=emit_apt_line(cut,style,'HF02 retained '+a['lines'][0][4:])
            if old_len-new_len>.05:
                out+=rebuilt;paint_clipped+=bool(rebuilt);paint_removed+=not bool(rebuilt);paint_delta.append(dict(name=a['lines'][0][4:],removed_m=old_len-new_len));continue
    out+=a['lines']
out+=apt_area(new_foundation,'HF02 terminal and fixed-tunnel foundation')
out += [l for a in restored for l in a['lines']]+['99']
(STAGE/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n',encoding='utf-8')

# Serialize the revised DSF retaining all library table indexes.
head=[l for l in dsf['head'] if l.strip() and not l.startswith(('#','FILTER','DIVISIONS','HEIGHTS'))]
idx=len(dsf['objects']);head.append('OBJECT_DEF objects/United_Maintenance_Exterior.obj')
body=[]
for i,e in enumerate(dsf['entities']):
    if i not in discard:body+=replace.get(i,e['lines'])
lon,lat=ll(*origin);body.append(f'OBJECT {idx} {lon:.9f} {lat:.9f} 0')
source=STAGE/'Sources/modified-south-scenery.txt';source.write_text('\n'.join(head+['DIVISIONS 32','FILTER 0']+body)+'\n')
dst=STAGE/'Earth nav data/+20-100/+29-096.dsf'
proc=subprocess.run([str(W/'xptools-24-5/tools/DSFTool.exe'),'--text2dsf',str(source),str(dst)],capture_output=True,text=True);proc.check_returncode();(ROOT/'work/dsf-compile.log').write_text(proc.stdout+proc.stderr)
check=ROOT/'work/roundtrip-south.txt'
proc=subprocess.run([str(W/'xptools-24-5/tools/DSFTool.exe'),'--dsf2text',str(dst),str(check)],capture_output=True,text=True);proc.check_returncode()

# Regression guard: route data, aircraft starts, flows, and runway definitions are
# unchanged; only paint, foundations, and the restored jetway records differ.
reparsed=parse_apt(STAGE/'Earth nav data/apt.dat')
codes={1,100,1000,1001,1002,1003,1004,1100,1110,1101,1201,1202,1204,1205,1206,1300,1400,1401}
assert [a['lines'] for a in apt if a['code'] in codes]==[a['lines'] for a in reparsed if a['code'] in codes]
assert sum(a['code']==1500 for a in reparsed)==116
assert hashfile(STAGE/'Earth nav data/+30-100/+30-096.dsf')==hashfile(LIVE/'Earth nav data/+30-100/+30-096.dsf')
assert all(hashfile(LIVE/p)==h for p,h in json.loads((ROOT/'live_before.json').read_text()).items())
scene['models']=[dict(m,path=str(STAGE/'objects'/pathlib.Path(m['path']).name)) for m in scene['models']]
(ROOT/'work/scene-hf02.json').write_text(json.dumps(scene,indent=2))
(ROOT/'work/sign-tiles-hf02.json').write_text(json.dumps(nm.SIGN_TILES,indent=2))
report=dict(status='STAGED - NOT INSTALLED',restored_animated_jetways=len(restored),total_animated_jetways=116,obsolete_jetways_not_restored=len(rejected),
    facade_winding_repairs=len(facade_fixes),facade_repairs=facade_fixes,ground_identifier_count=len(label_specs),label_replacements=label_replacements,
    cleanup=cleanup_counts,old_paint_blocks_removed=paint_removed,old_paint_blocks_clipped=paint_clipped,paint_delta=paint_delta,
    foundation_m2=new_foundation.area,hangar_shell=dict(origin=origin,footprint_m2=ig.area,height=22,open_side='east',basis='Existing 20m interior-only facade; interpreted 22m external shell'),
    aircraft_routes_unchanged=True,service_routes_unchanged=True,starts_and_flows_unchanged=True,installed_files_unchanged=True,
    restored_records=[a['lines'][0] for a in restored],restored_record_source='Installed current Global Airports KIAH apt.dat; original compiled base selection',
    current_size_code_updates=enum_updates,new_jetway_absolute_heading_repairs=32,jetways_not_restored=rejected,ground_labels=label_specs)
(ROOT/'HF02_Detail_Validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('facade_repairs','label_replacements','paint_delta','restored_records','jetways_not_restored','ground_labels')},indent=2))
