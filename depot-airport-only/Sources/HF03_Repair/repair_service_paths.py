"""Reroute only service edges affected by the corrected parked jetways."""
import pathlib,sys,pickle,json,ast,math,heapq
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair';sys.path.insert(0,str(PREV/'work'))
from sign_groups import *
from shapely.geometry import MultiPoint
from shapely.ops import nearest_points
from route_common import smooth_pavement
from shapely.prepared import prep
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
plan,d,apt,scene=pickle.loads((ROOT/'work/current.pkl').read_bytes());newjets,_,planes=pickle.loads((ROOT/'work/jetways.pkl').read_bytes())
LIB=pathlib.Path(r'X:\X-Plane 12\Resources/default scenery/airport scenery');out=[];templates={};animation_counts={}
tree=ast.parse((PREV/'work/prepare_previews.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('addmesh','rotation','trans','lerp','active_jetway')],type_ignores=[]),'native helpers','exec'))
ground=[]
for a,j in zip(newjets,scene['jetways']):
 out.clear();active_jetway(a,'After',0);v=np.array(out[-1]['vertices']);ground.append(MultiPoint(v[(v[:,2]>.05)&(v[:,2]<3.5),:2]).convex_hull)
parked=unary_union(ground)
nodes={a['parts'][4]:xy(float(a['parts'][2]),float(a['parts'][1])) for a in apt if a['code']==1201}
edges=[a for a in apt if a['code']==1206]
solids=unary_union([v['geom'] for v in plan['models'].values()]+[plan['buildings']['iah-ta-2'],plan['buildings']['iah-tc-2']])
pavement=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and int(a['parts'][1]) not in (0,3,4,5,13,15)])
pillars=unary_union([Point(j['base']).buffer(.65) for j in scene['jetways']])
obs=unary_union([parked,solids,pillars,*planes]).buffer(2.35,quad_segs=3,join_style=2)
free=pavement.buffer(-2.35).difference(obs)
safe_pavement=prep(pavement.buffer(-2.30))
affected=[i for i,a in enumerate(edges) if LineString([nodes[a['parts'][1]],nodes[a['parts'][2]]]).distance(parked)<2.2]
affectednodes={n for i in affected for n in edges[i]['parts'][1:3]}
moved={}
for n in affectednodes:
 p=Point(nodes[n])
 if not free.covers(p):
  q=nearest_points(p,free.buffer(-.1))[1]
  assert p.distance(q)<25,(n,p.distance(q))
  moved[n]=list(q.coords[0]);nodes[n]=tuple(q.coords[0])
affected=sorted(set(affected)|{i for i,a in enumerate(edges) if any(n in moved for n in a['parts'][1:3])})

def path_between(a,b):
 direct=LineString([a,b])
 region=free.intersection(direct.buffer(70,cap_style=3,join_style=2))
 innerbad=prep(obs.buffer(-.005))
 def visible(p,q):
  line=LineString([p,q])
  return not innerbad.intersects(line) and safe_pavement.covers(line)
 if visible(a,b):return [a,b]
 points=[tuple(a),tuple(b)]
 for poly in polygon_parts(region):
  points+=list(poly.exterior.coords)[:-1]
  for ring in poly.interiors:points+=list(ring.coords)[:-1]
 points=list(dict.fromkeys((round(x,5),round(y,5)) for x,y in points))
 # Keep exact endpoints to avoid rounding onto an obstacle.
 points[0]=tuple(a);points[1]=tuple(b)
 n=len(points);dist={0:0};prev={};todo=[(math.dist(a,b),0,0)];finished=set()
 print('Finding local service path; candidates',n,flush=True)
 while todo:
  _,cost,i=heapq.heappop(todo)
  if i in finished:continue
  if i==1:
   ids=[1]
   while ids[-1]!=0:ids.append(prev[ids[-1]])
   return [points[k] for k in reversed(ids)]
  finished.add(i)
  for j in range(n):
   if j in finished or j==i:continue
   dc=math.dist(points[i],points[j]);new=cost+dc
   if new>=dist.get(j,float('inf')):continue
   if visible(points[i],points[j]):
    dist[j]=new;prev[j]=i;heapq.heappush(todo,(new+math.dist(points[j],b),new,j))
 raise RuntimeError('No safe service detour: '+str((a,b)))

replacements={};extra=[];paths=[];nextid=max(map(int,nodes))+1
for i in affected:
 e=edges[i];n0,n1=e['parts'][1:3];path=path_between(nodes[n0],nodes[n1]);ids=[n0]
 for p in path[1:-1]:
  node=str(nextid);nextid+=1;lon,lat=ll(*p);extra.append(f'1201 {lat:.9f} {lon:.9f} both {node} HF03 service detour');ids.append(node)
 ids.append(n1);rows=[f'1206 {a} {b} '+ ' '.join(e['parts'][3:]) for a,b in zip(ids,ids[1:])]
 replacements[e['lines'][0]]=rows
 paths.append(dict(old=e['lines'][0],new=rows,points=[list(p) for p in path],clearance_m=LineString(path).distance(parked),old_length=LineString([xy(float(next(x for x in apt if x['code']==1201 and x['parts'][4]==n)['parts'][2]),float(next(x for x in apt if x['code']==1201 and x['parts'][4]==n)['parts'][1])) for n in (n0,n1)]).length,new_length=LineString(path).length))
 print('REROUTED',n0,n1,'points',len(path),'clearance',round(paths[-1]['clearance_m'],2),flush=True)
report=dict(moved_nodes=moved,new_nodes=extra,replacements=replacements,paths=paths,affected_original_edges=len(affected))
(ROOT/'work/service-repair.json').write_text(json.dumps(report,indent=2))
(ROOT/'work/service-obstacles.pkl').write_bytes(pickle.dumps((ground,obs,free)))
print('Service detours ready',len(paths),'edges',len(extra),'new nodes')
