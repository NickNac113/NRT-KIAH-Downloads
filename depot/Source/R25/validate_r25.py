"""Validate exported geometry and preserved operations; no simulator acceptance."""
from pathlib import Path
import importlib.util,sys,ast,json,math,hashlib,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r25',ROOT/'source/build_r25.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;np=b.np;Image=b.Image;P=b.PACK
tree=ast.parse((g.LEGACY/'obj_reader.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'))
from shapely.strtree import STRtree
checks=[];measures={}
def check(n,v):
    checks.append(dict(name=n,passed=bool(v)))
    if not v:
        (ROOT/'output/Validation_Failure.json').write_text(json.dumps(dict(checks=checks,measurements=measures),indent=2));raise AssertionError(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=g.ag.parse_dsf(ROOT/'qa/R25_South.txt');dsf=g.ag.parse_dsf(ROOT/'qa/R25_Roundtrip.txt');old=b.BASE
key=lambda q:(q['kind'],q['resource'],q.get('param'))
check('Compiled DSF retains all resource and entity counts',Counter(map(key,src['entities']))==Counter(map(key,dsf['entities'])))
groups=defaultdict(list)
for q in dsf['entities']:groups[key(q)].append(q)
trees={k:STRtree([q['geom'] for q in qs]) for k,qs in groups.items()};used=defaultdict(set);drift=[];unmatched=[]
for q in src['entities']:
    if q['geom'].is_empty:continue
    k=key(q);c=[(q['geom'].hausdorff_distance(groups[k][int(i)]['geom']),int(i)) for i in trees[k].query(q['geom'].buffer(.26)) if int(i) not in used[k]]
    if not c:unmatched.append(q['resource']);continue
    v,i=min(c);used[k].add(i);drift.append(v)
measures['dsf_drift_m']=max(drift)
check('Every exported entity matches within 0.25 m after compilation',not unmatched and max(drift)<.25)
active={q['resource']:q for q in dsf['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
def mesh(name,vals=None):
    q=active['objects/nrt_test/'+name+'.obj'];return readobj(P/q['resource'],[q['geom'].x,q['geom'].y],vals=vals,full=True)
oldapt=g.ag.parse_apt(b.OLD/'Earth nav data/apt.dat');ap=g.ag.parse_apt(P/'Earth nav data/apt.dat')
def untouched(q):return not (q['code']==1300 and q['name']=='NRT11' or q['code']==120 and 'NRT11' in q['lines'][0])
check('Airport apt.dat unchanged except NRT11 start and guidance',[q['lines'] for q in ap if untouched(q)]==[q['lines'] for q in oldapt if untouched(q)])
check('All 119 native jetways preserved exactly',sum(q['code']==1500 for q in ap)==119)
check('Service vehicle route, types and destinations preserved',[q['lines'] for q in ap if q['code'] in [1201,1206,1400,1401]]==[q['lines'] for q in oldapt if q['code'] in [1201,1206,1400,1401]])
starts=[q for q in ap if q['code']==1300 and q['name'].startswith('NRT')]
check('Only the 15 main NRT starts remain',len(starts)==len({q['name'] for q in starts})==15 and not any('TEST' in q['name'] for q in starts))
q=next(q for q in starts if q['name']=='NRT11')
check('NRT11 remains nose east at revised stop',q['heading']==90 and q['geom'].distance(b.Point(b.GA_NG))<.015)
check('No random AI fleet assigned to the length-limited bay','1301 F none' in q['lines'])
for filename in ['sam.xml','opensam.xml']:
    check(filename+' byte-identical to working R24',sha(P/filename)==sha(b.OLD/filename))
    root=ET.parse(P/filename).getroot();dr=root.findall('datarefs/dataref');gui=root.findall('gui/checkbox')
    check(filename+' six independent default-open door controls',len(dr)==len(gui)==6 and all([(k.get('t'),k.get('v')) for k in d.findall('animation')][0]==('0','1') for d in dr))
refs={q.get('name') for q in ET.parse(P/'sam.xml').findall('datarefs/dataref')}
bad=[]
for rel in active:
    text=(P/rel).read_text();rows=[r.split() for r in text.splitlines()];vv=[r for r in rows if r and r[0]=='VT'];ids=[int(i) for r in rows if r and r[0] in ['IDX','IDX10'] for i in r[1:]]
    ct=next(r for r in rows if r and r[0]=='POINT_COUNTS')
    check('Valid OBJ geometry '+Path(rel).stem,int(ct[1])==len(vv) and int(ct[4])==len(ids) and all(0<=i<len(vv) for i in ids) and all(0<=int(r[1]) and int(r[1])+int(r[2])<=len(ids) and int(r[2])%3==0 for r in rows if r and r[0]=='TRIS'))
    check('Valid animations '+Path(rel).stem,all(v in refs for v in re.findall(r'nrt/kiah/[^\s]+',text)) and sum(r==['ANIM_begin'] for r in rows)==sum(r==['ANIM_end'] for r in rows))
    for r in rows:
        if r and r[0].startswith('TEXTURE'):
            name=' '.join(r[2:] if r[0]=='TEXTURE_DRAPED_NORMAL' else r[1:]);check('Texture exists '+Path(rel).stem+' '+r[0],(P/rel).parent.joinpath(name).exists())
for n in ['r25_jet_center','r25_jetway_portals','r25_fixed_8','r25_fixed_9A','r25_fixed_9B','r25_human_details']:
    txt=(P/'objects/nrt_test'/f'{n}.obj').read_text();check('PBR metalness shader enabled '+n,'NORMAL_METALNESS' in txt and 'TEXTURE_NORMAL' in txt)
nm=np.asarray(Image.open(P/'textures/nrt_test/r25_materials_NML.png'))
check('Normal map includes nonmetal surfaces and selective bronze metalness',nm[:,:,2].min()==0 and nm[:,:,2].max()>150 and np.ptp(nm[:,:,3])>100)
check('Ground IDs use own UV atlas',all('r25_ground_ids.dds' in (P/'objects/nrt_test'/f'{n}.obj').read_text() for n in ['r25_ground_ids','r25_access_ids']))
check('Building signs use separate identity atlas','r25_identity.dds' in (P/'objects/nrt_test/r25_identity.obj').read_text())
check('Removed old building, narrow stand label and full-apron wear placements',not any(Path(r).stem in ['r24_jet_center','r24_identity','r24_access_ids','r24_access_paint','r24_ground_ids','r24_ramp_details','ramp_wear','taxi_wear','fixed_8','fixed_9A','fixed_9B'] for r in active))
check('No broad dirt or skid overlays in campus',not any(q['geom'].intersects(b.box(2409,274,3157,765)) and any(v in q['resource'] for v in ['taxiway_dirt/center','Ground_Textures/Skid_Marks','Ground_Textures/Dirt','grunge_size_']) for q in dsf['entities']))
surfaces=[q for q in dsf['entities'] if q['kind']=='polygon' and '/pavement/' in q['resource'] and b.box(2409,274,3157,765).covers(q['geom'].representative_point())]
check('Native bases are new concrete and plain asphalt',surfaces and all(q['resource'].endswith(('/new.pol','/plain.pol')) for q in surfaces))
check('No small duplicate slab patch under canopy or former GA bay',not any(q['geom'].area<5000 and '/concrete' in q['resource'] and (q['geom'].intersection(b.CANOPY).area>1500 or q['geom'].intersection(b.box(2664,398,2706,440)).area>1200) for q in surfaces))
# Public stock + declared libraries only, with AEP absent from this resolver.
exports={}
for folder in [Path('X:/X-Plane 12/Resources/default scenery'),Path('X:/X-Plane 12/Custom Scenery/MisterX_Library'),Path('X:/X-Plane 12/Custom Scenery/openSAM_Library')]:
    for file in folder.rglob('library.txt'):
        for line in file.read_text(errors='replace').splitlines():
            r=line.split()
            if len(r)>2 and r[0] in ['EXPORT','EXPORT_BACKUP','EXPORT_EXTEND','EXPORT_EXCLUDE']:exports.setdefault(r[1],file.parent/' '.join(r[2:]))
            if len(r)>3 and r[0] in ['EXPORT_RATIO','EXPORT_SEASON']:exports.setdefault(r[2],file.parent/' '.join(r[3:]))
unresolved=[r for r in {q['resource'] for q in dsf['entities']} if not ((P/r).exists() or r in exports and exports[r].exists())]
measures['unresolved_resources']=unresolved
check('All DSF resources resolve without AEP',not unresolved)
check('No AEP resource path in runtime scenery',not any('aep' in r.lower() for r in {q['resource'] for q in dsf['entities']}))
# Exported geometry around each real fixed-link / native-jetway root.
facade=mesh('r25_jet_center')[0];portals=mesh('r25_jetway_portals')[0]
origin=active['objects/nrt_test/r25_jet_center.obj']['geom'];dx=origin.x-2674;dy=origin.y-330
portal_results=[]
for j in b.EVIDENCE['jetways']:
    q=active['objects/nrt_test/r25_fixed_'+j['id']+'.obj'];gap=q['geom'].distance(b.Point(j['base']))
    check('Fixed/native jetway base alignment '+j['id'],gap<.25)
    area=b.box(j['root'][0]+dx-1.55,3.85,j['root'][0]+dx+1.55,6.80)
    wall_tris=[b.Polygon(v[:,[0,2]]) for v in facade if np.max(np.abs(v[:,1]-(419.39+dy)))<.001]
    intrusion=b.union(wall_tris).intersection(area).area
    check('Glazing and mullions clear the recessed opening '+j['id'],intrusion<.005)
    portal_results.append(dict(id=j['id'],base_gap_m=gap,blocked_area_m2=intrusion))
measures['jetway_portals']=portal_results
# Preserve accepted security perimeter including the previous court cleanup.
fence=lambda q:'fence' in q['resource'].lower() or 'blast_deflectors' in q['resource'] or 'landside_security' in q['resource']
check('Fence resource counts unchanged',Counter(map(key,filter(fence,old['entities'])))==Counter(map(key,filter(fence,dsf['entities']))))
for rel in ['Earth nav data/+30-100/+30-096.dsf','objects/nrt_test/r24_indoor_parking.obj','objects/nrt_test/mx_stepped_hangar.obj','objects/nrt_test/mh2_accordion_hangar.obj','objects/nrt_test/fbo_ground_tower.obj','objects/nrt_test/landside_fence.obj','objects/nrt_test/landside_security.obj','objects/nrt_test/r22_nrt_truck_doors.obj']:
    check('Preserved '+rel,sha(P/rel)==sha(b.OLD/rel))
check('No new helipad mast or beacon',Counter(q['resource'] for q in dsf['entities'] if 'beacon' in q['resource'].lower() or 'light' in q['resource'].lower())==Counter(q['resource'] for q in old['entities'] if 'beacon' in q['resource'].lower() or 'light' in q['resource'].lower()))
# Read native exported curves, including the shared approach before NRT11.
sys.path.insert(0,str(b.b.APPROVED.parents[1]/'source'));import analyze as a
def pts(q):return [g.ag.xy(float(r.split()[2]),float(r.split()[1])) for r in q['lines'][1:]]
entry=pts(next(q for q in ap if q['code']==120 and 'Canopy pull-through entry' in q['lines'][0]))
departure=pts(next(q for q in ap if q['code']==120 and 'Canopy pull-through exit' in q['lines'][0]))
branch=pts(next(q for q in ap if q['code']==120 and 'R25 NRT11' in q['lines'][0]))
check('Canopy entry and exit geometry unchanged',b.Line(entry).hausdorff_distance(b.Line(b.PROPOSAL['arrival']))<.03 and b.Line(departure).hausdorff_distance(b.Line(b.PROPOSAL['departure']))<.03)
check('NRT11 guidance matches start and joins shared tangent',b.Line(branch).hausdorff_distance(b.Line(b.GA_ROUTE))<.03 and b.Line(entry).distance(b.Point(branch[0]))<.03 and b.Point(branch[-1]).distance(b.Point(b.GA_NG))<.015)
walk=b.Line(b.WALK).buffer(.8,cap_style=2,join_style=2).union(b.Line(b.GA_WALK).buffer(.8,cap_style=2))
from shapely.affinity import translate as shift
walk_origin=active['objects/nrt_test/r25_access_paint.obj']['geom']
walk=shift(walk,xoff=walk_origin.x-2674,yoff=walk_origin.y-430)
a.AIRCRAFT['NRT11 envelope']=b.GA_PLANNING
park=a.footprint('NRT11 envelope',b.GA_NG,90)
check('50 m length and 66 m span fit within painted box',b.GA_BOX.covers(park))
check('North-side walking approach retained',b.GA_WALK[0][1]>b.GA_WALK[-1][1] and b.Point(b.GA_WALK[-1]).distance(b.GA_BOX.boundary)<.01)
check('Walking route outside building and rotor reserve',walk.disjoint(b.FOOT) and walk.disjoint(b.HELI_RESERVE))
obs=dict(a.OBSTACLES);obs.update({'NRT10 reserve':b.HELI_RESERVE,'NRT9 A380 parked envelope':b.box(2722.2,435,2802.1,508)})
canopy=[];results={}
def densify(path):
    line=b.Line(path);return [list(line.interpolate(d).coords)[0] for d in np.linspace(0,line.length,math.ceil(line.length/.12))]
for name in ['G650','Lineage 1000E']:
    poses,steer=a.follow_path(name,densify(entry+departure[1:]))
    sw=b.union([a.footprint(name,p['ng'],p['heading']) for p in poses]).buffer(.1);canopy.append(sw)
    gaps={n:sw.distance(o) for n,o in obs.items()};gaps['NRT11 occupied']=sw.distance(park)
    check(name+' canopy movement with NRT11 occupied retains 2.5 m planning clearance',min(gaps.values())>2.5)
    check(name+' canopy route avoids marked walk',sw.disjoint(walk))
    results[name]=dict(gaps_m=gaps,max_steer_deg=steer)
common=b.Line(entry);distance=common.project(b.Point(branch[0]));prefix=[list(common.interpolate(d).coords)[0] for d in np.linspace(0,distance,math.ceil(distance/.12))]
poses,steer=a.follow_path('NRT11 envelope',densify(prefix+branch[1:]))
sw=b.union([a.footprint('NRT11 envelope',p['ng'],p['heading']) for p in poses]).buffer(.1)
gaps={n:sw.distance(o) for n,o in obs.items()};gaps['Pedestrian walk']=sw.distance(walk)
measures['nrt11']=dict(bay_m=[54,71],max_aircraft_m=[50,66],nosewheel=b.GA_NG,heading=b.GA_HEAD,parked_bounds=park.bounds,arrival_gaps_m=gaps,max_steer_deg=steer,final_heading=poses[-1]['heading'],departure='Pushback or tow; one movement at shared junction')
check('NRT11 full shared approach clears obstacles and walk',min(gaps.values())>2.5)
check('NRT11 full approach settles east-facing',abs((poses[-1]['heading']-90+180)%360-180)<1)
check('Parked NRT11 clears pedestrian route and helipad',park.distance(walk)>2.5 and park.distance(b.HELI_RESERVE)>2.5)
measures['canopy']=results
# Longer and wider alternatives fail the working-clearance reserve.
for label,delta in [('longer',dict(length=51)),('wider',dict(span=68))]:
    a.AIRCRAFT['alternative']={**b.GA_PLANNING,**delta}
    p=a.footprint('alternative',b.GA_NG,90)
    if label=='longer':lim=p.distance(b.union(canopy))
    else:
        ps,_=a.follow_path('alternative',densify(prefix+branch[1:]));ss=b.union([a.footprint('alternative',q['ng'],q['heading']) for q in ps]).buffer(.1);lim=ss.distance(walk)
    measures['nrt11'][label+'_alternative_clearance_m']=lim
    check(label+' candidate fails 2.5 m working reserve',lim<2.5)
props=json.loads((P/'Build_Evidence.json').read_text())['r25']['props']
for prop in props:
    if 'stowed' in prop['role'].lower() or prop['role'] in ['Stored cones','Wall-side fire point']:
        pt=b.Point(prop['origin']);check('Stowed equipment outside moving and parked envelopes '+prop['role'],pt.distance(sw)>2.5 and pt.distance(park)>2.5 and pt.distance(b.HELI_RESERVE)>2.5)
for snapshot,folder in [('R24_Hashes.json',b.OLD),('Published_Hashes.json',ROOT.parents[1]/'distribution/NRT_KIAH_Updater_R01/scenery')]:
    check('Protected baseline '+snapshot,all((folder/r).exists() and sha(folder/r)==h for r,h in json.loads((ROOT/'reference'/snapshot).read_text()).items()))
report=dict(passed=len(checks),checks=checks,measurements=measures,runtime_tested=False,limitations=['Planning rectangles and bicycle steering are offline geometry checks, not add-on acceptance. NRT11 must respect both span and length and uses pushback/tow departure.','Stock X-Plane wetness, canopy shelter, materials, dynamic lights and frame time still require the new-PC test. AEP is not required.','Six OpenSAM controls, marshaller and native jetway/service routes are retained; live interactions must be checked after a full restart.','Sparse static people are scenery props. No autonomous pedestrian or luxury-car controller is claimed.'])
(ROOT/'output/Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=len(checks),measurements=measures),indent=2))
