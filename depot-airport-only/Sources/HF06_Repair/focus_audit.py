import sys,pathlib,pickle,json
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF05_Repair\work')
from hf05_common import *
from route_common import network,aircraft_outline
ROOT=pathlib.Path(__file__).resolve().parents[1]
plan,apt,dsfs=pickle.loads((ROOT/'work/inventory.pkl').read_bytes())
scene=json.loads((ROOT.parent/'KIAH_R03_HF05_Repair/work/scene-hf03.json').read_text())
print('D5',next(j for j in scene['jetways'] if j['name']=='D5'))
print('models D5',[m for m in scene['models'] if 'D5' in m['path']])
ea=box(2570,650,2800,1900);nodes,edges=network(apt)
for name,d in dsfs:
 for i,e in enumerate(d['entities']):
  if e['geom'].intersects(ea) and ('red_3m' not in e['resource']): print('EA nearby',name,i,e['resource'],str(e['lines'][:2])[:300])
for i,a in enumerate(apt):
 if a['code']==20:
  p=Point(xy(float(a['parts'][2]),float(a['parts'][1])))
  if p.within(ea):print('sign',i,a['lines'])
 if a['code'] in (110,120) and a.get('geom') is not None and a['geom'].intersects(ea):print('EA surface/paint',i,a['lines'][0])
 if a['code']==1202 and LineString([nodes[a['start']],nodes[a['end']]]).intersects(ea):print('EA route',i,a['lines'],nodes[a['start']],nodes[a['end']])
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
for name,region in [('EA',box(2450,550,2950,2000)),('B',box(-700,400,-260,790))]:
 fig,ax=plt.subplots(figsize=(11,13));ax.set_facecolor('#859a70')
 for a in apt:
  if a['code']==110 and a['geom'].intersects(region):plot_poly(ax,smooth_pavement(a),'#d8d6cb','#aaa',.3)
  if a['code']==120 and a.get('geom') is not None and a['geom'].intersects(region):
   for line,style in sampled_apt_segments(a):
    if any(int(x)<100 for x in style):ax.plot(*line.xy,color='#b49221',lw=.6)
 for e in edges:
  g=LineString([nodes[e['a']],nodes[e['b']]])
  if e['code']==1202 and g.intersects(region):
   ax.plot(*g.xy,color='#2281a3',lw=1);p=g.interpolate(.5,normalized=True);ax.text(p.x,p.y,e['name'] or f"{e['a']}-{e['b']}",fontsize=6)
 for tile,d in dsfs:
  for i,e in enumerate(d['entities']):
   if e['geom'].intersects(region) and e['kind']=='object' and ('red_3m' in e['resource'] or 'closed' in e['resource'].lower()):ax.scatter(e['geom'].x,e['geom'].y,s=12,color='red')
 for m in plan['models'].values():
  if m['geom'].intersects(region):plot_poly(ax,m['geom'],'#507d80','#29494d')
 for a in apt:
  if a['code']==1300 and a['geom'].intersects(region):
   g=aircraft_outline(a['geom'].coords[0],a['heading'],a.get('rampmeta',['1301','C'])[1]);plot_poly(ax,g,'#dededeee','#333');ax.text(a['geom'].x,a['geom'].y,a['name'],fontsize=7)
 ax.set_xlim(region.bounds[0],region.bounds[2]);ax.set_ylim(region.bounds[1],region.bounds[3]);ax.set_aspect('equal');fig.savefig(ROOT/'work'/f'{name}-audit.png',dpi=140);plt.close(fig)
