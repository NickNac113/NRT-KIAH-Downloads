import sys, os, pathlib, math, json, re
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'pydeps'))
os.environ['MPLCONFIGDIR']=str(ROOT/'mpl-cache')
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, shape, mapping
from shapely.ops import unary_union, transform
from shapely import make_valid
LON0,LAT0=-95.341444444,29.984444444
_phi=math.radians(LAT0)
# Local WGS84 degree lengths at the airport; native apt/DSF coordinates remain WGS84.
SX=111412.84*math.cos(_phi)-93.5*math.cos(3*_phi)+.118*math.cos(5*_phi)
SY=111132.92-559.82*math.cos(2*_phi)+1.175*math.cos(4*_phi)-.0023*math.cos(6*_phi)
def xy(lon,lat): return ((lon-LON0)*SX,(lat-LAT0)*SY)
def ll(x,y): return (x/SX+LON0,y/SY+LAT0)
def project(g): return transform(lambda x,y,z=None: ((np.asarray(x)-LON0)*SX,(np.asarray(y)-LAT0)*SY),g)
def unproject(g): return transform(lambda x,y,z=None: (np.asarray(x)/SX+LON0,np.asarray(y)/SY+LAT0),g)
def safe_poly(points):
    if len(points)<3:return Polygon()
    g=make_valid(Polygon(points))
    return polys_only(g)
def polys_only(g):
    if g.geom_type in ('Polygon','MultiPolygon'):return g
    return unary_union([p for p in getattr(g,'geoms',[]) if p.geom_type in ('Polygon','MultiPolygon')])
def polygon_parts(g): return [g] if g.geom_type=='Polygon' else list(getattr(g,'geoms',[]))
def parse_apt(path):
    lines=pathlib.Path(path).read_text().splitlines(); blocks=[]; i=0
    while i<len(lines):
        line=lines[i]; s=line.split(); code=int(s[0]) if s and s[0].isdigit() else -1
        block={'code':code,'lines':[line],'parts':s}
        if code in (110,120,130):
            i+=1
            while i<len(lines) and lines[i].split() and lines[i].split()[0] in ('111','112','113','114','115','116'):
                block['lines'].append(lines[i]); i+=1
            loops=[]; pts=[]
            for row in block['lines'][1:]:
                v=row.split(); pts.append(xy(float(v[2]),float(v[1])))
                if v[0] in ('113','114','115','116'):
                    loops.append(pts); pts=[]
            if pts:loops.append(pts)
            block['loops']=loops
            if code in (110,130) and loops:
                outer=safe_poly(loops[0]); holes=unary_union([safe_poly(p) for p in loops[1:]])
                block['geom']=outer.difference(holes)
            elif loops: block['geom']=unary_union([LineString(p) for p in loops if len(p)>1])
            blocks.append(block);continue
        if code==1300:
            block.update(lat=float(s[1]),lon=float(s[2]),heading=float(s[3]),kind=s[4],equipment=s[5],name=' '.join(s[6:]))
            block['geom']=Point(xy(block['lon'],block['lat']))
            if i+1<len(lines) and lines[i+1].startswith('1301 '):
                i+=1;block['lines'].append(lines[i]);block['rampmeta']=lines[i].split()
        if code==100:
            block['geom']=LineString([xy(float(s[10]),float(s[9])),xy(float(s[19]),float(s[18]))]).buffer(float(s[1])/2,cap_style=2)
            block['name']=s[8]+'/'+s[17]
        if code==1201:block.update(lat=float(s[1]),lon=float(s[2]),id=int(s[4]))
        if code==1202:block.update(start=int(s[1]),end=int(s[2]),name=' '.join(s[5:]))
        blocks.append(block);i+=1
    return blocks
