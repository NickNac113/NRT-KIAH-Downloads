"""R24 approved canopy pull-through and campus refinements. File-based only."""
from pathlib import Path
import importlib.util,json,math,re,shutil,sys,hashlib,xml.etree.ElementTree as ET,ast
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R23_Jet_Center_Refinement_R19'
s=importlib.util.spec_from_file_location('r23',PREV/'source/build_r23.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;np=b.np;Image=b.Image;ImageDraw=b.ImageDraw;ImageFont=b.ImageFont
box=b.box;Point=b.Point;Polygon=b.Polygon;LineString=b.LineString;union=b.union
NAME='KIAH_NRT_R24_Pullthrough_Refinements_R21'
PACK=ROOT/'package'/NAME;OUT=ROOT/'output';QA=ROOT/'qa';OLD=PREV/'package/KIAH_NRT_R23_Jet_Center_Refinement_R19'
FOOT=b.FOOT;CANOPY=b.CANOPY;COLS=b.COLS;HELI=b.HELI
APPROVED=ROOT.parents[1]/'feasibility/KIAH_Canopy_Pullthrough_R24_Preview_R01/output/Measurements.json'
PROPOSAL=json.loads(APPROVED.read_text())['proposal']
NG=PROPOSAL['nosewheel'];DOOR=PROPOSAL['terminal_door'];HEAD=180
GA_NG=[2695.,431.];GA_HEAD=90.;GA_BOX=box(2674,418,2700,444)
GA_PLANNING=dict(length=22.,span=20.,nose_offset=3.,wheelbase=7.5)
# East-facing parking keeps the aircraft centered on the same GA location.
# A smooth main-gear lane change joins the shared tangent to the final east
# approach; derive nosewheel positions, including gear lead through the bend.
def ga_route():
    length=GA_PLANNING['wheelbase'];x0=g.SPINE+40.-length;x1=2667.5
    shift=GA_NG[1]-420.;points=[]
    for t in np.linspace(0,1,math.ceil((x1-x0)/.10)):
        y=420.+shift*(6*t**5-15*t**4+10*t**3)
        slope=shift*(30*t**4-60*t**3+30*t**2)/(x1-x0)
        forward=np.array([1.,slope]);forward/=np.linalg.norm(forward)
        points.append((np.array([x0+(x1-x0)*t,y])+length*forward).tolist())
    points.append(GA_NG)
    return points
GA_ROUTE=ga_route()
# Wrap the stepped building perimeter, then pass EAST of the GA stand.
# The existing west-facing pedestrian door is retained; no wall crossing.
WALK=[(2673.4,365),(2671,365),(2671,374.5),(2721,374.5),(2721,451),(2675,451),(2675,455)]
GA_WALK=[(2693,451),(2693,444)]
BLAST_PATHS=[[(3150.4,280),(2890.4,280)],[(3147.95,547),(3147.95,497),(3148.0,478),(3150.4,280)],[(2842.5,759.75),(3070,759.75)]]
REF_LEFT='nrt/kiah/r24/indoor_parking/left_open';REF_RIGHT='nrt/kiah/r24/indoor_parking/right_open'
g.PACK=PACK;g.OUT=OUT;g.QA=QA;g.placements=[];g.meshes=[];g.checks=[];g.changes=[]
BASE=json.loads((OLD/'Build_Evidence.json').read_text())
BASE_DSF=g.ag.parse_dsf(PREV/'qa/R23_Roundtrip.txt')
PLACEMENTS={q['resource']:dict(resource=q['resource'],origin=[q['geom'].x,q['geom'].y],heading=float(q['lines'][0].split()[-1])) for q in BASE_DSF['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
g.B={'placements':list(PLACEMENTS.values())}
retired=[];native=[];paint_cleanup=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    if (ROOT/'NRT_KIAH_R24_Test.zip').exists():raise RuntimeError('Sealed R24: create a successor')
    for p in [OUT,QA,ROOT/'reference',PACK]:p.mkdir(parents=True,exist_ok=True)
    hashes={p.relative_to(OLD).as_posix():sha(p) for p in OLD.rglob('*') if p.is_file()}
    snapshot=ROOT/'reference/R23_Hashes.json'
    if snapshot.exists():assert json.loads(snapshot.read_text())==hashes,'Baseline changed'
    else:snapshot.write_text(json.dumps(hashes,indent=2))
    shutil.copytree(OLD,PACK,dirs_exist_ok=True)
    shutil.copy2(APPROVED,ROOT/'reference/Approved_Pullthrough.json')

def materials():
    rng=np.random.default_rng(23019);yy,xx=np.mgrid[:512,:512]
    im=Image.new('RGB',(2048,1024));nm=Image.new('RGBA',im.size);lit=Image.new('RGB',im.size)
    colors=[[217,219,211],[25,51,57],[51,78,86],[167,160,142],[92,102,101],[128,107,76],[172,174,167],[67,73,72]]
    for i,color in enumerate(colors):
        noise=rng.normal(0,.65,(512,512));h=np.zeros_like(noise);gloss=np.full_like(noise,55)
        if i in [0,1]:
            seams=(xx%128<2)|(yy%256<2);noise-=seams*14;h-=seams*.25
        elif i==2:
            seams=(xx%128<3)|(yy%256<3);noise=noise*.12+9*np.cos(yy/650)-seams*22;h-=seams*.35;gloss[:]=168
        elif i==3:
            seams=(yy%128<2)|((xx+(yy//128%2)*128)%256<2);noise+=rng.normal(0,.8,noise.shape)-seams*14;gloss[:]=22;h=noise*.02
        elif i==4:
            seams=xx%64<3;noise-=seams*14;h+=seams*.45;gloss[:]=60
        elif i==5:
            seams=xx%24<2;noise-=seams*16;h+=seams*.35;gloss[:]=82
        elif i==6:
            seams=(xx%128<2)|(yy%128<2);noise-=seams*16;gloss[:]=18;h=noise*.02
        else:gloss[:]=36
        rgb=np.clip(np.array(color)[None,None,:]+noise[:,:,None],0,255).astype('uint8')
        dx=np.gradient(h,axis=1)*.25;dy=np.gradient(h,axis=0)*.25
        normal=np.stack([-dx,dy,np.ones_like(dx)],2);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
        n=np.dstack([(normal*.5+.5)*255,gloss]).clip(0,255).astype('uint8')
        loc=(i%4*512,i//4*512);im.paste(Image.fromarray(rgb),loc);nm.paste(Image.fromarray(n),loc)
        if i==2:
            light=np.full((512,512,3),[18,21,19],dtype='uint8');light[seams]=[1,2,2];lit.paste(Image.fromarray(light),loc)
    tex=PACK/'textures/nrt_test';im.save(tex/'r24_materials.png');nm.save(tex/'r24_materials_NML.png');lit.save(tex/'r24_materials_LIT.png')
    for name in ['r24_materials','r24_materials_LIT']:g.dds(tex/(name+'.png'))
    def uv(c,u,v):
        c={10:4,11:6}.get(c,c%8)
        return ((c%4*512+1+u*510)/2048,1-(c//4*512+1+(1-v)*510)/1024)
    g.material_uv=uv
    names=['INDOOR PARKING','NRT CANOPY','NRT10','NRT VIRTUAL HEADQUARTERS','ARRIVALS','PRIVATE AVIATION','NRT','NRT11','HELIPAD ACCESS','HOLD / ROTORS','MAX WINGSPAN 66 FT / 20 M']
    for ground in [False,True]:
        a=Image.new('RGBA',(2048,2048),(0,0,0,0));d=ImageDraw.Draw(a)
        for i,text in enumerate(names):
            y=i*144;d.rectangle((0,y,2047,y+143),fill=(220,172,36,255) if ground else (25,51,57,255))
            size=100
            while ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size).getlength(text)>1920:size-=1
            d.text((1024,y+72),text,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size),anchor='mm',fill=(25,30,27,255) if ground else (238,236,224,255))
            g.uvs[text]=(0,1-(y+144)/2048,1,1-y/2048)
        stem='r24_ground_ids' if ground else 'r24_identity';a.save(tex/(stem+'.png'));g.dds(tex/(stem+'.png'),True)
        if not ground:
            Image.fromarray((np.asarray(a)*np.array([.4,.4,.4,1])).astype('uint8')).save(tex/(stem+'_LIT.png'));g.dds(tex/(stem+'_LIT.png'),True)

def save(m):
    rel=g.save(m)
    if m.detailed:
        p=PACK/rel;p.write_text(p.read_text().replace('buildings.dds','r24_materials.dds').replace('buildings_NML.png','r24_materials_NML.png').replace('buildings_LIT.dds','r24_materials_LIT.dds'))
    return rel

def model():
    m=g.Mesh('r24_jet_center',[2674,330])
    # One exterior boundary eliminates the stacked walls at the R21/old FBO joint.
    for z0,z1,c in [(0,.8,3),(.8,7.4,2),(7.4,9.35,0),(9.35,10.1,1)]:m.extrude(FOOT,z0,z1,c)
    m.flat(FOOT.buffer(.65,join_style=2),10.1,4)
    for a,b in zip(list(FOOT.exterior.coords),list(FOOT.exterior.coords)[1:]):
        a=np.array(a);b=np.array(b);v=b-a;length=np.linalg.norm(v)
        # Raised mullions and a stone base at consistent 6 m bays.
        for t in np.arange(0,length,6):
            p=a+v*t/length;g.block(m,[p[0]-.07,p[1]-.07,p[0]+.07,p[1]+.07],.8,9.35,1)
        rail=LineString([a,b]).buffer(.055,cap_style=2);m.extrude(rail,4.35,4.5,1)
    # Repeated roof ribs, parapet, drainage and mechanical plant at human scale.
    m.extrude(FOOT.boundary.buffer(.13,join_style=2),10.1,10.45,0,0)
    for x in np.arange(2674,2882,4):
        roofline=LineString([(x,292),(x,420)]).intersection(FOOT)
        if not roofline.is_empty:m.extrude(roofline.buffer(.026,cap_style=2),10.11,10.16,4,4)
    for x,y in [(2680,367),(2745,385),(2770,385),(2848,383),(2868,383)]:
        g.block(m,[x-2,y-1.2,x+2,y+1.2],10.14,11.2,7,7)
        for z in np.arange(10.3,11.15,.17):g.rod(m,[x-2.02,y-1.22,z],[x+2.02,y-1.22,z],.045,1)
    for x,y in [(2673.8,331),(2673.8,370),(2725,333.8),(2822,419.5),(2882.1,336)]:g.rod(m,[x,y,.15],[x,y,9.8],.12,7)
    # Airside passenger entrance, port door side of a south-facing aircraft.
    g.block(m,[2673.60,312.7,2673.78,317.1],.16,3.65,1)
    for ya,yb in [(312.9,314.76),(314.96,316.9)]:
        g.block(m,[2673.54,ya,2673.60,yb],.26,3.45,2)
        g.rod(m,[2673.49,(ya+yb)/2,1.1],[2673.49,(ya+yb)/2,1.75],.045,5)
    # Paver threshold is outside the maximum wing envelope and has no raised kerb across the boarding path.
    m.extrude(box(2668.5,311.8,2674,318.2),.005,.035,6,6)
    g.block(m,[2670.2,311.7,2674,318.3],4.4,4.65,1,0)
    for y in [311.7,318.3]:g.block(m,[2673.5,y-.15,2674,y+.15],.1,7.5,5)
    # Existing 14 m minimum aircraft clearance remains, with a light soffit and a shared facade palette.
    for c in COLS:g.block(m,c.bounds,0,16.1,1,1)
    for b in [[2620,292,2674,294],[2620,346,2674,348],[2620,294,2621.2,346],[2672.8,294,2674,346]]:g.block(m,b,14,16.1,1,1)
    g.block(m,CANOPY.bounds,16.1,16.65,0,4)
    # Ceiling underside is a real face, visible when looking up from the aircraft.
    m.face([(2621,293,16.08),(2621,347,16.08),(2673,347,16.08),(2673,293,16.08)],0)
    for x in [2628,2641,2654,2667]:
        g.rod(m,[x,294,14.15],[x,346,14.15],.18,0)
        for y in range(294,344,4):g.rod(m,[x,y,14.15],[x,y+2,16],.09,0);g.rod(m,[x,y+2,16],[x,y+4,14.15],.09,0)
    for x in [2630,2648,2665]:
        for y in [301,320,339]:m.flood(x,y,15.7,0,0,2800)
    for y in [312.4,317.4]:m.flood(2673.2,y,4.1,-.1,0,400)
    # Landside entrance uses the same canopy edges, stone plinth and bronze soffit.
    g.block(m,[2696,324.2,2724,330.1],4.8,5.15,1,0)
    m.face([(2696,324.2,4.78),(2696,330.1,4.78),(2724,330.1,4.78),(2724,324.2,4.78)],5)
    for x in [2697,2723]:g.block(m,[x-.12,327.8,x+.12,328.05],.15,4.8,1)
    for x in [2706,2708,2710]:g.rod(m,[x,329.58,.15],[x,329.58,3.4],.09,5)
    for x in [2700,2710,2720]:m.flood(x,328,4.5,0,0,650)
    # Shallow repeated solar shades make the old terminal read as part of the new wing.
    for x in np.arange(2732,2880,12):g.block(m,[x,333.65,x+.18,333.93],.8,7.4,5)
    save(m)
    m=g.Mesh('r24_identity',[2674,330]);m.detailed=False;m.texture='r24_identity.png';m.normal=None;m.lit='r24_identity_LIT.dds';m.luminance=25
    g.sign(m,'NRT VIRTUAL HEADQUARTERS',2697,2723,329.78,7.7,1.2)
    g.sign(m,'ARRIVALS',2702,2718,324.15,4.86,.25)
    g.east_sign(m,'INDOOR PARKING',2512.08,359,17.1,28,1.9)
    # West-facing sign: reverse its horizontal physical axis to avoid mirrored lettering.
    u0,v0,u1,v1=g.uvs['PRIVATE AVIATION'];m.face([(2673.52,323,7.7),(2673.52,309,7.7),(2673.52,309,8.65),(2673.52,323,8.65)],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    g.sign(m,'NRT VIRTUAL HEADQUARTERS',2801,2824,333.78,7.8,1.2)
    fx,fy=g.D['landside']['flagpole'];u0,v0,u1,v1=g.uvs['NRT']
    m.face([(fx,fy,7.3),(fx+2.8,fy+.18,7.1),(fx+2.8,fy+.18,8.5),(fx,fy,8.8)],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    save(m)
    m=g.Mesh('r24_ground_ids',[2674,330],True);m.texture='r24_ground_ids.png';m.normal=None
    for text,c,w,h in [('INDOOR PARKING',[2542,359],16,270),('NRT CANOPY',[2648,377],12,180),('NRT10',[2675,457.5],9,0),('NRT11',[2671.5,431],9,90)]:m.label(text,c,w,2.0,heading=h)
    save(m)
    m=g.Mesh('r24_ramp_details',[2674,330],True)
    m.flat(box(2652,457,2698,503).boundary.buffer(.065,cap_style=2,join_style=2),0,5)
    # Stop bar, unobstructed pedestrian path and small passenger walk boundary, no aircraft-type labels.
    m.flat(LineString([(2646,314),(2650,314)]).buffer(.10,cap_style=2),0,4)
    for y in [312.5,317.2]:m.flat(LineString([(2653.8,y),(2668.5,y)]).buffer(.04,cap_style=2),0,5)
    save(m)

"""R24-specific build operations; seed_builder embeds these in build_r24.py."""
def parking_hangar():
    m=g.Mesh('r24_indoor_parking',[2473,359]);m.clockwise=True
    # Union each height band before extrusion: no intersecting wall solids or
    # coplanar end caps at the southwest/southeast corners.
    shell=union([box(2434,284,2435,433.3),box(2434,284,2512,285),box(2434,432.3,2512,433.3),box(2510,284,2512,290),box(2510,428,2512,433.3)])
    m.extrude(shell,0,16,0)
    m.extrude(shell.union(box(2510,290,2512,428)),16,20,0)
    g.block(m,[2434,284,2512,433.3],20,20.6,0,4)
    # A small construction gap to MH2 avoids the independently quantized
    # DSF placements creating another coplanar shared wall.
    for x in [2440,2462,2484,2507]:
        g.rod(m,[x,285,18.1],[x,432.3,18.1],.30,7)
        for y in np.arange(286,424,8):
            g.rod(m,[x,y,18.1],[x,y+4,19.85],.14,7);g.rod(m,[x,y+4,19.85],[x,y+8,18.1],.14,7)
    for x in [2447,2470,2493]:
        for y in [310,344,378,412]:g.block(m,[x-5,y-1.2,x+5,y+1.2],20.61,20.78,2,2)
    # Looking at the east facade, south is LEFT and north is RIGHT. Each half
    # has its own OpenSAM dataref and independent 12-leaf sliding pocket.
    for side,ref in [(-1,REF_LEFT),(1,REF_RIGHT)]:
        for j in range(12):
            ya,yb=sorted([359+side*j*5.75,359+side*(j+1)*5.75])
            target=284.05+j*.012 if side<0 else 427.4+j*.012
            delta=target-ya
            cmd=['ANIM_trans_begin '+ref,'ANIM_trans_key 0 0 0 0',f'ANIM_trans_key 1 {-j*.10:.6f} 0 {-delta:.6f}','ANIM_trans_end']
            def draw(ya=ya,yb=yb):
                g.block(m,[2510.8,ya,2511.05,yb],.05,15.95,1,1)
                g.block(m,[2511.065,ya+.10,2511.10,yb-.10],6,7.5,2,2)
            m.animated(cmd,draw)
    for y in [300,328,356,384,412]:m.flood(2508,y,18,0,0,9000)
    save(m)

def truck_doors_static():
    # Bake the existing authored open pose. No plugin refs remain on this OBJ.
    scope=dict(np=np,math=math,Image=Image)
    tr=ast.parse((g.LEGACY/'obj_reader.py').read_text())
    exec(compile(ast.Module(body=[n for n in tr.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'),scope)
    rel='objects/nrt_test/r22_nrt_truck_doors.obj';rows=(OLD/rel).read_text().splitlines()
    refs=set(re.findall(r'nrt/kiah/[^\s]+','\n'.join(rows)))
    # Local EN coordinates are converted back to the OBJ8 local axes below.
    tris,uv,_=scope['readobj'](OLD/rel,[0,0],vals={r:1 for r in refs},full=True)
    verts=[]
    for tri,tex in zip(tris,uv):
        p=np.column_stack([tri[:,0],tri[:,2],-tri[:,1]])
        normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=max(np.linalg.norm(normal),1e-12)
        for v,t in zip(p,tex):verts.append([*v,*normal,*t])
    out=[r for r in rows if r.startswith(('TEXTURE','GLOBAL_'))]
    out=['I','800','OBJ',*out,f'POINT_COUNTS {len(verts)} 0 0 {len(verts)}']
    out+=['VT '+' '.join(f'{v:.6f}' for v in p) for p in verts]
    for i in range(0,len(verts),10):
        ids=list(range(i,min(i+10,len(verts))));out+=['IDX10 '+' '.join(map(str,ids))] if len(ids)==10 else ['IDX '+str(x) for x in ids]
    out+=['ATTR_no_cull',f'TRIS 0 {len(verts)}']
    (PACK/rel).write_text('\n'.join(out)+'\n')

def cleanup():
    # Original open parking square extends behind the new building. Clear its
    # entire footprint rather than merely hiding the part inside the hangar.
    region=box(2410,276,2513,434.2).union(box(2646,395,2707,449))
    for name in ['paint','ramp_safety','ramp_wear','taxi_wear']:
        g.cut_obj('objects/nrt_test/'+name+'.obj',region)
    # R23 removed the fabric, but the fence's steel frame belongs to another
    # mesh. Remove BOTH pieces from the former west car-park boundary.
    g.cut_obj('objects/nrt_test/landside_fence.obj',box(2680,275,2742,343))
    # Clip just fence metal in the mixed security mesh; keep its guardhouse,
    # entry barrier, CCTV and original entrance canopy.
    for region in [box(2719.6,276.5,2720.4,333.5),box(2725.7,276.5,2733.3,277.5)]:
        g.cut_obj('objects/nrt_test/landside_security.obj',region)
    paint_cleanup.extend(g.changes)

def pedestrian_and_ga():
    # Low, flush paint only around the helicopter. No beacon or new mast.
    p=g.Mesh('r24_access_paint',[2674,430],True);p.layer=('markings',5)
    walk=LineString(WALK)
    corridor=walk.buffer(.8,cap_style=2,join_style=2).union(LineString(GA_WALK).buffer(.8,cap_style=2,join_style=2))
    # White edge outline, intentionally unpainted center for natural pavement.
    p.flat(corridor.boundary.buffer(.065,cap_style=2,join_style=2),0,5)
    for center,heading in [([2690,374.5],90),([2721,403],0),([2702,451],270),([2693,448],180)]:
        # Small pedestrian pictograms, rather than a vehicle taxi stripe.
        f=g.direction(heading);r=np.array([f[1],-f[0]])
        def xy(x,y):return np.array(center)+r*x+f*y
        p.flat(Point(xy(0,.60)).buffer(.14,quad_segs=8),0,5)
        for pts in [[(0,.40),(0,-.25)],[(-.37,.12),(.37,.12)],[(0,-.25),(-.35,-.75)],[(0,-.25),(.35,-.75)]]:
            p.flat(LineString([xy(*q) for q in pts]).buffer(.055,cap_style=2),0,5)
    p.flat(LineString([(2673.6,454.3),(2676.4,454.3)]).buffer(.13,cap_style=2),0,4)
    p.flat(LineString([(2691.6,444.5),(2694.4,444.5)]).buffer(.10,cap_style=2),0,4)
    # East-facing GA start, with pedestrian access at the north bay edge.
    p.flat(GA_BOX.boundary.buffer(.065,join_style=2),0,5)
    f=g.direction(GA_HEAD);right=np.array([f[1],-f[0]])
    p.flat(LineString([np.array(GA_NG)-right*2,np.array(GA_NG)+right*2]).buffer(.10,cap_style=2),0,4)
    save(p)
    p=g.Mesh('r24_access_ids',[2674,430],True);p.texture='r24_ground_ids.png';p.normal=None
    for text,c,w,h,head in [('HELIPAD ACCESS',[2721,429],9,1.1,90),('HOLD / ROTORS',[2675,453],6,1,0),('MAX WINGSPAN 66 FT / 20 M',[2687,415.5],14,1.2,0)]:p.label(text,c,w,h,heading=head)
    save(p)
    # A flush airside pedestrian door at the north side of the headquarters
    # wing provides an actual destination for the marked helipad walkway.
    m=g.Mesh('r24_heli_access_door',[2674,365]);m.clockwise=True
    g.block(m,[2673.60,363.9,2673.78,366.1],.12,3.1,1,1)
    g.block(m,[2673.53,364.05,2673.60,365.95],.22,2.95,2,2)
    g.rod(m,[2673.48,365.0,1.0],[2673.48,365.0,1.65],.045,5)
    save(m)

def apt():
    out=[]
    for q in g.ag.parse_apt(OLD/'Earth nav data/apt.dat'):
        if q['code']==1300 and q['name']=='NRT CANOPY':continue
        if q['code']==120 and 'canopy detached side-entry' in q['lines'][0]:continue
        for line in q['lines']:
            if line.strip()=='99':continue
            out.append(line.replace('NRT PRIVATE HANGAR','NRT INDOOR PARKING'))
    for name,ng,head,size,types in [('NRT CANOPY',NG,180,'C','jets'),('NRT11',GA_NG,GA_HEAD,'B','props|turboprops|jets')]:
        lo,la=g.ag.ll(*ng);out+=[f'1300 {la:.9f} {lo:.9f} {head} gate {types} {name}',f'1301 {size} none']
    # Native apt.dat painted-line records (WED type 51). These are guidance,
    # not autonomous ground movements or a promise of BBJ2 turning clearance.
    for label,points in [('Canopy pull-through entry',PROPOSAL['arrival']),('Canopy pull-through exit',PROPOSAL['departure']),('NRT11 connected east-facing parking',GA_ROUTE)]:
        points=list(LineString(points).simplify(.025,preserve_topology=True).coords)
        out+=['120 NRT R24 '+label]
        for i,(x,y) in enumerate(points):
            lo,la=g.ag.ll(x,y);last=i==len(points)-1
            out+=[f'{115 if last else 111} {la:.9f} {lo:.9f}'+('' if last else ' 51')]
    out.append('99');(PACK/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n')
    for name in ['sam.xml','opensam.xml']:
        tree=ET.parse(OLD/name);root=tree.getroot();root.set('name','NRT KIAH R24 Headquarters')
        refs=root.find('datarefs');gui=root.find('gui');instances=root.find('objects')
        for item in list(refs):
            if 'private_hangar' in item.get('name','') or 'truck_garage' in item.get('name',''):refs.remove(item)
        for item in list(gui):
            if item.get('instance') in ['private_hangar','truck_service']:gui.remove(item)
        for item in list(instances):
            if item.get('id')=='truck_service':instances.remove(item)
            elif item.get('id')=='private_hangar':item.set('id','indoor_parking')
        for side,ref in [('Left',REF_LEFT),('Right',REF_RIGHT)]:
            data=ET.SubElement(refs,'dataref',name=ref,autoplay='false',randomize_phase='false',augment_wind_speed='false')
            ET.SubElement(data,'animation',t='0',v='1');ET.SubElement(data,'animation',t='60',v='0')
            ET.SubElement(gui,'checkbox',label='Close Indoor Parking '+side,title=side+' sliding doors',instance='indoor_parking',dataref=ref)
        ET.indent(tree);tree.write(PACK/name,encoding='utf-8',xml_declaration=True)

def dsf():
    data=BASE_DSF;raw=(PREV/'qa/R23_Roundtrip.txt').read_text();objects=list(data['objects']);polygons=list(data['polygons']);defs=[];cmd=[]
    def idx(r,obj=False):
        ar=objects if obj else polygons
        if r not in ar:ar.append(r);defs.append(('OBJECT_DEF ' if obj else 'POLYGON_DEF ')+r)
        return ar.index(r)
    def line(r,pts,h=0,fac=False):
        a=[f'BEGIN_POLYGON {idx(r)} {h} {3 if fac else 2}','BEGIN_WINDING']
        for x,y in pts:
            lo,la=g.ag.ll(x,y);a.append(f'POLYGON_POINT {lo:.9f} {la:.9f}'+(' 0' if fac else ''))
        a+=['END_WINDING','END_POLYGON'];return a
    def obj(r,xy,h):
        lo,la=g.ag.ll(*xy);cmd.append(f'OBJECT {idx(r,True)} {lo:.9f} {la:.9f} {h}')
    replaced={'r21_private_hangar','r23_jet_center','r23_identity','r23_ground_ids','r23_ramp_details'}
    for q in data['entities']:
        r=q['resource'];erase=q['kind']=='object' and Path(r).stem in replaced
        if q['kind']=='polygon' and 'jet_blast_deflectors' in r and box(2800,270,3160,770).intersects(q['geom']):erase=True
        # Any still-native old parking guidance in the removed pad/hangar is
        # retired along with its custom painted meshes.
        if q['kind']=='polygon' and '/lines/' in r and box(2646,395,2707,449).covers(q['geom']):erase=True
        if erase:raw=raw.replace('\n'.join(q['lines']),'');retired.append(dict(resource=r,bounds=list(q['geom'].bounds)))
    for path in BLAST_PATHS:cmd+=line('lib/airport/Ramp_Equipment/jet_blast_deflectors/angled_mesh_1.fac',path,5,True)
    for p in g.placements:obj(p['resource'],p['origin'],p['heading'])
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(cmd)+'\n'
    src=QA/'R24_South.txt';src.write_text(raw)
    dst=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile.txt').write_text(g.run([g.TOOL,'--text2dsf',src,dst]));(QA/'Decompile.txt').write_text(g.run([g.TOOL,'--dsf2text',dst,QA/'R24_Roundtrip.txt']))

def main():
    prepare();materials();model();parking_hangar();truck_doors_static();cleanup();pedestrian_and_ga();apt();dsf()
    evidence=dict(BASE)
    evidence.update(name=NAME,layout='R24',revision='R21',placements=list(PLACEMENTS.values()),new_placements=g.placements,retired_dsf_entities=retired,clipped_objects=paint_cleanup,runtime_tested=False,
        r24=dict(canopy_nosewheel=NG,passenger_door=DOOR,marshaller=[2648,286],approved_proposal_sha256=sha(APPROVED),arrival=PROPOSAL['arrival'],departure=PROPOSAL['departure'],ga_nosewheel=GA_NG,ga_heading=GA_HEAD,ga_route=GA_ROUTE,ga_planning_vehicle=GA_PLANNING,ga_envelope=GA_BOX.bounds,ga_wingspan_m=20,ga_length_m=22,ga_departure='Pushback or tow out',walk=WALK,ga_walk=GA_WALK,ga_walk_approach='North',blast_paths=BLAST_PATHS,hangar_roof_m=20.6,hangar_clear_opening_m=16,hangar_control_refs=[REF_LEFT,REF_RIGHT],controls=6,truck_doors='Fixed open',beacon=False,headquarters_name='NRT VIRTUAL HEADQUARTERS'))
    (PACK/'Build_Evidence.json').write_text(json.dumps(evidence,indent=2))
    (OUT/'Build_Checks.json').write_text(json.dumps(g.checks,indent=2))
    print(json.dumps(dict(package=str(PACK),new_objects=len(g.placements),retired=len(retired),built=True)))

if __name__=='__main__':main()
