import pathlib,sys,pickle,json,ast,math,hashlib,copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'KIAH_R03_HF02_Repair/work'))
from sign_groups import *
from route_common import smooth_pavement
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
ROOT=pathlib.Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R03_HF03_Repair'
SOURCE=PREV/'staged/KIAH_2026-10-24_Review_R03_HF03'
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF04'
LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
plan,oldapt,dsf=pickle.loads((ROOT/'work/current.pkl').read_bytes())
tree=ast.parse((ROOT.parent/'KIAH_R03_HF02_Repair/work/repair_airport_details.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('sampled_apt_segments','apt_area','emit_apt_line')],type_ignores=[]),'helpers','exec'))
crop=box(-750,300,30,850)
nb=unary_union([smooth_pavement(a) for a in oldapt if a['code']==110 and a['lines'][0].endswith('Twy NB')])
new_apron=unary_union([smooth_pavement(a) for a in oldapt if a['code']==110 and 'B_North apron 2026' in a['lines'][0]])
mask=new_apron.intersection(box(-660,550,-190,710))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def visible_surfaces(apt):
    covered=Polygon();out=[]
    for i,a in enumerate(apt):
        if a['code'] not in (100,110):continue
        g=a['geom'] if a['code']==100 else smooth_pavement(a)
        if not g.intersects(crop):continue
        surf=int(a['parts'][1])%100
        if a['code']==110 and surf in (0,3,4,5,13,15):continue
        clipped=g.intersection(crop)
        out.append((i,surf,clipped.difference(covered)))
        covered=covered.union(clipped)
    return out
def plot_poly(ax,g,fc,ec='none',lw=.5):
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    for p in polygon_parts(polys_only(make_valid(g))):
        if p.is_empty:continue
        p=orient(p,sign=1);verts=[];codes=[]
        for ring in [p.exterior,*p.interiors]:
            pts=list(ring.coords);verts+=pts;codes+=[Path.MOVETO]+[Path.LINETO]*(len(pts)-2)+[Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts,codes),facecolor=fc,edgecolor=ec,lw=lw))
def plot_airport(ax,apt,labels=True):
    ax.set_facecolor('#879b6b')
    for i,s,g in visible_surfaces(apt):plot_poly(ax,g,'#858582' if s==1 or 20<=s<40 else '#d5d4ca')
    for a in apt:
        if a['code'] not in (110,120):continue
        for g,s in sampled_apt_segments(a):
            if not g.intersects(crop):continue
            if any(int(x)<100 for x in s):
                for seg in ([g] if g.geom_type=='LineString' else g.geoms):
                    ax.plot(*seg.xy,color='#a88a0c',lw=.65)
            if '102' in s:
                pts=[g.interpolate(t) for t in np.arange(0,g.length,16)]
                ax.scatter([p.x for p in pts],[p.y for p in pts],s=4,c='#1569e5')
    for n,m in plan['models'].items():
        if m['geom'].intersects(crop):plot_poly(ax,m['geom'],'#507d80','#29494d')
    if labels:
        for r in plan['new']:
            if crop.contains(Point(r['pos'])):ax.text(*r['pos'],r['name'],fontsize=8,color='#153b41')
    ax.set_xlim(crop.bounds[0],crop.bounds[2]);ax.set_ylim(crop.bounds[1],crop.bounds[3]);ax.set_aspect('equal');ax.set_xlabel('Metres east of reference');ax.set_ylabel('Metres north of reference')
if __name__=='__main__':
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(14,10));plot_airport(ax,oldapt)
    plot_poly(ax,mask,'none','#e44040',1)
    fig.savefig(ROOT/'work/actual-surfaces.png',dpi=140)
    for i in (22,24,61,91,108):
        a=oldapt[i];print(i,a['lines'][0])
        for g,s in sampled_apt_segments(a):
            if g.intersects(mask):print('  ',[round(x,1) for x in g.bounds],s,'inside',round(g.intersection(mask).length,1),'outside',round(g.difference(mask).length,1))
