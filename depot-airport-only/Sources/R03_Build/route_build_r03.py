from route_common import *
from shapely.ops import substring,nearest_points
import heapq,shutil,copy

def node_network(nodes,edges):
    """Split true intersections, merge coincident node IDs, retain directions and hot zones."""
    out=[];newnodes=dict(nodes);coordmap={};nextid=max(nodes)+1;stats=Counter()
    def getid(p,code):
        nonlocal nextid
        key=(code,round(p[0],3),round(p[1],3))
        if key not in coordmap:coordmap[key]=nextid;newnodes[nextid]=tuple(p);nextid+=1
        return coordmap[key]
    for code in (1202,1206):
        es=[e for e in edges if e['code']==code];gs=[line(e,nodes) for e in es];tree=STRtree(gs)
        splits=[{0.,g.length} for g in gs]
        for i,g in enumerate(gs):
            for j in tree.query(g,predicate='intersects'):
                if j<=i:continue
                hit=g.intersection(gs[j]);pts=[]
                for p in [hit] if not hasattr(hit,'geoms') else hit.geoms:
                    if p.geom_type=='Point':pts.append(p)
                    elif p.geom_type=='LineString':pts.extend(Point(c) for c in [p.coords[0],p.coords[-1]])
                for p in pts:splits[i].add(g.project(p));splits[j].add(gs[j].project(p))
        for e,g,dist in zip(es,gs,splits):
            ds=sorted(dist)
            for x,y in zip(ds,ds[1:]):
                if y-x<.025:continue
                a,b=getid(g.interpolate(x).coords[0],code),getid(g.interpolate(y).coords[0],code)
                if a==b:continue
                q=dict(e,a=a,b=b,attrs=list(e['attrs']));out.append(q)
            stats[str(code)+'_split_segments']+=max(0,len(ds)-2)
    # Merge exact duplicate pieces, retaining the union of runway protection metadata.
    unique={}
    for e in out:
        key=(e['code'],min(e['a'],e['b']),max(e['a'],e['b']))
        if key not in unique:unique[key]=e;continue
        q=unique[key];stats['duplicates_removed']+=1
        if q['direction']=='twoway' or e['direction']=='twoway' or (e['a']==q['b']):q['direction']='twoway'
        q['attrs']=list(dict.fromkeys(q['attrs']+e['attrs']))
        if q['kind']!='runway' and e['kind']=='runway':q['kind']=e['kind'];q['name']=e['name']
    return newnodes,list(unique.values()),dict(stats)

def shortest_grid(start,goal,safe,step=6,bounds=None):
    """Visibility-smoothed A*, with exact endpoints and cached segment checks."""
    if safe.covers(LineString([start,goal])):return [tuple(start),tuple(goal)]
    a=tuple(round(v/step) for v in start);b=tuple(round(v/step) for v in goal)
    ap=tuple(v*step for v in a);bp=tuple(v*step for v in b)
    if not safe.covers(LineString([start,ap])) or not safe.covers(LineString([bp,goal])):return None
    cost={a:0};came={};queue=[(math.dist(a,b),0,a)];closed=set();found=False
    for _ in range(100000):
        if not queue:break
        _,c,u=heapq.heappop(queue)
        if u in closed:continue
        closed.add(u)
        if u==b:found=True;break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
            v=(u[0]+dx,u[1]+dy);cp=(v[0]*step,v[1]*step)
            if bounds and not(bounds[0]<=cp[0]<=bounds[2] and bounds[1]<=cp[1]<=bounds[3]):continue
            nc=c+math.hypot(dx,dy)
            if nc>=cost.get(v,1e20):continue
            if not safe.covers(LineString([(u[0]*step,u[1]*step),cp])):continue
            cost[v]=nc;came[v]=u;heapq.heappush(queue,(nc+math.dist(v,b),nc,v))
    if not found:return None
    path=[b]
    while path[-1] in came:path.append(came[path[-1]])
    path=[tuple(start)]+[(p[0]*step,p[1]*step) for p in path[::-1]]+[tuple(goal)]
    result=[path[0]];i=0
    while i<len(path)-1:
        j=len(path)-1
        while j>i+1 and not safe.covers(LineString([path[i],path[j]])):j-=1
        if math.dist(result[-1],path[j])>.025:result.append(path[j])
        i=j
    return result

