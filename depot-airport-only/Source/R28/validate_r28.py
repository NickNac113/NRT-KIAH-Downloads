"""Independent exported-file, preservation and geometry checks for R28."""
from common import *
from collections import Counter,defaultdict,deque
import re
from preview_native import segments,read_fac,read_obj
from shapely.strtree import STRtree

checks=[];metrics={};notes=[]
def check(name,condition,detail=''):
    checks.append(dict(name=name,pass_=bool(condition),detail=detail))

def path_exists(adj,start,end):
    seen={start};queue=deque([start])
    while queue:
        node=queue.popleft()
        if node==end:return True
        for nxt in adj[node]:
            if nxt not in seen:seen.add(nxt);queue.append(nxt)
    return False

def objdata(path):
    rows=path.read_text().splitlines()
    v=np.array([list(map(float,r.split()[1:])) for r in rows if r.startswith('VT ')])
    ix=[int(a) for r in rows if r.startswith(('IDX ','IDX10 ')) for a in r.split()[1:]]
    draw=[tuple(map(int,r.split()[1:3])) for r in rows if r.startswith('TRIS ')]
    return rows,v,ix,draw


def dsf_vertices(entity):
    # Fence chains, point forests and open roof chains are valid DSF polygons
    # but do not have a filled Polygon centroid. Compare their source vertices.
    if entity['kind']=='polygon':
        return MultiPoint([ag.xy(*map(float,r.split()[1:3]))
                           for r in entity['lines'] if r.startswith('POLYGON_POINT ')])
    return entity['geom']

