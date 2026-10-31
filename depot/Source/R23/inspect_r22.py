from pathlib import Path
import sys,json,importlib.util
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=ROOT.parent/'KIAH_R21_Jet_Center_R17/source/build_r21.py'
s=importlib.util.spec_from_file_location('base',p);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
P=ROOT.parent/'KIAH_R22_Original_Garage_R18/package/KIAH_NRT_R22_Original_Garage_R18'
B=json.loads((P/'Build_Evidence.json').read_text())
print('Evidence keys',list(B))
placements={q['resource']:q for q in B['placements']+B['new_placements']}
data=g.ag.parse_dsf(ROOT.parent/'KIAH_R22_Original_Garage_R18/qa/R22_Roundtrip.txt')
local=[]
for q in data['entities']:
 if q['geom'].intersects(g.box(2400,275,2890,560)):
  if q['resource'].endswith('.fac') or q['kind']=='object' or 'pavement' in q['resource']:
   local.append(dict(resource=q['resource'],bounds=list(q['geom'].bounds),lines=q['lines'] if 'Fence' in q['resource'] else q['lines'][:1]))
print(json.dumps(local,indent=1))
for q in placements.values():
 if not (P/q['resource']).exists():continue
 rows=(P/q['resource']).read_text().splitlines()
 vs=g.np.array([list(map(float,s.split()[1:4])) for s in rows if s.startswith('VT ')])
 if len(vs)==0:continue
 vs[:,0]+=q['origin'][0];vs[:,2]=q['origin'][1]-vs[:,2]
 if any(x in q['resource'] for x in ['paint','fence','fbo','wear','safety']):
  print(q['resource'],q['origin'],vs.min(0).round(2).tolist(),vs.max(0).round(2).tolist())
(ROOT/'qa/R22_Local_Entities.json').write_text(json.dumps(local,indent=2))
(ROOT/'qa/R22_Placements.json').write_text(json.dumps(placements,indent=2))
