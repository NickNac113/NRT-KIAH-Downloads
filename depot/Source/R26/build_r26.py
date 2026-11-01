"""R26 work lights, separated pedestrian lane and native airside service access.

Isolated successor. Does not install, publish, or change a predecessor.
"""
from pathlib import Path
import importlib.util,sys,json,math,hashlib,shutil
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R25_Realism_R22'
s=importlib.util.spec_from_file_location('r25',PREV/'source/build_r25.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;np=b.np;box=b.box;Point=b.Point;Line=b.Line;union=b.union
NAME='KIAH_NRT_R26_Lighting_Access_R23';PACK=ROOT/'package'/NAME;OUT=ROOT/'output';QA=ROOT/'qa'
OLD=PREV/'package/KIAH_NRT_R25_Realism_R22';SOURCE=PREV/'qa/R25_Roundtrip.txt'
BASE=g.ag.parse_dsf(SOURCE);APT=g.ag.parse_apt(OLD/'Earth nav data/apt.dat')
EVIDENCE=json.loads((OLD/'Build_Evidence.json').read_text())
PLACEMENTS={q['resource']:q for q in BASE['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
# A four-metre lateral stand adjustment buys clearance from the full A380
# rectangle, not an optimistic assumption about where its swept wing tapers.
OLD_NRT9=next(q for q in APT if q['code']==1300 and q['name']=='NRT9')
DX=4.0;NRT9=[OLD_NRT9['geom'].x+DX,OLD_NRT9['geom'].y]
WALK=b.WALK;GA_WALK=b.GA_WALK;HELI=b.HELI_RESERVE
SERVICE_LINK=box(2809.2697,590.5,2817.2697,601.0)
LIGHTS=[];CHANGES=[];ROUTES=[];NODES=[];MARKS=[]
g.PACK=PACK;g.OUT=OUT;g.QA=QA;g.placements=[];g.meshes=[];g.changes=[];g.checks=[]
b.PACK=PACK;b.OUT=OUT;b.QA=QA
g.B={'placements':[dict(resource=r,origin=[q['geom'].x,q['geom'].y]) for r,q in PLACEMENTS.items()]}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(folder):return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
def prepare():
    assert not (ROOT/'NRT_KIAH_R26_Test.zip').exists(),'Sealed revision; use a successor'
    for p in [PACK,OUT,QA,ROOT/'reference']:p.mkdir(parents=True,exist_ok=True)
    for filename,folder in [('R25_Hashes.json',OLD),('Published_Hashes.json',ROOT.parents[1]/'distribution/NRT_KIAH_Updater_R01/scenery')]:
        p=ROOT/'reference'/filename;now=snapshot(folder)
        if p.exists():assert json.loads(p.read_text())==now,filename+' changed'
        else:p.write_text(json.dumps(now,indent=2))
    shutil.copytree(OLD,PACK,dirs_exist_ok=True)
    # Retired during this unsealed build: use the nine existing roof fixtures.
    obsolete=PACK/'objects/nrt_test/r26_canopy_work_lights.obj'
    if obsolete.is_file():obsolete.unlink()

def new_mesh(name,origin,draped=False):
    # Use the established OBJ8 writer. Simple fixture metal samples the existing
    # colour atlas; no new texture library or proprietary asset is needed.
    m=g.Mesh(name,origin,draped);m.detailed=False;m.texture='atlas.png';m.normal=None
    return m

def fixture(m,ident,xyz,target,cd,half,role,mount):
    p=np.array(xyz,float);aim=np.array(target,float)-p;aim/=np.linalg.norm(aim)
    pitch=math.degrees(math.asin(-aim[2]));assert pitch>half+1,'Beam must stay below horizon'
    right=np.cross(aim,[0,0,1.])
    if np.linalg.norm(right)<.01:right=np.array([1.,0,0])
    right/=np.linalg.norm(right);up=np.cross(right,aim);up/=np.linalg.norm(up)
    # Rectangular LED head, shallow rain hood, metal back and real mounting arm.
    def face(center,w,h,c):
        m.face([center+right*x*w/2+up*y*h/2 for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]],c)
    back=p-aim*.18
    face(back,.65,.42,1);face(p,.59,.34,8)
    for axis,side in [(up,.21),(-up,.21),(right,.325),(-right,.325)]:
        tangent=right if abs(np.dot(axis,up))>.5 else up;extent=.325 if abs(np.dot(axis,up))>.5 else .21
        m.face([back+axis*side-tangent*extent,back+axis*side+tangent*extent,p+axis*side+tangent*extent,p+axis*side-tangent*extent],1)
    g.rod(m,mount,back,.07,3)
    local=[p[0]-m.o[0],p[2],m.o[1]-p[1]];direction=[aim[0],aim[2],-aim[1]]
    width=math.cos(math.radians(half));pos=' '.join(f'{v:.5f}' for v in local);dr=' '.join(f'{v:.7f}' for v in direction)
    # _pm definitions in stock lights.txt have DAY=0. A bounded directional spill
    # provides actual light; a small lamp billboard is not a substitute for it.
    m.lights.append(f'LIGHT_PARAM spot_params_sp_pm {pos} 0.96 0.98 1.0 1 {cd}cd {dr} {width:.7f}')
    m.lights.append(f'LIGHT_PARAM spot_params_bb_pm {pos} 0.96 0.98 1.0 {cd/160:g}cd {dr} 0.15')
    LIGHTS.append(dict(id=ident,position=xyz,target=target,candela=cd,half_angle_deg=half,pitch_down_deg=pitch,role=role,mount=mount,object=m.name,night_only=True,existing_fixture=False))

def lights():
    m=new_mesh('r26_terminal_work_lights',[2800,419.39])
    # Cross light the service/nose areas from the parapet, leaving all three
    # rotundas and their moving tunnel geometry alone.
    for i,x in enumerate([2737,2754,2772,2806,2828,2844,2865,2878],1):
        fixture(m,'T%02d'%i,[x,420.05,9.35],[x,435.0,0],24000,27,'Terminal nose/service apron',[x,419.30,9.35])
    for ident,x,y in [('T09',2750,449),('T10',2780,449),('T11',2829,451),('T12',2855,451)]:
        fixture(m,ident,[x,420.1,9.45],[x,y,0],48000,14,'Focused stand throw',[x,419.25,9.45])
    # West facade: NRT11 nose + the sheltered pedestrian approach.
    for i,y in enumerate([391,411],1):
        fixture(m,'W%02d'%i,[2724.05,y,8.8],[2709,y,0],18000,27,'NRT11 work area',[2724.65,y,8.8])
    fixture(m,'W03',[2673.55,365,6.5],[2670.7,370.8,0],2500,30,'Pedestrian doorway',[2674.05,365,6.5])
    g.save(m)
    # The roof already has nine modeled lamps at 15.7m. Retune those actual
    # lamps, preserving their mounts and the accepted structural headroom.
    rel='objects/nrt_test/r25_jet_center.obj';rows=(PACK/rel).read_text().splitlines()
    origin=PLACEMENTS[rel]['geom'];spills=glows=0
    for i,row in enumerate(rows):
        r=row.split()
        if len(r)<6 or r[0]!='LIGHT_PARAM' or r[3]!='15.700':continue
        assert r[1] in ['spot_params_sp_pm','spot_params_bb_pm']
        if r[1]=='spot_params_sp_pm':
            assert r[9]=='2800cd';r[5:10]=['0.96','0.98','1.0','1','7500cd'];r[-1]=f'{math.cos(math.radians(39)):.7f}';spills+=1
            x,y=origin.x+float(r[2]),origin.y-float(r[4])
            LIGHTS.append(dict(id='C%02d'%spills,position=[x,y,15.7],target=[x,y,0],candela=7500,half_angle_deg=39,pitch_down_deg=90,role='Existing canopy downlight upgraded',mount=[x,y,16.08],object='r25_jet_center',night_only=True,existing_fixture=True))
        else:
            assert r[8]=='280cd';r[5:9]=['0.96','0.98','1.0','47cd'];glows+=1
        rows[i]=' '.join(r)
    assert spills==glows==9
    (PACK/rel).write_text('\n'.join(rows)+'\n')
    m=new_mesh('r26_hangar_work_lights',[2512,440])
    for i,(y,z,role) in enumerate([(316,19.1,'Indoor Parking apron'),(359,19.1,'Indoor Parking apron'),(402,19.1,'Indoor Parking apron'),(449,18.9,'MH2 apron'),(474,18.9,'MH2 apron'),(507,15.5,'MH1 apron'),(574,15.5,'MH1 apron')],1):
        fixture(m,'M%02d'%i,[2512.65,y,z],[2536,y,0],42000,27,role,[2511.7,y,z])
    g.save(m)

def shift_markings():
    # Both meshes are static and use unshared triangle vertices. Leave the red
    # jetway movement boxes fixed because their rotundas do not move.
    for rel in ['objects/nrt_test/paint.obj','objects/nrt_test/ramp_safety.obj']:
        rows=(PACK/rel).read_text().splitlines();vlines=[i for i,r in enumerate(rows) if r.startswith('VT ')];v=np.array([list(map(float,rows[i].split()[1:])) for i in vlines]);ids=[int(a) for r in rows if r.startswith(('IDX ','IDX10 ')) for a in r.split()[1:]]
        q=PLACEMENTS[rel];origin=[q['geom'].x,q['geom'].y];selected=set();triangles=0
        for i in range(0,len(ids),3):
            ii=ids[i:i+3];vv=v[ii];en=vv[:,[0,2]]*np.array([1,-1])+origin
            inside=box(2718,430,2807,535).covers(Point(en.mean(0)))
            if rel.endswith('ramp_safety.obj'):inside=inside and np.max(np.abs(vv[:,6]-.34375))<1e-6
            if inside:selected.update(ii);triangles+=1
        assert triangles==(6 if rel.endswith('/paint.obj') else 8),(rel,triangles)
        # Reject a partial shared-vertex edit rather than tearing neighbouring art.
        for i in range(0,len(ids),3):assert sum(j in selected for j in ids[i:i+3]) in [0,3]
        for j in selected:
            v[j,0]+=DX;rows[vlines[j]]='VT '+' '.join(f'{a:.6f}' for a in v[j])
        (PACK/rel).write_text('\n'.join(rows)+'\n');CHANGES.append(dict(resource=rel,triangles_shifted=triangles,dx_m=DX,red_jetway_boxes_unchanged=True))

def densify(points,step=14):
    out=[]
    for a,c in zip(points,points[1:]):
        a=np.array(a,float);c=np.array(c,float);n=max(1,math.ceil(np.linalg.norm(c-a)/step))
        out.extend((a+(c-a)*t/n).tolist() for t in range(n))
    return out+[list(points[-1])]

def service_routes():
    nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in APT if q['code']==1201};next_id=max(nodes)+1;lookup={tuple(np.round(v,3)):k for k,v in nodes.items()}
    def node(p):
        nonlocal next_id
        key=tuple(np.round(p,3))
        if key not in lookup:
            lookup[key]=next_id;NODES.append(dict(id=next_id,xy=list(p)));next_id+=1
        return lookup[key]
    # Branch at the existing paved road corner, then run down the clear gap
    # between NRT8 and NRT9. Aircraft service endpoints stay on concrete.
    c=nodes[919];x=c[0]
    paths=[('Terminal service approach',[c,(x,550),(x,525),(x,435)]),
      ('Cargo transfer',[(x,550),(2945,550),(3006,550),(3008,548),(3008,334)]),
      ('Cargo 1-4 service',[(2945,550),(2945,740)])]
    edges=set()
    for name,points in paths:
        pts=densify(points);nn=[node(p) for p in pts]
        for a,c in zip(nn,nn[1:]):
            key=tuple(sorted([a,c]))
            if key in edges:continue
            edges.add(key);ROUTES.append(dict(a=a,b=c,name='NRT R26 '+name))
        MARKS.append(dict(name=name,points=[list(p) for p in points]))
    # Add explicit junction nodes shared by all chains. Densification must
    # include the branch point at y550 rather than leaving an unjoined crossing.
    assert any(n['xy']==[x,550] for n in NODES)
    p=new_mesh('r26_service_road_paint',[2900,500],True);p.layer=('markings',3)
    # Short white broken edges denote the service road. Gaps at aircraft taxi
    # crossings avoid confusing these markings with yellow taxi guidance.
    crossing=union([Point([x,567]).buffer(14),Point([2897,550]).buffer(16)])
    for mark in MARKS:
        line=Line(mark['points']);boundary=line.buffer(3,cap_style=2,join_style=2).boundary.difference(crossing)
        for ln in g.lines(boundary):
            for a in np.arange(0,ln.length,9):
                end=min(a+3,ln.length)
                if end-a>.2:
                    from shapely.ops import substring
                    p.flat(substring(ln,a,end).buffer(.055,cap_style=2),0,5)
    g.save(p)

def apt():
    out=[];changed=0
    for q in APT:
        if q['code']==1300 and q['name']=='NRT9':
            r=q['lines'][0].split();lo,la=g.ag.ll(*NRT9);r[1]=f'{la:.9f}';r[2]=f'{lo:.9f}';out+=[' '.join(r),*q['lines'][1:]];changed+=1;continue
        if q['code']==120 and abs(q['geom'].bounds[0]-OLD_NRT9['geom'].x)<.02 and abs(q['geom'].bounds[2]-OLD_NRT9['geom'].x)<.02 and abs(q['geom'].bounds[1]-NRT9[1])<.02:
            out.append(q['lines'][0]+' / R26 pedestrian clearance')
            for line in q['lines'][1:]:
                r=line.split();x,y=g.ag.xy(float(r[2]),float(r[1]));lo,la=g.ag.ll(x+DX,y);r[1]=f'{la:.9f}';r[2]=f'{lo:.9f}';out.append(' '.join(r))
            changed+=1;continue
        out += [s for s in q['lines'] if s.strip()!='99']
    assert changed==2
    out.append('110 2 0.25 0 NRT R26 paved service road connector')
    coords=list(SERVICE_LINK.exterior.coords)[:-1]
    for i,(x,y) in enumerate(coords):
        lo,la=g.ag.ll(x,y);out.append(f'{113 if i==len(coords)-1 else 111} {la:.9f} {lo:.9f}')
    for n in NODES:
        lo,la=g.ag.ll(*n['xy']);out.append(f'1201 {la:.9f} {lo:.9f} both {n["id"]} NRT R26 paved service')
    for e in ROUTES:out.append(f'1206 {e["a"]} {e["b"]} twoway {e["name"]}')
    out+=['99'];(PACK/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n')

def dsf():
    raw=SOURCE.read_text();objects=list(BASE['objects']);defs=[];commands=[]
    # Bridge the measured 6.8m unpaved verge between the inherited service road
    # and our apron. Only the gap gets a native surface overlay; no floating slab.
    pavement=union([q['geom'] for q in APT if q['code'] in [100,110]]+[q['geom'] for q in BASE['entities'] if q['kind']=='polygon' and '/pavement/' in q['resource']])
    polys=list(BASE['polygons']);r='lib/airport/ground/pavement/concrete_L/new.pol'
    if r not in polys:polys.append(r);defs.append('POLYGON_DEF '+r)
    from shapely.geometry.polygon import orient
    for p in g.parts(SERVICE_LINK.difference(pavement)):
        commands += [f'BEGIN_POLYGON {polys.index(r)} 0 2','BEGIN_WINDING']
        for x,y in list(orient(p,1).exterior.coords)[:-1]:
            lo,la=g.ag.ll(x,y);commands.append(f'POLYGON_POINT {lo:.9f} {la:.9f}')
        commands += ['END_WINDING','END_POLYGON']
    for p in g.placements:
        r=p['resource']
        if r not in objects:objects.append(r);defs.append('OBJECT_DEF '+r)
        lo,la=g.ag.ll(*p['origin']);commands.append(f'OBJECT {objects.index(r)} {lo:.9f} {la:.9f} {p["heading"]}')
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(commands)+'\n'
    src=QA/'R26_South.txt';src.write_text(raw);dst=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile.txt').write_text(g.run([g.TOOL,'--text2dsf',src,dst]))
    (QA/'Decompile.txt').write_text(g.run([g.TOOL,'--dsf2text',dst,QA/'R26_Roundtrip.txt']))

def main():
    prepare();lights();shift_markings();service_routes();apt();dsf()
    e=dict(EVIDENCE);e.update(name=NAME,layout='R26',revision='R23',runtime_tested=False)
    e['r26']=dict(lights=LIGHTS,new_light_count=22,upgraded_light_count=9,new_placements=g.placements,nrt9_nosewheel=NRT9,nrt9_shift_east_m=DX,walk=WALK,ga_walk=GA_WALK,marking_changes=CHANGES,service_nodes=NODES,service_edges=ROUTES,service_paths=MARKS,service_link_bounds=list(SERVICE_LINK.bounds),service_diagnosis='NB road network inherited unchanged from public baseline. No NRT airside service branch in R25; 6.8m grass verge separates the service road and campus. Added connected paved routes and an 8m-wide short native connector; final AI approach still requires testing.',helipad_poles_added=0,beacon=False,public_release=False)
    (PACK/'Build_Evidence.json').write_text(json.dumps(e,indent=2));(OUT/'Change_List.json').write_text(json.dumps(e['r26'],indent=2))
    print(json.dumps(dict(package=str(PACK),lights=len(LIGHTS),service_nodes=len(NODES),service_edges=len(ROUTES),shift=NRT9)))
if __name__=='__main__':main()
