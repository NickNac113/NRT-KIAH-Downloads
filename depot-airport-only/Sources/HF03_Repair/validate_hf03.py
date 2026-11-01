import pathlib,sys,json,pickle,ast,math,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
sys.path.insert(0,str(PREV/'work'))
from sign_groups import *
from prepare_hf02 import audit,sha
from route_common import smooth_pavement
from shapely.geometry import MultiPoint
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03';LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
LIB=LIVE.parents[1]/'Resources/default scenery/airport scenery'
plan,before,oldapt,oldscene=pickle.loads((ROOT/'work/current.pkl').read_bytes())
apt=parse_apt(STAGE/'Earth nav data/apt.dat');dsf=parse_dsf(ROOT/'work/roundtrip-south.txt')
scene=json.loads((ROOT/'work/scene-hf03.json').read_text());details=json.loads((PREV/'HF02_Detail_Validation.json').read_text())
newjets,jshapes,planes=pickle.loads((ROOT/'work/jetways.pkl').read_bytes())
checks=[]
def test(name,value,detail=None):
 checks.append(dict(check=name,passed=bool(value),detail=detail));print(('PASS ' if value else 'FAIL ')+name,detail if detail is not None else '')
models=[audit(p) for p in (STAGE/'objects').glob('*.obj')]
test('All 38 custom models have outward clockwise faces without zero-area triangles',len(models)==38 and all(m['clockwise_outward']==m['triangles'] and not m['degenerate'] for m in models),dict(models=len(models),triangles=sum(m['triangles'] for m in models)))
codes={100,1000,1001,1002,1003,1004,1100,1110,1101,1202,1204,1205,1300,1301,1400,1401}
airnodes={n for a in apt if a['code']==1202 for n in a['parts'][1:3]}
test('Aircraft taxi routes/nodes, starts, runways, flow rules and service spawns remain byte-identical',[a['lines'] for a in apt if a['code'] in codes or (a['code']==1201 and a['parts'][4] in airnodes)]==[a['lines'] for a in oldapt if a['code'] in codes or (a['code']==1201 and a['parts'][4] in airnodes)],dict(collections.Counter(a['code'] for a in apt if a['code'] in {100,1300,1202,1206})))
jets=[a for a in apt if a['code']==1500];oldjets=[a for a in oldapt if a['code']==1500]
test('116 animated jetways remain, with all 84 retained jetways unchanged',len(jets)==116 and [a['lines'] for a in jets[32:]]==[a['lines'] for a in oldjets[32:]])
test('Only parked heading, extension and cabin heading change on the 32 rebuilt jetways',all(a['parts'][:6]==b['parts'][:6] and a['parts'][9:]==b['parts'][9:] for a,b in zip(jets[:32],oldjets[:32])))
bad=[]
for a in jets:
 s=a['parts'];lo,hi=[(11,23),(14,29),(17,38),(20,47)][int(s[5])%10];base=(float(s[6])-float(s[3])+180)%360-180;cabin=(float(s[8])-float(s[6])+180)%360-180
 if not(lo-.01<=float(s[7])<=hi+.01 and -60.01<=base<=60.01 and -90.01<=cabin<=.01):bad.append(a['lines'][0])
# Older retained arms can have historical parked attitudes; evaluate changes only.
test('All 32 repaired parking positions stay inside stock model motion limits',not any(a['lines'][0] in bad for a in jets[:32]),dict(retained_historical_records_outside_modeled_limits=sum(a['lines'][0] in bad for a in jets[32:])))
tree=ast.parse((PREV/'work/prepare_previews.py').read_text());out=[];templates={};animation_counts={}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('addmesh','rotation','trans','lerp','active_jetway')],type_ignores=[]),'native helpers','exec'))
hulls=[];lowhulls=[]
for i,a in enumerate(jets):
 out.clear();active_jetway(a,'After',i);v=np.array(out[-1]['vertices']);hulls.append(MultiPoint(v[v[:,2]>.3,:2]).convex_hull)
 lowhulls.append(MultiPoint(v[(v[:,2]>.05)&(v[:,2]<3.5),:2]).convex_hull)
