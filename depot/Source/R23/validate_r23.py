"""Exported-file validation, not a simulator acceptance claim."""
import importlib.util,sys,ast,math,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r23',ROOT/'source/build_r23.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
np=b.np;Image=b.Image;g=b.g;PACK=b.PACK;OLD=b.OLD
checks=[];measures={}
def check(name,value):
    checks.append(dict(name=name,passed=bool(value)))
    if not value:raise AssertionError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=g.ag.parse_dsf(ROOT/'qa/R23_South.txt');new=g.ag.parse_dsf(ROOT/'qa/R23_Roundtrip.txt')
check('Compiled DSF roundtrip has all entities',len(source['entities'])==len(new['entities']))
from collections import defaultdict,Counter
from shapely.strtree import STRtree
def entity_key(q):return (q['kind'],q['resource'],q.get('param'),q['lines'][0].split()[-1] if q['kind']=='polygon' else None)
check('DSFTool retains all entity types despite reordering',Counter(entity_key(q) for q in source['entities'])==Counter(entity_key(q) for q in new['entities']))
groups=defaultdict(list)
for q in new['entities']:groups[entity_key(q)].append(q)
trees={k:STRtree([q['geom'] for q in v]) for k,v in groups.items()};used=defaultdict(set);gaps=[]
for q in source['entities']:
    if q['geom'].is_empty:continue
    k=entity_key(q);choices=[(q['geom'].hausdorff_distance(groups[k][int(i)]['geom']),int(i)) for i in trees[k].query(q['geom'].buffer(.26)) if int(i) not in used[k]]
    check('DSF roundtrip geometry match '+q['resource'],bool(choices))
    distance,i=min(choices);used[k].add(i);gaps.append(distance)
drift=max(gaps)
check('Compiled coordinates stay within 0.25 m of authored geometry',drift<.25);measures['max_dsf_quantization_m']=drift
ap=g.ag.parse_apt(PACK/'Earth nav data/apt.dat');prev=g.ag.parse_apt(OLD/'Earth nav data/apt.dat')
check('All native terminal and FBO jetway rows retained exactly',[q['lines'] for q in ap if q['code']==1500]==[q['lines'] for q in prev if q['code']==1500])
measures['native_jetways']=sum(q['code']==1500 for q in ap)
helipads=[q for q in ap if q['code']==102]
campus_helipads=[q for q in helipads if b.Point(g.ag.xy(float(q['parts'][3]),float(q['parts'][2]))).distance(b.Point(*b.HELI))<100]
check('Exactly one NRT helipad with conventional H2 designator',[q['parts'][1] for q in campus_helipads]==['H2'])
check('Helipad identifiers are unique and conventional',len({q['parts'][1] for q in helipads})==len(helipads) and all(q['parts'][1].startswith('H') for q in helipads))
starts=[q for q in ap if q['code']==1300 and q['name'].startswith('NRT')]
check('Fourteen main NRT starts',len(starts)==14 and len({q['name'] for q in starts})==14)
check('No obsolete start names',not any(q['name'] in ['NRT10A','NRT10B','NRT11','NRT12','NRT MH3','NRT MX OPEN'] for q in starts))
can=next(q for q in starts if q['name']=='NRT CANOPY')
check('Canopy start faces south with the left door toward the terminal',can['heading']==180 and can['geom'].distance(b.Point(b.NG))<.02)
check('Private hangar outward start unchanged',next(q['lines'] for q in starts if q['name']=='NRT PRIVATE HANGAR')==next(q['lines'] for q in prev if q['code']==1300 and q['name']=='NRT PRIVATE HANGAR'))
refs=[]
for name in ['sam.xml','opensam.xml']:
    a=ET.parse(PACK/name).getroot();p=ET.parse(OLD/name).getroot()
    check(name+' eight separate door controls',len(a.findall('gui/checkbox'))==8)
    check(name+' all door definitions and anchors preserved',all(ET.tostring(a.find(k)).strip()==ET.tostring(p.find(k)).strip() for k in ['datarefs','objects','gui']))
    for r in a.findall('datarefs/dataref'):
        refs.append(r.get('name'));check('Open by default '+r.get('name')+' '+name,r.get('autoplay')=='false' and [x.get('v') for x in r.findall('animation')]==['1','0'])
for stem in ['mx_stepped_hangar','mh2_accordion_hangar','r21_private_hangar','r22_nrt_truck_doors','fixed_8','fixed_9A','fixed_9B','fbo_ground_tower']:
    rel='objects/nrt_test/'+stem+'.obj';check('Existing function geometry unchanged '+stem,sha(PACK/rel)==sha(OLD/rel))
