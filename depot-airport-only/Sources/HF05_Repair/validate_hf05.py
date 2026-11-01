from hf05_common import *
apt=parse_apt(STAGE/'Earth nav data/apt.dat')
report=json.loads((ROOT/'HF05_Changes.json').read_text());checks=[]
def check(name,ok,detail=None):
    checks.append(dict(check=name,passed=bool(ok),detail=detail))
    if not ok:print('FAIL',name,detail)

edits={r['source_index'] for r in report['native_asphalt']}
check('All airport records except the single clipped asphalt source are byte-identical',
      [a['lines'] for i,a in enumerate(oldapt) if i not in edits]==[a['lines'] for a in apt if 'HF05 clipped' not in a['lines'][0]])
changed=[a for a in apt if 'HF05 clipped' in a['lines'][0]]
after=unary_union([precise_pavement(a) for a in changed])
independent=unary_union([precise_pavement(oldapt[i],.000125) for i in edits])
expected=polys_only(independent.difference(mask))
check('Clipped asphalt is valid with CCW outer rings and CW holes',all(a['geom'].is_valid and Polygon(a['loops'][0]).exterior.is_ccw and all(not Polygon(r).exterior.is_ccw for r in a['loops'][1:]) for a in changed),len(changed))
remaining=after.intersection(mask.buffer(-.001)).area
check('No source asphalt survives inside the B North cleanup area',remaining<.001,remaining)
outside=after.symmetric_difference(expected)
maxdist=after.boundary.hausdorff_distance(expected.boundary)
check('Outside asphalt agrees with an independently finer curve sampling within 1 mm',maxdist<.001,dict(max_boundary_distance_m=maxdist,symmetric_difference_sqm=outside.area))
concrete=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and (int(a['parts'][1])==2 or 50<=int(a['parts'][1])<60)])
check('Removed asphalt area remains covered by concrete apron',independent.intersection(mask).difference(concrete.buffer(.003)).area<.01)
check('All runways, routes, starts, flows and moving jetway records remain unchanged',
      all([a['lines'] for a in oldapt if a['code']==c]==[a['lines'] for a in apt if a['code']==c] for c in (100,1201,1202,1204,1205,1206,1300,1400,1401,1500)),
      {str(c):sum(a['code']==c for a in apt) for c in (100,1201,1202,1206,1300,1400,1401,1500)})

all_fixed={};n=0;bad_before=0;max_entity_delta=0;meta=[]
for entry in report['exclusion_syntax_repairs']:
    tile=entry['tile'];before=ROOT/'work'/f'{tile}-before.txt';rt=ROOT/'work'/f'{tile}-roundtrip.txt'
    oldrows=[l for l in before.read_text().splitlines() if l.startswith('PROPERTY sim/exclude_')]
    newrows=[l for l in rt.read_text().splitlines() if l.startswith('PROPERTY sim/exclude_')]
    assert len(oldrows)==len(newrows)
    for l,r in zip(oldrows,newrows):
        k,g=parse_exclusion(l,strict=False);k2,g2=parse_exclusion(r)
        assert k==k2 and g.equals(g2)
        all_fixed.setdefault(k,[]).append(g2)
        if ';' in r:assert g2.exterior.is_ccw;n+=1
        try:parse_exclusion(l)
        except ValueError:bad_before+=1
    # Decode the property-patched binary and compare every placement,
    # resource order, command type, dimension and data plane.
    b=parse_dsf(before);a=parse_dsf(rt)
    assert b['objects']==a['objects'] and b['polygons']==a['polygons']
    assert len(b['entities'])==len(a['entities'])
    stable=True
    for e,f in zip(b['entities'],a['entities']):
        assert e['resource']==f['resource'] and e['kind']==f['kind']
        assert len(e['lines'])==len(f['lines'])
        for s,t in zip(e['lines'],f['lines']):
            if s==t:continue
            v=s.split();w=t.split();assert v[0]==w[0] and len(v)==len(w)
            assert v[0] in ('POLYGON_POINT','OBJECT','OBJECT_MSL','OBJECT_AGL'),(s,t)
            ns=list(map(float,v[1:]));nt=list(map(float,w[1:]))
            delta=max(abs(x-y) for x,y in zip(ns,nt));max_entity_delta=max(max_entity_delta,delta)
            stable&=delta<1e-8
    oldnon=[l for l in before.read_text().splitlines() if l.startswith(('PROPERTY ','FILTER ')) and not l.startswith('PROPERTY sim/exclude_')]
    newnon=[l for l in rt.read_text().splitlines() if l.startswith(('PROPERTY ','FILTER ')) and not l.startswith('PROPERTY sim/exclude_')]
    assert oldnon==newnon
    meta.append(dict(tile=tile,placements=len(a['entities']),unchanged=stable))
