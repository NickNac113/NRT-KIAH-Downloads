import sys,pathlib,pickle,json
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF05_Repair\work')
from hf05_common import *
from route_common import network,aircraft_outline
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely import affinity
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'previews-final';OUT.mkdir(exist_ok=True)
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
plan,oldapt,dsfs=pickle.loads((ROOT/'work/inventory.pkl').read_bytes());apt=parse_apt(STAGE/'Earth nav data/apt.dat')
nodes,edges=network(apt);oldline,newlines,arr,dep=pickle.loads((ROOT/'work/b-lane.pkl').read_bytes())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
def base(ax,region):
    ax.set_facecolor('#91a27d');covered=Polygon()
    for a in apt:
        if a['code']!=110:continue
        g=smooth_pavement(a)
        if not g.intersects(region):continue
        surf=int(a['parts'][1])%100
        if surf in (0,3,4,5,13,15):continue
        g=g.intersection(region);visible=g.difference(covered);covered=covered.union(g)
        plot_poly(ax,visible,'#b5b6b1' if surf==1 or 20<=surf<40 else '#e0dfd4')
    for a in apt:
        if a['code'] not in (110,120):continue
        if a['lines'][0].startswith('120 HF06'):continue
        for line,style in sampled_apt_segments(a):
            if line.intersects(region) and any(int(x)<100 for x in style):ax.plot(*line.xy,color='#b9a345',lw=.55,alpha=.65)
    for m in plan['models'].values():
        if m['geom'].intersects(region):plot_poly(ax,m['geom'],'#4d7177','#314e54',.8)
    ax.set_xlim(region.bounds[0],region.bounds[2]);ax.set_ylim(region.bounds[1],region.bounds[3]);ax.set_aspect('equal')
    ax.set_xticks([]);ax.set_yticks([])

fig,ax=plt.subplots(figsize=(14,12));fig.patch.set_facecolor('#f7f7f2');region=box(-650,380,-180,765);base(ax,region)
swept=pickle.loads((ROOT/'work/swept-long.pkl').read_bytes());plot_poly(ax,swept,'#14898b22','#14898b',.7)
for a in apt:
    if a['code']==1300 and a['geom'].intersects(region):
        size=a.get('rampmeta',['1301','C'])[1]
        if size=='C':
            plane=affinity.scale(aircraft_outline((0,0),0,'C'),xfact=1,yfact=56/40,origin=(0,0))
            plane=affinity.translate(affinity.rotate(plane,-a['heading'],origin=(0,0)),*a['geom'].coords[0])
        else:plane=aircraft_outline(a['geom'].coords[0],a['heading'],size)
        plot_poly(ax,plane,'#fbfbf5','#53616a',.7)
        ax.annotate(a['name'].removeprefix('Gate '),a['geom'].coords[0],xytext=(0,7),textcoords='offset points',ha='center',weight='bold',fontsize=9,color='#263d44')
ax.plot(*oldline.xy,color='#d45c40',lw=2.5,ls='--',zorder=7)
for l in newlines:ax.plot(*l.xy,color='#097d83',lw=3,zorder=8)
for l in (LineString(arr),LineString(dep)):
    a=l.interpolate(.38,normalized=True);b=l.interpolate(.62,normalized=True);ax.annotate('',(b.x,b.y),(a.x,a.y),arrowprops=dict(arrowstyle='-|>',color='#075257',lw=2),zorder=9)
ax.annotate('NB  →',(-535,724),fontsize=13,weight='bold',color='#26464d')
ax.annotate('Straight apron lane\n36 m wingspan route',(-375,550),(-357,480),arrowprops=dict(arrowstyle='-',color='#075257'),fontsize=11,color='#075257')
ax.annotate('Rounded arrival / departure\n30 m modeled radius',(-375,690),(-325,746),ha='center',arrowprops=dict(arrowstyle='-',color='#075257'),fontsize=10,color='#075257')
ax.set_title('B NORTH  /  HF06 taxi-lane correction',loc='left',fontsize=22,weight='bold',pad=25)
ax.legend(handles=[Line2D([0],[0],color='#097d83',lw=3,label='HF06 paint and aircraft route'),Line2D([0],[0],color='#d45c40',lw=2,ls='--',label='Removed HF05 bend'),Line2D([0],[0],color='#14898b',lw=7,alpha=.25,label='Sampled moving-aircraft footprint')],loc='lower left',fontsize=10,framealpha=.95)
fig.text(.12,.047,'Reference: United Terminal B gallery rendering, uploaded October 2024. Geometry is interpreted, not surveyed.',fontsize=10,color='#45535a')
fig.text(.12,.027,'Shaded sweep: 56 m long / 36 m span generic aircraft. Static clearance passes; actual AI turning still needs simulator testing.',fontsize=10,color='#45535a')
fig.savefig(OUT/'03_B_North_Route.png',dpi=150,bbox_inches='tight');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(15,9));fig.patch.set_facecolor('#f7f7f2')
for ax,region,title,ends in [(axs[0],box(2565,625,2830,1100),'SOUTH  /  NB to EC',(264,338)),(axs[1],box(2565,1450,2830,1925),'NORTH  /  ED to EE',(349,345))]:
    base(ax,region)
    for e in edges:
        if e['code']!=1202:continue
        l=LineString([nodes[e['a']],nodes[e['b']]])
        if not l.intersects(region):continue
        col='#087e82' if e['name']=='EA' else '#708596';ax.plot(*l.xy,color=col,lw=3 if e['name']=='EA' else 1.4)
        if e['name'] in ('NB','EC','ED','EE','EB'):
            p=l.intersection(region).interpolate(.55,normalized=True);ax.text(p.x,p.y+10,e['name'],fontsize=10,color='#344d5b',ha='center')
    for tile,d in dsfs:
        for e in d['entities']:
            if e['kind']=='object' and e['resource'].endswith('/red_3m.obj') and e['geom'].intersects(region):ax.scatter(e['geom'].x,e['geom'].y,marker='x',s=32,color='#cd5a3c',zorder=6)
    ax.set_title(title,loc='left',fontsize=16,pad=18,weight='bold');ax.text(2630,region.centroid.y,'EA',rotation=90,color='#075457',weight='bold',fontsize=17)
fig.suptitle('EAST CARGO  /  EA open for your VATSIM variant',fontsize=23,x=.12,ha='left',y=.99,weight='bold')
fig.legend(handles=[Line2D([0],[0],color='#087e82',lw=3,label='Added bidirectional EA route'),Line2D([0],[0],marker='x',color='#cd5a3c',ls='',label='22 removed barricades across both ends')],loc='lower center',ncol=2,bbox_to_anchor=(.5,.055))
fig.text(.12,.025,'Pavement, existing centerline and taxiway signs retained. This is an intentional simulator exception to the real-world closure.',fontsize=10,color='#45535a')
fig.subplots_adjust(top=.89,bottom=.12,wspace=.18);fig.savefig(OUT/'05_EA_VATSIM.png',dpi=150,bbox_inches='tight');plt.close(fig)
print('Created B and EA review maps.')
