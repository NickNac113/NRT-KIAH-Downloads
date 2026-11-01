"""Exported-file, clearance and network checks. Never simulator acceptance."""
from pathlib import Path
import importlib.util,sys,json,math,re,xml.etree.ElementTree as ET
from collections import Counter,defaultdict,deque
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r26',ROOT/'source/build_r26.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;np=b.np;box=b.box;Line=b.Line;Point=b.Point;union=b.union;P=b.PACK
E=json.loads((P/'Build_Evidence.json').read_text())['r26'];checks=[];measure={}
def check(name,v):
    checks.append(dict(name=name,passed=bool(v)))
    if not v:
        (b.OUT/'Validation_Failure.json').write_text(json.dumps(dict(checks=checks,measurements=measure),indent=2));raise AssertionError(name)
dsf=g.ag.parse_dsf(b.QA/'R26_Roundtrip.txt');src=g.ag.parse_dsf(b.QA/'R26_South.txt');ap=g.ag.parse_apt(P/'Earth nav data/apt.dat')
active={q['resource']:q for q in dsf['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
key=lambda q:(q['kind'],q['resource'],q.get('param'))
check('Compiled scene has expected entities',Counter(map(key,src['entities']))==Counter(map(key,dsf['entities'])))
from shapely.strtree import STRtree
group=defaultdict(list)
for q in dsf['entities']:group[key(q)].append(q)
trees={k:STRtree([q['geom'] for q in a]) for k,a in group.items()};used=defaultdict(set);drifts=[]
for q in src['entities']:
    if q['geom'].is_empty:continue
    k=key(q);c=[(q['geom'].hausdorff_distance(group[k][int(i)]['geom']),int(i)) for i in trees[k].query(q['geom'].buffer(.26)) if int(i) not in used[k]]
    check('DSF match '+q['resource'],bool(c)) if not c else None
    drift,i=min(c);used[k].add(i);drifts.append(drift)
measure['dsf_max_drift_m']=max(drifts);check('Compiled coordinate error below 0.25m',max(drifts)<.25)
# Runtime parsing and preservation, rather than superficial source checks.
refs={q.get('name') for q in ET.parse(P/'sam.xml').findall('datarefs/dataref')}
for rel in active:
    rows=(P/rel).read_text().splitlines();rr=[r.split() for r in rows];vv=[r for r in rr if r and r[0]=='VT'];ids=[int(a) for r in rr if r and r[0] in ['IDX','IDX10'] for a in r[1:]]
    counts=next(r for r in rr if r and r[0]=='POINT_COUNTS')
    check('Valid OBJ '+Path(rel).stem,int(counts[1])==len(vv) and int(counts[4])==len(ids) and all(0<=i<len(vv) for i in ids) and all(int(r[1])+int(r[2])<=len(ids) and int(r[2])%3==0 for r in rr if r and r[0]=='TRIS'))
    check('Resolved texture / animation '+Path(rel).stem,all((P/rel).parent.joinpath(' '.join(r[2:] if r[0]=='TEXTURE_DRAPED_NORMAL' else r[1:])).is_file() for r in rr if r and r[0].startswith('TEXTURE')) and all(t in refs for t in re.findall(r'nrt/kiah/[^\s]+','\n'.join(rows))))
for f in ['sam.xml','opensam.xml','Earth nav data/+30-100/+30-096.dsf','objects/nrt_test/r25_access_paint.obj','objects/nrt_test/r25_access_ids.obj','objects/nrt_test/r24_indoor_parking.obj','objects/nrt_test/r25_fixed_8.obj','objects/nrt_test/r25_fixed_9A.obj','objects/nrt_test/r25_fixed_9B.obj']:
    check('Preserved '+f,b.sha(P/f)==b.sha(b.OLD/f))
rel='objects/nrt_test/r25_jet_center.obj'
old=(b.OLD/rel).read_text().splitlines();new=(P/rel).read_text().splitlines()
changed_light=lambda s:s.startswith('LIGHT_PARAM ') and s.split()[3]=='15.700'
check('HQ geometry and all non-canopy lights unchanged',[r for r in old if not changed_light(r)]==[r for r in new if not changed_light(r)])
check('Exactly nine canopy spill/billboard pairs retuned',sum(a!=c for a,c in zip(old,new))==18 and len(old)==len(new))
for filename in ['sam.xml','opensam.xml']:
    root=ET.parse(P/filename).getroot();dr=root.findall('datarefs/dataref');gui=root.findall('gui/checkbox')
    check(filename+' six default-open independent controls',len(dr)==len(gui)==6 and all([(a.get('t'),a.get('v')) for a in q.findall('animation')][0]==('0','1') for q in dr))
check('All native jetways unchanged',[q['lines'] for q in ap if q['code']==1500]==[q['lines'] for q in b.APT if q['code']==1500])
check('All 15 main NRT starts retained',len([q for q in ap if q['code']==1300 and q['name'].startswith('NRT')])==15)
changed=lambda q:(q['code']==1300 and q.get('name')=='NRT9') or (q['code']==120 and q['geom'].bounds[2]-q['geom'].bounds[0]<.1 and 2762<q['geom'].bounds[0]<2767 and 437<q['geom'].bounds[1]<439) or any('NRT R26' in s for s in q['lines'])
check('No unrelated apt airport data changed',[q['lines'] for q in ap if not changed(q)]==[q['lines'] for q in b.APT if not changed(q)])
q=next(q for q in ap if q['code']==1300 and q['name']=='NRT9');check('NRT9 start moved four metres east, same heading',q['heading']==180 and q['geom'].distance(Point(b.NRT9))<.01)
line=next(q for q in ap if q['code']==120 and 'R26 pedestrian' in q['lines'][0])
check('NRT9 nosewheel aligned to translated guidance',line['geom'].distance(Point(b.NRT9))<.01)

def verts(rel,pack=P,origin=None):
    q=active[rel];origin=origin or [q['geom'].x,q['geom'].y];rr=[r.split() for r in (pack/rel).read_text().splitlines()];v=np.array([list(map(float,r[1:])) for r in rr if r and r[0]=='VT']);ids=[int(a) for r in rr if r and r[0] in ['IDX','IDX10'] for a in r[1:]];tri=v[ids].reshape(-1,3,8);en=tri[:,:,[0,2]]*np.array([1,-1])+origin
    return tri,en
white=[]
for rel,count in [('objects/nrt_test/paint.obj',6),('objects/nrt_test/ramp_safety.obj',8)]:
    old=b.PLACEMENTS[rel];o=[old['geom'].x,old['geom'].y];v0,_=verts(rel,b.OLD,o);v1,en=verts(rel,P,o);d=v1-v0;moved=np.max(np.abs(d),axis=(1,2))>1e-6
    check('Only selected stand triangles changed '+rel,int(moved.sum())==count and np.allclose(d[moved,:,0],4) and np.max(np.abs(d[moved,:,1:]))<1e-6)
    if rel.endswith('ramp_safety.obj'):
        check('Jetway exclusion boxes left in place',all(np.max(np.abs(t[:,:,6]-.34375))<1e-6 for t in [v1[moved]]))
        white=[b.b.Polygon(t) for t in en[moved]]
paint_origin=active['objects/nrt_test/r25_access_paint.obj']['geom']
from shapely.affinity import translate
walk=Line(b.WALK).buffer(.8,cap_style=2,join_style=2).union(Line(b.GA_WALK).buffer(.8,cap_style=2))
walk=translate(walk,xoff=paint_origin.x-2674,yoff=paint_origin.y-430)
# Conservative full-width rectangles cover fuselage, wing and tail, including
# parts where an actual aircraft is narrower. No credit for a tapered wing.
n9=box(b.NRT9[0]-79.75/2,b.NRT9[1]-3,b.NRT9[0]+79.75/2,b.NRT9[1]+70)
n8=box(2842.527-44.84/2,435,2842.527+44.84/2,490)
n11=box(2667,379.5,2717,445.5)
measure['nrt9_walk_clearance_m']=n9.distance(walk);measure['nrt9_nrt8_clearance_m']=n9.distance(n8);measure['walk_stand_paint_gap_m']=union(white).distance(walk)
check('Pedestrian corridor outside full parked A380 envelope by >4m',n9.distance(walk)>4)
check('Walking paint no longer crosses NRT9 boundary',union(white).distance(walk)>1)
check('NRT8 and shifted NRT9 envelopes retain >12m',n9.distance(n8)>12)
check('Accepted NRT11 envelope retains 2.5m to walk',n11.distance(walk)>2.5)
check('Walk outside building and rotor area',walk.disjoint(b.b.FOOT) and walk.disjoint(b.HELI))
measure['jetway_reach']={}
for j in b.EVIDENCE['jetways']:
    if j['stand']!='NRT9':continue
    # A conservative 4m half-fuselage projection gives lateral stand-off;
    # runtime door position and articulating tunnel remain an add-on test.
    lateral=j['base'][0]-(b.NRT9[0]+4)
    measure['jetway_reach'][j['id']]=dict(lateral_standoff_m=lateral,published_range=j['range'])
    check('NRT9 '+j['id']+' lateral stand-off remains within telescope range',j['range'][0]<=lateral<=j['range'][1])

# Native lighting API definitions from the actual stock installation.
lights_txt=Path('X:/X-Plane 12/Resources/bitmaps/world/lites/lights.txt').read_text()
defs={r.split()[1]:int(r.split()[2]) for r in lights_txt.splitlines() if r.startswith('LIGHT_PARAM_DEF')}
new_spills=[]
for rel in active:
    if not (Path(rel).stem.startswith('r26_') or rel=='objects/nrt_test/r25_jet_center.obj'):continue
    for row in (P/rel).read_text().splitlines():
        if not row.startswith('LIGHT_PARAM '):continue
        r=row.split();check('Stock light arity '+Path(rel).stem+' '+r[1],r[1] in defs and len(r)-5==defs[r[1]])
        if rel=='objects/nrt_test/r25_jet_center.obj' and r[3]!='15.700':continue
        if r[1]=='spot_params_sp_pm':
            d=np.array(list(map(float,r[10:13])));new_spills.append(r)
            check('Normalized downward light '+Path(rel).stem,abs(np.linalg.norm(d)-1)<1e-5 and d[1]<0)
check('22 new and 9 upgraded actual photometric spills',len(new_spills)==len(E['lights'])==31 and sum(l['existing_fixture'] for l in E['lights'])==9)
for name in ['spot_params_sp_pm','spot_params_bb_pm']:
    line=next(l for l in lights_txt.splitlines() if l.startswith(('SPILL_HW_DIR','BILLBOARD_HW')) and l.split()[1]==name)
    check(name+' uses stock night-only definition',line.split()[-1]=='0')
measure['nearest_light_to_helipad_reserve_m']=min(Point(l['position'][:2]).distance(b.HELI) for l in E['lights'])
check('All new light fixtures >50m from pad reserve',measure['nearest_light_to_helipad_reserve_m']>50)
check('All beams below horizon',all(l['pitch_down_deg']>l['half_angle_deg']+1 for l in E['lights']))
check('Existing canopy lamps keep their 15.7m height',all(l['position'][2]==15.7 and l['existing_fixture'] for l in E['lights'] if l['id'].startswith('C')))
fence=lambda q:any(x in q['resource'].lower() for x in ['fence','blast_deflectors','landside_security'])
check('Security and blast fence placements unchanged',Counter(map(key,filter(fence,b.BASE['entities'])))==Counter(map(key,filter(fence,dsf['entities']))))
check('No additional masts, beacon or helipad starts',Counter(q['resource'] for q in dsf['entities'] if 'flood_1_led' in q['resource'] or 'beacon' in q['resource'].lower())==Counter(q['resource'] for q in b.BASE['entities'] if 'flood_1_led' in q['resource'] or 'beacon' in q['resource'].lower()))

# Actual route graph connectivity and pavement containment, with a 6m road
# envelope. Existing routes and service fleets are preserved byte for byte.
oldroutes=[q['lines'] for q in b.APT if q['code']==1206]
check('Inherited service routes retained',[q['lines'] for q in ap if q['code']==1206 and 'NRT R26' not in q['lines'][0]]==oldroutes)
check('No service spawns or destinations altered',[q['lines'] for q in ap if q['code'] in [1400,1401]]==[q['lines'] for q in b.APT if q['code'] in [1400,1401]])
public=(g.LEGACY.parent/'reference/public_apt.dat').read_text()
check('NB routes traced to original airport source',all(s in public for s in ['1206 918 919 twoway','1206 919 972 twoway','1206 972 1176 twoway']))
nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in ap if q['code']==1201};edges=[q for q in ap if q['code']==1206 and 'NRT R26' in q['lines'][0]]
adj=defaultdict(set)
for q in edges:
    a,c=map(int,q['parts'][1:3]);check('Service edge endpoints exist '+str(a),a in nodes and c in nodes);adj[a].add(c);adj[c].add(a)
seen={919};pending=deque([919])
while pending:
    for n in adj[pending.popleft()]:
        if n not in seen:seen.add(n);pending.append(n)
check('All 59 new service nodes connected to inherited road',set(n['id'] for n in E['service_nodes'])<=seen and len(E['service_nodes'])==59)
crew={q['id'] for q in b.APT if q['code']==1201 and 'NRT arrivals' in q['lines'][0]}
check('Landside crew-car circuit remains disconnected',not seen.intersection(crew))
pavement=union([q['geom'] for q in ap if q['code'] in [100,110]]+[q['geom'] for q in dsf['entities'] if q['kind']=='polygon' and '/pavement/' in q['resource']])
paths=union([Line([nodes[int(q['parts'][1])],nodes[int(q['parts'][2])]]) for q in edges]);road=paths.buffer(3,cap_style=2,join_style=2)
measure['new_service_length_m']=paths.length;measure['service_road_unpaved_m2']=road.difference(pavement).area
check('Full six-metre service-road envelope stays paved',road.difference(pavement).area<.1)
obstacles={'NRT9 A380':n9,'NRT8 A300':n8,'NRT11':n11,'HQ':b.b.FOOT,'Helipad':b.HELI,'Canopy':b.b.CANOPY}
for q in ap:
    if q['code']==1300 and q['name'] in ['NRT1','NRT2','NRT3','NRT4','NRT5','NRT6','NRT7']:
        x,y=q['geom'].x,q['geom'].y;large=q['name'] in ['NRT5','NRT6','NRT7'];length,span,nose=(76.3,68.4,5) if large else (52.,41.1,4.)
        obstacles[q['name']]=box(x+ nose-length,y-span/2,x+nose,y+span/2)
gaps={n:road.distance(o) for n,o in obstacles.items()};measure['service_road_clearance_m']=gaps
check('Service roads avoid buildings, helipad and occupied stand envelopes',min(gaps.values())>2.5)
check('No service road across pedestrian lane',road.distance(walk)>2.5)
# External dependency resolution with AEP deliberately excluded.
exports={}
for folder in [Path('X:/X-Plane 12/Resources/default scenery'),Path('X:/X-Plane 12/Custom Scenery/MisterX_Library'),Path('X:/X-Plane 12/Custom Scenery/openSAM_Library')]:
    for f in folder.rglob('library.txt'):
        for line in f.read_text(errors='replace').splitlines():
            r=line.split()
            if len(r)>2 and r[0] in ['EXPORT','EXPORT_BACKUP','EXPORT_EXTEND','EXPORT_EXCLUDE']:exports.setdefault(r[1],f.parent/' '.join(r[2:]))
            if len(r)>3 and r[0] in ['EXPORT_RATIO','EXPORT_SEASON']:exports.setdefault(r[2],f.parent/' '.join(r[3:]))
unresolved=[r for r in {q['resource'] for q in dsf['entities']} if not ((P/r).is_file() or r in exports and exports[r].is_file())];measure['unresolved']=unresolved
check('Every scene asset resolves without AEP',not unresolved)
for filename,folder in [('R25_Hashes.json',b.OLD),('Published_Hashes.json',ROOT.parents[1]/'distribution/NRT_KIAH_Updater_R01/scenery')]:
    check('Protected baseline '+filename,b.snapshot(folder)==json.loads((ROOT/'reference'/filename).read_text()))
report=dict(passed=len(checks),checks=checks,measurements=measure,runtime_tested=False,limitations=['No simulator appearance/performance or moving-vehicle acceptance. Ground routing is a plausible repair, not proof of the observed cause.','X-Plane controls the final off-network approach to served aircraft and does not universally avoid scenery objects or other aircraft. Test requested services at the NRT stands.','NRT9 four-metre lateral move preserves native jetway bases; final docking with each add-on requires testing.','Light appearance and 22 additional spills plus 9 upgraded spills need a night performance test. No AEP dependency; no additional helipad mast or beacon.'])
(b.OUT/'Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=len(checks),measurements=measure),indent=2))
if (b.OUT/'Validation_Failure.json').is_file():(b.OUT/'Validation_Failure.json').unlink()
