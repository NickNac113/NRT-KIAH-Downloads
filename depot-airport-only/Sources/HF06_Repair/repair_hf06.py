"""Successor repair. No writes to Custom Scenery or third-party libraries."""
import sys,pathlib,pickle,json,struct,importlib.util
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF05_Repair\work')
from hf05_common import *
from route_common import network,aircraft_outline,adjacency,reachable
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\outputs\KIAH_2026-10-24_Review_R03_HF05')
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
plan,apt,dsfs=pickle.loads((ROOT/'work/inventory.pkl').read_bytes())
scene=json.loads((ROOT.parent/'KIAH_R03_HF05_Repair/work/scene-hf03.json').read_text())
spec=importlib.util.spec_from_file_location('nm06',SOURCE/'Sources/Build/native_mesh.py');nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(nm)
changes={'revision':'KIAH R03 HF06','jetway_joints':[],'EA_barriers':[]}
def obj_parts(rows):
 return ([l for l in rows if l.startswith('VT ')],[int(v) for l in rows if l.startswith(('IDX ','IDX10 ')) for v in l.split()[1:]])
for j in scene['jetways']:
 name=j['name'];src=SOURCE/'objects'/f'bridge_{name}.obj';old=src.read_text().splitlines();vs,ix=obj_parts(old)
 # A stationary circular rotunda surrounds the native apt1500 pivot. The
 # stock moving tunnel starts 0.93m in front of that pivot at neutral pitch.
 # Radius 1.70m closes the rear joint through +/-60 degrees of rotation.
 m=nm.Mesh('HF06 rotunda '+name);circle=Point(0,0).buffer(1.70,quad_segs=12)
 m.extrude(circle,3.65,4.30,'metal',None)
 m.extrude(circle,4.30,6.95,'glass',None)
 m.extrude(circle.buffer(.07),6.95,7.20,'metal','metal')
 # Close the underside; no new ground-level column or clearance obstruction.
 for tri in constrained_delaunay_triangles(circle).geoms:
  pts=list(orient(tri,sign=-1).exterior.coords)[:3];m.face([(x,y,3.65) for x,y in pts],'metal',nm.uv_rect(nm.TILES['metal'])[:3])
 temp=ROOT/'work/rotunda.obj';m.write(temp);nv,ni=obj_parts(temp.read_text().splitlines())
 newix=ix+[n+len(vs) for n in ni]
 header=[l for l in old[:next(i for i,l in enumerate(old) if l.startswith('VT '))] if not l.startswith('POINT_COUNTS')]
 header.append(f'POINT_COUNTS {len(vs)+len(nv)} 0 0 {len(newix)}')
 rows=header+vs+nv+['IDX '+str(n) for n in newix]+['ATTR_LOD 0 14000',f'TRIS 0 {len(newix)}','']
 (STAGE/src.relative_to(SOURCE)).write_text('\n'.join(rows),encoding='utf-8')
 changes['jetway_joints'].append(dict(gate=name,pivot=j['base'],radius_m=1.70,height_m=[3.65,7.20],original_vertices_preserved=len(vs),added_vertices=len(nv)))

def atom(k,p):return k+struct.pack('<I',len(p)+8)+p
def atoms(data,start=0,end=None):
 end=len(data) if end is None else end
 while start<end:
  size=struct.unpack_from('<I',data,start+4)[0];assert size>=8 and start+size<=end
  yield data[start:start+4],data[start+8:start+size]
  start+=size
 assert start==end
def prune_commands(data,entities,remove):
 out=[];i=0;ei=0;definition=None;counts=collections.Counter();history=[]
 u16=lambda off:struct.unpack_from('<H',data,off)[0]
 while i<len(data):
  start=i;op=data[i];i+=1;counts[op]+=1;indices=None;history.append((start,op,data[start:start+20].hex()))
  fixed={1:2,2:4,3:1,4:2,5:4,6:1,7:2,8:4,10:4,13:6,16:0,17:1,18:9,25:4,28:4,31:4}
  if op in fixed:i+=fixed[op]
  elif op in (9,11,23,24,26,27,29,30):i+=1+data[i]*(4 if op in (11,24,27,30) else 2)
  elif op==12:i+=3+data[i+2]*2
  elif op==15:i+=3+(data[i+2]+1)*2
  elif op==14:
   n=data[i+2];i+=3
   for _ in range(n):i+=1+data[i]*2
  elif op in (32,33,34):
   width={32:1,33:2,34:4}[op];length=int.from_bytes(data[i:i+width],'little');i+=width+length
  else:raise ValueError(('unknown DSF opcode',op,start,history[-12:]))
  assert i<=len(data)
  if op in (3,4,5):definition=int.from_bytes(data[start+1:i],'little')
  if op==7:indices=[u16(start+1)]
  if op==8:indices=list(range(u16(start+1),u16(start+3)))
  if indices is not None:
   keep=[]
   for n in indices:
    assert entities[ei]['kind']=='object' and entities[ei]['index']==definition,(ei,definition)
    if ei not in remove:keep.append(n)
    ei+=1
   if keep==indices:out.append(data[start:i])
   else:out.extend(b'\x07'+struct.pack('<H',n) for n in keep)
  else:
   if op in (12,13,14,15):
    assert entities[ei]['kind']=='polygon' and entities[ei]['index']==definition,(ei,definition);ei+=1
   out.append(data[start:i])
 assert ei==len(entities),(ei,len(entities))
 return b''.join(out),dict(counts)