check('North airport tile byte-identical',sha(PACK/'Earth nav data/+30-100/+30-096.dsf')==sha(OLD/'Earth nav data/+30-100/+30-096.dsf'))
for rel,h in json.loads((ROOT/'reference/R22_Hashes.json').read_text()).items():check('Sealed R22 preserved '+rel,sha(OLD/rel)==h)

# Resolve resources against the installed public library catalogs, never copy their data.
exports={}
for root in [Path('X:/X-Plane 12/Resources/default scenery'),Path('X:/X-Plane 12/Custom Scenery/MisterX_Library'),Path('X:/X-Plane 12/Custom Scenery/openSAM_Library')]:
    for p in root.rglob('library.txt'):
        for line in p.read_text(errors='replace').splitlines():
            t=line.split()
            if len(t)>2 and t[0] in ['EXPORT','EXPORT_BACKUP','EXPORT_EXTEND','EXPORT_EXCLUDE']:exports.setdefault(t[1],p.parent/' '.join(t[2:]))
            if len(t)>3 and t[0] in ['EXPORT_RATIO','EXPORT_SEASON']:exports.setdefault(t[2],p.parent/' '.join(t[3:]))
for r in set(source['objects']+source['polygons']):
    if r.startswith(('lib/','MisterX_Library/','openSAM/')):check('Library resource resolves '+r,r in exports and exports[r].exists())
    else:check('Package resource resolves '+r,(PACK/r).exists())
for p in (PACK/'objects').rglob('*.obj'):
    rows=[s.split() for s in p.read_text().splitlines()];vs=[r for r in rows if r and r[0]=='VT'];ii=[int(v) for r in rows if r and r[0] in ['IDX','IDX10'] for v in r[1:]];count=next(r for r in rows if r and r[0]=='POINT_COUNTS')
    check('OBJ vertices/indices '+p.name,len(vs)==int(count[1]) and len(ii)==int(count[4]) and all(0<=v<len(vs) for v in ii))
    check('OBJ finite coordinates '+p.name,all(math.isfinite(float(v)) for r in vs for v in r[1:]))
    for r in rows:
        if r and r[0] in ['TEXTURE','TEXTURE_LIT','TEXTURE_NORMAL','TEXTURE_DRAPED','TEXTURE_DRAPED_NORMAL']:
            rel=' '.join(r[2:] if r[0]=='TEXTURE_DRAPED_NORMAL' else r[1:]);check('OBJ material '+p.name+' '+r[0],(p.parent/rel).exists())
        if r and r[0]=='TRIS':check('OBJ draw range '+p.name,0<=int(r[1]) and int(r[1])+int(r[2])<=len(ii) and int(r[2])%3==0)
    check('OBJ balanced animations '+p.name,sum(r==['ANIM_begin'] for r in rows)==sum(r==['ANIM_end'] for r in rows))

# The route is an authored positioning guide, not a simulation of nosewheel steering.
obstacles=b.union([b.FOOT,*b.COLS,b.box(2434,284,2512,434)])
fits={}
for name,d in g.D['aircraft'].items():
    nose_offset=4.0 if 'BBJ' in name else 3.14 if 'Lineage' in name else 3.5
    env=b.box(2648-d['span_m']/2,303-nose_offset,2648+d['span_m']/2,303-nose_offset+d['length_m'])
    gap=env.distance(obstacles);check(name+' parked envelope clear of building and columns',gap>2)
    check(name+' entire planning envelope beneath canopy roof',b.CANOPY.covers(env))
    check(name+' at least 1.5 m beneath minimum roof structure',14-d['height_m']>=1.49)
    fits[name]=dict(parked_envelope=list(env.bounds),minimum_horizontal_gap_m=round(gap,2),roof_gap_m=round(14-d['height_m'],2),nose_offset_assumption_m=nose_offset)
check('Lineage observed L1 lies on doorway centerline',abs((303+.86)-b.DOOR[1])<.01)
check('BBJ parked wing envelope does not enter passenger threshold',fits['BBJ2 / 737-800']['parked_envelope'][2]<2668.5)
measures['parked_aircraft']=fits
route_sweeps=[];route=np.array(b.APPROACH)
for i in range(len(route)-1):
    delta=route[i+1]-route[i];f=delta/np.linalg.norm(delta);r=np.array([f[1],-f[0]])
    for a in np.linspace(0,1,max(2,math.ceil(np.linalg.norm(delta)))):
        p=route[i]+a*delta
        route_sweeps.append(b.Polygon([p+f*x+r*y for x,y in [(4,-17.9),(4,17.9),(-35.5,17.9),(-35.5,-17.9)]]))