planeunion=unary_union(planes)
clear=[h.distance(planeunion) for h in hulls[:32]]
test('Actual parked jetway meshes clear conservative aircraft envelopes by at least 4.4 m',min(clear)>=4.4,round(min(clear),3))
solids=unary_union([shape(g) for g in scene['model_outlines'].values()]+[plan['buildings']['iah-ta-2'],plan['buildings']['iah-tc-2']])
test('Repaired parked meshes do not intersect terminal buildings',all(g.distance(solids)>.15 for g in hulls[:32]),round(min(g.distance(solids) for g in hulls[:32]),3))
fixed=[LineString([j['door'],j['base']]).buffer(1.5,cap_style=2) for j in scene['jetways']]
conflicts=[(scene['jetways'][i]['name'],k) for i,g in enumerate(hulls[:32]) for k,h in enumerate(hulls) if i!=k and g.distance(h)<.3]
test('Repaired parked meshes clear every other moving arm',not conflicts,conflicts)
conflicts=[(scene['jetways'][i]['name'],scene['jetways'][k]['name']) for i,g in enumerate(hulls[:32]) for k,h in enumerate(fixed) if i!=k and g.distance(h)<.3]
test('Repaired parked meshes clear other authored fixed bridges',not conflicts,conflicts)
nodepos={a['parts'][4]:xy(float(a['parts'][2]),float(a['parts'][1])) for a in apt if a['code']==1201}
low=unary_union(lowhulls[:32]);sedges=[a for a in apt if a['code']==1206]
service_clear=min(LineString([nodepos[a['parts'][1]],nodepos[a['parts'][2]]]).distance(low) for a in sedges)
test('All service centerlines clear low parked jetway geometry by at least 2.2 m',service_clear>=2.2,round(service_clear,3))
stops=[Point(xy(float(a['parts'][2]),float(a['parts'][1]))) for a in apt if a['code'] in (1400,1401)]
test('All 119 service starts/destinations clear low parked jetway geometry',len(stops)==119 and min(p.distance(low) for p in stops)>=2.2,round(min(p.distance(low) for p in stops),3))
def components(data,restrict=None):
 edges=[a['parts'][1:3] for a in data if a['code']==1206];nodes={n for e in edges for n in e};adj={n:set() for n in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 groups=[]
 while nodes:
  todo=[nodes.pop()];group=set(todo)
  while todo:
   n=todo.pop()
   for b in adj[n]:
    if b in nodes:nodes.remove(b);todo.append(b);group.add(b)
  groups.append(frozenset(group if restrict is None else group.intersection(restrict)))
 return set(groups)
old_service_nodes={n for a in oldapt if a['code']==1206 for n in a['parts'][1:3]}
test('Service network connectivity is preserved through seven local detours',components(oldapt)==components(apt,old_service_nodes),dict(before_edges=588,after_edges=len(sedges)))
pavement=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and int(a['parts'][1]) not in (3,4,5,13)])
custom=unary_union([shape(g) for g in scene['model_outlines'].values()])
test('Continuous hard surface remains beneath the custom terminals',custom.difference(pavement.buffer(.01)).area<.1)
test('Current stand-label mesh and atlas remain unchanged',sha(STAGE/'objects/Current_Stand_Labels.obj')==sha(LIVE/'objects/Current_Stand_Labels.obj') and all(sha(p)==sha(LIVE/p.relative_to(STAGE)) for p in (STAGE/'textures').glob('*')))
mask=shape(json.loads((ROOT/'work/cleanup-mask.json').read_text())['apron'])
test('No inherited draped gate label remains inside the rebuilt apron zones',not any(e['geom'].intersects(mask) for e in dsf['entities'] if e['resource'].endswith(('DrapedLocSigns.pol','DrapedDirSigns.pol'))))
ex=collections.defaultdict(list)
for line in dsf['head']:
 if not line.startswith('PROPERTY sim/exclude_'):continue
 _,kind,data=line.split(' ',2);extent,*ring=data.split(';');kind=kind.split('_')[-1]
 if ring:
  nums=list(map(float,ring[0].split(',')));g=Polygon([xy(*nums[i:i+2]) for i in range(0,len(nums),2)])
 else:
  w,s,e,n=map(float,extent.split('/'));g=box(*xy(w,s),*xy(e,n))
 ex[kind].append(g)
