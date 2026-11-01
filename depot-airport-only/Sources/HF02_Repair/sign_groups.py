import sys,pickle,pathlib,json
W=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\work')
sys.path.insert(0,str(W));sys.path.insert(0,str(W/'pydeps'))
from airport_geometry import *
from shapely.strtree import STRtree
ROOT=pathlib.Path(__file__).resolve().parents[1]

def groups(dsf):
    es=[(i,e) for i,e in enumerate(dsf['entities']) if any(s in e['resource'] for s in ('DrapedLocSigns.pol','DrapedDirSigns.pol'))]
    gs=[e['geom'] for i,e in es];tree=STRtree(gs);unseen=set(range(len(es)));out=[]
    while unseen:
        stack=[unseen.pop()];ids=[]
        while stack:
            i=stack.pop();ids.append(i)
            for j in tree.query(gs[i].buffer(.3),predicate='intersects'):
                j=int(j)
                if j in unseen:unseen.remove(j);stack.append(j)
        chars=[];direction=None
        for i in ids:
            idx,e=es[i];a=np.array([list(map(float,l.split()[1:])) for l in e['lines'] if l.startswith('POLYGON_POINT')])
            if a.shape[1]!=4:continue
            uv=a[:,2:].mean(axis=0);col=min(10,int(uv[0]/.0898));row=min(3,int((1-uv[1])*4))
            char=['0123456789A','BCDEFGHIJKL','MNPQRSTUVWX','YZ         '][row][col]
            low=a[np.argmin(a[:,2]),:2];high=a[np.argmax(a[:,2]),:2];vec=np.array(xy(*high))-np.array(xy(*low))
            if np.linalg.norm(vec)>.01:direction=vec/np.linalg.norm(vec)
            chars.append((idx,e,char))
        if not chars or direction is None:continue
        chars.sort(key=lambda t:np.dot(np.array(t[1]['geom'].centroid.coords[0]),direction))
        out.append(dict(text=''.join(c for _,_,c in chars),indices=[idx for idx,_,_ in chars],geom=unary_union([e['geom'] for _,e,_ in chars]),right=direction))
    return out

if __name__=='__main__':
    plan,dsf,apt=pickle.loads((ROOT/'work/context.pkl').read_bytes())
    renamed=[r for r in plan['ramps'] if r.get('old_name') and r['old_name']!=r['name']]
    for g in groups(dsf):
        matches=[r for r in renamed if r['old_name'].removeprefix('Gate ')==g['text'] and r['geom'].distance(g['geom'])<110]
        if matches:print(g['text'],'->',matches[0]['name'],round(matches[0]['geom'].distance(g['geom']),1),[round(v,1) for v in g['geom'].centroid.coords[0]])
