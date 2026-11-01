from hf05_common import *
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
fig,ax=plt.subplots(figsize=(16,9));fig.patch.set_facecolor('#111e29');ax.set_facecolor('#2d4238')
apt=parse_apt(STAGE/'Earth nav data/apt.dat')
for i,s,g in visible_surfaces(apt):plot_poly(ax,g,'#6c7375' if s==1 or 20<=s<40 else '#b9c4c8')
def curve_polygon(e):
    rows=['110 22 0.25 90.0 AEP source'];ring=[]
    for l in e['lines']:
        if l.startswith('POLYGON_POINT'):
            v=l.split()[1:];assert len(v)==4
            ring.append(f'112 {v[1]} {v[0]} {v[3]} {v[2]}')
        elif l=='END_WINDING':
            ring[-1]='114'+ring[-1][3:];rows+=ring;ring=[]
    return precise_pavement({'lines':rows},.01)
asphalt=unary_union([curve_polygon(e) for e in aep['entities'] if e['resource'].endswith('Asphalt_L_Taxi_Top_Plain.pol') and e['geom'].intersects(mask)])
plot_poly(ax,asphalt.intersection(crop),'#b77544','#e9a45d',.8)
plot_poly(ax,mask,'none','#67ead4',2)
for n,m in plan['models'].items():
    if m['geom'].intersects(crop):plot_poly(ax,m['geom'],'#355e7c','#183449',1)
for a in apt:
    if a['code']==120 and a['lines'][0].startswith('120 Stand '):
        for g,s in sampled_apt_segments(a):
            if g.intersects(crop):ax.plot(*g.xy,color='#f5d65d',lw=.7)
for r in plan['new']:
    if box(-710,455,-65,835).contains(Point(r['pos'])):ax.text(*r['pos'],r['name'],color='#102333',fontsize=9,ha='center',va='center',clip_on=True,bbox=dict(fc='#edf7f8',ec='none',alpha=.9,pad=1))
ax.text(-165,718,'NB retained',fontsize=11,color='#112e3f',weight='bold')
ax.text(-580,795,'NA retained',fontsize=11,color='#112e3f',weight='bold')
ax.set_xlim(-730,-50);ax.set_ylim(440,850);ax.set_aspect('equal');ax.tick_params(colors='#b4c7d0')
ax.set_xlabel('Metres east of airport reference',color='#b4c7d0');ax.set_ylabel('Metres north of airport reference',color='#b4c7d0')
fig.suptitle('AEP overlay audit — B North',color='#edf7f8',fontsize=22,x=.09,ha='left')
ax.set_title('Orange: old AEP asphalt footprint targeted by the corrected exclusions. Outline: local apron cleanup.',color='#b4c7d0',fontsize=12,pad=14,loc='left')
legend=ax.legend(handles=[Patch(facecolor='#b77544',label='Old AEP overlay footprint'),Patch(facecolor='none',edgecolor='#67ead4',label='HF05 apron cleanup'),Patch(facecolor='#355e7c',label='Rebuilt terminal')],loc='lower right',framealpha=.95)
fig.text(.09,.02,'Source geometry audit, not a simulator screenshot. AEP remains enabled; only the intended local exclusions are corrected.',color='#b4c7d0',fontsize=11)
fig.subplots_adjust(top=.87,bottom=.1,left=.08,right=.97)
fig.savefig(ROOT/'previews-final/05_AEP_Overlay_Audit.png',dpi=130)
plt.close(fig)
