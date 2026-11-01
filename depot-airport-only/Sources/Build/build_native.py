from native_mesh import *
import shutil,subprocess,csv,hashlib,heapq
from collections import Counter
from shapely.prepared import prep
from r02_details import stale_west_barrier,scenery_detail_cleanup,equipment_and_lights,ea_barriers

def apt_poly(g,name,surface=50):
    rows=[]
    for i,p in enumerate(polygon_parts(polys_only(g))):
        if p.area<1:continue
        rows.append(f'110 {surface} 0.25 0.0 {name} {i+1}')
        for ring in [orient(p,sign=1).exterior,*orient(p,sign=1).interiors]:
            coords=list(ring.coords)[:-1]
            for j,(x,y) in enumerate(coords):
                lon,lat=ll(x,y);rows.append(f'{113 if j==len(coords)-1 else 111} {lat:.8f} {lon:.8f}')
    return rows
def apt_line(coords,name,style=51):
    rows=['120 '+name]
    for i,(x,y) in enumerate(coords):
        lon,lat=ll(x,y);last=i==len(coords)-1;rows.append(f'{115 if last else 111} {lat:.8f} {lon:.8f}'+('' if last else ' '+str(style)))
    return rows
def poly_entity(index,param,g):
    rows=[]
    for p in polygon_parts(polys_only(g)):
        if p.area<2:continue
        rows+=[f'BEGIN_POLYGON {index} {param} 3','BEGIN_WINDING']
        for x,y in list(orient(p,sign=1).exterior.coords)[:-1]:
            lon,lat=ll(x,y);rows.append(f'POLYGON_POINT {lon:.9f} {lat:.9f} 0')
        rows+=['END_WINDING','END_POLYGON']
    return rows
def astar(start,goal,free,step=8):
    # Local grid used only for modeled apron route links; existing runway graph stays intact.
    start=tuple(round(v/step) for v in start);goal=tuple(round(v/step) for v in goal)
    if not free(Point(np.array(start)*step)):return None
    queue=[(0,start)];came={};cost={start:0};finish=None
    for _ in range(24000):
        if not queue:break
        _,a=heapq.heappop(queue)
        if a==goal:finish=a;break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            b=(a[0]+dx,a[1]+dy);ng=cost[a]+math.hypot(dx,dy)
            if ng>=cost.get(b,1e9):continue
            if not free(LineString([np.array(a)*step,np.array(b)*step])):continue
            cost[b]=ng;came[b]=a;heapq.heappush(queue,(ng+math.dist(b,goal),b))
    if finish is None:return None
    path=[finish]
    while path[-1] in came:path.append(came[path[-1]])
    path=[tuple(np.array(p)*step) for p in path[::-1]]
    simple=[path[0]];i=0
    while i<len(path)-1:
        j=len(path)-1
        while j>i+1 and not free(LineString([path[i],path[j]])):j-=1
        simple.append(path[j]);i=j
    return simple