def add_path(nodes,edges,path,code,name,kind='truck',source='R03'):
    ids=[];used={e[k] for e in edges if e['code']==code for k in ('a','b')}
    for p in path:
        matches=[n for n in used if math.dist(nodes[n],p)<.01]
        if matches:n=matches[0]
        else:n=max(nodes,default=-1)+1;nodes[n]=tuple(p);used.add(n)
        ids.append(n)
    for a,b in zip(ids,ids[1:]):
        if a!=b:edges.append(dict(code=code,a=a,b=b,direction='twoway',kind=kind,name=name,attrs=[],source=source,old_index=len(edges)))

def write_apt(apt,nodes,edges,truck_records,extra_paint,path):
    used={e[k] for e in edges for k in ('a','b')};ids={n:i for i,n in enumerate(sorted(used))}
    headers=[a for a in apt if a['code'] in (1,16,17)]
    if len(headers)!=1 or headers[0]['lines'][0].split()[4]!='KIAH':
        raise ValueError('Export requires exactly one KIAH airport declaration')
    rows=['I','1200 KIAH 2026-10-24 Review R03 - ground routing revision']
    for a in apt:
        if a['code'] in (-1,99,1200,1201,1202,1204,1205,1206):continue
        if a['code']==120 and '2026 apron circulation' in a['lines'][0]:continue
        if a.get('drop'):continue
        rows+=a['lines']
    rows+=extra_paint+['1200']
    for n,i in ids.items():
        lon,lat=ll(*nodes[n]);rows.append(f'1201 {lat:.8f} {lon:.8f} both {i} R03N{i}')
    for e in edges:
        suffix=f'{e["kind"]} {e["name"]}' if e['code']==1202 else e['name']
        rows.append(f'{e["code"]} {ids[e["a"]]} {ids[e["b"]]} {e["direction"]} {suffix}'.strip());rows+=e['attrs']
    rows+=truck_records+['99'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(rows)+'\n')

def repair_directions(nodes,edges,changes):
    seeds={e[k] for e in edges if e['code']==1202 and e['kind']=='runway' for k in ('a','b')}
    for step in range(200):
        f=reachable(adjacency(edges,1202),seeds);b=reachable(adjacency(edges,1202,reverse=True),seeds)
        allnodes=set(adjacency(edges,1202));bad=(allnodes-f)|(allnodes-b)
        if not bad:return
        choices=[]
        for e in edges:
            if e['code']!=1202 or e['kind']=='runway' or e['direction']!='oneway':continue
            if (e['a'] not in f and e['b'] in f) or (e['b'] not in b and e['a'] in b):
                # Prefer apron and parallel taxiway corrections to reversing rapid runway exits.
                score=(0 if not e['name'] else 200)+line(e,nodes).length
                choices.append((score,e))
        if not choices:raise RuntimeError(f'No repair for directional trap: {len(bad)} nodes')
        e=min(choices,key=lambda q:q[0])[1];e['direction']='twoway';e['source']='R03 direction repair'
        changes.append(dict(type='direction',edge=e['old_index'],name=e['name'],reason='One-way edge stranded connected taxi nodes; retain geometry and runway protection',position=list(line(e,nodes).centroid.coords[0])))
    raise RuntimeError('Direction repair did not converge')

