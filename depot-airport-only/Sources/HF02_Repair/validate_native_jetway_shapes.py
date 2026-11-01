from sign_groups import *
from shapely.geometry import MultiPoint
import gzip,hashlib
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF02'
scene=json.loads((ROOT/'work/scene-hf02.json').read_text())
data=json.load(gzip.open(ROOT/'work/native-review-context.json.gz','rt'))
assert json.loads((ROOT/'work/native-review-inputs.json').read_text())['After']==hashlib.sha256((STAGE/'Earth nav data/apt.dat').read_bytes()).hexdigest()
moves=[]
for x in data:
    if x['name'].startswith('After native moving jetway'):
        vs=np.array(x['vertices']);ps=vs[(vs[:,2]>4)&(vs[:,2]<7.4),:2]
        moves.append(MultiPoint(ps).convex_hull)
conflicts=[]
for i,j in enumerate(scene['jetways']):
    for k,q in enumerate(scene['jetways']):
        if i==k:continue
        fixed=LineString([q['door'],q['base']]).buffer(1.5,cap_style=2)
        area=moves[i].intersection(fixed).area
        if area>.2:conflicts.append(dict(kind='moving vs fixed',gates=[j['name'],q['name']],area_m2=area))
    for k in range(i+1,len(moves)):
        area=moves[i].intersection(moves[k]).area
        if area>.2:conflicts.append(dict(kind='moving vs moving',gates=[j['name'],scene['jetways'][k]['name'] if k<32 else 'retained '+str(k-32)],area_m2=area))
report=json.loads((ROOT/'HF02_Final_Validation.json').read_text())
report['checks'].append(dict(check='Actual parked moving models clear neighboring new fixed and all moving bridges',passed=not conflicts,detail=conflicts))
report['total']=len(report['checks']);report['passed']=sum(x['passed'] for x in report['checks'])
(ROOT/'HF02_Final_Validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(conflicts,indent=2));print(f"{report['passed']}/{report['total']} checks passed")
if conflicts:raise SystemExit(1)
