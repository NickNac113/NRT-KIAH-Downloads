"""Exported geometry, unchanged-airport, route and control regression checks."""
from pathlib import Path
import importlib.util,sys,ast,json,math,hashlib,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r24',ROOT/'source/build_r24.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
np=b.np;g=b.g;Image=b.Image;P=b.PACK
tree=ast.parse((g.LEGACY/'obj_reader.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'))
from shapely.strtree import STRtree
checks=[];measures={}
def check(n,v):
    checks.append(dict(name=n,passed=bool(v)))
    if not v:
        (ROOT/'output/Validation_Failure.json').write_text(json.dumps(checks,indent=2));raise AssertionError(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=g.ag.parse_dsf(ROOT/'qa/R24_South.txt');dsf=g.ag.parse_dsf(ROOT/'qa/R24_Roundtrip.txt')
check('DSF roundtrip retains entity count',len(src['entities'])==len(dsf['entities']))
def key(q):return q['kind'],q['resource'],q.get('param')
check('DSF roundtrip retains resource and type counts',Counter(map(key,src['entities']))==Counter(map(key,dsf['entities'])))
group=defaultdict(list)
for q in dsf['entities']:group[key(q)].append(q)
trees={k:STRtree([q['geom'] for q in qs]) for k,qs in group.items()};used=defaultdict(set);drift=[]
for q in src['entities']:
    if q['geom'].is_empty:continue
    k=key(q);c=[(q['geom'].hausdorff_distance(group[k][int(i)]['geom']),int(i)) for i in trees[k].query(q['geom'].buffer(.26)) if int(i) not in used[k]]
    check('Geometry matched '+q['resource'],bool(c));v,i=min(c);used[k].add(i);drift.append(v)
check('DSF quantization below 0.25 m',max(drift)<.25);measures['max_dsf_drift_m']=max(drift)
active={q['resource']:q for q in dsf['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
def mesh(name,vals=None):
    q=active['objects/nrt_test/'+name+'.obj'];return readobj(P/q['resource'],[q['geom'].x,q['geom'].y],vals=vals)[0]
oldapt=g.ag.parse_apt(b.OLD/'Earth nav data/apt.dat');ap=g.ag.parse_apt(P/'Earth nav data/apt.dat')
check('119 native jetways retained byte-for-byte',[q['lines'] for q in ap if q['code']==1500]==[q['lines'] for q in oldapt if q['code']==1500] and sum(q['code']==1500 for q in ap)==119)
check('All existing service routes and spawn types preserved',[q['lines'] for q in ap if q['code'] in [1201,1206,1400,1401]]==[q['lines'] for q in oldapt if q['code'] in [1201,1206,1400,1401]])
check('All helipad records unchanged - one NRT pad',[q['lines'] for q in ap if q['code']==102]==[q['lines'] for q in oldapt if q['code']==102])
starts=[q for q in ap if q['code']==1300 and q['name'].startswith('NRT')]
check('15 distinct main starts without test locations',len(starts)==len({q['name'] for q in starts})==15 and not any('TEST' in q['name'] for q in starts))
for name,xy,h in [('NRT CANOPY',b.NG,180),('NRT11',b.GA_NG,b.GA_HEAD)]:
    q=next(q for q in starts if q['name']==name);check(name+' actual start and heading',q['geom'].distance(b.Point(xy))<.015 and q['heading']==h)
q=next(q for q in starts if q['name']=='NRT INDOOR PARKING');old=next(q for q in oldapt if q['code']==1300 and q['name']=='NRT PRIVATE HANGAR')
check('Indoor Parking outward start retained',q['heading']==90 and q['geom'].distance(old['geom'])<.001)
check('Retired labels absent from active start menu',not any(q['name'] in ['NRT PRIVATE HANGAR','NRT10B','NRT MX OPEN','NRT MH3'] for q in starts))
# Reconstruct the ACTUAL exported native guidance before clearance testing.
guide=[]
for tag in ['entry','exit']:
    q=next(q for q in ap if q['code']==120 and 'Canopy pull-through '+tag in q['lines'][0])
    pts=[g.ag.xy(float(r.split()[2]),float(r.split()[1])) for r in q['lines'][1:]]
    guide.extend(pts if not guide else pts[1:]);expected=b.PROPOSAL['arrival' if tag=='entry' else 'departure']
    check(tag+' guidance matches approved line within 3 cm',b.LineString(pts).hausdorff_distance(b.LineString(expected))<.03)
    check(tag+' native black-bordered yellow paint',all(r.split()[-1]=='51' for r in q['lines'][1:-1]) and q['lines'][-1].startswith('115 '))
sys.path.insert(0,str(b.APPROVED.parents[1]/'source'));import analyze as a
path=b.LineString(guide);path=[list(path.interpolate(x).coords)[0] for x in np.linspace(0,path.length,math.ceil(path.length/.15))]
ga=b.box(2676,421,2698,441)
mainwalk=b.LineString(b.WALK).buffer(.8,join_style=2,cap_style=2)
gawalk=b.LineString(b.GA_WALK).buffer(.8,join_style=2,cap_style=2)
walk=mainwalk.union(gawalk)
check('Small GA envelope inside marked bay',b.GA_BOX.covers(ga))
check('GA parking and walking route remain outside rotor reserve',ga.disjoint(b.box(2652,457,2698,503)) and walk.disjoint(b.box(2652,457,2698,503)))
check('Pedestrian path clear of GA envelope and headquarters',mainwalk.distance(ga)>4 and gawalk.distance(ga)>2.5 and walk.disjoint(b.FOOT))
check('GA sidewalk connects from north and reaches marked bay',b.GA_WALK[0][1]>b.GA_WALK[-1][1] and b.Point(b.GA_WALK[0]).distance(b.LineString(b.WALK))<.01 and b.Point(b.GA_WALK[-1]).distance(b.GA_BOX.boundary)<.01)
obs=dict(a.OBSTACLES);obs.update({'GA parked envelope':ga,'Helipad reserve':b.box(2652,457,2698,503)})
sweeps={};fits={}
for name in ['Lineage 1000E','G650']:
    poses,steer=a.follow_path(name,path);sw=b.union([a.footprint(name,p['ng'],p['heading']) for p in poses]).buffer(.1);sweeps[name]=sw
    gaps={n:sw.distance(geom) for n,geom in obs.items()}
    check(name+' exported pull-through clears all fixed obstacles',min(gaps.values())>2.5)
    check(name+' pull-through clear of marked pedestrian corridor',sw.disjoint(walk))
    parked=a.footprint(name,b.NG,180);check(name+' fully under roof at new stop',b.CANOPY.covers(parked))
    fits[name]=dict(min_gap_m=min(gaps.values()),nearest=min(gaps,key=gaps.get),max_steer_deg=steer,walk_gap_m=sw.distance(walk),parked_bounds=parked.bounds)
measures['aircraft']=fits
# Reopen the exported GA branch as well; test a 20m x 22m planning aircraft
# from the common tangent into the east-facing stop, including its gear lag.
a.AIRCRAFT['GA planning envelope']=b.GA_PLANNING
q=next(q for q in ap if q['code']==120 and 'NRT11 connected' in q['lines'][0])
pts=[g.ag.xy(float(r.split()[2]),float(r.split()[1])) for r in q['lines'][1:]]
branch=b.LineString(pts)
check('GA branch matches generated entry guide',branch.hausdorff_distance(b.LineString(b.GA_ROUTE))<.03)
check('GA branch connects to approved canopy tangent',b.LineString(b.PROPOSAL['arrival']).distance(b.Point(pts[0]))<.03)
check('GA line ends at east-facing start',b.Point(pts[-1]).distance(b.Point(b.GA_NG))<.015 and b.GA_HEAD==90)
check('GA route uses native yellow guidance',all(r.split()[-1]=='51' for r in q['lines'][1:-1]))
points=[list(branch.interpolate(x).coords)[0] for x in np.linspace(0,branch.length,math.ceil(branch.length/.10))]
poses,steer=a.follow_path('GA planning envelope',points,heading=90)
sw=b.union([a.footprint('GA planning envelope',p['ng'],p['heading']) for p in poses]).buffer(.1)
gaps={n:sw.distance(geom) for n,geom in a.OBSTACLES.items()}
gaps['Helipad reserve']=sw.distance(b.box(2652,457,2698,503))
check('GA entry clears fixed obstacles and rotor reserve',min(gaps.values())>2.5)
check('GA entry and parked envelope clear pedestrian corridor',sw.distance(walk)>2.5 and ga.distance(walk)>2.5)
check('GA arrival aligns with east-facing stop',abs((poses[-1]['heading']-b.GA_HEAD+180)%360-180)<1)
check('GA planning aircraft fits marked bay at stop',b.GA_BOX.covers(a.footprint('GA planning envelope',b.GA_NG,b.GA_HEAD)))
check('East-side pedestrian route has no aircraft line crossings',walk.disjoint(branch) and walk.disjoint(b.LineString(guide)))
check('Walk stays outside the stepped headquarters footprint',walk.disjoint(b.FOOT) and b.Point(b.WALK[0]).distance(b.FOOT)<1)
measures['ga_access']=dict(min_obstacle_gap_m=min(gaps.values()),nearest=min(gaps,key=gaps.get),walk_gap_m=sw.distance(walk),max_steer_deg=steer,final_heading_deg=poses[-1]['heading'],nosewheel=b.GA_NG,departure='Pushback or tow out')
check('Passenger doorway retains Lineage L1 planning alignment',abs(b.DOOR[1]-(b.NG[1]+.86))<.001)
check('Existing marshaller retained outside pull-through',sum(q['resource']=='openSAM/dgs/marshaller.agp' and q['geom'].distance(b.Point(2648,286))<.25 for q in dsf['entities'])==1)
heights={}
for name in ['r24_indoor_parking','mh2_accordion_hangar']:
    t=mesh(name);heights[name]=float(t[:,:,2].max())
check('Parking Hangar matches MH2 roof and skylight height',abs(heights['r24_indoor_parking']-heights['mh2_accordion_hangar'])<.001);measures['hangar_height']=heights
# Compare four evaluated door poses; changes to one control cannot move the other.
states={}
for left,right in [(0,0),(0,1),(1,0),(1,1)]:states[(left,right)]=mesh('r24_indoor_parking',{b.REF_LEFT:left,b.REF_RIGHT:right})
ld=np.max(np.abs(states[(1,0)]-states[(0,0)]),axis=(1,2))>.001;rd=np.max(np.abs(states[(0,1)]-states[(0,0)]),axis=(1,2))>.001
check('Both door halves animate independently',ld.any() and rd.any() and not (ld&rd).any())
check('Both-open geometry equals combined independent changes',np.allclose(states[(1,1)]-states[(0,0)],states[(1,0)]+states[(0,1)]-2*states[(0,0)]))
measures['left_triangles_moving']=int(ld.sum());measures['right_triangles_moving']=int(rd.sum())
for x,y in [(2505,325),(2505,393)]:
    opening=b.box(x-1,y-27,x+8,y+27);t=states[(1,1)]
    # Check a representative 54m bay, 0.5-15.9m above the floor.
    hit=sum(b.Polygon(v[:,:2]).convex_hull.intersects(opening) for v in t if v[:,2].max()>.5 and v[:,2].min()<15.9)
    check('Opened half-bay clear at '+str(y),hit==0)
origin=active['objects/nrt_test/r24_indoor_parking.obj']['geom'];hangar=states[(0,0)]
for axis,plane,axes in [(0,origin.x+39,(1,2)),(0,origin.x-39,(1,2)),(1,origin.y-75,(0,2))]:
    polys=[b.Polygon(v[:,axes]) for v in hangar if np.max(np.abs(v[:,axis]-plane))<.00002]
    area=sum(p.area for p in polys);covered=b.union(polys).area
    check('No overlapping outer wall faces '+str((axis,plane)),area-covered<.002)
refs=set()
for filename in ['sam.xml','opensam.xml']:
    root=ET.parse(P/filename).getroot();dr=root.findall('datarefs/dataref');gui=root.findall('gui/checkbox');inst={q.get('id') for q in root.findall('objects/instance')}
    check(filename+' exactly six independent door controls',len(dr)==len(gui)==6)
    names={q.get('name') for q in dr};refs|=names
    check(filename+' truck and former private controls removed',not any('truck' in v or 'private_hangar' in v for v in names))
    check(filename+' split Indoor Parking controls registered',{b.REF_LEFT,b.REF_RIGHT}.issubset(names))
    check(filename+' valid GUI bindings',all(q.get('dataref') in names and q.get('instance') in inst for q in gui))
    check(filename+' all doors default open',all(q.get('autoplay')=='false' and [(a.get('t'),a.get('v')) for a in q.findall('animation')][0]==('0','1') for q in dr))
check('Truck doors no longer reference OpenSAM',not re.search(r'ANIM_|nrt/kiah/',(P/'objects/nrt_test/r22_nrt_truck_doors.obj').read_text()))
# The truck-door bake must match the old open pose exactly, including rotation.
truckrefs=set(re.findall(r'nrt/kiah/[^\s]+',(b.OLD/'objects/nrt_test/r22_nrt_truck_doors.obj').read_text()))
oldtruck=readobj(b.OLD/'objects/nrt_test/r22_nrt_truck_doors.obj',[0,0],vals={r:1 for r in truckrefs})[0]
newtruck=readobj(P/'objects/nrt_test/r22_nrt_truck_doors.obj',[0,0])[0]
check('Truck doors baked in prior fully-open position',np.allclose(oldtruck,newtruck,atol=.000002))
for rel in active:
    text=(P/rel).read_text();rows=[s.split() for s in text.splitlines()];vv=[r for r in rows if r and r[0]=='VT'];ids=[int(i) for r in rows if r and r[0] in ['IDX','IDX10'] for i in r[1:]]
    count=next(r for r in rows if r and r[0]=='POINT_COUNTS')
    check('OBJ counts '+rel,int(count[1])==len(vv) and int(count[4])==len(ids) and all(0<=i<len(vv) for i in ids))
    check('OBJ animation references '+rel,all(ref in refs for ref in re.findall(r'nrt/kiah/[^\s]+',text)))
    check('OBJ balanced animations '+rel,sum(r==['ANIM_begin'] for r in rows)==sum(r==['ANIM_end'] for r in rows))
    for r in rows:
        if r and r[0].startswith('TEXTURE'):
            rp=' '.join(r[2:] if r[0]=='TEXTURE_DRAPED_NORMAL' else r[1:]);check('Material exists '+rel+' '+r[0],(P/rel).parent.joinpath(rp).exists())
        if r and r[0]=='TRIS':check('Draw range '+rel,0<=int(r[1]) and int(r[1])+int(r[2])<=len(ids) and int(r[2])%3==0)
for name in ['paint','ramp_safety','ramp_wear','taxi_wear']:
    t=mesh(name);region=b.box(2410,276,2513,434.2).union(b.box(2646,395,2707,449)).buffer(-.25)
    check('Legacy paint cleared behind hangar and GA bay '+name,not any(region.contains(b.Point(v[:,:2].mean(0))) for v in t))
for name in ['landside_fence','landside_security']:
    t=mesh(name);cut=b.box(2719.7,278,2720.3,332)
    check('No former court fence fabric or frame '+name,not any(cut.contains(b.Point(v[:,:2].mean(0))) for v in t if v[:,2].min()>.17))
fences=[q for q in dsf['entities'] if 'jet_blast_deflectors' in q['resource'] and b.box(2800,270,3160,770).intersects(q['geom'])]
check('Three complete cargo blast fence runs exported',len(fences)==3)
for i,pts in enumerate(b.BLAST_PATHS):
    line=b.LineString(pts);q=min(fences,key=lambda q:q['geom'].hausdorff_distance(line));check('Full fence line coverage '+str(i),q['geom'].hausdorff_distance(line)<.25 and q['param']==5)
south=min(fences,key=lambda q:q['geom'].bounds[1]);points=[g.ag.xy(float(r.split()[1]),float(r.split()[2])) for r in south['lines'] if r.startswith('POLYGON_POINT')]
check('South blast face now points north toward apron',points[0][0]>points[-1][0])
measures['blast_length_m']=sum(b.LineString(p).length for p in b.BLAST_PATHS)
check('No new beacon or lighting mast',Counter(q['resource'] for q in dsf['entities'] if 'light' in q['resource'].lower() or 'beacon' in q['resource'].lower())==Counter(q['resource'] for q in b.BASE_DSF['entities'] if 'light' in q['resource'].lower() or 'beacon' in q['resource'].lower()))
for rel in ['Earth nav data/+30-100/+30-096.dsf','objects/nrt_test/mx_stepped_hangar.obj','objects/nrt_test/mh2_accordion_hangar.obj','objects/nrt_test/fixed_8.obj','objects/nrt_test/fixed_9A.obj','objects/nrt_test/fixed_9B.obj','objects/nrt_test/fbo_ground_tower.obj']:
    check('Unchanged function '+rel,sha(P/rel)==sha(b.OLD/rel))
for rel,h in json.loads((ROOT/'reference/R23_Hashes.json').read_text()).items():check('Sealed R23 unchanged '+rel,sha(b.OLD/rel)==h)
seal=json.loads((ROOT/'reference/Previous_Seal.json').read_text())
check('Prior sealed R24 candidate preserved',sha(Path(seal['archive']))==seal['sha256'])
# Check external resource resolution without copying third-party libraries.
exports={}
for root in [Path('X:/X-Plane 12/Resources/default scenery'),Path('X:/X-Plane 12/Custom Scenery/MisterX_Library'),Path('X:/X-Plane 12/Custom Scenery/openSAM_Library')]:
    for file in root.rglob('library.txt'):
        for row in file.read_text(errors='replace').splitlines():
            t=row.split()
            if len(t)>2 and t[0] in ['EXPORT','EXPORT_BACKUP','EXPORT_EXTEND','EXPORT_EXCLUDE']:exports.setdefault(t[1],file.parent/' '.join(t[2:]))
            if len(t)>3 and t[0] in ['EXPORT_RATIO','EXPORT_SEASON']:exports.setdefault(t[2],file.parent/' '.join(t[3:]))
for r in {q['resource'] for q in dsf['entities']}:
    check('Runtime library resolution '+r,(P/r).exists() or (r in exports and exports[r].exists()))
report=dict(passed=len(checks),checks=checks,measurements=measures,runtime_tested=False,limitations=['G650 and Lineage steering remains an X-Plane test. BBJ2 is tow-only and excluded from the forward-turn requirement.','Pedestrian route is scenery paint, not automatic walking agents. Keep pedestrians off the ramp during aircraft or helicopter movements.','OpenSAM marshalling uses the revised apt.dat stand; live stop behavior and independent door checkboxes require runtime testing.'])
(ROOT/'output/Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=len(checks),measurements=measures),indent=2))
