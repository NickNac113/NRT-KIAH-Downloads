"""R27 isolated shelter, jetway alignment, mast and service-access correction.

No simulator automation or public publication. Predecessors are read-only.
"""
from pathlib import Path
import importlib.util,sys,json,math,hashlib,shutil,inspect,copy
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R26_Lighting_Access_R23'
s=importlib.util.spec_from_file_location('r26',PREV/'source/build_r26.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;r25=b.b;r24=r25.b;np=b.np;box=b.box;Point=b.Point;Line=b.Line;union=b.union
NAME='KIAH_NRT_R27_Shelter_Service_R24';PACK=ROOT/'package'/NAME;OUT=ROOT/'output';QA=ROOT/'qa'
OLD=PREV/'package/KIAH_NRT_R26_Lighting_Access_R23';SOURCE=PREV/'qa/R26_Roundtrip.txt'
BASE=g.ag.parse_dsf(SOURCE);APT=g.ag.parse_apt(OLD/'Earth nav data/apt.dat')
EVIDENCE=json.loads((OLD/'Build_Evidence.json').read_text())
PLACEMENTS={q['resource']:q for q in BASE['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
MAST_RESOURCE='lib/airport/Common_Elements/Lighting/flood_1_led_24m_omni.obj'
MAST=[2724.3,422.0]
FLOORS={'canopy':box(2620,292,2674,348).difference(union(r25.COLS)).difference(box(2668.5,311.8,2674,318.2)),
 'indoor':box(2435,285,2510,432.3).union(box(2510,290,2512,428))}
NODES=[];EDGES=[];REPLACED={};PATHS=[];PARKS=[];DESTS=[];CHANGES=[];JETWAYS=copy.deepcopy(EVIDENCE['jetways'])
for j in JETWAYS:
    if j['stand']=='NRT9':
        j['base'][0]+=4;j['root'][0]+=4
g.PACK=PACK;g.OUT=OUT;g.QA=QA;g.placements=[];g.meshes=[];g.changes=[];g.checks=[]
r25.PACK=PACK;r25.EVIDENCE=copy.deepcopy(EVIDENCE);r25.EVIDENCE['jetways']=JETWAYS

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(folder):return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
def prepare():
    assert not (ROOT/'NRT_KIAH_R27_Test.zip').exists(),'Sealed revision; use a successor'
    for p in [PACK,OUT,QA,ROOT/'reference']:p.mkdir(parents=True,exist_ok=True)
    for fn,folder in [('R26_Hashes.json',OLD),('Published_Hashes.json',ROOT.parents[1]/'distribution/NRT_KIAH_Updater_R01/scenery')]:
        dest=ROOT/'reference'/fn;now=snapshot(folder)
        if dest.exists():assert json.loads(dest.read_text())==now,fn+' changed'
        else:dest.write_text(json.dumps(now,indent=2))
    shutil.copytree(OLD,PACK,dirs_exist_ok=True)

def finish_uv(c,u,v):
    N=1024;c={10:4,11:6}.get(c,c%8)
    return ((c%4*N+2+u*(N-4))/(4*N),1-(c//4*N+2+(1-v)*(N-4))/(2*N))

def headquarters():
    g.material_uv=finish_uv
    src=inspect.getsource(r24.model).replace('r24_','r25_')
    src=src[:src.index('    save(m)')]+ '    save(m)\n'
    src=src.replace('p=a+v*t/length;g.block',"p=a+v*t/length\n            if any(abs(p[1]-419.39)<.2 and abs(p[0]-j['root'][0])<2.05 for j in EVIDENCE['jetways']):continue\n            g.block")
    src=src.replace('m.extrude(rail,4.35,4.5,1)',"m.extrude(rail.difference(union([box(j['root'][0]-1.75,418.8,j['root'][0]+1.75,419.95) for j in EVIDENCE['jetways']])),4.35,4.5,1)")
    scope=dict(vars(r24));scope.update(g=g,save=g.save,EVIDENCE=r25.EVIDENCE)
    exec(src,scope);scope['model']()
    # Retain the reviewed R26 lighting exactly after rebuilding only facade cuts.
    rel='objects/nrt_test/r25_jet_center.obj';p=PACK/rel
    oldlights=[r for r in (OLD/rel).read_text().splitlines() if r.startswith('LIGHT_PARAM ')]
    rows=[r for r in p.read_text().splitlines() if not r.startswith('LIGHT_PARAM ')]
    p.write_text('\n'.join(rows+oldlights)+'\n')
    m=g.Mesh('r25_jetway_portals',[2800,419.39])
    for j in JETWAYS:
        x=j['root'][0]
        for q in [box(x-2.05,419.40,x-1.70,419.90),box(x+1.70,419.40,x+2.05,419.90)]:m.extrude(q,3.5,7.05,0)
        g.block(m,[x-2.05,419.40,x+2.05,419.90],7.05,7.30,1,0)
        g.block(m,[x-1.70,418.90,x+1.70,420.10],3.65,3.72,7,7)
        g.block(m,[x-1.70,418.90,x+1.70,420.10],6.98,7.05,7,7)
        for xx in [x-1.76,x+1.76]:g.block(m,[xx-.04,418.90,xx+.04,420.10],3.72,7.05,7,7)
    g.save(m)

def red_boxes():
    rel='objects/nrt_test/ramp_safety.obj';rows=(PACK/rel).read_text().splitlines()
    vl=[i for i,r in enumerate(rows) if r.startswith('VT ')];v=np.array([list(map(float,rows[i].split()[1:])) for i in vl])
    ids=[int(a) for r in rows if r.startswith(('IDX ','IDX10 ')) for a in r.split()[1:]]
    q=PLACEMENTS[rel];o=np.array([q['geom'].x,q['geom'].y]);selected=set();count=0
    region=box(2779,419.5,2796,435)
    for i in range(0,len(ids),3):
        ii=ids[i:i+3];vv=v[ii];en=vv[:,[0,2]]*np.array([1,-1])+o
        if np.max(np.abs(vv[:,6]-.40625))<1e-6 and region.covers(Point(en.mean(0))):selected.update(ii);count+=1
    assert count==24,('NRT9 red box triangles',count) # 12 triangles per closed rectangular outline
    for i in range(0,len(ids),3):assert sum(j in selected for j in ids[i:i+3]) in [0,3]
    for j in selected:v[j,0]+=4;rows[vl[j]]='VT '+' '.join(f'{a:.6f}' for a in v[j])
    (PACK/rel).write_text('\n'.join(rows)+'\n');CHANGES.append(dict(resource=rel,red_triangles_shifted=count,dx_m=4))

def simple(name,origin,draped=False):
    m=r25.OriginalMesh(name,origin,draped);m.detailed=False;m.texture='atlas.png';m.normal=None
    return m

def sheltered_floors():
    # Same modeled, non-draped floor material and height used by MH1/MH2.
    # This is a visible floor, not a claim of rain-particle occlusion.
    from materials import material_uv as original_uv
    g.material_uv=original_uv
    for name,geom in FLOORS.items():
        m=r25.OriginalMesh('r27_'+name+'_floor',list(geom.centroid.coords)[0]);m.flat(geom,.03,11);m.save()
    m=simple('r27_sheltered_guidance',[2648,359])
    covered=union(list(FLOORS.values()))
    for q in APT:
        if q['code']!=120 or q.get('geom') is None:continue
        ln=q['geom'].intersection(covered)
        if ln.is_empty:continue
        m.flat(ln.buffer(.22,cap_style=2).intersection(covered),.041,7)
        m.flat(ln.buffer(.085,cap_style=2).intersection(covered),.045,4)
    m.flat(Line([(2646,314),(2650,314)]).buffer(.10,cap_style=2),.047,4)
    for y in [312.5,317.2]:m.flat(Line([(2653.8,y),(2668.5,y)]).buffer(.04,cap_style=2),.047,5)
    m.save();g.material_uv=finish_uv

def service_routes():
    nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in APT if q['code']==1201};nextid=max(nodes)+1
    lookup={tuple(np.round(p,3)):i for i,p in nodes.items()}
    def node(p):
        nonlocal nextid
        key=tuple(np.round(p,3))
        if key not in lookup:
            lookup[key]=nextid;nodes[nextid]=list(p);NODES.append(dict(id=nextid,xy=list(p)));nextid+=1
        return lookup[key]
    def chain(points,name,step=20):
        pts=b.densify(points,step);ii=[node(p) for p in pts]
        return [dict(a=a,b=c,name=name) for a,c in zip(ii,ii[1:])]
    # Preserve the inherited NB road shape. More vertices give the native AI
    # closer network access points instead of nearly kilometre-long segments.
    split_pairs={frozenset(p) for p in [(918,919),(972,1176),(1176,1177),(1176,883)]}
    for q in APT:
        if q['code']!=1206:continue
        a,c=map(int,q['parts'][1:3])
        if frozenset((a,c)) in split_pairs:
            assert q['parts'][3]=='twoway'
            REPLACED[q['lines'][0]]=chain([nodes[a],nodes[c]],'NRT R27 NB paved approach')
        # Split the actual existing R26 edge at the dispatch-yard T junction.
        elif 'NRT R26 Cargo transfer' in q['lines'][0] and min(nodes[a][0],nodes[c][0])<2892<max(nodes[a][0],nodes[c][0]) and abs(nodes[a][1]-550)<.01:
            REPLACED[q['lines'][0]]=chain([nodes[a],(2892,550),nodes[c]],'NRT R27 yard junction')
    assert len(REPLACED)==5
    paths=[('Local service yard',[(2892,425),(2892,550)]),
      ('West airside access',[(nodes[919][0],550),(2613,550),(2613,355),(2606,355),(2606,300)])]
    for name,points in paths:
        PATHS.append(dict(name=name,points=points));EDGES.extend(chain(points,'NRT R27 '+name,14))
    for i,kind in enumerate(['food','gpu','baggage_loader','baggage_train','fuel_liners','fuel_jets','pushback']):
        PARKS.append(dict(xy=[2904,430+i*14],heading=270,type=kind,cars=1 if kind=='baggage_train' else 0,name='NRT R27 '+kind+' service parking'))
    DESTS.append(dict(xy=[2904,536],heading=270,types='food|gpu|baggage_loader|baggage_train|fuel_liners|fuel_jets|pushback',name='NRT R27 service holding'))
    # Native vehicles are not constrained by paint. This marks the real graph.
    m=simple('r27_service_road_paint',[2750,500],True);m.layer=('markings',3)
    from shapely.ops import substring
    taxi=union([q['geom'] for q in APT if q['code']==120 and q.get('geom') is not None]);crossings=taxi.buffer(4)
    for p in PATHS:
        boundary=Line(p['points']).buffer(3,cap_style=2,join_style=2).boundary.difference(crossings)
        for ln in g.lines(boundary):
            for d in np.arange(0,ln.length,9):
                if min(d+3,ln.length)-d>.2:m.flat(substring(ln,d,min(d+3,ln.length)).buffer(.055,cap_style=2),0,5)
    for p in PARKS:
        x,y=p['xy'];m.flat(Line([(x-5,y-2.1),(x+10,y-2.1),(x+10,y+2.1),(x-5,y+2.1)]).buffer(.06,cap_style=2,join_style=2),0,5)
    # Aircraft crossing give-way triangles, outside the yellow guidance.
    for y in [420,315]:
        for yy,sgn in [(y+7,-1),(y-7,1)]:
            x=2613 if y==420 else 2606
            for xx in [x-1,x,x+1]:m.flat(r25.Polygon([(xx-.35,yy),(xx+.35,yy),(xx,yy+sgn*.65)]).boundary.buffer(.05),0,5)
    m.save()

def apt():
    out=[];shifted=0
    for q in APT:
        if q['code']==1500:
            r=q['lines'][0].split();xy=g.ag.xy(float(r[2]),float(r[1]))
            if any(j['stand']=='NRT9' and Point(xy).distance(Point(j['base']))<.1 for j in EVIDENCE['jetways']):
                lo,la=g.ag.ll(xy[0]+4,xy[1]);r[1]=f'{la:.9f}';r[2]=f'{lo:.9f}';out+=[' '.join(r),*q['lines'][1:]];shifted+=1;continue
        if q['code']==1206 and q['lines'][0] in REPLACED:
            out += [f'1206 {e["a"]} {e["b"]} twoway {e["name"]}' for e in REPLACED[q['lines'][0]]];continue
        out.extend(r for r in q['lines'] if r.strip()!='99')
    assert shifted==2
    for n in NODES:
        lo,la=g.ag.ll(*n['xy']);out.append(f'1201 {la:.9f} {lo:.9f} both {n["id"]} NRT R27 paved service')
    for e in EDGES:out.append(f'1206 {e["a"]} {e["b"]} twoway {e["name"]}')
    for p in PARKS:
        lo,la=g.ag.ll(*p['xy']);out.append(f'1400 {la:.9f} {lo:.9f} {p["heading"]} {p["type"]} {p["cars"]} {p["name"]}')
    for p in DESTS:
        lo,la=g.ag.ll(*p['xy']);out.append(f'1401 {la:.9f} {lo:.9f} {p["heading"]} {p["types"]} {p["name"]}')
    (PACK/'Earth nav data/apt.dat').write_text('\n'.join(out+['99'])+'\n')

def dsf():
    raw=SOURCE.read_text();objects=list(BASE['objects']);defs=[];cmd=[]
    for ident in ['9A','9B']:
        rel='objects/nrt_test/r25_fixed_'+ident+'.obj';q=PLACEMENTS[rel]
        r=q['lines'][0].split();lo,la=g.ag.ll(q['geom'].x+4,q['geom'].y);r[2]=f'{lo:.9f}';r[3]=f'{la:.9f}'
        assert raw.count(q['lines'][0])==1;raw=raw.replace(q['lines'][0],' '.join(r))
    add=[p for p in g.placements if p['resource'] not in PLACEMENTS]+[dict(resource=MAST_RESOURCE,origin=MAST,heading=0)]
    for p in add:
        r=p['resource']
        if r not in objects:objects.append(r);defs.append('OBJECT_DEF '+r)
        lo,la=g.ag.ll(*p['origin']);cmd.append(f'OBJECT {objects.index(r)} {lo:.9f} {la:.9f} {p["heading"]}')
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(cmd)+'\n'
    src=QA/'R27_South.txt';src.write_text(raw);dst=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile.txt').write_text(g.run([g.TOOL,'--text2dsf',src,dst]));(QA/'Decompile.txt').write_text(g.run([g.TOOL,'--dsf2text',dst,QA/'R27_Roundtrip.txt']))

def main():
    prepare();headquarters();red_boxes();sheltered_floors();service_routes();apt();dsf()
    evidence=copy.deepcopy(EVIDENCE);evidence.update(name=NAME,layout='R27',revision='R24',runtime_tested=False,jetways=JETWAYS)
    evidence['r27']=dict(jetway_shift_east_m=4,jetways=JETWAYS,marking_changes=CHANGES,mast=dict(resource=MAST_RESOURCE,xy=MAST,heading=0),floors={n:dict(bounds=list(p.bounds),area_m2=p.area,height_m=.03) for n,p in FLOORS.items()},new_placements=g.placements,service_nodes=NODES,service_edges=EDGES,replaced_edges=REPLACED,service_paths=PATHS,vehicle_parking=PARKS,vehicle_destinations=DESTS,beacon=False,public_release=False,runtime_tested=False,service_limitation='Native AI final approaches and traffic behavior require in-simulator testing. No proven root cause is claimed from the screenshot.',weather_limitation='Modeled floors mirror dry MH1/MH2 treatment; rain particles and threshold appearance require wet-weather testing.')
    (PACK/'Build_Evidence.json').write_text(json.dumps(evidence,indent=2));(OUT/'Change_List.json').write_text(json.dumps(evidence['r27'],indent=2))
    print(json.dumps(dict(package=str(PACK),nodes=len(NODES),roads=len(EDGES),parking=len(PARKS),jetways_shifted=2)))
if __name__=='__main__':main()