def build():
    plan=build_plan();PACK.mkdir(parents=True,exist_ok=True);(PACK/'Earth nav data/+20-100').mkdir(parents=True,exist_ok=True);(PACK/'Earth nav data/+30-100').mkdir(parents=True,exist_ok=True)
    names=[g['name'] for g in plan['gates']]+[r['name'] for r in plan['new']]+['B','D','E','C12','C14','C15','CLOSED']
    atlas(names,PACK/'textures');models=[];jws=[];markings=Mesh('Current_Stand_Labels');preview_only=[]
    for name,m in plan['models'].items():
        origin=m['geom'].centroid.coords[0];mesh=terminal_mesh(name,m['geom'],m['height'])
        models.append(mesh.write(PACK/'objects'/f'{name}.obj',origin))
    for r in plan['new']+plan['details']:
        if r.get('alternative'):continue
        building=r['building'] if 'building' in r else plan['models'][r['model']]['geom']
        j=make_jetway(r,building);jws.append(j);base=j['base']
        models.append(jetway_mesh(j).write(PACK/'objects'/f'bridge_{r["name"]}.obj',base))
        po=jetway_mesh(j,active=True).write(ROOT/'preview-mesh'/f'active_{r["name"]}.obj',base);po['preview_only']=True;preview_only.append(po)
        f=heading_vec(r['heading']);ground_sign(markings,np.array(r['pos'])-f*8,r['heading'],r['name'])
    # Update painted identifiers for retained, newly renumbered B South and D East starts.
    for r in plan['ramps']:
        name=r['name'].removeprefix('Gate ')
        if r.get('old_name') and r['old_name']!=r['name'] and name in SIGN_TILES:
            ground_sign(markings,np.array(r['geom'].coords[0])-heading_vec(r['heading'])*5,r['heading'],name,4.5,2)
    models.append(markings.write(PACK/'objects/Current_Stand_Labels.obj',(0,0),True))
    solids=unary_union([v['geom'] for v in plan['models'].values()]);zone=unary_union(list(plan['zones'].values())+[solids])
    # Remove outdated scenery within the redeveloped aprons. Clip long building strips rather than deleting adjoining terminals.
    kept=[];clipped=[];removed=Counter()
    for e in plan['dsf']['entities']:
        g=e['geom'];res=e['resource'];is_ground=res.endswith(('.pol','.lin','.str'))
        if stale_west_barrier(e):removed['reopened west taxiways: '+res]+=1;continue
        if scenery_detail_cleanup(e,plan):removed['stand detail replacement: '+res]+=1;continue
        if e['kind']=='object':
            if zone.contains(g):removed[res]+=1;continue
        elif g.intersects(zone):
            if is_ground:
                if any(t in res for t in ['pavement','terrain_FX']):pass
                elif zone.covers(g) or g.intersection(zone).length>g.length*.5:removed[res]+=1;continue
            elif res.endswith('.fac') and g.geom_type in ('Polygon','MultiPolygon'):
                remain=g.difference(zone.buffer(.35));ratio=remain.area/max(g.area,.01)
                if ratio<.04:removed[res]+=1;continue
                if g.intersection(zone).area>.25:
                    clipped+=poly_entity(e['index'],e['param'],remain);removed['clipped '+res]+=1;continue
            elif zone.covers(g):removed[res]+=1;continue
        kept.extend(e['lines'])
    dsf=plan['dsf'];head=[l for l in dsf['head'] if not l.startswith(('#','FILTER','DIVISIONS','HEIGHTS')) and l.strip()]
    head=[l.replace('WorldEditor2.5.2r1','KIAH_Current_Layout_R02') for l in head]
    objects=list(dsf['objects'])
    placements=[]
    for m in models:
        rel=pathlib.Path(m['path']).relative_to(PACK).as_posix();idx=len(objects);objects.append(rel);head.append('OBJECT_DEF '+rel)
        lon,lat=ll(*m['origin']);placements.append(f'OBJECT {idx} {lon:.9f} {lat:.9f} 0')
    equipment,pads=equipment_and_lights(plan)
    added_items=equipment+ea_barriers()
    for item in added_items:
        lon,lat=ll(*item['pos'])
        if lat>=30:continue
        ref=item['resource']
        if ref not in objects:objects.append(ref);head.append('OBJECT_DEF '+ref)
        placements.append(f'OBJECT {objects.index(ref)} {lon:.9f} {lat:.9f} {item["heading"]:.2f}')
    dsftext='\n'.join(head+['DIVISIONS 32','FILTER 0']+kept+clipped+placements)+'\n'
    (ROOT/'generated').mkdir(exist_ok=True);textpath=ROOT/'generated/+29-096.txt';textpath.write_text(dsftext,encoding='utf-8')
    # Native routing: trim only local redevelopment conflicts; retain every runway active-zone attribute.
    apt=plan['apt'];nodes={a['id']:a for a in apt if a['code']==1201};edges=[];last=None;local=zone.buffer(12)
    primary=[r for r in plan['new'] if not r.get('alternative')]
    plane_union=unary_union([aircraft_outline(r['pos'],r['heading'],r['size']) for r in primary])
    ac_obstacle=unary_union([solids.buffer(21)]+[aircraft_outline(r['pos'],r['heading'],r['size']).buffer(21 if r['size']=='C' else 35) for r in primary])
    gv_obstacle=unary_union([solids.buffer(2),plane_union.buffer(2)])
    removed_edges=Counter()
    for a in apt:
        if a['code'] in (1202,1206):
            s=a['parts'];start,end=int(s[1]),int(s[2]);g=LineString([xy(nodes[start]['lon'],nodes[start]['lat']),xy(nodes[end]['lon'],nodes[end]['lat'])]);ob=ac_obstacle if a['code']==1202 else gv_obstacle
            if a['code']==1202 and a.get('name')=='EA':
                last=None;removed_edges['EA current closure']+=1;continue
            if g.intersects(ob) and g.intersects(local.buffer(80)):last=None;removed_edges[a['code']]+=1;continue
            last={'code':a['code'],'start':start,'end':end,'lines':list(a['lines']),'geom':g};edges.append(last)
        elif a['code'] in (1204,1205) and last:last['lines']+=a['lines']
    pavement=unary_union([a['geom'] for a in apt if a['code']==110]);newpavements={n:z.difference(solids) for n,z in plan['zones'].items() if n in ('B_North','D_West')}
    newpavements['B_North']=geobox(-95.3482,29.98738,-95.34350,29.9911).difference(solids)
    pavement=unary_union([pavement,*newpavements.values()])
    # Build apron links around actual staged building/aircraft envelopes and join the retained ATC network.
    used_air={e[k] for e in edges if e['code']==1202 for k in ('start','end')};node_xy={i:xy(a['lon'],a['lat']) for i,a in nodes.items()};nextid=max(nodes)+1;newlines=[];route_report=[]
    safe=prep(pavement.buffer(-18).difference(ac_obstacle));bounds=box(-760,330,580,830)
    def free(g):return bounds.covers(g) and safe.covers(g)
    targets=[(-660,425),(-385,510),(-122,535),(155,450),(450,500)]
    for target in targets:
        if not free(Point(target)):
            choices=[(target[0]+dx,target[1]+dy) for dx in range(-32,33,8) for dy in range(-32,33,8) if free(Point(target[0]+dx,target[1]+dy))]
            if not choices:route_report.append({'target':target,'status':'no safe link'});continue
            target=min(choices,key=lambda p:math.dist(p,target))
        candidates=sorted([i for i in used_air if free(Point(node_xy[i])) and node_xy[i][1]>680],key=lambda i:math.dist(node_xy[i],target))[:12]
        path=None;anchor=None
        for i in candidates:
            path=astar(target,node_xy[i],free)
            if path and free(LineString([path[-1],node_xy[i]])):anchor=i;break
        if not path:route_report.append({'target':target,'status':'no safe link'});continue
        ids=[]
        for p in path[:-1]:
            lon,lat=ll(*p);nodes[nextid]={'id':nextid,'lat':lat,'lon':lon,'parts':['1201',str(lat),str(lon),'both',str(nextid),'Apron2026']};node_xy[nextid]=p;ids.append(nextid);nextid+=1
        ids.append(anchor)
        for a,b in zip(ids,ids[1:]):
            if a==b:continue
            width_code='e' if target[0]>100 else 'c'
            edge={'code':1202,'start':a,'end':b,'lines':[f'1202 {a} {b} twoway taxiway_{width_code} Apron'],'geom':LineString([node_xy[a],node_xy[b]])};edges.append(edge)
            newlines+=apt_line([node_xy[a],node_xy[b]],'2026 apron circulation')
        route_report.append({'target':target,'status':'linked','segments':len(ids)-1})
    used={e[k] for e in edges for k in ('start','end')};ids={old:i for i,old in enumerate(sorted(used))};net=['1200']
    for old,new in ids.items():
        n=nodes[old];net.append(f'1201 {n["lat"]:.8f} {n["lon"]:.8f} both {new} N{new}')
    for e in edges:
        parts=e['lines'][0].split();parts[1]=str(ids[e['start']]);parts[2]=str(ids[e['end']]);net.append(' '.join(parts));net+=e['lines'][1:]
    output=[];removed_apt=Counter()
    for a in apt:
        code=a['code']
        if code in (99,1200,1201,1202,1204,1205,1206,1300):continue
        if code==120 and a.get('geom') is not None and box(-880,-45,-680,10).covers(a['geom']) and a['lines'][1].split()[-1]=='51':
            removed_apt['old Terminal A remote stand markings']+=1;continue
        if code==120 and a.get('geom') is not None and a['geom'].intersects(zone):removed_apt[code]+=1;continue
        if code in (20,1400,1401):
            s=a['parts'];p=Point(xy(float(s[2]),float(s[1])))
            if zone.contains(p):removed_apt[code]+=1;continue
        if code==1:
            s=a['parts'];s[1]='96';output.append(' '.join(s));continue
        if code==100:
            s=a['parts'];s[1]='45.72';output.append(' '.join(s));continue
        output.extend(a['lines'])
    output[1]='1200 KIAH 2026-10-24 Review R02 - direct native build'
    for n,g in newpavements.items():output+=apt_poly(g,n+' apron 2026')
    output+=newlines
    for r in primary+plan['details']:
        p=np.array(r['pos']);f=heading_vec(r['heading']);right=np.array([f[1],-f[0]])
        output+=apt_line([p-f*48,p],'Stand '+r['name']+' lead-in');output+=apt_line([p-right*2,p+right*2],'Stand '+r['name']+' stop')
    for pad in pads:
        output+=apt_line(list(pad['geom'].exterior.coords),'GSE equipment bay '+pad['name'],20)
    output+=net
    for r in plan['ramps']:
        output.append(f'1300 {r["lat"]:.8f} {r["lon"]:.8f} {r["heading"]%360:.2f} {r["kind"]} {r["equipment"]} {r["name"]}')
        meta=list(r.get('rampmeta',['1301','C','airline']))
        if r['kind']=='misc':meta=meta[:2]+['none']
        output.append(' '.join(meta))
    for j in jws:
        lon,lat=ll(*j['base']);output.append(f'1500 {lat:.8f} {lon:.8f} {j["heading"]:.2f} 1 {j["size"]} {j["heading"]:.2f} {j["length"]:.2f} {j["cabin_heading"]:.2f}')
    output+=['99'];(PACK/'Earth nav data/apt.dat').write_text('\n'.join(output)+'\n',encoding='utf-8')
    base=ROOT/'KIAH-99761/compiled/KIAH_Scenery_Pack';shutil.copy2(base/'COPYING',PACK/'COPYING');shutil.copy2(base/'README.txt',PACK/'Gateway-original-README.txt')
    north=parse_dsf(ROOT/'compiler-check/+30-096.txt');nhead=[l for l in north['head'] if not l.startswith(('#','FILTER','DIVISIONS','HEIGHTS')) and l.strip()];nobj=list(north['objects']);nplacements=[]
    for item in added_items:
        lon,lat=ll(*item['pos'])
        if lat<30:continue
        ref=item['resource']
        if ref not in nobj:nobj.append(ref);nhead.append('OBJECT_DEF '+ref)
        nplacements.append(f'OBJECT {nobj.index(ref)} {lon:.9f} {lat:.9f} {item["heading"]:.2f}')
    ntext=ROOT/'generated/+30-096.txt';ntext.write_text('\n'.join(nhead+['DIVISIONS 32','FILTER 0']+[l for e in north['entities'] for l in e['lines']]+nplacements)+'\n')
    nr=subprocess.run([str(ROOT/'xptools-24-5/tools/DSFTool.exe'),'--text2dsf',str(ntext),str(PACK/'Earth nav data/+30-100/+30-096.dsf')],capture_output=True,text=True);nr.check_returncode()
    result=subprocess.run([str(ROOT/'xptools-24-5/tools/DSFTool.exe'),'--text2dsf',str(textpath),str(PACK/'Earth nav data/+20-100/+29-096.dsf')],capture_output=True,text=True)
    (ROOT/'generated/compiler.log').write_text(result.stdout+result.stderr);print(result.stdout);result.check_returncode()
    exported=parse_apt(PACK/'Earth nav data/apt.dat')
    preview={'models':models,'jetways':jws,'preview_only':preview_only,'new_stands':[{k:v for k,v in r.items() if k not in ('geom','building')} for r in plan['new']+plan['details']],'model_outlines':{k:mapping(v['geom']) for k,v in plan['models'].items()},'retained_entities':len(kept),'date':DATE,'equipment':added_items,'inactive_directory_gates':plan['inactive']}
    (ROOT/'generated/scene.json').write_text(json.dumps(preview,indent=2));(ROOT/'generated/sign_tiles.json').write_text(json.dumps(SIGN_TILES))
    report={'build_date':DATE,'pack':str(PACK),'ramp_count':len(plan['ramps']),'runways':5,'new_B_north_gates':22,'new_D_west_primary_gates':6,'D_west_manual_alternates':8,'new_active_jetways':len(jws),'removed_scenery':dict(removed),'removed_apt':dict(removed_apt),'removed_edges':dict(removed_edges),'apron_route_links':route_report,'models':models,'installed':False,'simulator_tested':False}
    report.update(stale_west_barriers_removed=sum(stale_west_barrier(e) for e in plan['dsf']['entities']),equipment_and_light_placements=len(equipment),equipment_bays=len(pads),current_EA_closure_barriers=len(ea_barriers()),gate_decisions=plan['inactive'])
    (ROOT/'generated/build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('removed_scenery','models')},indent=2))
    return report
if __name__=='__main__':build()