check('All 4732 exclusion records match WED exporter syntax after binary round-trip',n==4732 and bad_before==4732,dict(corrected=n,previous_invalid=bad_before))
check('Exclusion footprints, categories, record order and airport filters are preserved',True)
check('All DSF placements and asset references preserved through binary round-trip',all(x['unchanged'] for x in meta),dict(tiles=meta,max_numeric_delta=max_entity_delta))
fixed={k:unary_union(v) for k,v in all_fixed.items()}

def eliminated(e,areas):
    kind='obj' if e['kind']=='object' else e['resource'].rsplit('.',1)[-1]
    if kind not in areas:return False
    ps=[e['geom']] if kind=='obj' else [Point(p) for loop in e.get('loops',[]) for p in loop]
    return any(areas[kind].contains(p) for p in ps)

targets=[(i,e) for i,e in enumerate(aep['entities']) if e['geom'].intersects(mask)]
checks_by_kind=collections.Counter(e['resource'].rsplit('.',1)[-1] for _,e in targets)
left=[dict(index=i,resource=e['resource']) for i,e in targets if not eliminated(e,fixed)]
check('AEP overlay primitives touching the B North repair are covered by corrected exclusions',not left,dict(total=len(targets),by_kind=dict(checks_by_kind),remaining=left))
asphalt=[(i,e) for i,e in targets if 'Asphalt' in e['resource']]
check('Both AEP legacy asphalt and asphalt snow overlays are explicitly suppressed',len(asphalt)==2 and all(eliminated(e,fixed) for _,e in asphalt),[dict(index=i,resource=e['resource']) for i,e in asphalt])
changed_runtime=[]
for folder in ('Earth nav data','objects','textures'):
    for p in (SOURCE/folder).rglob('*'):
        if p.is_file() and sha(p)!=sha(STAGE/p.relative_to(SOURCE)):changed_runtime.append(p.relative_to(SOURCE).as_posix())
check('Runtime changes limited to airport pavement and southern DSF exclusions',set(changed_runtime)=={'Earth nav data/apt.dat','Earth nav data/+20-100/+29-096.dsf'},changed_runtime)
check('All custom models and textures preserved',all(sha(p)==sha(STAGE/p.relative_to(SOURCE)) for folder in ('objects','textures') for p in (SOURCE/folder).rglob('*') if p.is_file()))
check('Installed HF04 package remains untouched',snapshot_tree(LIVE)==json.loads((ROOT/'live_before.json').read_text()))
check('Scenery order and AEP installation remain untouched',sha(LIVE.parent/'scenery_packs.ini')==(ROOT/'ini_before.sha256').read_text() and all(sha(pathlib.Path(p))==h for p,h in json.loads((ROOT/'aep_before.json').read_text()).items()))
validation=dict(revision='KIAH R03 HF05',status='OFFLINE ONLY - SIMULATOR TEST PENDING',passed=sum(c['passed'] for c in checks),total=len(checks),checks=checks)
(ROOT/'HF05_Validation.json').write_text(json.dumps(validation,indent=2))
print(json.dumps(validation,indent=2));assert all(c['passed'] for c in checks)
(ROOT/'work/aep-validated-exclusions.pkl').write_bytes(pickle.dumps(fixed))
