"""Meaningful exported-scene checks; not simulator acceptance."""
from pathlib import Path
import importlib.util,sys,json,math,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict,deque
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r27',ROOT/'source/build_r27.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;np=b.np;box=b.box;Point=b.Point;Line=b.Line;union=b.union;P=b.PACK
E=json.loads((P/'Build_Evidence.json').read_text())['r27'];checks=[];measure={}
def check(name,v):
    checks.append(dict(name=name,passed=bool(v)))
    if not v:
        (b.OUT/'Validation_Failure.json').write_text(json.dumps(dict(checks=checks,measurements=measure),indent=2));raise AssertionError(name)
ds=g.ag.parse_dsf(b.QA/'R27_Roundtrip.txt');src=g.ag.parse_dsf(b.QA/'R27_South.txt');ap=g.ag.parse_apt(P/'Earth nav data/apt.dat')
active={q['resource']:q for q in ds['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
key=lambda q:(q['kind'],q['resource'],q.get('param'))
check('Compiled scene entity counts',Counter(map(key,src['entities']))==Counter(map(key,ds['entities'])))
from shapely.strtree import STRtree
group=defaultdict(list)
for q in ds['entities']:group[key(q)].append(q)
trees={k:STRtree([q['geom'] for q in vv]) for k,vv in group.items()};used=defaultdict(set);drifts=[]
for q in src['entities']:
    if q['geom'].is_empty:continue
    k=key(q);near=[(q['geom'].hausdorff_distance(group[k][int(i)]['geom']),int(i)) for i in trees[k].query(q['geom'].buffer(.26)) if int(i) not in used[k]]
    if not near:check('Missing DSF geometry '+q['resource'],False)
    d,i=min(near);used[k].add(i);drifts.append(d)
measure['compiled_max_coordinate_error_m']=max(drifts);check('Compiled coordinates within 0.25m',max(drifts)<.25)
refs={q.get('name') for q in ET.parse(P/'sam.xml').findall('datarefs/dataref')}
for rel in active:
    rr=[r.split() for r in (P/rel).read_text().splitlines()];vv=[r for r in rr if r and r[0]=='VT'];ids=[int(x) for r in rr if r and r[0] in ['IDX','IDX10'] for x in r[1:]];counts=next(r for r in rr if r and r[0]=='POINT_COUNTS')
    check('OBJ structure '+Path(rel).stem,int(counts[1])==len(vv) and int(counts[4])==len(ids) and all(0<=i<len(vv) for i in ids) and all(int(r[1])+int(r[2])<=len(ids) and int(r[2])%3==0 for r in rr if r and r[0]=='TRIS'))
    check('OBJ assets '+Path(rel).stem,all((P/rel).parent.joinpath(' '.join(r[2:] if r[0]=='TEXTURE_DRAPED_NORMAL' else r[1:])).is_file() for r in rr if r and r[0].startswith('TEXTURE')) and all(x in refs for x in re.findall(r'nrt/kiah/[^\s]+',(P/rel).read_text())))
allowed={'Build_Evidence.json','Earth nav data/apt.dat','Earth nav data/+20-100/+29-096.dsf','objects/nrt_test/r25_jet_center.obj','objects/nrt_test/r25_jetway_portals.obj','objects/nrt_test/ramp_safety.obj'}
changed=[r for r,h in b.snapshot(b.OLD).items() if b.sha(P/r)!=h];measure['changed_predecessor_files']=changed
check('Only scoped predecessor files changed',set(changed)==allowed)
for f in ['sam.xml','opensam.xml']:
    root=ET.parse(P/f).getroot();dr=root.findall('datarefs/dataref');gui=root.findall('gui/checkbox')
    check(f+' retains six default-open controls',len(dr)==len(gui)==6 and all([(a.get('t'),a.get('v')) for a in q.findall('animation')][0]==('0','1') for q in dr))
check('All aircraft and heli starts unchanged',[q['lines'] for q in ap if q['code'] in [102,1300]]==[q['lines'] for q in b.APT if q['code'] in [102,1300]])
check('All aircraft guidance unchanged',[q['lines'] for q in ap if q['code'] in [120,1202,1204]]==[q['lines'] for q in b.APT if q['code'] in [120,1202,1204]])
oldjet=[q for q in b.APT if q['code']==1500];newjet=[q for q in ap if q['code']==1500];moved=[]
for old,new in zip(oldjet,newjet):
    if old['lines']==new['lines']:continue
    a,c=old['parts'],new['parts'];xy=g.ag.xy(float(a[2]),float(a[1]));xy2=g.ag.xy(float(c[2]),float(c[1]));moved.append(xy2)
    check('Native jetway translated east only',abs(xy2[0]-xy[0]-4)<.01 and abs(xy2[1]-xy[1])<.01 and a[3:]==c[3:])
check('Only both NRT9 native jetways moved',len(oldjet)==len(newjet)==119 and len(moved)==2)
for ident in ['9A','9B']:
    rel='objects/nrt_test/r25_fixed_'+ident+'.obj';q=b.PLACEMENTS[rel];a=active[rel]
    check('Fixed connection '+ident+' moved with arm',a['geom'].distance(Point(q['geom'].x+4,q['geom'].y))<.25)
    j=next(j for j in E['jetways'] if j['id']==ident);check('Arm '+ident+' at evidence anchor',min(Point(p).distance(Point(j['base'])) for p in moved)<.25)
    oldj=next(j for j in b.EVIDENCE['jetways'] if j['id']==ident)
    check('Facade portal '+ident+' moved equally',abs(j['root'][0]-oldj['root'][0]-4)<.001)

def vertices(rel,pack=P):
    rows=(pack/rel).read_text().splitlines();v=np.array([list(map(float,r.split()[1:])) for r in rows if r.startswith('VT ')]);ids=np.array([int(a) for r in rows if r.startswith(('IDX ','IDX10 ')) for a in r.split()[1:]])
    return v,ids
rel='objects/nrt_test/ramp_safety.obj';v0,i0=vertices(rel,b.OLD);v1,i1=vertices(rel);d=v1-v0;movedv=np.max(np.abs(d),axis=1)>1e-6
check('Only two red movement boxes shifted',int(movedv.sum())==72 and np.allclose(d[movedv,0],4) and np.max(np.abs(d[movedv,1:]))<1e-6 and np.allclose(v1[movedv,6],.40625) and np.array_equal(i0,i1))
for name,geom in b.FLOORS.items():
    rel='objects/nrt_test/r27_'+name+'_floor.obj';v,ids=vertices(rel);q=active[rel];en=v[ids][:,[0,2]]*[1,-1]+[q['geom'].x,q['geom'].y]
    area=union([b.r25.Polygon(t) for t in en.reshape(-1,3,2)])
    check(name+' modeled dry floor covers sheltered area',area.symmetric_difference(geom).area<geom.length*.25 and np.allclose(v[:,1],.03))
    txt=(P/rel).read_text();check(name+' floor uses MH material without wet overlay','buildings.dds' in txt and 'ATTR_draped' not in txt and 'WEATHER' not in txt)
rel='objects/nrt_test/r27_sheltered_guidance.obj';v,ids=vertices(rel);check('Guidance visible above modeled floor',v[:,1].min()>.03 and v[:,1].max()<.05)
oldlights=[r for r in (b.OLD/'objects/nrt_test/r25_jet_center.obj').read_text().splitlines() if r.startswith('LIGHT_PARAM ')]
newlights=[r for r in (P/'objects/nrt_test/r25_jet_center.obj').read_text().splitlines() if r.startswith('LIGHT_PARAM ')]
check('All reviewed HQ and canopy light settings retained',oldlights==newlights)
mast=[q for q in ds['entities'] if q['kind']=='object' and q['resource']==b.MAST_RESOURCE];oldmast=[q for q in b.BASE['entities'] if q['kind']=='object' and q['resource']==b.MAST_RESOURCE]
check('Exactly one matching stock mast added',len(mast)==len(oldmast)+1)
pos=min(mast,key=lambda q:q['geom'].distance(Point(b.MAST)))['geom']
asset=Path('X:/X-Plane 12/Resources/default scenery/airport scenery/Common_Elements/Lighting/flood_1_led_24m_omni.obj')
vv=np.array([list(map(float,r.split()[1:4])) for r in asset.read_text().splitlines() if r.startswith('VT')]);base=vv[vv[:,1]<10];foot=box(pos.x+base[:,0].min(),pos.y-base[:,2].max(),pos.x+base[:,0].max(),pos.y-base[:,2].min())
walk=Line(b.r25.WALK).buffer(.8,cap_style=2,join_style=2).union(Line(b.r25.GA_WALK).buffer(.8,cap_style=2));heli=b.r25.HELI_RESERVE
nrt9=b.EVIDENCE['r26']['nrt9_nosewheel'];n9=box(nrt9[0]-79.75/2,nrt9[1]-3,nrt9[0]+79.75/2,nrt9[1]+70);n8=box(2842.527-44.84/2,435,2842.527+44.84/2,490);n11=box(2667,379.5,2717,445.5)
measure['mast_clearance_m']={n:foot.distance(o) for n,o in {'HQ':b.r25.FOOT,'walk':walk,'NRT9':n9,'NRT11':n11,'heli':heli}.items()}
check('Mast base outside building, walking lane and aircraft',min(measure['mast_clearance_m'].values())>1)
# The requested HQ-corner pole supersedes the old two-pad mast layout.
# Report its actual setback; do not invent an FAA setback or reuse the
# earlier wall-fixture test's 50 m threshold as a pole requirement.
measure['mast_helipad_center_distance_m']=pos.distance(Point(b.r25.HELI))
measure['mast_height_m']=float(vv[:,1].max())
check('Requested corner mast stays outside preserved helipad reserve',not foot.intersects(heli))
check('No new beacon or elevated helipad fixture',not any('beacon' in q['resource'].lower() for q in ds['entities'] if q not in b.BASE['entities']))

# Actual native airport graph, including shared junction nodes.
nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in ap if q['code']==1201};adj=defaultdict(set)
for q in ap:
    if q['code']!=1206:continue
    a,c=map(int,q['parts'][1:3]);assert a in nodes and c in nodes
    adj[a].add(c);adj[c].add(a)
seen={919};queue=deque([919])
while queue:
    for n in adj[queue.popleft()]-seen:seen.add(n);queue.append(n)
check('All new service nodes connected to inherited network',set(n['id'] for n in E['service_nodes'])<=seen)
crew={q['id'] for q in b.APT if q['code']==1201 and 'NRT arrivals' in q['lines'][0]};check('No airside link through public car park',not crew.intersection(seen))
for row,ee in E['replaced_edges'].items():
    a,c=map(int,row.split()[1:3]);old=Line([nodes[a],nodes[c]]);new=union([Line([nodes[e['a']],nodes[e['b']]]) for e in ee]);check('Inherited road preserved '+str(a)+'-'+str(c),old.hausdorff_distance(new)<.01)
paved=union([q['geom'] for q in ap if q['code'] in [100,110]]+[q['geom'] for q in ds['entities'] if q['kind']=='polygon' and '/pavement/' in q['resource']])
newlines=union([Line([nodes[e['a']],nodes[e['b']]]) for e in E['service_edges']]);road=newlines.buffer(3,cap_style=2,join_style=2)
measure['new_road_unpaved_m2']=road.difference(paved).area;check('Full new service road width lies on pavement',measure['new_road_unpaved_m2']<.1)
obstacles={'NRT9':n9,'NRT8':n8,'NRT11':n11,'HQ':b.r25.FOOT,'canopy':b.r25.CANOPY,'heli':heli,'walk':walk,'hangars':box(2417,284,2513,592)}
for q in ap:
    if q['code']==1300 and q.get('name') in ['NRT1','NRT2','NRT3','NRT4','NRT5','NRT6','NRT7']:
        x,y=q['geom'].x,q['geom'].y;large=q['name'] in ['NRT5','NRT6','NRT7'];length,span,nose=(76.3,68.4,5) if large else (52.,41.1,4.)
        obstacles[q['name']]=box(x+nose-length,y-span/2,x+nose,y+span/2)
measure['new_road_clearance_m']={n:road.distance(o) for n,o in obstacles.items()};check('New road avoids occupied stands and structures',min(measure['new_road_clearance_m'].values())>2.5)
for p in E['vehicle_parking']+E['vehicle_destinations']:
    x,y=p['xy'];stall=box(x-5,y-2.1,x+10,y+2.1)
    check('Paved parking '+p['name'],paved.buffer(.05).covers(stall) and min(stall.distance(o) for o in obstacles.values())>2.5)
    nearest=min(seen,key=lambda n:Point(nodes[n]).distance(Point(p['xy'])))
    check('Paved network entry '+p['name'],Line([p['xy'],nodes[nearest]]).buffer(2.1).difference(paved).area<.1)
check('Seven local native service vehicles and matching holding destination',len(E['vehicle_parking'])==7 and len(E['vehicle_destinations'])==1 and all(p['type'] in E['vehicle_destinations'][0]['types'].split('|') for p in E['vehicle_parking']))
check('All inherited service parking and destinations retained',[q['lines'] for q in ap if q['code'] in [1400,1401] and 'NRT R27' not in q['lines'][0]]==[q['lines'] for q in b.APT if q['code'] in [1400,1401]])

exports={}
for folder in [Path('X:/X-Plane 12/Resources/default scenery'),Path('X:/X-Plane 12/Custom Scenery/MisterX_Library'),Path('X:/X-Plane 12/Custom Scenery/openSAM_Library')]:
    for f in folder.rglob('library.txt'):
        for line in f.read_text(errors='replace').splitlines():
            r=line.split()
            if len(r)>2 and r[0] in ['EXPORT','EXPORT_BACKUP','EXPORT_EXTEND','EXPORT_EXCLUDE']:exports.setdefault(r[1],f.parent/' '.join(r[2:]))
            if len(r)>3 and r[0] in ['EXPORT_RATIO','EXPORT_SEASON']:exports.setdefault(r[2],f.parent/' '.join(r[3:]))
unresolved=[r for r in {q['resource'] for q in ds['entities']} if not ((P/r).is_file() or r in exports and exports[r].is_file())];measure['unresolved']=unresolved
check('All assets resolve without AEP',not unresolved)
for fn,folder in [('R26_Hashes.json',b.OLD),('Published_Hashes.json',ROOT.parents[1]/'distribution/NRT_KIAH_Updater_R01/scenery')]:check('Protected '+fn,b.snapshot(folder)==json.loads((ROOT/'reference'/fn).read_text()))
report=dict(passed=len(checks),checks=checks,measurements=measure,runtime_tested=False,limitations=[E['service_limitation'],E['weather_limitation'],'Both jetways translated with their stand; actual add-on docking needs testing. Stock mast night appearance/performance needs testing.'])
(b.OUT/'Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=len(checks),measurements=measure),indent=2))
