from layout_plan import *
from collections import defaultdict, Counter
from shapely.strtree import STRtree
from shapely.prepared import prep

R03=ROOT/'r03'
BASE=OUT/'KIAH_2026-10-24_Review_R02'
TARGET=OUT/'KIAH_2026-10-24_Review_R03'
SPAN=dict(zip('ABCDEF',[15,24,36,52,65,80]))

def network(apt):
    nodes={a['id']:xy(a['lon'],a['lat']) for a in apt if a['code']==1201}
    edges=[];last=None
    for a in apt:
        if a['code'] in (1202,1206):
            s=a['parts'];last=dict(code=a['code'],a=int(s[1]),b=int(s[2]),direction=s[3],kind=s[4] if a['code']==1202 else 'truck',name=' '.join(s[5:] if a['code']==1202 else s[4:]),attrs=[],source='R02',old_index=len(edges))
            edges.append(last)
        elif a['code'] in (1204,1205) and last:last['attrs']+=a['lines']
    return nodes,edges

def line(e,nodes):return LineString([nodes[e['a']],nodes[e['b']]])
def allowed(e,size):return e['kind']=='runway' or e['kind'].upper().split('_')[-1]>=size
def adjacency(edges,code,size=None,reverse=False,undirected=False):
    g=defaultdict(set)
    for e in edges:
        if e['code']!=code or (size and not allowed(e,size)):continue
        a,b=e['a'],e['b'];g[a];g[b]
        if reverse:a,b=b,a
        g[a].add(b)
        if e['direction']=='twoway' or undirected:g[b].add(a)
    return g
def reachable(g,seeds):
    seen=set(seeds);stack=list(seen)
    while stack:
        a=stack.pop()
        for b in g.get(a,set())-seen:seen.add(b);stack.append(b)
    return seen
def components(g):
    unseen=set(g);out=[]
    while unseen:
        c=reachable(g,[next(iter(unseen))]);out.append(c);unseen-=c
    return sorted(out,key=len,reverse=True)
def strongly_connected(g):
    # Kosaraju, iterative to handle the whole airport without recursion limits.
    seen=set();order=[]
    for a in g:
        if a in seen:continue
        stack=[(a,False)]
        while stack:
            n,done=stack.pop()
            if done:order.append(n);continue
            if n in seen:continue
            seen.add(n);stack.append((n,True));stack.extend((v,False) for v in g[n] if v not in seen)
    rev=defaultdict(set)
    for a,bs in g.items():
        rev[a]
        for b in bs:rev[b].add(a)
    seen=set();out=[]
    for a in reversed(order):
        if a in seen:continue
        comp=reachable(rev,[a])-seen;seen|=comp;out.append(comp)
    return sorted(out,key=len,reverse=True)

def smooth_pavement(a):
    # apt.dat Bezier handle points toward the next vertex; the incoming handle is reflected.
    rings=[];verts=[]
    for row in a['lines'][1:]:
        s=row.split();p=np.array(xy(float(s[2]),float(s[1])))
        h=np.array(xy(float(s[4]),float(s[3]))) if s[0] in ('112','114','116') else p
        verts.append((p,h))
        if s[0] in ('113','114','115','116'):
            points=[]
            for (p,h),(q,j) in zip(verts,verts[1:]+verts[:1]):
                n=max(1,int((np.linalg.norm(h-p)+np.linalg.norm(q-h)+np.linalg.norm(j-q))/2))
                n=min(n,120)
                for t in np.linspace(0,1,n,endpoint=False):points.append((1-t)**3*p+3*(1-t)**2*t*h+3*(1-t)*t*t*(2*q-j)+t**3*q)
            rings.append(safe_poly(points));verts=[]
    return rings[0].difference(unary_union(rings[1:])) if rings else Polygon()

def scene_context(apt):
    import pickle,hashlib
    cache=R03/'context-cache.pkl'
    digest=hashlib.sha256('\n'.join(l for a in apt if a['code'] in (100,110,1300) for l in a['lines']).encode()).hexdigest()
    if cache.exists():
        old=pickle.loads(cache.read_bytes())
        if old[0]==digest:return old[1]
    plan=build_plan()
    dsfs=[parse_dsf(ROOT/'generated'/n) for n in ['+29-096.txt','+30-096.txt']]
    entities=[e for d in dsfs for e in d['entities']]
    buildings=[e['geom'] for e in entities if e['kind']=='polygon' and e['resource'].endswith('.fac') and any(t in e['resource'].lower() for t in ['term_building','hangar','warehouse']) and e['geom'].area>12]
    buildings += [m['geom'] for m in plan['models'].values()]
    solids=unary_union(buildings)
    runways=[a for a in apt if a['code']==100]
    pavement=unary_union([smooth_pavement(a) for a in apt if a['code']==110]+[a['geom'] for a in runways])
    ramps=[a for a in apt if a['code']==1300]
    planes=[dict(name=r['name'],geom=aircraft_outline(r['geom'].coords[0],r['heading'],r.get('rampmeta',['1301','C'])[1])) for r in ramps if r['kind']!='misc']
    result=dict(plan=plan,dsfs=dsfs,entities=entities,buildings=buildings,solids=solids,runways=runways,pavement=pavement,ramps=ramps,planes=planes)
    cache.write_bytes(pickle.dumps((digest,result)))
    return result