ea=box(2630,725,2672,1805)
for tile,d in dsfs:
 remove={i for i,e in enumerate(d['entities']) if e['kind']=='object' and e['resource'].endswith('/red_3m.obj') and ea.contains(e['geom'])}
 assert len(remove)==11
 src=next((SOURCE/'Earth nav data').rglob(tile+'.dsf'));raw=src.read_bytes();assert raw[:8]==b'XPLNEDSF' and hashlib.md5(raw[:-16]).digest()==raw[-16:]
 output=[]
 for key,payload in atoms(raw,12,len(raw)-16):
  if key==b'SDMC':payload,counts=prune_commands(payload,d['entities'],remove)
  output.append(atom(key,payload))
 body=raw[:12]+b''.join(output);(STAGE/src.relative_to(SOURCE)).write_bytes(body+hashlib.md5(body).digest())
 rt=ROOT/'work'/f'{tile}-roundtrip.txt';dsf_decode(STAGE/src.relative_to(SOURCE),rt)
 new=parse_dsf(rt);expected=[e['lines'] for i,e in enumerate(d['entities']) if i not in remove]
 assert expected==[e['lines'] for e in new['entities']]
 assert [l for l in d['head'] if not l.startswith('#')]==[l for l in new['head'] if not l.startswith('#')]
 changes['EA_barriers'].append(dict(tile=tile,removed=[dict(index=i,resource=d['entities'][i]['resource'],xy=list(d['entities'][i]['geom'].coords[0])) for i in sorted(remove)],all_other_placements_exact=True))

# EA already has pavement, centerline and taxiway signs. Its missing aircraft
# route is restored between existing NB, EC, ED and EE junctions. This is the
# user's explicit simulator/VATSIM variant, not a real-world reopening claim.
nodes,edges=network(apt);newroutes=[]
for a,b in [(264,338),(338,349),(349,345)]:
 assert not any(e['code']==1202 and {e['a'],e['b']}=={a,b} for e in edges)
 newroutes.append(f'1202 {a} {b} twoway taxiway_E EA')
rawapt=(SOURCE/'Earth nav data/apt.dat').read_text();rows=rawapt.splitlines();at=next(i for i,l in enumerate(rows) if l.startswith('1206 '));rows[at:at]=newroutes
(STAGE/'Earth nav data/apt.dat').write_text('\n'.join(rows)+'\n',encoding='utf-8')
changes['EA_routes']=newroutes
changes['EA_variant']='User requested open EA for VATSIM. Category E, bidirectional simulator route between NB/EC/ED/EE. Real-world closure remains acknowledged; controller instructions govern online.'

# Audit B paint against the actual R03 category-C route and modeled stands.
bpaint=next(a for a in apt if a['lines'][0]=='120 R03 aircraft circulation 106')['geom']
planes=[(a['name'],aircraft_outline(a['geom'].coords[0],a['heading'],a.get('rampmeta',['1301','C'])[1])) for a in apt if a['code']==1300 and a['kind']!='misc']
nearest=sorted([(n,g.distance(bpaint)) for n,g in planes],key=lambda v:v[1])[:5]
route=unary_union([LineString([nodes[e['a']],nodes[e['b']]]) for e in edges if e['code']==1202 and (e['a'],e['b']) in [(856,857),(857,858),(858,328)]])
changes['B15_B17_audit']=dict(paint_matches_route_max_deviation_m=bpaint.hausdorff_distance(route),route_category='C (36m maximum wingspan)',nearest_parked_aircraft_to_centerline_m=nearest,remaining_wingtip_margin_for_36m_span_m=min(v[1] for v in nearest)-18,real_world_paint_verified=False,action='Alignment retained pending a current surveyed apron chart. This is a modeled circulation line, not certified current real-world paint.')
(ROOT/'HF06_Changes.json').write_text(json.dumps(changes,indent=2))
print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in changes.items()},indent=2))