def main():
    oldhash=json.loads((ROOT/'reference/R27_Hashes.json').read_text())
    check('Sealed R27 files are unchanged',snapshot(PREV)==oldhash)
    current=snapshot(PACK)
    changed=[k for k in oldhash if current.get(k)!=oldhash[k]]
    allowed={'Earth nav data/apt.dat','Earth nav data/+20-100/+29-096.dsf'}|{
        'objects/bridge_B'+str(i)+'.obj' for i in range(1,24) if i!=13}
    check('Existing-file changes are limited to B shell placement, B bridges and taxi guidance',set(changed)==allowed,changed)
    metrics['unchanged_predecessor_files']=len(oldhash)-len(changed)
    metrics['changed_existing_files']=len(changed)
    apt=ag.parse_apt(PACK/'Earth nav data/apt.dat')
    dsf=ag.parse_dsf(ROOT/'qa/R28_Roundtrip.txt')
    authored=ag.parse_dsf(ROOT/'qa/R28_DSF.txt')
    ev=json.loads((ROOT/'qa/R28_Evidence.json').read_text())
    changes=ev['changes'][-1]
    excluded=set(changes['removed']+changes['replaced'])
    preserved=[a['lines'] for a in APT if a['lines'][0] not in excluded and a['code']!=99]
    remain=[a['lines'] for a in apt if a['lines'][0] not in excluded and not a['lines'][0].startswith('120 R28') and a['code']!=99]
    # Exclude only the four explicitly renamed NG edges from both comparisons.
    pairs={frozenset(p) for p in [(112,109),(109,110),(110,14),(14,111)]}
    remain=[a for a in remain if not(a[0].startswith('1202 ') and frozenset(map(int,a[0].split()[1:3])) in pairs)]
    check('All unrelated apt.dat records are preserved exactly',preserved==remain)
    for codes,label in [({1300},'Every aircraft and helicopter start'),({1500},'All native animated jetways'),({1400,1401,1402,1206},'Service parking and vehicle destinations')]:
        a=[q['lines'] for q in APT if q['code'] in codes];b=[q['lines'] for q in apt if q['code'] in codes]
        check(label+' unchanged',a==b,len(a))
    check('Native pavement and wet-weather materials unchanged',[q['lines'] for q in APT if q['code']==110]==[q['lines'] for q in apt if q['code']==110])
    controls=[p for p in PREV.rglob('*') if p.is_file() and ('sam' in p.name.lower() or p.suffix.lower()=='.xml')]
    check('OpenSAM configuration unchanged',all(sha(p)==sha(PACK/p.relative_to(PREV)) for p in controls),len(controls))
    oldentities=Counter(tuple(q['lines']) for q in DSF['entities'] if q['resource']!='objects/B_North.obj')
    authored_existing=Counter(tuple(q['lines']) for q in authored['entities'][:-len(ev['facades'])])
    check('All existing DSF placements except the B North shell preserved',oldentities==authored_existing)
    check('B North custom shell placement removed',not any(q['resource']=='objects/B_North.obj' for q in dsf['entities']))
    check('DSF compiled and roundtripped',len(dsf['entities'])==len(authored['entities']) and (PACK/'Earth nav data/+20-100/+29-096.dsf').read_bytes()[:8]==b'XPLNEDSF')
    roundtrip_error=0;before=defaultdict(list);after=defaultdict(list)
    # DSFTool sorts entities by definition; compare their identity and geometry,
    # not their serialized order. Every exported entity must match exactly once.
    for q in authored['entities']:before[(q['kind'],q['resource'],q.get('param'))].append(q)
    for q in dsf['entities']:after[(q['kind'],q['resource'],q.get('param'))].append(q)
    check('DSF roundtrip preserves entity identities and counts',{k:len(v) for k,v in before.items()}=={k:len(v) for k,v in after.items()})
    for key,aa in before.items():
        bb=after[key];geometry=[dsf_vertices(b) for b in bb]
        tree=STRtree([g.centroid for g in geometry]);used=set()
        for a in aa:
            source=dsf_vertices(a)
            candidates=[int(i) for i in tree.query(source.centroid.buffer(.15)) if int(i) not in used]
            assert candidates,('Roundtrip geometry missing',key,a['geom'].bounds)
            error,i=min((source.hausdorff_distance(geometry[i]),i) for i in candidates)
            used.add(i);roundtrip_error=max(roundtrip_error,error)
    # DSF's integer coordinate pools introduce measurable quantization. This is
    # separate from the millimetre-level authored apt.dat centerline checks.
    check('DSF coordinates survive native encoding within 15 cm',roundtrip_error<.15,roundtrip_error)
    metrics['dsf_roundtrip_max_error_m']=roundtrip_error
    buildings=[f for f in ev['facades'] if f['name'].endswith(' upper')]
    footprint=unary_union([Polygon(f['points']) for f in buildings])
    error=footprint.boundary.hausdorff_distance(B.boundary)
    check('B footprint retained within 15 cm',error<=.151,error)
    metrics['footprint_max_change_m']=error
    for f in ev['facades']:
        resource=f['resource'];path=EXPORTS.get(resource)
        check(f['name']+' stock resource resolves without AEP',path is not None and path.is_file(),resource)
        data=read_fac(str(path));fl=min(data['floors'],key=lambda p:abs(max(p['heights'])-f['height']))
        check(f['name']+' wall selectors valid',all(0<=w<len(fl['walls']) for w in f['walls']))
        if data['ring']:
            polygon=Polygon(f['points'])
            check(f['name']+' valid outward facade winding',polygon.is_valid and polygon.exterior.is_ccw)
        if f['name'].endswith((' upper',' ground')):
            pref=f['name'].rsplit(' ',1)[0]
            layers=[q for q in ev['facades'] if q['name'].startswith(pref) and not q['name'].startswith('bridge')]
            check(f['name']+' roof and wall terrain anchors match',all(q['points'][:2]==f['points'][:2] for q in layers))
        if f['name'].endswith(' upper'):
            check(f['name']+' native passenger glass and 14.2 m roof',6 in f['walls'] and abs(max(fl['heights'])-14.2)<.001)
        if f['name'].startswith('bridge_'):
            check(f['name']+' 8.01 m glass corridor',all(w==1 for w in f['walls']) and abs(max(fl['heights'])-8.01)<.001)
    for key in sorted(allowed-{'Earth nav data/apt.dat','Earth nav data/+20-100/+29-096.dsf'}):
        rows,v,ix,draw=objdata(PACK/key);oldrows,ov,oix,odraw=objdata(PREV/key)
        start=next(i for i,q in enumerate(ov) if q[1]<4.2999);sign=start+22
        expected=ov.copy();expected[sign:sign+4,1]+=1.1
        check(key+' retained supports and pivot connector',np.allclose(v,expected,atol=.000001))
        check(key+' valid draw indices',len(ix)%3==0 and max(ix)<len(v) and all(a+c<=len(ix) for a,c in draw))
        check(key+' old solid tunnel not drawn',all(not all(j<start for j in ix[i:i+3]) for i in range(0,len(ix),3)))
        check(key+' sign clears new corridor roof',min(v[sign:sign+4,1])>=8.3)
    nodes={q['id']:ag.xy(q['lon'],q['lat']) for q in apt if q['code']==1201};adj=defaultdict(set)
    edges=[q for q in apt if q['code']==1202]
    check('Aircraft network endpoints all exist',all(q['start'] in nodes and q['end'] in nodes for q in edges))
    for e in edges:
        adj[e['start']].add(e['end'])
        if e['parts'][3]=='twoway':adj[e['end']].add(e['start'])
    check('R1 arrival connects from NB',path_exists(adj,1451,856))
    check('R1 departure connects to NB',path_exists(adj,856,1452))
    check('Obsolete duplicate branch nodes removed',855 not in nodes and 859 not in nodes)
    check('ND connects through its retained spine',path_exists(adj,326,125))
    check('NG connects through its retained spine',path_exists(adj,112,111))
    paint={q['lines'][0]:q for q in apt if q['code']==120}
    lane_metrics=[]
    for lane in ev['taxi']:
        line=LineString(lane['points'])
        candidates=[q for name,q in paint.items() if ('R28 B North '+lane['name']+' -') in name] if lane['name']!='R1' else [q for name,q in paint.items() if name=='120 R03 aircraft circulation 106']
        if not candidates and lane['name']=='R1':
            candidates=[q for q in apt if q['code']==120 and q.get('geom') is not None and q['geom'].hausdorff_distance(line)<.1]
        check(lane['name']+' has exactly one matching painted spine',len(candidates)==1,len(candidates))
        if candidates:
            native=unary_union([a for a,s in segments(candidates[0]) if '51' in s])
            deviation=line.hausdorff_distance(native)
            check(lane['name']+' paint follows aircraft graph within 2 cm',deviation<.02,deviation)
        nearest=min((aircraft_outline(q['geom'].coords[0],q['heading']).distance(line),q['name']) for q in STARTS)
        lane_metrics.append(dict(lane=lane['name'],nearest_parked_example=nearest[1],centerline_to_example_outline_m=nearest[0],remaining_with_36m_transit_span_m=nearest[0]-18))
    for name,ids in [('arrival',[1451,*range(1453,1464),1450]),('departure',[1450,*range(1464,1475),1452])]:
        p=paint['120 R28 B North R1 '+name];curve=unary_union([g for g,s in segments(p)])
        graph=LineString([nodes[i] for i in ids]);diff=graph.hausdorff_distance(curve)
        check('R1 '+name+' curve follows network within 20 cm',diff<.2,diff)
        metrics['R1_'+name+'_paint_graph_max_error_m']=diff
    metrics['static_lane_screen']=lane_metrics
    notes.append('Static illustrative silhouettes use 56.7 m length / 35.8 m span at each existing B start. They are not aircraft-specific swept paths, wingtip certification or a guarantee of simultaneous operation.')
    notes.append('C-side parallel NG guidance and all adjacent terminal routes are preserved. The screenshot does not establish operational permission for simultaneous adjacent aircraft.')
    metrics['B_North_gate_count']=len(STARTS)
    metrics['native_facade_instances']=len(ev['facades'])
    metrics['roof_HVAC']=sum('HVAC' in f['name'] for f in ev['facades'])
    metrics['roof_skylights']=sum('skylight' in f['name'] for f in ev['facades'])
    result=dict(revision='R28',status='PASS' if all(q['pass_'] for q in checks) else 'FAIL',passed=sum(q['pass_'] for q in checks),total=len(checks),metrics=metrics,notes=notes,checks=checks,runtime_acceptance='Pending X-Plane testing; no install or publication performed.')
    (ROOT/'qa/Validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
    print('FAILURES',json.dumps([q for q in checks if not q['pass_']],indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
