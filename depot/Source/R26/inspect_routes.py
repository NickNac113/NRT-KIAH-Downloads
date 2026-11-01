from pathlib import Path
import importlib.util,sys,json
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R25_Realism_R22'
s=importlib.util.spec_from_file_location('r25',PREV/'source/build_r25.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g
OUT=ROOT/'output';OUT.mkdir(parents=True,exist_ok=True)
ap=g.ag.parse_apt(b.PACK/'Earth nav data/apt.dat');dsf=g.ag.parse_dsf(PREV/'qa/R25_Roundtrip.txt')
nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in ap if q['code']==1201}
region=b.box(2150,200,3300,1100)
routes=[];stops=[]
for q in ap:
    r=q['parts']
    if q['code']==1206:
        a,z=int(r[1]),int(r[2]);geom=b.Line([nodes[a],nodes[z]])
        if geom.intersects(region):routes.append(dict(line=q['lines'][0],start=nodes[a],end=nodes[z],length=geom.length))
    if q['code'] in [1400,1401]:
        pt=g.ag.xy(float(r[2]),float(r[1]))
        if b.Point(pt).intersects(region):stops.append(dict(line=q['lines'][0],xy=pt))
print(json.dumps(dict(routes=[q for q in routes if 'NRT arrivals' not in q['line']],stops=stops),indent=2))
(OUT/'NB_Route_Audit.json').write_text(json.dumps(dict(routes=routes,stops=stops),indent=2))
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1800,1050),'#e9eee1');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
def pt(p):return ((p[0]-1600),1030-(p[1]-150))
def shape(geom,fill):
    for q in g.parts(geom):
        if q.geom_type!='Polygon':continue
        d.polygon([pt(p) for p in q.exterior.coords],fill=fill,outline='#9fa99d')
        for r in q.interiors:d.polygon([pt(p) for p in r.coords],fill='#e9eee1')
for q in ap:
    if q['code']==110 and q['geom'].intersects(region):shape(q['geom'],'#c4c9c3')
for q in dsf['entities']:
    if '/pavement/' in q['resource'] and q['geom'].intersects(region):shape(q['geom'],'#d5d8d2')
shape(b.FOOT,'#8caaaa')
for q in routes:
    a,z=q['start'],q['end'];d.line([pt(a),pt(z)],fill='#bd422c',width=2)
    if 'NRT' not in q['line']:d.text(pt(((a[0]+z[0])/2,(a[1]+z[1])/2)),'-'.join(q['line'].split()[1:3]),font=font,fill='#722010')
for q in ap:
    if q['code']==1300 and q['name'].startswith('NRT'):
        d.text(pt((q['geom'].x,q['geom'].y)),q['name'],font=font,fill='#18474b')
d.line([pt(p) for p in b.WALK],fill='#197f9f',width=2)
im.save(OUT/'NB_Route_Audit.png')
