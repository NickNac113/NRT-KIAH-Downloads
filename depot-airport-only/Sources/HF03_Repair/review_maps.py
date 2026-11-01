"""Maps of the staged native data; no simulator traffic is modeled."""
import pathlib, sys, pickle, json
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'KIAH_R03_HF02_Repair/work'))
from sign_groups import *
from route_common import smooth_pavement
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'previews-final'
plan,d,apt,scene=pickle.loads((ROOT/'work/current.pkl').read_bytes())
newjets,hulls,planes=pickle.loads((ROOT/'work/jetways.pkl').read_bytes())
ground,obs,free=pickle.loads((ROOT/'work/service-obstacles.pkl').read_bytes())
fix=json.loads((ROOT/'work/service-repair.json').read_text())
change=json.loads((ROOT/'HF03_Changes.json').read_text())
mask=json.loads((ROOT/'work/cleanup-mask.json').read_text())
nodes={a['parts'][4]:xy(float(a['parts'][2]),float(a['parts'][1])) for a in apt if a['code']==1201}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titleweight':'bold'})

def backdrop(ax,bounds):
    area=box(*bounds)
    ax.set_facecolor('#edf0e6')
    for a in apt:
        if a['code']==110 and a['geom'].intersects(area):
            draw_geom(ax,smooth_pavement(a),facecolor='#f6f5f0',edgecolor='#deddd6',linewidth=.5)
    for k,v in plan['models'].items():
        if v['geom'].intersects(area):
            draw_geom(ax,v['geom'],facecolor='#a2bbb7',edgecolor='#597b75',linewidth=.8)
    ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[1],bounds[3]);ax.set_aspect('equal')
    ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_color('#adb7b3')

fig,axes=plt.subplots(1,2,figsize=(16,9),gridspec_kw={'width_ratios':[1,1]})
for ax,bounds,title in zip(axes,[(-315,525,-120,680),(165,520,355,705)],['Terminal B · B5–B8','D West · D4–D6']):
    backdrop(ax,bounds);area=box(*bounds)
    for a in apt:
        if a['code']==1206:
            g=LineString([nodes[a['parts'][1]],nodes[a['parts'][2]]])
            if g.intersects(area):draw_geom(ax,g,edgecolor='#adb5b5',linewidth=1)
    for p in planes:
        if p.intersects(area):draw_geom(ax,p,facecolor='#cde7eb',edgecolor='#3b8396',alpha=.6,linewidth=.6)
    for j,g in zip(scene['jetways'],ground):
        if g.intersects(area):
            draw_geom(ax,g,facecolor='#b79578',edgecolor='#705035',linewidth=1)
            ax.text(*j['door'],j['name'].removeprefix('Gate '),fontsize=10,weight='bold',color='#193a37',ha='center',clip_on=True)
    for p in fix['paths']:
        ids=p['old'].split()[1:3];old=LineString([nodes[i] for i in ids]);new=LineString(p['points'])
        if old.intersects(area):
            draw_geom(ax,old,edgecolor='#c34c4c',linewidth=2,linestyle='--')
            draw_geom(ax,new,edgecolor='#147b60',linewidth=2.5)
    ax.set_title(title,pad=12)
fig.suptitle('HF03 · Service paths around the retracted jetways',fontsize=19,weight='bold',y=.97)
fig.legend(handles=[Line2D([0],[0],color='#147b60',lw=3,label='Staged service path'),Line2D([0],[0],color='#c34c4c',lw=2,ls='--',label='Replaced path'),Patch(color='#b79578',label='Jetway wheels / stairs'),Patch(color='#cde7eb',label='Aircraft clearance guide')],loc='lower center',ncol=4,bbox_to_anchor=(.5,.055),frameon=False)
fig.text(.5,.025,'Seven original edges rerouted · minimum 2.35 m centerline clearance to low jetway geometry · driving behavior still needs X-Plane testing',ha='center',color='#485452')
fig.subplots_adjust(top=.91,bottom=.14,wspace=.1)
fig.savefig(OUT/'15_Service_Path_Repair.png',dpi=130);plt.close(fig)

fig,ax=plt.subplots(figsize=(17,10));bounds=(-650,-440,1450,850);backdrop(ax,bounds)
for seg in pickle.loads((ROOT/'work/roads.pkl').read_bytes()):
    draw_geom(ax,seg['geom'],edgecolor='#b7bbc0',linewidth=1)
for key in ['apron','landside']:
    draw_geom(ax,shape(mask[key]),facecolor='#e7bc6a',edgecolor='#c68c30',alpha=.18,linewidth=.7)
for seg in change['road_segments']:
    draw_geom(ax,LineString([xy(p[0],p[1]) for p in seg['points']]),edgecolor='#b44165',linewidth=3)
for name,pos in [('B North',(-370,560)),('B lobby',(-360,240)),('D West',(290,600)),('International terminal',(765,365)),('D East',(1120,515)),('Taxiway bridge crossing',(760,-290))]:
    ax.text(*pos,name,ha='center',color='#163934',fontsize=11,weight='bold',bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=3))
ax.set_title('HF03 · Old apron overlays and conflicting road segments',fontsize=19,pad=17)
fig.legend(handles=[Patch(color='#e7bc6a',alpha=.5,label='Main cleanup zones'),Line2D([0],[0],color='#b44165',lw=3,label='11 excluded road segments'),Patch(color='#a2bbb7',label='Rebuilt footprints')],loc='lower center',ncol=3,bbox_to_anchor=(.5,.06),frameon=False)
fig.text(.5,.035,'Local exclusions suppress conflicting lower-layer road geometry and traffic; this repair does not build replacement tunnels.',ha='center',color='#485452')
fig.text(.5,.015,'Data overview, not a simulator screenshot. Small additional exclusions remove old labels in renumbered areas.',ha='center',color='#485452')
fig.subplots_adjust(top=.91,bottom=.14)
fig.savefig(OUT/'16_Overlay_Road_Repair.png',dpi=130);plt.close(fig)
for p in fix['paths']: print(p['old'],round(p['old_length'],1),'->',round(p['new_length'],1),'m')