def complete_width_connections(nodes,edges,ctx,pave,obstacles,changes):
    # Work with measured modeled clearance, widening metadata only where the route can accommodate it.
    def capacity(e):
        if e['kind']=='runway':return 'F'
        clear=line(e,nodes).distance(obstacles)
        return max([s for s,w in SPAN.items() if w/2+2<=clear+.1],default='')
    # The inherited network has a short widebody pinch point between B South and the south taxi spine.
    potential=[dict(e,kind='runway' if e['kind']=='runway' else 'taxiway_'+capacity(e)) for e in edges if e['code']==1202 and capacity(e)]
    comps=strongly_connected(adjacency(potential,1202,'F'))
    runway_comps=[c for c in comps if any(e['kind']=='runway' and e['a'] in c for e in potential)]
    if len(runway_comps)>1:
        safe=prep(pave.buffer(.5).difference(obstacles.buffer(42)))
        main=max(runway_comps,key=len)
        for other in runway_comps:
            if other is main:continue
            pairs=sorted((math.dist(nodes[a],nodes[b]),a,b) for a in main for b in other)[:18];success=False
            for dist,a,b in pairs:
                if dist>250:break
                bounds=LineString([nodes[a],nodes[b]]).buffer(180).bounds
                path=shortest_grid(nodes[a],nodes[b],safe,2,bounds)
                if not path:continue
                old=[e for e in edges if e['code']==1202 and {e['a'],e['b']}=={a,b}]
                name=old[0]['name'] if old else 'Apron circulation'
                for e in old:edges.remove(e)
                add_path(nodes,edges,path,1202,name,'taxiway_F','R03 widebody clearance detour')
                changes.append(dict(type='widebody clearance connection',path=path,replaced_segments=len(old)));success=True;break
            if not success:raise RuntimeError('Unable to link widebody runway networks with modeled clearance')
    for size in 'BCDEF':
        es=[e for e in edges if e['code']==1202];caps={id(e):capacity(e) for e in es}
        pg=defaultdict(list)
        for e in es:
            if caps[id(e)]<size:continue
            cost=line(e,nodes).length*(.01 if allowed(e,size) else 1)+(.01 if allowed(e,size) else 20)
            pg[e['a']].append((e['b'],cost,e))
            if e['direction']=='twoway':pg[e['b']].append((e['a'],cost,e))
        anchors=[e['a'] for e in es if e['kind']=='runway' and e['name']=='15L/33R'];anchor=anchors[0]
        potential=[dict(e,kind='runway' if e['kind']=='runway' else 'taxiway_'+caps[id(e)]) for e in es if caps[id(e)]>=size]
        main=next(c for c in strongly_connected(adjacency(potential,1202,size)) if anchor in c)
        targets={}
        for r in ctx['runways']:
            candidates=[e['a'] for e in es if e['kind']=='runway' and e['name']==r['name'] and e['a'] in main]
            if not candidates:raise RuntimeError('No capable runway path '+size+' '+r['name'])
            targets[candidates[0]]=r['name']
        for r in ctx['ramps']:
            if r.get('rampmeta',['1301','C'])[1]!=size:continue
            choices=[e for e in es if e['kind']!='runway' and caps[id(e)]>=size and e['a'] in main and e['b'] in main]
            choices.sort(key=lambda e:line(e,nodes).distance(r['geom']))
            viable=[e for e in choices[:30] if not LineString([r['geom'],nearest_points(r['geom'],line(e,nodes))[1]]).intersects(ctx['solids'])]
            e=(viable or choices)[0]
            for n in (e['a'],e['b']):targets[n]=r['name']
            # Ensure the adjacent segment itself admits the ramp's class.
            if not allowed(e,size):
                old=e['kind'];e['kind']='taxiway_'+size;e['source']='R03 width connectivity';changes.append(dict(type='width connection',name=e['name'],old=old,new=e['kind'],position=list(line(e,nodes).centroid.coords[0])))
        def tree(reverse=False):
            g=defaultdict(list)
            for u,arcs in pg.items():
                for v,w,e in arcs:
                    if reverse:g[v].append((u,w,e))
                    else:g[u].append((v,w,e))
            dist={anchor:0};prev={};q=[(0,anchor)]
            while q:
                d,u=heapq.heappop(q)
                if d>dist[u]+1e-8:continue
                for v,w,e in g[u]:
                    nd=d+w
                    if nd<dist.get(v,1e30):dist[v]=nd;prev[v]=(u,e);heapq.heappush(q,(nd,v))
            return prev
        for reverse in (False,True):
            prev=tree(reverse)
            for target,name in targets.items():
                n=target
                while n!=anchor:
                    if n not in prev:raise RuntimeError('Missing directed width path '+size+' '+name)
                    n,e=prev[n]
                    if not allowed(e,size):
                        old=e['kind'];e['kind']='taxiway_'+size;e['source']='R03 width connectivity';changes.append(dict(type='width connection',name=e['name'],old=old,new=e['kind'],position=list(line(e,nodes).centroid.coords[0])))

