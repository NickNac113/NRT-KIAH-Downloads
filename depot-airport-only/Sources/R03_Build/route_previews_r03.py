from route_common import *
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon as PatchPolygon
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
import csv

PREVIEW=OUT/'KIAH_Previews_R03';PREVIEW.mkdir(exist_ok=True)
apt=parse_apt(TARGET/'Earth nav data/apt.dat');nodes,edges=network(apt);ctx=scene_context(apt)
build=json.loads((R03/'build-report.json').read_text());valid=json.loads((R03/'validation.json').read_text())
BG='#101f2a';FG='#e5eef2';MUTED='#a7bec9';AIR='#edc66d';SERVICE='#46daba';NEW='#70eafa';DEPOT='#ff9673'

def polygon(ax,geo,color,alpha=1):
    for p in polygon_parts(geo):
        if p.geom_type!='Polygon':continue
        verts=[];codes=[]
        from shapely.geometry.polygon import orient
        p=orient(p,sign=1)
        for ring in [p.exterior,*p.interiors]:
            q=list(ring.coords);verts+=q;codes += [MPath.MOVETO]+[MPath.LINETO]*(len(q)-2)+[MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor='none',alpha=alpha))

def setup(title,subtitle,limits,figsize=(18,11)):
    fig=plt.figure(figsize=figsize,facecolor=BG);ax=fig.add_axes([.035,.115,.93,.735]);ax.set_facecolor(BG)
    fig.text(.035,.945,title,color=FG,fontsize=24,fontweight='bold');fig.text(.035,.9,subtitle,color=MUTED,fontsize=11)
    for a in apt:
        if a['code'] in (100,110):polygon(ax,a['geom'],'#526871' if a['code']==100 else '#293e4b')
    for g in ctx['buildings']:polygon(ax,g,'#7e949f')
    if limits:
        for p in ctx['planes']:
            if p['geom'].intersects(box(limits[0],limits[2],limits[1],limits[3])):polygon(ax,p['geom'],'#405968')
    ax.set_xlim(limits[:2]);ax.set_ylim(limits[2:]);ax.set_aspect('equal');ax.axis('off')
    return fig,ax

def routes(ax,mode='both',width=1.0):
    for code,color in [(1202,AIR),(1206,SERVICE)]:
        if (mode=='service' and code==1202) or (mode=='aircraft' and code==1206):continue
        ee=[e for e in edges if e['code']==code]
        ax.add_collection(LineCollection([list(line(e,nodes).coords) for e in ee],colors=color,linewidths=width,alpha=.9))
        for e in ee:
            g=line(e,nodes)
            if e['direction']=='oneway' and code==1202 and g.length>30:
                a=g.interpolate(.45,normalized=True);b=g.interpolate(.58,normalized=True);ax.annotate('',xy=b.coords[0],xytext=a.coords[0],arrowprops=dict(arrowstyle='->',color=AIR,lw=.8),annotation_clip=True)

def points(ax,limits,overview=False):
    for i,p in enumerate(build['parks']):
        x,y=p['point']
        if limits[0]<=x<=limits[1] and limits[2]<=y<=limits[3]:
            ax.scatter([x],[y],c=DEPOT,s=34,marker='s' if p['type']=='destination' else 'o',edgecolors=BG,lw=.5,zorder=6)
    for t in build['targets']:
        if t['name']=='E processor service':continue
        x,y=t['point']
        if limits[0]<=x<=limits[1] and limits[2]<=y<=limits[3]:
            offset={'C12':(8,10),'C14':(-25,-10),'C15':(-23,5),'B10':(9,-11),'B11':(-14,11),'B9':(11,8)}.get(t['name'],(4,5))
            ax.plot(x,y,'.',color=NEW,ms=5)
            if not overview or t['name'] in {'A20','B1','B5','B18','B23','D1','D6'}:
                ax.annotate(t['name'],(x,y),xytext=offset,textcoords='offset points',color=FG,fontsize=8,clip_on=True)

def footer(fig,text):
    fig.text(.035,.057,text,color=MUTED,fontsize=10)
    fig.text(.035,.025,'R03 • Native routing geometry • Offline preview • Not installed or simulator-tested',color=MUTED,fontsize=9)

