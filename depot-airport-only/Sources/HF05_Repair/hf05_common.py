import sys,pathlib,pickle,re,shutil,subprocess,collections
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF04_Repair\work')
from common import *
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\outputs\KIAH_2026-10-24_Review_R03_HF04')
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF05'
plan,oldapt,own,aep,mask,exports,exclusions=pickle.loads((ROOT/'work/context.pkl').read_bytes())
DSFTOOL=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\work\xptools-24-5\tools\DSFTool.exe')

def precise_pavement(a,tolerance=.0005):
    # Adaptive cubic subdivision. Distance of both handles from the finite
    # endpoint segment bounds the convex hull and thus the curve error.
    def cubic(p,c,d,q,depth=0):
        segment=LineString([p,q])
        if depth>=22 or max(segment.distance(Point(c)),segment.distance(Point(d)))<=tolerance:
            return [tuple(p)]
        a0=(p+c)/2;b0=(c+d)/2;c0=(d+q)/2
        d0=(a0+b0)/2;e0=(b0+c0)/2;m=(d0+e0)/2
        return cubic(p,a0,d0,m,depth+1)+cubic(m,e0,c0,q,depth+1)
    rings=[];nodes=[]
    for row in a['lines'][1:]:
        s=row.split();p=np.array(xy(float(s[2]),float(s[1])))
        h=np.array(xy(float(s[4]),float(s[3]))) if s[0] in ('112','114','116') else p
        nodes.append((p,h))
        if s[0] in ('113','114'):
            ring=[]
            for (p,h),(q,k) in zip(nodes,nodes[1:]+nodes[:1]):ring+=cubic(p,h,2*q-k,q)
            rings.append(Polygon(ring));nodes=[]
    assert not nodes
    g=rings[0].difference(unary_union(rings[1:]))
    assert g.is_valid
    return g

def native_area(g,header):
    rows=[]
    for p in polygon_parts(g):
        if p.is_empty:continue
        p=orient(p,sign=1);rows.append(header)
        for ring in [p.exterior,*p.interiors]:
            pts=list(ring.coords)[:-1]
            for j,(x,y) in enumerate(pts):
                lon,lat=ll(x,y);rows.append(f'{113 if j==len(pts)-1 else 111} {lat:.9f} {lon:.9f}')
    return rows

def parse_exclusion(row,strict=True):
    _,kind,data=row.split(' ',2);extent,sep,points=data.partition(';')
    w,s,e,n=map(float,extent.split('/'));bbox=box(*xy(w,s),*xy(e,n))
    if not sep:return kind.removeprefix('sim/exclude_'),bbox
    if '/' in points:
        coords=[tuple(map(float,p.split('/'))) for p in points.split(',')]
    elif strict:
        raise ValueError('Not WED lon/lat,lon/lat syntax')
    else:
        ns=list(map(float,points.split(',')));coords=list(zip(ns[::2],ns[1::2]))
    assert len(coords)>=3 and all(len(p)==2 for p in coords)
    g=Polygon([xy(*p) for p in coords])
    assert g.is_valid and bbox.buffer(.0002).covers(g)
    return kind.removeprefix('sim/exclude_'),g

def dsf_decode(src,out):
    result=subprocess.run([str(DSFTOOL),'--dsf2text',str(src),str(out)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    return result.stdout+result.stderr

def snapshot_tree(path):return {p.relative_to(path).as_posix():sha(p) for p in path.rglob('*') if p.is_file()}

def data_commands(path):
    # Preserve complete command order, especially FILTER placement. Do not use
    # parse_dsf's separated header/entity representation when rewriting a DSF.
    return [l for l in path.read_text().splitlines() if l and not l.startswith(('#','PROPERTY ','I','800 ','DSF2TEXT'))]
