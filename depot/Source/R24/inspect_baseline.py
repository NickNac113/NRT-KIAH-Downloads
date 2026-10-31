from pathlib import Path
import importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R23_Jet_Center_Refinement_R19'
s=importlib.util.spec_from_file_location('baseline',PREV/'source/build_r23.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
P=PREV/'package/KIAH_NRT_R23_Jet_Center_Refinement_R19'
d=b.g.ag.parse_dsf(PREV/'qa/R23_Roundtrip.txt')
ents=[]
for i,q in enumerate(d['entities']):
    if q['kind']=='polygon' and any(t in q['resource'].lower() for t in ['fence','deflect']):
        if b.box(2300,250,3200,850).intersects(q['geom']):
            ents.append(dict(i=i,r=q['resource'],param=q.get('param'),wkt=q['geom'].wkt,lines=q['lines']))
    elif q['kind']=='object' and q['resource'].startswith('objects/nrt_test/'):
        p=P/q['resource'];vs=[list(map(float,r.split()[1:4])) for r in p.read_text().splitlines() if r.startswith('VT ')]
        if not vs:continue
        v=b.np.array(vs);x,y=q['geom'].x,q['geom'].y
        ents.append(dict(i=i,r=q['resource'],origin=[x,y],heading=q['lines'][0],bounds=[x+v[:,0].min(),y-v[:,2].max(),x+v[:,0].max(),y-v[:,2].min()],z=[v[:,1].min(),v[:,1].max()]))
ap=b.g.ag.parse_apt(P/'Earth nav data/apt.dat')
apt=[dict(name=q.get('name'),lines=q['lines']) for q in ap if q['code']==1300 and q.get('name','').startswith('NRT')]
(ROOT/'qa').mkdir(exist_ok=True);(ROOT/'qa/Baseline_Spatial.json').write_text(json.dumps(dict(entities=ents,starts=apt),indent=2))
for q in ents:
    if 'wkt' in q or any(t in q['r'] for t in ['hangar','paint','fence','safety','mark','ids','identity']):print(json.dumps(q))
print(json.dumps(apt,indent=2))