route_union=b.union(route_sweeps)
check('Sampled BBJ2 rectangular approach envelope clears buildings and columns',route_union.disjoint(obstacles))
check('Sampled approach remains outside retained helipad reserve',route_union.disjoint(b.box(2652,457,2698,503)))
measures['sampled_approach_obstacle_gap_m']=round(route_union.distance(obstacles),2)

# Validate the model's actual below-clearance triangles against the planned aircraft volumes.
tree=ast.parse((g.LEGACY/'obj_reader.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'OBJ-reader','exec'))
tris,_=readobj(PACK/'objects/nrt_test/r23_jet_center.obj',[2674,330])
for name,d in g.D['aircraft'].items():
    env=b.box(*fits[name]['parked_envelope']);hits=0
    for t in tris:
        if t[:,2].min()>d['height_m'] or t[:,2].max()<.1:continue
        if b.Polygon(t[:,:2]).convex_hull.intersects(env):hits+=1
    check(name+' actual exported structure clears planned aircraft box',hits==0)

car_sweeps=[]
v=np.array(b.VEHICLE)
for i,p in enumerate(v[:-1]):
    f=v[i+1]-p;f/=np.linalg.norm(f);r=np.array([f[1],-f[0]])
    car_sweeps.append(b.Polygon([p+f*a+r*c for a,c in [(-2.5,-1),(2.5,-1),(2.5,1),(-2.5,1)]]))
sweep=b.union(car_sweeps)
check('5 x 2 m crew-car envelope stays clear of terminal and median',sweep.disjoint(b.FOOT) and sweep.disjoint(g.MEDIAN))
check('Crew-car route never crosses aircraft canopy or helipad',sweep.disjoint(b.CANOPY) and sweep.disjoint(b.box(2652,457,2698,503)))
measures['crew_car_clearance_m']=round(sweep.distance(b.FOOT.union(g.MEDIAN)),2)
node_ids=[q['id'] for q in ap if q['code']==1201];check('Taxi/service node IDs unique',len(node_ids)==len(set(node_ids)))
edges=[q['parts'] for q in ap if q['code']==1206 and 'NRT arrivals' in q['lines'][0]]
check('Every new service-route edge resolves',all(int(q[1]) in node_ids and int(q[2]) in node_ids and q[3]=='oneway' for q in edges))
check('New service route forms a closed directed loop',{q[1] for q in edges}=={q[2] for q in edges} and len(edges)>20)
spur=b.LineString([(2730,310),(2744,310)]).buffer(2.6,cap_style=2)
check('Parking-lot connection stays clear of building, median and aircraft apron',spur.disjoint(b.FOOT) and spur.disjoint(g.MEDIAN) and spur.disjoint(b.CANOPY))
check('Custom OpenSAM marshaller placed ahead of the side-entry stand',sum(q['resource']=='openSAM/dgs/marshaller.agp' and q['geom'].distance(b.Point(2648,286))<.25 for q in new['entities'])==1)
removed={'fbo.obj','r21_terminal_canopy.obj','r21_stand_ids.obj','r21_identity.obj','signs_fbo.obj'}
check('No retired model placements',not any(Path(q['resource']).name in removed for q in new['entities']))
# Painted leftovers must be absent throughout the explicitly cleared rectangles.
for name in ['paint','ramp_safety','ramp_wear','taxi_wear']:
    tris,_=readobj(PACK/('objects/nrt_test/'+name+'.obj'),[2700,500])
    check('No old paint/wear fragments inside reworked area '+name,all(not b.CLEAN.buffer(-.02).contains(b.Point(t[:,:2].mean(0))) for t in tris))
check('No donor garage files reintroduced',not any('garage_t02_' in p.name for p in PACK.rglob('*')))
result=dict(passed=len(checks),checks=checks,measurements=measures,runtime_tested=False,limitations=['Aircraft rectangles are conservative parked fit checks; taxi steering, tow operation and door alignment for other add-ons require simulator tests.','OpenSAM startup detection needs the supplied-PC restart check; no plugin binary changed.','Native crew-car routes and DGS require simulator acceptance.'])
(ROOT/'output/Validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