def build():
    apt=parse_apt(BASE/'Earth nav data/apt.dat');nodes,edges=network(apt);ctx=scene_context(apt);changes=[]
    plan=ctx['plan'];plane_union=unary_union([p['geom'] for p in ctx['planes']]);obstacles=unary_union([ctx['solids'],plane_union])
    pave=unary_union([ctx['pavement']]+[e['geom'] for e in ctx['entities'] if e['kind']=='polygon' and '/pavement/' in e['resource'] and e['geom'].area>0])
    for r in ctx['runways']:
        s=r['parts'];center=LineString([xy(float(s[10]),float(s[9])),xy(float(s[19]),float(s[18]))])
        for n in {e[k] for e in edges if e['code']==1202 and e['kind']=='runway' and e['name']==r['name'] for k in ('a','b')}:
            pt=Point(nodes[n]);snap=center.interpolate(center.project(pt))
            if snap.distance(pt)>.1:changes.append(dict(type='runway centerline alignment',runway=r['name'],offset_m=round(snap.distance(pt),3),position=nodes[n]))
            nodes[n]=snap.coords[0]
    # Replace the R01 apron links using all retained aircraft envelopes, not just the rebuilt stands.
    edges=[e for e in edges if not(e['code']==1202 and e['name']=='Apron')]
    degree=Counter(n for e in edges if e['code']==1202 for n in (e['a'],e['b']))
    width_report=[];remove=[]
    for e in edges:
        if e['code']!=1202 or e['kind']=='runway':continue
        g=line(e,nodes);clear=g.distance(obstacles);old=e['kind'][-1].upper()
        usable=[s for s,w in SPAN.items() if w/2+2<=clear+.1 and s<=old]
        if usable and usable[-1]==old:continue
        # Do not drive the fixed route all the way into aircraft maneuvering space.
        if (degree[e['a']]==1 or degree[e['b']]==1) and not e['name']:
            remove.append(e);changes.append(dict(type='trim ramp spur',edge=e['old_index'],position=list(g.centroid.coords[0]),reason='Fixed taxi route entered a parked-aircraft clearance envelope; final ramp maneuver remains simulator controlled'))
        elif usable:
            e['kind']='taxiway_'+usable[-1];e['source']='R03 size correction';changes.append(dict(type='size',edge=e['old_index'],name=e['name'],old=old,new=usable[-1],clearance_m=round(clear,2),position=list(g.centroid.coords[0])))
        else:
            # A connected segment needs a local detour, keeping its original allowed wingspan.
            clearance=SPAN[old]/2+2;safe=prep(pave.buffer(1).difference(obstacles.buffer(clearance)))
            a,b=nodes[e['a']],nodes[e['b']]
            path=shortest_grid(a,b,safe,4,g.buffer(160).bounds)
            if path:
                remove.append(e);add_path(nodes,edges,path,1202,e['name'],'taxiway_'+old,'R03 aircraft detour')
                changes.append(dict(type='detour',edge=e['old_index'],name=e['name'],position=list(g.centroid.coords[0])))
            else:raise RuntimeError(f'Unresolved aircraft route clearance on {e["old_index"]} {e["name"]}: {clear:.1f} m')
    for e in remove:edges.remove(e)
    repair_directions(nodes,edges,changes)
    print('Aircraft existing repairs:',len(changes),flush=True)
    for target,size in [((-660,425),'C'),((-385,510),'C'),((-122,535),'C'),((147,490),'E'),((450,500),'E')]:
        safegeo=pave.buffer(.5).difference(obstacles.buffer(SPAN[size]/2+2));safe=prep(safegeo)
        picks=[(target[0]+dx,target[1]+dy) for dx in range(-48,49,4) for dy in range(-48,49,4) if safe.covers(Point(target[0]+dx,target[1]+dy))]
        if not picks:raise RuntimeError(f'No safe apron point {target}')
        pt=min(picks,key=lambda p:math.dist(p,target))
        used={e[k] for e in edges if e['code']==1202 and allowed(e,size) for k in ('a','b')}
        anchors=sorted([n for n in used if safe.covers(Point(nodes[n])) and nodes[n][1]>680],key=lambda n:math.dist(nodes[n],pt))[:10]
        path=None
        for n in anchors:
            path=shortest_grid(pt,nodes[n],safe,4,(-850,320,620,850))
            if path:break
        if not path:raise RuntimeError(f'No safe apron route {target}')
        add_path(nodes,edges,path,1202,'Apron R03','taxiway_'+size)
        changes.append(dict(type='new apron link',target=pt,size=size,path=path))
    nodes,edges,node_stats=node_network(nodes,edges)
    repair_directions(nodes,edges,changes)
    complete_width_connections(nodes,edges,ctx,pave,obstacles,changes)
    nodes,edges,_=node_network(nodes,edges)
    print('Aircraft links replaced and noded',flush=True)
    # Service routes avoid buildings, parked aircraft, fixed equipment and runway protection areas.
    runway_keepout=unary_union([a['geom'].buffer(60) for a in ctx['runways']])
    fixed=[e['geom'].buffer(3.5) for e in ctx['entities'] if e['kind']=='object' and any(t in e['resource'] for t in ['Ramp_Equipment/','Barriers/','Lighting/'])]
    service_ob=unary_union([ctx['solids'].buffer(4),plane_union.buffer(4),runway_keepout,*fixed])
    safegeo=pave.buffer(.5).difference(service_ob);safe=prep(safegeo)
    # Remove the isolated obsolete B/D fragments and local routes now inside modeled envelopes.
    focus=box(-740,325,455,730)
    removed=[]
    for e in edges:
        if e['code']==1206 and line(e,nodes).intersects(focus) and not safe.covers(line(e,nodes)):
            removed.append(e)
    for e in removed:edges.remove(e)
    changes.append(dict(type='service obsolete segments removed',count=len(removed)))
    targets=[]
    for r in [q for q in plan['new'] if not q.get('alternative')]+plan['details']:
        p=np.array(r['pos']);f=heading_vec(r['heading']);right=np.array([f[1],-f[0]])
        length={'C':40,'E':74}[r['size']]
        ideal=p-f*(length+14)
        candidates=[tuple(ideal+right*d+f*v) for d in range(-24,25,4) for v in range(-16,33,4)]
        candidates=[q for q in candidates if safe.covers(Point(q))]
        if not candidates:raise RuntimeError('No clear service access '+r['name'])
        pt=min(candidates,key=lambda q:math.dist(q,ideal));targets.append(dict(name=r['name'],point=pt,model=r['model']))
    # Processor baggage operations stay on the airside east service spine.
    targets.append(dict(name='E processor service',point=(1080,178),model='International_Processor'))
    for t in targets:
        pt=t['point']
        if not safe.covers(Point(pt)):
            opts=[(pt[0]+x,pt[1]+y) for x in range(-40,41,4) for y in range(-40,41,4) if safe.covers(Point(pt[0]+x,pt[1]+y))]
            if not opts:raise RuntimeError('No service access '+t['name'])
            pt=min(opts,key=lambda p:math.dist(p,t['point']));t['point']=pt
        used={e[k] for e in edges if e['code']==1206 for k in ('a','b')}
        anchors=sorted([n for n in used if safe.covers(Point(nodes[n])) and -1000<nodes[n][0]<1200 and -180<nodes[n][1]<770],key=lambda n:math.dist(nodes[n],pt))[:18]
        path=None
        for n in anchors:
            path=shortest_grid(pt,nodes[n],safe,4,(-1040,-180,1240,770))
            if path:break
        if not path:raise RuntimeError('No service connection '+t['name'])
        add_path(nodes,edges,path,1206,'Service '+t['name']);t['path']=path
        print('Service approach:',t['name'],len(path)-1,'segments',flush=True)
    nodes,edges,service_node_stats=node_network(nodes,edges)
    # Reconnect local fragments to the main terminal network; keep the GA network separate.
    for attempt in range(12):
        comps=components(adjacency(edges,1206,undirected=True));main=max(comps,key=lambda c:sum(-1000<nodes[n][0]<1200 and 150<nodes[n][1]<770 for n in c))
        fragments=[c for c in comps if c!=main and any(focus.contains(Point(nodes[n])) for n in c)]
        if not fragments:break
        joined=False
        for comp in fragments:
            pairs=sorted([(math.dist(nodes[a],nodes[b]),a,b) for a in comp if safe.covers(Point(nodes[a])) for b in main if safe.covers(Point(nodes[b])) and -1000<nodes[b][0]<1200 and 150<nodes[b][1]<770])[:18]
            for _,a,b in pairs:
                path=shortest_grid(nodes[a],nodes[b],safe,4,(-1040,150,1240,770))
                if path:
                    add_path(nodes,edges,path,1206,'Terminal service connector');joined=True;changes.append(dict(type='service fragment connection',path=path));break
        if not joined:
            # A short orphan under the rebuilt B connector has no depot, destination or gate approach.
            disposable=[c for c in fragments if len(c)<=4 and all(e['source']=='R02' for e in edges if e['code']==1206 and e['a'] in c) and not any(min(math.dist(t['point'],nodes[n]) for n in c)<60 for t in targets)]
            if disposable:
                dead=set().union(*disposable);before=len(edges);edges=[e for e in edges if not(e['code']==1206 and e['a'] in dead)]
                changes.append(dict(type='obsolete isolated service spur retired',count=before-len(edges),positions=[nodes[n] for n in dead]));continue
            (R03/'fragment-debug.json').write_text(json.dumps([{'count':len(c),'points':[nodes[n] for n in c]} for c in fragments],indent=2))
            overview(apt,nodes,edges,ctx,R03/'fragment-debug.png',(-1040,1100,300,800),False)
            raise RuntimeError('Unreachable local service fragment')
        nodes,edges,_=node_network(nodes,edges)
    # Real moving service vehicles; parks are beside the route, never directly on its centerline.
    trucks=[];parks=[];occupied=[]
    fleet=['baggage_train','baggage_loader','fuel_liners','food','gpu','pushback']
    for model in ['B_North','D_West']:
        ts=[t for t in targets if t['model']==model]
        for i,typ in enumerate(fleet*2 if model=='B_North' else fleet):
            t=ts[(i*2)%len(ts)];pt=t['point'];found=None
            for dx,dy in [(x,y) for y in (10,-10,16,-16,22,-22,34,-34,46,-46) for x in (0,8,-8,16,-16,24,-24,40,-40,56,-56)]:
                q=(pt[0]+dx,pt[1]+dy);foot=box(q[0]-2.2,q[1]-5.5,q[0]+2.2,q[1]+5.5)
                if not safegeo.covers(foot) or any(foot.distance(v)<2 for v in occupied):continue
                near=min((line(e,nodes) for e in edges if e['code']==1206),key=lambda g:g.distance(Point(q)))
                if near.distance(foot)<2 or near.distance(Point(q))>=35 or not safe.covers(LineString([q,nearest_points(Point(q),near)[1]])):continue
                if any(line(e,nodes).distance(foot)<SPAN.get(e['kind'][-1].upper(),80)/2+2 for e in edges if e['code']==1202):continue
                found=q;occupied.append(foot);break
            if not found:raise RuntimeError('No service parking '+model+' '+typ)
            lon,lat=ll(*found);name=f'R03 {model} {typ} {i+1}';trucks.append(f'1400 {lat:.8f} {lon:.8f} 0.0 {typ} {2 if typ=="baggage_train" else 0} {name}')
            parks.append(dict(name=name,point=found,type=typ,model=model))
    # Baggage circulation destinations are offset from the service road so stopped trucks do not block it.
    for park in parks[::4]:
        # Use a distinct clear destination near the same operating zone; do not overlap parked vehicles.
        p=park['point'];chosen=None
        for dx in (10,-10,18,-18,26,-26):
            q=(p[0]+dx,p[1]);foot=box(q[0]-2,q[1]-5,q[0]+2,q[1]+5)
            if not safegeo.covers(foot) or any(foot.distance(o)<2 for o in occupied):continue
            near=min((line(e,nodes) for e in edges if e['code']==1206),key=lambda g:g.distance(Point(q)))
            if near.distance(foot)<2 or near.distance(Point(q))>35 or not safe.covers(LineString([q,nearest_points(Point(q),near)[1]])):continue
            if any(line(e,nodes).distance(foot)<SPAN.get(e['kind'][-1].upper(),80)/2+2 for e in edges if e['code']==1202):continue
            chosen=q;occupied.append(foot);break
        if chosen:
            lon,lat=ll(*chosen);trucks.append(f'1401 {lat:.8f} {lon:.8f} 0.0 baggage_train|crew_car R03 {park["model"]} service destination');parks.append(dict(name='Destination '+park['name'],point=chosen,type='destination',model=park['model']))
    shutil.copytree(BASE,TARGET,dirs_exist_ok=True)
    paint=[]
    for i,c in enumerate(changes):
        if c['type'] not in ('new apron link','widebody clearance connection'):continue
        paint.append(f'120 R03 aircraft circulation {i}')
        for j,p in enumerate(c['path']):
            lon,lat=ll(*p);last=j==len(c['path'])-1;paint.append(f'{115 if last else 111} {lat:.8f} {lon:.8f}'+('' if last else ' 51'))
    write_apt(apt,nodes,edges,trucks,paint,TARGET/'Earth nav data/apt.dat')
    report=dict(changes=changes,node_stats=node_stats,service_node_stats=service_node_stats,targets=targets,parks=parks,counts=dict(aircraft=sum(e['code']==1202 for e in edges),service=sum(e['code']==1206 for e in edges),new_truck_records=len(trucks)),installed=False,simulator_tested=False)
    (R03/'build-report.json').write_text(json.dumps(report,indent=2))
    final=parse_apt(TARGET/'Earth nav data/apt.dat');nn,ee=network(final)
    overview(final,nn,ee,ctx,R03/'draft-routes.png',(-1000,1200,150,820),False)
    print(json.dumps(report['counts']),flush=True)
    return report

if __name__=='__main__':build()
