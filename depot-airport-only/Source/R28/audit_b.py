import sys, os, json, collections
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
for name in ['qa','output','reference']: (ROOT/name).mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'qa/mpl-cache')
OLD=Path('C:/Users/Nick/Documents/Codex/2026-10-24/cou/work')
sys.path.insert(0,str(OLD))
import airport_geometry as ag
os.environ['MPLCONFIGDIR']=str(ROOT/'qa/mpl-cache')
from shapely.geometry import box,Point
BASE=ROOT.parent/'KIAH_R27_Shelter_Service_R24'
PACK=BASE/'package/KIAH_NRT_R27_Shelter_Service_R24'
DSF=ag.parse_dsf(BASE/'qa/R27_Roundtrip.txt')
APT=ag.parse_apt(PACK/'Earth nav data/apt.dat')
region=box(-720,300,100,720)
es=[q for q in DSF['entities'] if q['geom'].intersects(region)]
fac=[q for q in es if q['resource'].endswith('.fac')]
report={'B_object':[dict(resource=q['resource'],coords=q['coords']) for q in es if 'B_North' in q['resource']],
 'neighbor_facades':[dict(resource=q['resource'],param=q['param'],bounds=q['geom'].bounds,example=q['lines'][:7]) for q in fac],
 'resource_counts':dict(collections.Counter(q['resource'] for q in es)),
 'lines':[dict(header=q['lines'][0],bounds=q['geom'].bounds) for q in APT if q['code']==120 and q.get('geom') is not None and q['geom'].intersects(region)],
 'B_starts':[dict(name=q['name'],xy=list(q['geom'].coords[0]),heading=q['heading']) for q in APT if q['code']==1300 and q['name'].startswith('Gate B') and q['geom'].y>320]}
(ROOT/'qa/Baseline_Audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['neighbor_facades','lines','resource_counts']},indent=2))
print('Facade summary',dict(collections.Counter(q['resource'] for q in fac)))
print('B line names', [q['header'] for q in report['lines'] if 'B' in q['header']])
if __name__=='__main__':
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(16,11));ax.set_facecolor('#c8c6bc')
 for q in APT:
  if q['code']==110 and q['geom'].intersects(region): ag.draw_geom(ax,q['geom'],facecolor='#dddcd5',edgecolor='#bbb',linewidth=.3)
 for q in es:
  if q['resource'].endswith('.fac'): ag.draw_geom(ax,q['geom'],facecolor='#78909b' if 'term_' in q['resource'] else 'none',edgecolor='#607d8b',linewidth=.3)
 for q in APT:
  if q['code']==120 and q.get('geom') is not None and q['geom'].intersects(region): ag.draw_geom(ax,q['geom'],edgecolor='#ce9a16',linewidth=.6)
  if q['code']==1300 and q['geom'].intersects(region): ax.text(q['geom'].x,q['geom'].y,q['name'].removeprefix('Gate '),fontsize=7,ha='center')
 # Actual custom B footprint from the retained public reference.
 gj=json.loads(Path('X:/X-Plane 12/Custom Scenery/KIAH_2026-10-24_Review_R03/Sources/current-terminal-footprints.geojson').read_text())
 print('footprint properties',[f['properties'] for f in gj['features']][:5])
 for f in gj['features']:
  if 'B_North' in str(f['properties']): ag.draw_geom(ax,ag.project(ag.shape(f['geometry'])),facecolor='#607d8b',edgecolor='#173c49',linewidth=1)
 ax.set(xlim=(-730,130),ylim=(300,730));ax.set_aspect('equal');fig.tight_layout();fig.savefig(ROOT/'output/Baseline_Plan.png',dpi=150)