invalid=[(k,round(g.area,7),g.wkt) for k,gs in ex.items() for g in gs if not g.is_valid or g.area<=.01]
test('All native exclusion polygons are valid and nonempty',not invalid,invalid[:5])
unions={k:unary_union(gs).buffer(.02) for k,gs in ex.items()}
aep=pickle.loads((ROOT/'work/aep.pkl').read_bytes());hits=json.loads((ROOT/'work/aep-exclusion-audit.json').read_text());miss=[]
for hit in hits:
 e=aep['entities'][hit['index']];points=[e['geom']] if hit['kind']=='obj' else [Point(p[:2]) for loop in e['loops'] for p in loop]
 if not any(unions[hit['kind']].covers(p) for p in points):miss.append(hit)
test('All targeted AEP glyphs, old paint and grunge have contained vertices for exclusion',not miss,dict(targets=len(hits),misses=len(miss)))
road_report=json.loads((ROOT/'HF03_Changes.json').read_text())['road_segments']
test('Every targeted lower-layer road segment has an excluded endpoint',len(road_report)>=7 and all(any(unions['net'].covers(Point(xy(*p[:2]))) for p in (r['points'][0],r['points'][-1])) for r in road_report),len(road_report))
test('Excluded AEP primitives stay within the Houston airport area',all(-4500<h['bounds'][0]<5500 and -4500<h['bounds'][1]<2500 and h['bounds'][2]<6000 and h['bounds'][3]<3000 for h in hits))
test('Native southern tile compiled and decoded with KIAH airport filter',len(dsf['entities'])>10000 and 'PROPERTY sim/filter/aptid KIAH' in dsf['head'])
oldbars=[e for e in before['entities'] if 'red' in e['resource'].lower() and 'barrier' in e['resource'].lower()]
newbars=[e for e in dsf['entities'] if 'red' in e['resource'].lower() and 'barrier' in e['resource'].lower()]
bardiff=max((a['geom'].distance(b['geom']) for a,b in zip(oldbars,newbars)),default=0)
test('Northern tile is byte-identical and east-side EA barricades remain in place',sha(STAGE/'Earth nav data/+30-100/+30-096.dsf')==sha(LIVE/'Earth nav data/+30-100/+30-096.dsf') and len(oldbars)==len(newbars) and all(a['resource']==b['resource'] for a,b in zip(oldbars,newbars)) and bardiff<.06,dict(count=len(newbars),max_compile_quantization_m=bardiff))
test('Live installed package is unchanged',all(sha(LIVE/p)==h for p,h in json.loads((ROOT/'live_before.json').read_text()).items()))
test('Scenery order remains unchanged',sha(LIVE.parent/'scenery_packs.ini')=='c1c9bce079f40d1d3f238ffec043cdb8b7dc773875e30764c0745d46ad3c6bd8')
report=dict(revision='R03 HF03',status='STAGED - NOT INSTALLED',passed=sum(c['passed'] for c in checks),total=len(checks),checks=checks,models=models,parked_clearance={j['name']:round(c,3) for j,c in zip(scene['jetways'],clear)},runtime_pending=['Parked jetway clearance using actual aircraft spawn and terrain','Automatic docking and retraction at rebuilt and retained gates','AEP overlay suppression and road traffic in X-Plane','Ground services, pushback and taxi behavior'])
(ROOT/'HF03_Validation.json').write_text(json.dumps(report,indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
