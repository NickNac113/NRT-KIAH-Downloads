from pathlib import Path
import importlib.util,sys,json,math
from collections import defaultdict,deque
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R26_Lighting_Access_R23'
s=importlib.util.spec_from_file_location('r26',PREV/'source/build_r26.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;P=PREV/'package/KIAH_NRT_R26_Lighting_Access_R23';OUT=ROOT/'output';OUT.mkdir(parents=True,exist_ok=True)
ap=g.ag.parse_apt(P/'Earth nav data/apt.dat');ds=g.ag.parse_dsf(PREV/'qa/R26_Roundtrip.txt')
nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in ap if q['code']==1201}
paved=b.union([q['geom'] for q in ap if q['code'] in [100,110]]+[q['geom'] for q in ds['entities'] if q['kind']=='polygon' and any(k in q['resource'].lower() for k in ['/pavement/','concrete','asphalt','road'])])
paved_margin=paved.buffer(.2)
edges=[];adj=defaultdict(set)
for q in ap:
 if q['code']==1206:
  a,c=map(int,q['parts'][1:3]);ln=b.Line([nodes[a],nodes[c]]);adj[a].add(c);adj[c].add(a)
  edges.append(dict(a=a,b=c,start=nodes[a],end=nodes[c],name=q['lines'][0],length=ln.length,unpaved=ln.difference(paved_margin).length))
components=[];todo=set(adj)
while todo:
 seed=next(iter(todo));seen={seed};queue=deque([seed])
 while queue:
  for n in adj[queue.popleft()]-seen:seen.add(n);queue.append(n)
 todo-=seen;components.append(seen)
cn={n:i for i,c in enumerate(components) for n in c}
stops=[]
for q in ap:
 if q['code'] in [1300,1400,1401]:
  r=q['parts'];xy=g.ag.xy(float(r[2]),float(r[1]));pt=b.Point(xy);near=sorted((pt.distance(b.Point(nodes[n])),n) for n in adj)[:3]
  stops.append(dict(code=q['code'],name=q['lines'][0],xy=xy,nearest=[dict(node=n,distance=d,component=cn[n],xy=nodes[n],direct_unpaved=b.Line([xy,nodes[n]]).difference(paved_margin).length) for d,n in near]))
region=b.box(1100,150,3300,1250)
local=[e for e in edges if b.Line([e['start'],e['end']]).intersects(region)]
data=dict(jetways=json.loads((P/'Build_Evidence.json').read_text())['jetways'],components=[dict(count=len(c),bounds=b.union([b.Point(nodes[n]) for n in c]).bounds,contains919=919 in c) for c in components],edges=local,stops=stops,masts=[dict(resource=q['resource'],xy=[q['geom'].x,q['geom'].y],heading=q.get('heading'),raw=q.get('lines')) for q in ds['entities'] if q['kind']=='object' and 'flood_1_led_24m' in q['resource']])
(OUT/'Route_Diagnosis.json').write_text(json.dumps(data,indent=2))
print(json.dumps(dict(jetways=data['jetways'],components=data['components'],bad_local_edges=[e for e in local if e['unpaved']>2],local_stop_problems=[q for q in stops if q['code']!=1300 and 1000<q['xy'][0]<3300 and 150<q['xy'][1]<1200 and q['nearest'][0]['direct_unpaved']>2],masts=data['masts']),indent=2))
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(2200,1100),'#cad2bf');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
def p(xy):return (xy[0]-1100,1100-(xy[1]-150))
for poly in g.parts(paved.intersection(region)):
 d.polygon([p(v) for v in poly.exterior.coords],fill='#e4e6df')
 for ring in poly.interiors:d.polygon([p(v) for v in ring.coords],fill='#cad2bf')
for e in local:
 d.line([p(e['start']),p(e['end'])],fill='#b81f31' if e['unpaved']>2 else '#267292',width=2)
 if e['length']>50:d.text(p(e['start']),str(e['a']),fill='#102830',font=font)
for q in stops:
 if not region.covers(b.Point(q['xy'])):continue
 xy=p(q['xy']);d.ellipse([xy[0]-3,xy[1]-3,xy[0]+3,xy[1]+3],fill='#8d43a1' if q['code']==1300 else '#e17d23')
 if q['code']==1300 and q['name'].split()[-1].startswith('NRT'):d.text(xy,q['name'].split()[-1],fill='#153748',font=font)
im.save(OUT/'Route_Diagnosis.png')