def parse_dsf(path):
    lines=pathlib.Path(path).read_text().splitlines(); objdefs=[]; polydefs=[]; head=[]; entities=[];i=0
    while i<len(lines):
        line=lines[i];s=line.split();key=s[0] if s else ''
        if key=='OBJECT_DEF':objdefs.append(line.split(' ',1)[1]);head.append(line)
        elif key=='POLYGON_DEF':polydefs.append(line.split(' ',1)[1]);head.append(line)
        elif key in ('OBJECT','OBJECT_MSL','OBJECT_AGL'):
            entities.append({'kind':'object','lines':[line],'index':int(s[1]),'coords':[float(v) for v in s[2:]],'geom':Point(xy(float(s[2]),float(s[3])))})
        elif key=='BEGIN_POLYGON':
            rows=[line];i+=1;loops=[];pts=[]
            while i<len(lines):
                row=lines[i];rows.append(row);v=row.split();k=v[0] if v else ''
                if k=='POLYGON_POINT':pts.append(xy(float(v[1]),float(v[2])))
                if k=='END_WINDING':loops.append(pts);pts=[]
                if k=='END_POLYGON':break
                i+=1
            geom=safe_poly(loops[0]) if loops else Polygon()
            if loops and len(loops[0])==2:geom=LineString(loops[0])
            elif len(loops)>1:geom=geom.difference(unary_union([safe_poly(x) for x in loops[1:]]))
            entities.append({'kind':'polygon','lines':rows,'index':int(s[1]),'param':int(s[2]),'loops':loops,'geom':geom})
        else:head.append(line)
        i+=1
    for e in entities:e['resource']=(objdefs if e['kind']=='object' else polydefs)[e['index']]
    return {'head':head,'objects':objdefs,'polygons':polydefs,'entities':entities}
def current_sources():
    r=ROOT/'references'; pois=json.loads((r/'pois.json').read_text()); gates=[];buildings={};floors={}
    for letter in 'ABCDE':
        for level in (1,2,3):
            name=f'iah-t{letter.lower()}-{level}'; f=json.loads((r/(name+'.json')).read_text());floors[name]=f
            polys=[project(shape(v['geometry'])) for v in f['features'] if v['properties'].get('category')=='element.building' and v['geometry']['type']=='Polygon']
            buildings[name]=unary_union([polys_only(make_valid(g)) for g in polys])
    for v in pois.values():
        if v.get('category')=='gate':
            p=v['position'];gates.append({'name':v['name'].replace('Gate ',''),'id':v['poiId'],'floor':p['floorId'],'lon':p['longitude'],'lat':p['latitude'],'point':Point(xy(p['longitude'],p['latitude']))})
    return buildings,gates,floors
def draw_geom(ax,g,**kw):
    import matplotlib.patches as patches
    if g.is_empty:return
    if g.geom_type in ('Polygon','MultiPolygon'):
        for p in polygon_parts(g):
            ax.add_patch(patches.Polygon(p.exterior.coords,closed=True,**kw))
    elif g.geom_type in ('LineString','MultiLineString'):
        gs=[g] if g.geom_type=='LineString' else g.geoms
        for l in gs:ax.plot(*l.xy,color=kw.get('edgecolor',kw.get('facecolor','#999')),lw=kw.get('linewidth',.4))
if __name__=='__main__':
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    apt=parse_apt(ROOT/'KIAH-99761/KIAH.dat');dsf=parse_dsf(ROOT/'compiler-check/+29-096.txt');b,g,f=current_sources()
    fig,ax=plt.subplots(figsize=(18,9));fig.patch.set_facecolor('#111b25');ax.set_facecolor('#111b25')
    for a in apt:
        if a['code'] in (100,110):draw_geom(ax,a['geom'],facecolor='#37434a',edgecolor='#566169',linewidth=.2)
    for e in dsf['entities']:
        if e['resource'].endswith('.fac') and any(x in e['resource'] for x in ('term_building','term_bridge','term_roof')):
            draw_geom(ax,e['geom'],facecolor='#7c6659',edgecolor='#b59380',linewidth=.3)
    for letter in 'ABCDE':
        for level in (1,2):draw_geom(ax,b[f'iah-t{letter.lower()}-{level}'],facecolor='none',edgecolor='#30e0b0',linewidth=.9)
    for p in g:
        x,y=p['point'].coords[0];ax.text(x,y,p['name'],color='white',fontsize=5,ha='center',va='center')
    ax.set_xlim(xy(-95.353,29.98)[0],xy(-95.329,29.98)[0]);ax.set_ylim(xy(-95.34,29.9828)[1],xy(-95.34,29.991)[1]);ax.set_aspect('equal');ax.tick_params(colors='white');ax.set_title('Current official outlines (green) / Gateway buildings (brown)',color='white')
    fig.tight_layout();fig.savefig(ROOT/'footprint-audit.png',dpi=160)
    print('Building areas:',{k:round(v.area) for k,v in b.items()});print('Terminal gates',len(g))
