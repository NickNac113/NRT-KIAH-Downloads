import pathlib,sys,pickle,json,ast,math,copy
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
sys.path.insert(0,str(PREV/'work'))
from sign_groups import *
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
from layout_plan import heading_vec,aircraft_outline
from shapely.geometry import MultiPoint
from shapely.affinity import rotate,translate
LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
LIB=LIVE.parents[1]/'Resources/default scenery/airport scenery'
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03'
tree=ast.parse((PREV/'work/prepare_previews.py').read_text())
out=[];templates={};animation_counts={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('addmesh','rotation','trans','lerp','active_jetway')],type_ignores=[]),'helper','exec'))
plan,d,apt,scene=pickle.loads((ROOT/'work/current.pkl').read_bytes())
jets=[a for a in apt if a['code']==1500]
primary=[r for r in plan['new'] if not r.get('alternative')]+plan['details']
planes=[]
for r in primary:
 f=heading_vec(r['heading']);right=np.array([f[1],-f[0]]);p=np.array(r['pos'])
 # Include a 6 m forward nose allowance and 44.5 m class-C body (A321 check).
 length=44.5 if r['size']=='C' else 74
 fus=Polygon([p+right*x+f*y for x,y in [(-2.6,6),(2.6,6),(2.6,-length+6),(-2.6,-length+6)]])
 planes.append(unary_union([aircraft_outline(p,r['heading'],r['size']),fus]))
planeunion=unary_union(planes)
solids=unary_union([v['geom'] for v in plan['models'].values()]+[plan['buildings']['iah-ta-2'],plan['buildings']['iah-tc-2']])
fixed=[LineString([j['door'],j['base']]).buffer(1.5,cap_style=2) for j in scene['jetways']]
def shape_for(a):
 out.clear();active_jetway(a,'After',0);v=np.array(out[-1]['vertices']);return MultiPoint(v[v[:,2]>.3,:2]).convex_hull
retained=unary_union([shape_for(a) for a in jets[32:]])
nodes={a['parts'][4]:xy(float(a['parts'][2]),float(a['parts'][1])) for a in apt if a['code']==1201}
service=unary_union([LineString([nodes[a['parts'][1]],nodes[a['parts'][2]]]) for a in apt if a['code']==1206])
servicestops=unary_union([Point(xy(float(a['parts'][2]),float(a['parts'][1]))) for a in apt if a['code'] in (1400,1401)])
canonical={};groundcanonical={}
for size in range(4):
 for length in ([11,14,17,20][size]+.15,):
  a={'parts':['1500',str(LAT0),str(LON0),'0','1',str(size),'0',str(length),'315']}
  canonical[size]=shape_for(a)
  v=np.array(out[-1]['vertices']);groundcanonical[size]=MultiPoint(v[(v[:,2]>.05)&(v[:,2]<3.5),:2]).convex_hull
chosen=[];report=[];newjets=[]
for i,(a,j,r) in enumerate(zip(jets,scene['jetways'],primary)):
 assert j['name']==r['name']
 size=int(a['parts'][5]);length=[11,14,17,20][size]+.15
 base=j['base'];install=float(a['parts'][3]);otherfixed=unary_union([g for k,g in enumerate(fixed) if k!=i]);others=unary_union([retained,*chosen])
 options=[]
 for delta in range(-60,61,3):
  heading=(install+delta)%360
  g=translate(rotate(canonical[size],-heading,origin=(0,0)),*base)
  ground=translate(rotate(groundcanonical[size],-heading,origin=(0,0)),*base)
  clear=g.distance(planeunion);bd=g.distance(solids);fd=g.distance(otherfixed);md=g.distance(others)
  sd=ground.distance(service);sp=ground.distance(servicestops)
  # Select aircraft-safe positions first; repair affected service paths separately.
  if clear>=2 and bd>=.2 and fd>=.35 and md>=.35:
   score=abs(delta)*.05-max(0,min(clear,5))*1.5
   options.append((score,heading,g,clear,bd,fd,md,sd,sp))
 if not options:
  print('NO SAFE POSITION',j['name'],flush=True);raise SystemExit(1)
 _,heading,g,clear,bd,fd,md,sd,sp=min(options,key=lambda x:x[0]);chosen.append(g)
 b=copy.deepcopy(a);b['parts'][6]=f'{heading:.3f}';b['parts'][7]=f'{length:.3f}';b['parts'][8]=f'{(heading-45)%360:.3f}';b['lines']=[' '.join(b['parts'])];newjets.append(b)
 report.append(dict(gate=j['name'],old_record=a['lines'][0],new_record=b['lines'][0],aircraft_clearance_m=clear,building_clearance_m=bd,neighbor_fixed_clearance_m=fd,neighbor_moving_clearance_m=md,service_centerline_clearance_m=sd,service_stop_clearance_m=sp))
 print(j['name'],round(length,2),round((heading-install+180)%360-180,1),'air gap',round(clear,2),flush=True)
 j.update(parked_heading=heading,length=length,cabin_heading=(heading-45)%360,end=(np.array(base)+heading_vec(heading)*length).tolist())
(ROOT/'work/jetways.json').write_text(json.dumps(report,indent=2))
(ROOT/'work/scene-hf03.json').write_text(json.dumps(scene,indent=2))
(ROOT/'work/jetways.pkl').write_bytes(pickle.dumps((newjets,chosen,planes)))