limits=(-1040,1210,-200,840)
fig,ax=setup('KIAH / GROUND-SERVICE ROUTES','33 service approaches • 18 new moving vehicle starts • 5 circulation destinations • Terminal network connected',limits)
routes(ax,'service',1.1);points(ax,limits,overview=True)
for label,p in [('A',(-830,220)),('B NORTH',(-420,350)),('C',(350,240)),('D WEST',(270,370)),('E / PROCESSOR',(850,180))]:ax.text(*p,label,color=FG,fontsize=11,ha='center',bbox=dict(facecolor=BG,alpha=.85,edgecolor='none',pad=3))
footer(fig,'Green: vehicle routes   •   Orange circles: vehicle parking   •   Orange squares: destinations   •   Gray aircraft: parked-clearance guides')
fig.savefig(PREVIEW/'01_Service_Overview.png',dpi=160);plt.close(fig)

for filename,title,limits in [('02_B_North_Routes.png','B NORTH / SERVICE AND AIRCRAFT ROUTES',(-720,-55,310,750)),('03_D_West_Routes.png','D WEST + C CONNECTOR / ROUTING',(-195,490,335,770))]:
    fig,ax=setup(title,'Baggage • baggage loader • fuel • catering • GPU • pushback | Bidirectional service access checked',limits,(16,11))
    routes(ax,'both',1.1);points(ax,limits)
    footer(fig,'Gold: aircraft taxi routes   •   Green: service-vehicle routes   •   Orange: moving vehicle parking / destinations')
    fig.savefig(PREVIEW/filename,dpi=165);plt.close(fig)

allgeo=unary_union([a['geom'] for a in apt if a['code'] in (100,110)]);w,s,e,n=allgeo.bounds
fig,ax=setup('KIAH / AIRCRAFT TAXI NETWORK','988 segments audited • 240 starts checked • Five runway networks reachable with aircraft size and direction respected',(w-150,e+150,s-150,n+150),(16,15))
routes(ax,'aircraft',.65)
for r in ctx['runways']:
    p=r['geom'].centroid;ax.text(p.x,p.y,r['name'],fontsize=9,color=FG,ha='center',bbox=dict(facecolor=BG,edgecolor='none',pad=3))
for e in edges:
    if e['code']==1202 and any(s.startswith('1204 ') for s in e['attrs']):ax.plot(*line(e,nodes).xy,color='#ec946a',lw=.95)
footer(fig,'Gold: aircraft routes   •   Orange: runway-protection metadata   •   All routes checked for references, junctions, pavement and modeled clearance')
fig.savefig(PREVIEW/'04_Aircraft_Network.png',dpi=165);plt.close(fig)

# Native geometry and graph for the self-contained interactive review. Keep visible detail modest.
def rings(g):return [[[[round(x,2),round(y,2)] for x,y in ring.coords] for ring in [p.exterior,*p.interiors]] for p in polygon_parts(g) if p.geom_type=='Polygon']
w,s,e,n=allgeo.bounds
data=dict(nodes={str(i):[round(x,3),round(y,3)] for i,(x,y) in nodes.items()},edges=[dict(i=i,a=e['a'],b=e['b'],c=e['code'],d=e['direction'],s=e['kind'][-1].upper() if e['kind']!='runway' else 'F',r=e['name'] if e['kind']=='runway' else None) for i,e in enumerate(edges)],pavement=[poly for a in apt if a['code'] in (100,110) for poly in rings(a['geom'].simplify(2))],buildings=[poly for g in ctx['buildings'] for poly in rings(g.simplify(1))],planes=[poly for p in ctx['planes'] for poly in rings(p['geom'])],service=build['targets'],parks=build['parks'],runways=[r['name'] for r in ctx['runways']],bounds=[w-100,e+100,s-100,n+100])
with (R03/'Ramp_Access_Audit.csv').open(encoding='utf-8-sig') as f:access={r['ramp']:r for r in csv.DictReader(f)}
data['ramps']=[dict(name=r['name'],size=r['rampmeta'][1],p=list(r['geom'].coords[0]),edge=int(access[r['name']]['access_segment']),note=access[r['name']]['note']) for r in ctx['ramps']]
(R03/'review-data.json').write_text(json.dumps(data,separators=(',',':')))
print(PREVIEW)
