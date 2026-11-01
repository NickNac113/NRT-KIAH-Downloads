import sys,pathlib,shutil,json,pickle,hashlib
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF05_Repair\work')
from hf05_common import *
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\outputs\KIAH_2026-10-24_Review_R03_HF05')
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
ROOT.mkdir(exist_ok=True);(ROOT/'work').mkdir(exist_ok=True)
if not STAGE.exists():shutil.copytree(SOURCE,STAGE)
if not (ROOT/'live_before.json').exists():
 (ROOT/'live_before.json').write_text(json.dumps(snapshot_tree(LIVE),indent=2))
 (ROOT/'aep_before.json').write_text(json.dumps({p.name:snapshot_tree(p) for p in [LIVE.parent/'AEP',LIVE.parent/'AEP Overlays']},indent=2))
apt=parse_apt(STAGE/'Earth nav data/apt.dat')
dsfs=[]
for p in (SOURCE/'Earth nav data').rglob('*.dsf'):
 out=ROOT/'work'/f'{p.stem}-before.txt';dsf_decode(p,out);dsfs.append((p.stem,parse_dsf(out)))
ea=box(1500,0,4500,2100);bn=box(-750,420,-300,760)
for name,d in dsfs:
 for i,e in enumerate(d['entities']):
  if e['geom'].intersects(ea) and any(s in e['resource'].lower() for s in ('barrier','closed','closure','no_entry','noentry')):
   print('EA furniture',name,i,e['resource'],list(e['geom'].centroid.coords),e['lines'][:1])
for i,a in enumerate(apt):
 if a['code']==120 and a.get('geom') is not None and a['geom'].intersects(bn):
  print('B paint',i,a['lines'])
nodes={a['id']:xy(a['lon'],a['lat']) for a in apt if a['code']==1201}
for i,a in enumerate(apt):
 if a['code']==1202:
  geom=LineString([nodes[a['start']],nodes[a['end']]])
  if geom.intersects(bn) or ('EA' in a['name'] or 'EB'==a['name']):print('route',i,a['lines'],list(geom.coords))
(ROOT/'work/inventory.pkl').write_bytes(pickle.dumps((plan,apt,dsfs)))
