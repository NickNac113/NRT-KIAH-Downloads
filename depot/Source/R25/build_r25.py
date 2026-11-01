"""R25 stock-X-Plane finish pass. Isolated authoring; never installs or publishes."""
from pathlib import Path
import importlib.util, sys, math, json, hashlib, shutil, ast, inspect
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]; PREV=ROOT.parent/'KIAH_R24_Pullthrough_Refinements_R21'
s=importlib.util.spec_from_file_location('r24',PREV/'source/build_r24.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g; np=b.np; Image=b.Image;ImageDraw=b.ImageDraw;ImageFont=b.ImageFont
box=b.box;Point=b.Point;Line=b.LineString;Polygon=b.Polygon;union=b.union
OLD=PREV/'package/KIAH_NRT_R24_Pullthrough_Refinements_R21'
NAME='KIAH_NRT_R25_Realism_R22';PACK=ROOT/'package'/NAME;OUT=ROOT/'output';QA=ROOT/'qa'
SOURCE=PREV/'qa/R24_Roundtrip.txt';BASE=g.ag.parse_dsf(SOURCE)
EVIDENCE=json.loads((OLD/'Build_Evidence.json').read_text())
g.PACK=PACK;g.OUT=OUT;g.QA=QA;g.placements=[];g.meshes=[];g.changes=[];g.checks=[]
g.B={'placements':[dict(resource=q['resource'],origin=[q['geom'].x,q['geom'].y]) for q in BASE['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')]}
b.PACK=PACK;b.OUT=OUT;b.QA=QA
FOOT=b.FOOT;CANOPY=b.CANOPY;COLS=b.COLS;HELI=b.HELI;PROPOSAL=b.PROPOSAL
GA_NG=[2713.,412.5];GA_HEAD=90.;GA_BOX=box(2665,377.5,2719,448.5)
GA_PLANNING=dict(length=50.,span=66.,nose_offset=4.,wheelbase=18.)
WALK=b.WALK;GA_WALK=[(2693,451),(2693,448.5)]
HELI_RESERVE=box(2652,457,2698,503)
LABEL_CENTER=[2663.,412.5]
native=[];retired=[];surfaces=[];props=[];portal_info=[]
IDENTITY_UVS={};GROUND_UVS={}
LIB=json.loads((ROOT.parents[1]/'feasibility/KIAH_R25_Realism_Proposal_R01/Audit.json').read_text())
LIBMAP={a['resource']:a['exports'][0]['file'] for a in LIB['assets']}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(folder):return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
def prepare():
    if (ROOT/'NRT_KIAH_R25_Test.zip').exists():raise RuntimeError('R25 sealed; create a successor')
    for p in [PACK,OUT,QA,ROOT/'reference']:p.mkdir(parents=True,exist_ok=True)
    hashes=snapshot(OLD);dest=ROOT/'reference/R24_Hashes.json'
    if dest.exists():assert json.loads(dest.read_text())==hashes,'R24 baseline changed'
    else:dest.write_text(json.dumps(hashes,indent=2))
    published=ROOT.parents[1]/'distribution/NRT_KIAH_Updater_R01/scenery'
    pub=ROOT/'reference/Published_Hashes.json'
    if not pub.exists():pub.write_text(json.dumps(snapshot(published),indent=2))
    shutil.copytree(OLD,PACK,dirs_exist_ok=True)

def ga_route():
    length=GA_PLANNING['wheelbase'];x0=g.SPINE+40-length;x1=GA_NG[0]-length-8
    shift=GA_NG[1]-420;points=[]
    for t in np.linspace(0,1,math.ceil((x1-x0)/.10)):
        y=420+shift*(6*t**5-15*t**4+10*t**3)
        slope=shift*(30*t**4-60*t**3+30*t**2)/(x1-x0)
        forward=np.array([1.,slope]);forward/=np.linalg.norm(forward)
        points.append((np.array([x0+(x1-x0)*t,y])+length*forward).tolist())
    points.append(GA_NG);return points
GA_ROUTE=ga_route()

# Use original, physically scaled material tiles. Native pavement itself stays
# a public Laminar resource, with its normal/decal/weather maps provided by XP.
def materials():
    b.materials() # retains existing identity artwork, authored in this workspace
    IDENTITY_UVS.update(g.uvs)
    N=1024; yy,xx=np.mgrid[:N,:N];rng=np.random.default_rng(2501)
    color=Image.new('RGB',(4*N,2*N));normal=Image.new('RGBA',color.size);lit=Image.new('RGB',color.size)
    palette=[[211,214,207],[28,43,47],[62,87,92],[177,173,159],[124,134,133],[135,111,78],[188,186,174],[67,72,70]]
    for i,c in enumerate(palette):
        grain=rng.normal(0,.45,(N,N));height=np.zeros((N,N));gloss=np.full((N,N),50.);metal=np.zeros((N,N));em=np.zeros((N,N,3))
        if i==0:
            seam=(xx%512<3)|(yy%512<3);grain-=seam*19;height-=seam*.16;gloss[:]=76
        elif i==1:
            seam=(xx%512<3);grain-=seam*9;height-=seam*.10;gloss[:]=100
        elif i==2:
            # Deep blue-grey glazing; subtle tonal variation, no painted glare.
            seam=(xx%256<7)|(yy%512<5);grain=grain*.1+2*np.cos(xx/300)-seam*22
            height-=seam*.10;gloss[:]=195;gloss[seam]=85
            for row in range(2):
                for col in range(4):
                    if (row*4+col) in [1,4,6]:em[row*512+6:(row+1)*512-5,col*256+8:(col+1)*256-6]=[23,20,15]
        elif i==3:
            seam=(yy%256<3)|((xx+(yy//256%2)*256)%512<3);grain+=rng.normal(0,.65,grain.shape)-seam*13;height=grain*.012;gloss[:]=27
        elif i==4:
            seam=xx%128<5;grain-=seam*16;height+=seam*.20;gloss[:]=72
        elif i==5:
            seam=xx%64<3;grain-=seam*19;height+=seam*.16;gloss[:]=108;metal[:]=.72
        elif i==6:
            seam=(xx%256<3)|(yy%256<3);grain-=seam*14;height=grain*.012;gloss[:]=28
        else:gloss[:]=55
        rgb=np.clip(np.array(c)[None,None,:]+grain[:,:,None],0,255).astype('uint8')
        dx=np.gradient(height,axis=1)*.3;dy=np.gradient(height,axis=0)*.3
        # XP12 NORMAL_METALNESS: RG normal XY, B metalness, A gloss.
        nm=np.dstack([128-dx*127,128+dy*127,metal*255,gloss]).clip(0,255).astype('uint8')
        pos=(i%4*N,i//4*N);color.paste(Image.fromarray(rgb),pos);normal.paste(Image.fromarray(nm),pos);lit.paste(Image.fromarray(em.astype('uint8')),pos)
    tex=PACK/'textures/nrt_test'
    for suffix in ['.png','.dds','_LIT.png','_LIT.dds']:
        shutil.copy2(tex/('r24_identity'+suffix),tex/('r25_identity'+suffix))
    for suffix,im in [('',color),('_NML',normal),('_LIT',lit)]:im.save(tex/('r25_materials'+suffix+'.png'))
    g.dds(tex/'r25_materials.png');g.dds(tex/'r25_materials_LIT.png')
    def uv(c,u,v):
        c={10:4,11:6}.get(c,c%8)
        return ((c%4*N+2+u*(N-4))/(4*N),1-(c//4*N+2+(1-v)*(N-4))/(2*N))
    g.material_uv=uv
    words=['INDOOR PARKING','NRT CANOPY','NRT10','NRT11','HELIPAD ACCESS','HOLD / ROTORS','MAX WINGSPAN','216.5 FT / 66 M','MAX LENGTH 164 FT / 50 M']
    im=Image.new('RGBA',(2048,2048));d=ImageDraw.Draw(im)
    for i,word in enumerate(words):
        y=i*192;board=i<4
        if board:d.rectangle((0,y,2047,y+191),fill=(221,177,44,255))
        fs=125
        while ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs).getlength(word)>1960:fs-=1
        d.text((1024,y+96),word,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs),anchor='mm',fill=(28,32,28,255) if board else (221,177,44,255))
        g.uvs[word]=(0,1-(y+192)/2048,1,1-y/2048)
    im.save(tex/'r25_ground_ids.png');g.dds(tex/'r25_ground_ids.png',True)
    GROUND_UVS.update(g.uvs)

OriginalMesh=g.Mesh
class FinishMesh(OriginalMesh):
    def face(self,pts,color=0,uv=None,mapped=False):
        if self.detailed and uv is None and len(pts)==4:
            a,c,d,e=map(lambda x:np.array(x,float),pts)
            # 4m x 4m modules: sub-metre seams retain real scale at close range.
            du=np.linalg.norm(c-a);dv=np.linalg.norm(e-a);nu=max(1,math.ceil(du/4));nv=max(1,math.ceil(dv/4))
            for j in range(nv):
                for i in range(nu):
                    u0=i*4/du if du else 0;u1=min(1,(i+1)*4/du) if du else 1
                    v0=j*4/dv if dv else 0;v1=min(1,(j+1)*4/dv) if dv else 1
                    q=[a+(c-a)*u+(e-a)*v for u,v in [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]]
                    uvq=[g.material_uv(color,u,v) for u,v in [(0,0),((u1-u0)*du/4,0),((u1-u0)*du/4,(v1-v0)*dv/4),(0,(v1-v0)*dv/4)]]
                    OriginalMesh.face(self,q,color,uvq,True)
            return
        OriginalMesh.face(self,pts,color,uv,mapped)
    def extrude(self,geom,z0,z1,c,roof=None):
        if self.name=='r25_jet_center' and geom.equals(FOOT):
            # A real reveal around each fixed jetway link, no glazing plane
            # crossing the tunnel and no overlapping facade at its root.
            from shapely.geometry.polygon import orient
            for poly in g.parts(geom):
                for ring in [orient(poly,1).exterior,*poly.interiors]:
                    for aa,bb in zip(ring.coords,list(ring.coords)[1:]):
                        if abs(aa[1]-419.39)<1e-5 and abs(bb[1]-419.39)<1e-5:
                            xlo,xhi=sorted([aa[0],bb[0]])
                            cuts=union([box(j['root'][0]-1.75,3.70,j['root'][0]+1.75,7.02) for j in EVIDENCE['jetways']])
                            for x in np.arange(xlo,xhi,4):
                                for z in np.arange(z0,z1,4):
                                    wall=box(x,z,min(x+4,xhi),min(z+4,z1)).difference(cuts)
                                    for piece in g.parts(wall):
                                        for tri in g.constrained_delaunay_triangles(piece).geoms:
                                            v=list(tri.exterior.coords)[:-1]
                                            # Mapping is local to each real 4m module, without modulo seams.
                                            self.face([(xx,419.39,zz) for xx,zz in v],c,[g.material_uv(c,(xx-x)/4,(zz-z)/4) for xx,zz in v],True)
                        else:self.face([(*aa,z0),(*bb,z0),(*bb,z1),(*aa,z1)],c)
            if roof is not None:self.flat(geom,z1,roof)
        else:OriginalMesh.extrude(self,geom,z0,z1,c,roof)
    def save(self):
        rel=OriginalMesh.save(self);p=PACK/rel;txt=p.read_text()
        if self.detailed:
            txt=txt.replace('buildings.dds','r25_materials.dds').replace('buildings_NML.png','r25_materials_NML.png').replace('buildings_LIT.dds','r25_materials_LIT.dds')
            txt=txt.replace('GLOBAL_specular 1.0','GLOBAL_specular 1.0\nNORMAL_METALNESS\nGLOBAL_luminance 12')
        if not self.draped:txt=txt.replace('ATTR_no_cull','ATTR_LOD 0 '+('500' if self.name=='r25_human_details' else '5000')+'\nATTR_no_cull',1)
        p.write_text(txt);return rel
g.Mesh=FinishMesh
def save(m):return g.save(m)

def headquarters():
    # Reuse the accepted geometry, changing finish and the three tunnel roots.
    src=inspect.getsource(b.model).replace('r24_','r25_')
    src=src.replace("('NRT11',[2671.5,431],9,90)","('NRT11',LABEL_CENTER,13,90)")
    src=src.replace("m=g.Mesh('r25_identity'","g.uvs.update(IDENTITY_UVS)\n    m=g.Mesh('r25_identity'")
    src=src.replace("m=g.Mesh('r25_ground_ids'","g.uvs.update(GROUND_UVS)\n    m=g.Mesh('r25_ground_ids'")
    # Facade rails and mullions also stop at the openings, not just glazing.
    src=src.replace("p=a+v*t/length;g.block", "p=a+v*t/length\n            if any(abs(p[1]-419.39)<.2 and abs(p[0]-j['root'][0])<2.05 for j in EVIDENCE['jetways']):continue\n            g.block")
    src=src.replace("m.extrude(rail,4.35,4.5,1)", "m.extrude(rail.difference(union([box(j['root'][0]-1.75,418.8,j['root'][0]+1.75,419.95) for j in EVIDENCE['jetways']])),4.35,4.5,1)")
    scope=dict(vars(b));scope.update(g=g,save=save,LABEL_CENTER=LABEL_CENTER,IDENTITY_UVS=IDENTITY_UVS,GROUND_UVS=GROUND_UVS,EVIDENCE=EVIDENCE)
    exec(src,scope);scope['model']()
    # Portal frames are part of the building, not a replacement animated jetway.
    m=g.Mesh('r25_jetway_portals',[2800,419.39])
    for j in EVIDENCE['jetways']:
        x=j['root'][0];a=[x,419.39];c=j['base']
        left=box(x-2.05,419.40,x-1.70,419.90);right=box(x+1.70,419.40,x+2.05,419.90)
        for q in [left,right]:m.extrude(q,3.5,7.05,0)
        g.block(m,[x-2.05,419.40,x+2.05,419.90],7.05,7.30,1,0)
        g.block(m,[x-1.70,418.90,x+1.70,420.10],3.65,3.72,7,7)
        g.block(m,[x-1.70,418.90,x+1.70,420.10],6.98,7.05,7,7)
        for xx in [x-1.76,x+1.76]:g.block(m,[xx-.04,418.90,xx+.04,420.10],3.72,7.05,7,7)
        # Flush sill, gasket, drip edge; no raised obstruction on the apron.
        portal_info.append(dict(id=j['id'],root=a,opening=[3.5,3.32],floor_m=4))
    save(m)
    for j in EVIDENCE['jetways']:
        m=g.Mesh('r25_fixed_'+j['id'],j['base']);x,y=j['base'];a=[x,419.30];c=[x,y]
        q=Line([a,c]).buffer(1.6,cap_style=2)
        m.extrude(q,3.72,4.,0,0);m.extrude(q,4.,6.6,2);m.extrude(q,6.6,6.85,0,4)
        m.extrude(Point(c).buffer(1.70,quad_segs=16),3.65,4.3,0,0)
        m.extrude(Point(c).buffer(1.70,quad_segs=16),4.3,6.95,2)
        m.extrude(Point(c).buffer(1.70,quad_segs=16),6.95,7.2,0,4)
        m.extrude(Point(c).buffer(.6,quad_segs=12),0,3.72,7,7)
        for yy in np.arange(419.9,y-1.7,1.8):
            for xx in [x-1.63,x+1.63]:g.block(m,[xx-.035,yy-.04,xx+.035,yy+.04],4,6.6,1,1)
        save(m)
    # Tangible entrance detail at human scale, all on the landside footway.
    m=g.Mesh('r25_human_details',[2710,329])
    for x in [2706.4,2708.1,2709.8]:
        g.block(m,[x,329.48,x+1.55,329.59],.18,3.20,1,1)
        g.block(m,[x+.08,329.44,x+1.47,329.48],.28,3.10,2,2)
        g.rod(m,[x+1.30,329.40,1.02],[x+1.30,329.40,1.75],.05,5)
    g.block(m,[2705.9,328.65,2711.65,329.9],.15,.165,7,7)
    for x in [2700,2717.5]:
        g.block(m,[x,328.4,x+2.2,328.95],.52,.65,5,5)
        for xx in [x+.15,x+2.05]:g.block(m,[xx,328.52,xx+.08,328.83],.15,.53,1,1)
    for x in [2695.3,2721.5]:
        m.extrude(box(x-.42,328.8,x+.42,329.55),.15,.95,1,3)
    save(m)

def stand_and_walk():
    p=g.Mesh('r25_access_paint',[2674,430],True);p.layer=('markings',5)
    corridor=Line(WALK).buffer(.8,cap_style=2,join_style=2).union(Line(GA_WALK).buffer(.8,cap_style=2))
    p.flat(corridor.boundary.buffer(.065,cap_style=2,join_style=2),0,5)
    p.flat(GA_BOX.boundary.buffer(.065,join_style=2),0,5)
    p.flat(Line([(2713,409),(2713,416)]).buffer(.12,cap_style=2),0,4)
    p.flat(Line([(2673.6,454.3),(2676.4,454.3)]).buffer(.13,cap_style=2),0,4)
    p.flat(Line([(2691.6,449.2),(2694.4,449.2)]).buffer(.10,cap_style=2),0,4)
    for center,heading in [([2690,374.5],90),([2721,403],0),([2702,451],270)]:
        f=g.direction(heading);r=np.array([f[1],-f[0]])
        def xy(x,y):return np.array(center)+r*x+f*y
        p.flat(Point(xy(0,.6)).buffer(.14,quad_segs=8),0,5)
        for pts in [[(0,.40),(0,-.25)],[(-.37,.12),(.37,.12)],[(0,-.25),(-.35,-.75)],[(0,-.25),(.35,-.75)]]:p.flat(Line([xy(*q) for q in pts]).buffer(.055,cap_style=2),0,5)
    save(p)
    p=g.Mesh('r25_access_ids',[2674,430],True);p.texture='r25_ground_ids.png';p.normal=None
    for txt,xy,w,h,head in [('HELIPAD ACCESS',[2721,429],9,1.1,90),('HOLD / ROTORS',[2675,453],6,1,0),
       ('MAX WINGSPAN',[2660,412.5],18,1.8,90),('216.5 FT / 66 M',[2658,412.5],22,1.8,90),('MAX LENGTH 164 FT / 50 M',[2655.8,412.5],22,1.3,90)]:p.label(txt,xy,w,h,heading=head)
    save(p)

def native_details():
    # Sparse crew and correctly stowed equipment, not random clutter.
    for resource,xy,heading,role in [
      ('MisterX_Library/People/Pilot_1.obj',[2714,328.4],180,'Arrival waiting area'),
      ('MisterX_Library/People/Worker_1.obj',[2734,287],90,'Security gate staff'),
      ('MisterX_Library/Airport/Vehicles/GPUs/Medium/Generic_Stowed.obj',[2732,423.5],180,'NRT9 stowed service nook'),
      ('lib/airport/Ramp_Equipment/traffic_cone_stack_1.obj',[2730,422.4],0,'Stored cones'),
      ('lib/airport/Common_Elements/Miscellaneous/fire_extinguisher_1.obj',[2730.2,420.2],0,'Wall-side fire point'),
    ]:
        assert resource in LIBMAP and Path(LIBMAP[resource]).is_file()
        props.append(dict(resource=resource,origin=xy,heading=heading,role=role))

def apt():
    out=[]
    for q in g.ag.parse_apt(OLD/'Earth nav data/apt.dat'):
        if q['code']==1300 and q['name']=='NRT11':continue
        if q['code']==120 and 'NRT11 connected' in q['lines'][0]:continue
        out += [s for s in q['lines'] if s.strip()!='99']
    lo,la=g.ag.ll(*GA_NG);out += [f'1300 {la:.9f} {lo:.9f} 90 gate props|turboprops|jets NRT11','1301 F none']
    out += ['120 NRT R25 NRT11 east-facing enlarged stand']
    pts=list(Line(GA_ROUTE).simplify(.02).coords)
    for i,(x,y) in enumerate(pts):
        lo,la=g.ag.ll(x,y);last=i==len(pts)-1
        out += [f'{115 if last else 111} {la:.9f} {lo:.9f}'+('' if last else ' 51')]
    out += ['99'];(PACK/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n')

def dsf():
    data=BASE;raw=SOURCE.read_text();objects=list(data['objects']);polygons=list(data['polygons']);defs=[];commands=[]
    def idx(r,obj=False):
        ar=objects if obj else polygons
        if r not in ar:ar.append(r);defs.append(('OBJECT_DEF ' if obj else 'POLYGON_DEF ')+r)
        return ar.index(r)
    def poly(r,geom,param=0):
        from shapely.geometry.polygon import orient
        ans=[]
        for p in g.parts(geom):
            if p.area<.005:continue
            p=orient(p,1);ans += [f'BEGIN_POLYGON {idx(r)} {param} 2']
            for ring in [p.exterior,*p.interiors]:
                ans+=['BEGIN_WINDING']
                for x,y in list(ring.coords)[:-1]:
                    lo,la=g.ag.ll(x,y);ans += [f'POLYGON_POINT {lo:.9f} {la:.9f}']
                ans+=['END_WINDING']
            ans+=['END_POLYGON']
        return ans
    def line(r,points):
        ans=[f'BEGIN_POLYGON {idx(r)} 0 2','BEGIN_WINDING']
        for x,y in points:
            lo,la=g.ag.ll(x,y);ans += [f'POLYGON_POINT {lo:.9f} {la:.9f}']
        ans += ['END_WINDING','END_POLYGON'];return ans
    def obj(r,xy,h=0):
        lo,la=g.ag.ll(*xy);commands.append(f'OBJECT {idx(r,True)} {lo:.9f} {la:.9f} {h}')
    campus=box(2409,274,3157,765)
    replaced={'r24_jet_center','r24_identity','r24_ground_ids','r24_ramp_details','r24_access_paint','r24_access_ids','fixed_8','fixed_9A','fixed_9B'}
    retired_wear={'ramp_wear','taxi_wear'}
    for q in data['entities']:
        r=q['resource'];stem=Path(r).stem;erase=q['kind']=='object' and (stem in replaced or stem in retired_wear)
        if q['geom'].intersects(campus):
            if q['kind']=='polygon' and '/pavement/' in r and campus.covers(q['geom'].representative_point()):
                if q['geom'].area<5000 and '/concrete' in r and (q['geom'].intersection(box(2664,398,2706,440)).area>1200 or q['geom'].intersection(CANOPY).area>1500):
                    raw=raw.replace('\n'.join(q['lines']),'');retired.append(dict(resource=r,bounds=list(q['geom'].bounds),reason='Duplicate small slab overlay removed'))
                    continue
                # Replace the physical base, not an opaque overlay on top.
                new=r.rsplit('/',1)[0]+('/plain.pol' if '/asphalt' in r else '/new.pol')
                if any(s in r for s in ['/worn.pol','/dirty.pol','/patched.pol']):
                    raw=raw.replace('\n'.join(q['lines']),'\n'.join(poly(new,q['geom'],q.get('param',0))))
                    surfaces.append(dict(before=r,after=new,bounds=list(q['geom'].bounds),area=q['geom'].area))
                continue
            if q['kind']=='object' and ('grunge_size_' in r or stem.startswith('floor_wear')):erase=True
            if q['kind']=='polygon' and any(s in r for s in ['taxiway_dirt/center','Ground_Textures/Skid_Marks','Ground_Textures/Dirt']):erase=True
            # The old small GA square's different base is redundant; restore
            # the one coherent apron instead of a second offset slab grid.
            if q['kind']=='polygon' and '/pavement_FX/seams/concrete.lin' in r and CANOPY.buffer(2).intersects(q['geom']):erase=True
        if erase:
            raw=raw.replace('\n'.join(q['lines']),'');retired.append(dict(resource=r,bounds=list(q['geom'].bounds)))
    # Long, light rubber tracks where wheels travel. No oil wash over the apron.
    track='lib/airport/ground/pavement_FX/taxiway_dirt/tracks/2m.lin'
    for pts in [[(g.SPINE-4,300),(g.SPINE-4,450)],[(g.SPINE+4,300),(g.SPINE+4,450)],[(2671,408.7),(2709,408.7)],[(2671,416.3),(2709,416.3)],[(2644.2,355),(2644.2,384)],[(2651.8,355),(2651.8,384)]]:
        commands+=line(track,pts);native.append(dict(resource=track,points=pts))
    # Neat apron drainage at the fixed jetway roots, wall-side and flush.
    drain='lib/airport/ground/pavement_FX/drains/drain_1.lin'
    for pts in [[(2778,420.3),(2798,420.3)],[(2855,420.3),(2866,420.3)]]:
        commands+=line(drain,pts);native.append(dict(resource=drain,points=pts))
    for p in g.placements+props:obj(p['resource'],p['origin'],p['heading'])
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(commands)+'\n'
    src=QA/'R25_South.txt';src.write_text(raw);dst=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile.txt').write_text(g.run([g.TOOL,'--text2dsf',src,dst]))
    (QA/'Decompile.txt').write_text(g.run([g.TOOL,'--dsf2text',dst,QA/'R25_Roundtrip.txt']))

def main():
    prepare();materials();headquarters();stand_and_walk();native_details();apt();dsf()
    evidence=dict(EVIDENCE)
    evidence.update(name=NAME,layout='R25',revision='R22',runtime_tested=False,new_placements=g.placements,
        r25=dict(stock_xplane_target=True,aep_required=False,style='New, maintained, lightly used',ga_nosewheel=GA_NG,ga_heading=GA_HEAD,ga_route=GA_ROUTE,ga_envelope=list(GA_BOX.bounds),ga_planning=GA_PLANNING,walk=WALK,ga_walk=GA_WALK,ga_departure='Pushback or tow out',ga_label_center=LABEL_CENTER,ga_limit_position='Three and five metres behind ID, same heading as NRT8/9 convention',portals=portal_info,surfaces=surfaces,retired=retired,native_details=native,props=props,controls=6,beacon=False,review_pending=True))
    (PACK/'Build_Evidence.json').write_text(json.dumps(evidence,indent=2))
    (OUT/'Change_List.json').write_text(json.dumps(evidence['r25'],indent=2))
    print(json.dumps(dict(package=str(PACK),objects=len(g.placements),native_props=len(props),surface_changes=len(surfaces),retired=len(retired))))
if __name__=='__main__':main()