def crossing_pairs(edges,nodes,code):
    es=[e for e in edges if e['code']==code];gs=[line(e,nodes) for e in es];tree=STRtree(gs);out=[]
    for i,g in enumerate(gs):
        for j in tree.query(g,predicate='intersects'):
            if j<=i:continue
            a,b=es[i],es[j]
            if {a['a'],a['b']}&{b['a'],b['b']}:continue
            hit=g.intersection(gs[j]);out.append((a,b,hit))
    return out

def overview(apt,nodes,edges,ctx,path,limits=None,labels=False):
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(18,10));fig.patch.set_facecolor('#101f2a');ax.set_facecolor('#101f2a')
    for a in apt:
        if a['code'] in (100,110):draw_geom(ax,a['geom'],facecolor='#354b58',edgecolor='none')
    for g in ctx['buildings']:draw_geom(ax,g,facecolor='#879ba5',edgecolor='none')
    for r in ctx['planes']:draw_geom(ax,r['geom'],facecolor='#566c77',edgecolor='none')
    for e in edges:
        c='#f1c85b' if e['code']==1202 else '#3de1b6'
        if e['source']!='R02':c='#ee82e9' if e['code']==1202 else '#64f9ff'
        g=line(e,nodes);ax.plot(*g.xy,color=c,lw=.7)
        if labels and (e['source']!='R02' or e['code']==1206):
            p=g.interpolate(.5,normalized=True);ax.text(p.x,p.y,str(e['old_index']),fontsize=5,color='white')
    for a in apt:
        if a['code'] in (1400,1401):
            s=a['parts'];p=xy(float(s[2]),float(s[1]));ax.plot(*p,'o' if a['code']==1400 else 's',color='#ff9467',ms=3)
    if limits:ax.set_xlim(limits[:2]);ax.set_ylim(limits[2:])
    ax.set_aspect('equal');ax.tick_params(colors='white');fig.tight_layout();fig.savefig(path,dpi=150);plt.close(fig)

if __name__=='__main__':
    import faulthandler
    faulthandler.dump_traceback_later(45,repeat=True)
    print('Reading context',flush=True)
    apt=parse_apt(BASE/'Earth nav data/apt.dat');nodes,edges=network(apt);ctx=scene_context(apt)
    print('Context ready',flush=True)
    report={}
    for code in (1202,1206):
        es=[e for e in edges if e['code']==code];g=adjacency(es,code,undirected=True);comps=components(g)
        report[str(code)]=dict(edges=len(es),directions=dict(Counter(e['direction'] for e in es)),components=[dict(n=len(c),center=np.mean([nodes[n] for n in c],axis=0).tolist()) for c in comps],strong_components=[len(c) for c in strongly_connected(adjacency(es,code))],crossings=[dict(a=a['old_index'],b=b['old_index'],point=list(p.centroid.coords[0])) for a,b,p in crossing_pairs(es,nodes,code)])
    print('Graph audit ready',flush=True)
    bad=[]
    pave=ctx['pavement'].buffer(1);paveprep=prep(pave);solidprep=prep(ctx['solids'])
    planegeoms=[r['geom'] for r in ctx['planes']];planetree=STRtree(planegeoms)
    for e in edges:
        if e['code']!=1202 or e['kind']=='runway':continue
        g=line(e,nodes);bc=g.intersection(ctx['solids']).length if solidprep.intersects(g) else 0
        off=0 if paveprep.covers(g) else g.difference(pave).length
        pc=[ctx['planes'][i]['name'] for i in planetree.query(g,predicate='intersects')]
        if bc>.1 or off>2 or pc:bad.append(dict(id=e['old_index'],name=e['name'],building=round(bc,2),off=round(off,2),planes=pc,center=list(g.centroid.coords[0])))
    report['aircraft_geometry_flags']=bad
    (R03/'initial-audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    overview(apt,nodes,edges,ctx,R03/'initial-terminal-routes.png',(-1050,1100,180,850),True)
