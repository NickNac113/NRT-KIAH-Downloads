import sys,pathlib,pickle,json,ast,math
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF05_Repair\work')
from hf05_common import *
from route_common import network,aircraft_outline,adjacency,reachable
from compatibility_guard import exclusions,exclusion_digest,audit
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\outputs\KIAH_2026-10-24_Review_R03_HF05')
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
plan,oldapt,dsfs=pickle.loads((ROOT/'work/inventory.pkl').read_bytes())
apt=parse_apt(STAGE/'Earth nav data/apt.dat');nodes,edges=network(apt)
changes=json.loads((ROOT/'HF06_Changes.json').read_text());checks=[]
def check(name,ok,detail=None):
    checks.append(dict(check=name,passed=bool(ok),detail=detail))
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
stable_codes=(100,110,20,1204,1205,1206,1300,1400,1401,1500)
check('Runways, pavement, signs, service routes, starts and all 116 moving jetways unchanged',
    all([a['lines'] for a in apt if a['code']==c]==[a['lines'] for a in oldapt if a['code']==c] for c in stable_codes),
    {str(c):sum(a['code']==c for a in apt) for c in stable_codes})
old_rest=[a['lines'] for a in oldapt if a['code'] not in (1201,1202) and a['lines'][0]!='120 R03 aircraft circulation 106']
new_rest=[a['lines'] for a in apt if a['code'] not in (1201,1202) and not a['lines'][0].startswith('120 HF06 B North')]
check('All other airport records preserved',old_rest==new_rest)
check('Every aircraft and vehicle route references existing nodes',all(e['a'] in nodes and e['b'] in nodes for e in edges))
check('No duplicate route-node IDs',len(nodes)==sum(a['code']==1201 for a in apt))
g=adjacency(edges,1202,'C');ge=adjacency(edges,1202,'E')
check('B apron arrival from NB and departure to NB remain connected',856 in reachable(g,[328]) and 324 in reachable(g,[856]))
check('EA is connected bidirectionally through NB, EC, ED and EE',all(set((264,338,349,345))<=reachable(ge,[n]) for n in (264,338,349,345)))
paint=unary_union([a['geom'] for a in apt if a['lines'][0].startswith('120 HF06 B North')])
b_edges=[e for e in edges if e['name']=='B North apron']
route=unary_union([LineString([nodes[e['a']],nodes[e['b']]]) for e in b_edges])
delta=paint.hausdorff_distance(route)
check('New B painted line matches aircraft route',delta<.001,dict(max_deviation_m=delta,segments=len(b_edges)))
pavement=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and int(a['parts'][1]) not in (0,3,4,5,13,15)])
new_routes=[e for e in edges if e['name']=='B North apron' or e['name']=='EA']
off=sum(LineString([nodes[e['a']],nodes[e['b']]]).difference(pavement.buffer(.1)).length for e in new_routes)
check('B and EA route centerlines stay on pavement',off<.01,dict(off_pavement_m=off))
planes=[(a['name'],aircraft_outline(a['geom'].coords[0],a['heading'],a.get('rampmeta',['1301','C'])[1])) for a in apt if a['code']==1300 and a['kind']!='misc']
_,lines,_,_=pickle.loads((ROOT/'work/b-lane.pkl').read_bytes())
sweeps=[]
for idx,line in enumerate(lines):
    for reverse in ([False,True] if idx==0 else [False]):
        line=LineString(list(line.coords)[::-1]) if reverse else line
        for d in np.linspace(0,line.length,max(2,int(line.length/1.5)+1)):
            p=line.interpolate(d);a=line.interpolate(max(0,d-.5));b=line.interpolate(min(line.length,d+.5))
            h=math.degrees(math.atan2(b.x-a.x,b.y-a.y))
            sweeps.append(aircraft_outline(p.coords[0],h,'C'))
swept=unary_union(sweeps)
closest=sorted([(n,swept.distance(p)) for n,p in planes],key=lambda v:v[1])[:6]
building=unary_union([m['geom'] for m in plan['models'].values()])
check('Sampled 36 m span / 40 m length moving aircraft clears modeled parked aircraft and terminals',closest[0][1]>4.5 and swept.distance(building)>4.5,dict(minimum_parked_clearance_m=closest,building_clearance_m=swept.distance(building),samples=len(sweeps),scope='Nose-wheel path and tangent at <=1.5 m spacing. Generic modeled footprints; not an aircraft-specific turning simulation.'))
(ROOT/'work/swept.pkl').write_bytes(pickle.dumps(swept))
longcheck=json.loads((ROOT/'HF06_Long_Aircraft_Check.json').read_text())
check('Longer 45 m and 56 m aircraft models also clear modeled parked aircraft',all(r['minimum_clearances_m'][0][1]>4.5 for r in longcheck),longcheck)
rotunda_ok=True
for j in changes['jetway_joints']:
    name='objects/bridge_'+j['gate']+'.obj'
    def parts(p):
        rows=p.read_text().splitlines();return [l for l in rows if l.startswith('VT ')],[int(n) for l in rows if l.startswith(('IDX ','IDX10 ')) for n in l.split()[1:]]
    ov,oi=parts(SOURCE/name);nv,ni=parts(STAGE/name)
    rotunda_ok &= nv[:len(ov)]==ov and ni[:len(oi)]==oi and max(ni)<len(nv) and len(ni)%3==0
    xyz=np.array([list(map(float,l.split()[1:4])) for l in nv[len(ov):]])
    rotunda_ok &= abs(xyz[:,1].min()-3.65)<.001 and abs(xyz[:,1].max()-7.2)<.001
    # Stock tunnel rear edge at z=-.93 and x=+/- .83 at neutral pitch.
    # At +/-8 pitch its upper/lower rear corners remain within the joint wall.
    for pitch in np.linspace(-8,8,65):
        t=math.radians(pitch)
        for y in (-.35,2.65):
            z=-1.3 + math.sin(t)*y+math.cos(t)*.37
            height=4+math.cos(t)*y-math.sin(t)*.37
            rotunda_ok &= math.hypot(.83,z)<1.70 and 3.55<height<7.2
check('All 32 fixed bridge joints retain original geometry and add a closed circular connector',rotunda_ok,dict(count=32,radius_m=1.7,pitch_range_degrees=[-8,8],note='Radial overlap is independent of yaw. Stock tunnel rear dimensions checked; docking and terrain alignment still require simulator testing.'))
for entry,(tile,before) in zip(changes['EA_barriers'],dsfs):
    after=parse_dsf(ROOT/'work'/f'{tile}-roundtrip.txt');remove={r['index'] for r in entry['removed']}
    check(tile+' DSF keeps every placement except the 11 selected EA barriers',[e['lines'] for i,e in enumerate(before['entities']) if i not in remove]==[e['lines'] for e in after['entities']])
    check(tile+' exclusion properties unchanged',[l for l in before['head'] if l.startswith('PROPERTY ')]==[l for l in after['head'] if l.startswith('PROPERTY ')])
runtime=[p.relative_to(SOURCE).as_posix() for folder in ('Earth nav data','objects','textures') for p in (SOURCE/folder).rglob('*') if p.is_file() and sha(p)!=sha(STAGE/p.relative_to(SOURCE))]
check('Runtime edits limited to 32 connectors, two barrier tiles and airport routes',len(runtime)==35 and all(p.startswith('objects/bridge_') or p.startswith('Earth nav data/') for p in runtime),runtime)
# Store reviewed overlay baseline, not the newly edited state of unknown inputs.
baseline=dict(revision='HF06',exclusions={p.relative_to(SOURCE).as_posix():exclusion_digest(exclusions(p)) for p in (SOURCE/'Earth nav data').rglob('*.dsf')},aep_files=json.loads((ROOT/'aep_before.json').read_text()))
(ROOT/'work/AEP_Compatibility_Baseline.json').write_text(json.dumps(baseline,indent=2))
guard=audit(STAGE,pathlib.Path(r'X:\X-Plane 12'),baseline)
check('AEP baseline, strict exclusion format and scenery priority pass',guard['passed'],guard)
# Check both AEP tiles for closure objects directly on the EA route.
ea=LineString([nodes[n] for n in (264,338,349,345)]).buffer(22)
barriers=[]
for path in (LIVE.parent/'AEP Overlays/Earth nav data').rglob('*.dsf'):
    if path.stem not in ('+29-096','+30-096'):continue
    out=ROOT/'work'/('aep'+path.stem+'.txt');dsf_decode(path,out)
    for e in parse_dsf(out)['entities']:
        if any(t in e['resource'].lower() for t in ('barrier','barricade','closed')) and e['geom'].intersects(ea):barriers.append(dict(tile=path.stem,resource=e['resource']))
check('AEP has no closure objects to restore on EA',not barriers,barriers)
check('Installed HF05 remains unchanged',snapshot_tree(LIVE)==json.loads((ROOT/'live_before.json').read_text()))
check('Scenery order remains unchanged',sha(LIVE.parent/'scenery_packs.ini')=='c1c9bce079f40d1d3f238ffec043cdb8b7dc773875e30764c0745d46ad3c6bd8')
changes['B15_B17_audit']['action']='Superseded by HF06 straight lane and rounded connections.'
changes['B15_B17_revision']['sampled_aircraft_clearance_m']=closest[0][1]
(ROOT/'HF06_Changes.json').write_text(json.dumps(changes,indent=2))
report=dict(revision='KIAH R03 HF06',status='STAGED - OFFLINE VALIDATION ONLY',passed=sum(c['passed'] for c in checks),total=len(checks),checks=checks)
(ROOT/'HF06_Validation.json').write_text(json.dumps(report,indent=2));assert all(c['passed'] for c in checks)
