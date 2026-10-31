"""Legacy core retained for AST mesh-helper extraction. R17 uses refine_native.py."""
if __name__=='__main__':
    raise SystemExit('Use refine_native.py for R17; this file supplies legacy mesh helpers only.')
from probe import *
import airport_geometry as ag
from repair_support import styled_segments
import shutil, subprocess, hashlib, re
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from PIL import Image, ImageDraw, ImageFont
from materials import build_textures,material_uv
from finish_details import architectural,ramp_details

XP=Path('X:/X-Plane 12'); CS=XP/'Custom Scenery'
BASE=CS/'KIAH_2026-10-24_Review_R03'; PRIVATE=CS/'KIAH_NRT_Private'
NAME='KIAH_NRT_R17_Native_Surface_R13'; PACK=ROOT/'package'/NAME
TOOL=Path('C:/Users/Nick/Documents/Codex/2026-10-24/cou/work/xptools-24-5/tools/DSFTool.exe')
for p in [ROOT/'qa',ROOT/'output',ROOT/'reference',PACK]:p.mkdir(parents=True,exist_ok=True)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(p):return {f.relative_to(p).as_posix():sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
snap=ROOT/'reference/Before.json'
if not snap.exists():
    snap.write_text(json.dumps({'public':snapshot(BASE),'private':snapshot(PRIVATE),'previous_test':snapshot(CS/'KIAH_NRT_R05_Taxi_Test_R01'),'ini':sha(CS/'scenery_packs.ini')},indent=2))
    shutil.copy2(CS/'scenery_packs.ini',ROOT/'reference/scenery_packs.ini.before')
if not (PACK/'TEST_PACKAGE.txt').exists():
    assert not any(PACK.iterdir()),'Refusing to overwrite a non-test folder'
    for d in ['Earth nav data','objects','textures']:shutil.copytree(BASE/d,PACK/d,dirs_exist_ok=True)
    for name in ['COPYING','Gateway-original-README.txt']:
        if (BASE/name).exists():shutil.copy2(BASE/name,PACK/name)
    (PACK/'TEST_PACKAGE.txt').write_text('NRT R10 isolated visual finish R06. Not a released scenery.\n')
for d in ['objects/nrt_test','textures/nrt_test','Test modes','Source']: (PACK/d).mkdir(parents=True,exist_ok=True)

# One atlas for new test buildings, reference aircraft, and native draped labels.
COLORS=['#e5e9eb','#203947','#75b1bd','#66737a','#e3b52a','#f7f4e8','#df513d','#242a30','#a7b7bb','#35647d']
atlas=Image.new('RGBA',(1024,2048),(255,255,255,255));draw=ImageDraw.Draw(atlas)
for i,c in enumerate(COLORS):draw.rectangle((i*64,0,i*64+63,63),fill=c)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',42)
labels=[m.DISPLAY.get(n,n) for n in m.S]+['NRT10A','NRT10B','MAX 75F','MAX A300','A300','737','A380','747-8I','NOSE LOAD','KEEP CLEAR','NRT TAXI TEST','CARGO','NRT FBO','MH1 EAST DOOR','747-8I PROXY','GSE A','GSE B','NRT MAINTENANCE','OUTER','MIDDLE','TAIL','PRIVATE AVIATION','CHINOOK','NRT CARGO','NORTHERN RELIABLE TRANSPORT']+['D%02d'%i for i in range(1,15)]
uvs={}
for i,s in enumerate(labels):
    x=(i%2)*512;y=80+(i//2)*64
    ramp=s in [m.DISPLAY.get(n,n) for n in m.S] or s in ['MAX 75F','MAX A300','NRT10A','NRT10B']
    stencil=s in ['NOSE LOAD','KEEP CLEAR','CHINOOK','GSE A','GSE B','A300','737','A380','747-8I']
    draw.rectangle((x,y,x+511,y+63),fill=(0,0,0,0) if stencil else COLORS[4] if ramp else COLORS[1])
    fs=42
    while ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs).getlength(s)>490:fs-=1
    draw.text((x+256,y+31),s,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs),anchor='mm',fill=COLORS[4] if stencil else COLORS[7] if ramp else COLORS[5])
    uvs[s]=(x/1024,1-(y+64)/2048,(x+512)/1024,1-y/2048)
atlas.save(PACK/'textures/nrt_test/atlas.png')
build_textures(PACK,atlas)
# Laminar DDSTool supplies mipmapped diffuse/LIT textures; keep normal maps PNG.
dds=TOOL.with_name('DDSTool.exe')
for name in ['buildings','buildings_LIT','apron','ramp_wear']:
    args=[str(dds),'--png2dxt5' if name=='ramp_wear' else '--png2dxt1']
    q=subprocess.run(args+[str(PACK/'textures/nrt_test'/(name+'.png')),str(PACK/'textures/nrt_test'/(name+'.dds'))],capture_output=True,text=True)
    (ROOT/'qa'/('dds_'+name+'.txt')).write_text(q.stdout+q.stderr);assert q.returncode==0

placements=[];meshes=[]
class Mesh:
    def __init__(self,name,origin,draped=False):
        self.name=name;self.o=np.array(origin);self.v=[];self.draped=draped;self.ops=[];self.last=0
        self.detailed=not draped and name!='mx_7478I_proxy'
        self.texture='buildings.png' if self.detailed else 'atlas.png'
        self.layer=('markings',4);self.normal='buildings_NML.png' if self.detailed else None;self.lights=[]
        self.clockwise=draped;self.blended=False
    def face(self,pts,color=0,uv=None,mapped=False):
        if self.detailed and uv is None and len(pts)==4:
            # Tile at a physical scale; avoid stretching one texel over a building.
            a,b,c,d=map(np.array,pts);nu=max(1,math.ceil(np.linalg.norm(b-a)/6));nv=max(1,math.ceil(np.linalg.norm(d-a)/6))
            for j in range(nv):
                for i in range(nu):
                    q=[a+(b-a)*u+(d-a)*v for u,v in [(i/nu,j/nv),((i+1)/nu,j/nv),((i+1)/nu,(j+1)/nv),(i/nu,(j+1)/nv)]]
                    uvq=[material_uv(color,u,v) for u,v in [(0,0),(1,0),(1,1),(0,1)]]
                    self.face(q,color,uvq,True)
            return
        p=[np.array([q[0]-self.o[0],q[2],self.o[1]-q[1]]) for q in pts]
        n=np.cross(p[1]-p[0],p[2]-p[0]);norm=np.linalg.norm(n)
        if norm<1e-9:return
        n/=norm
        if uv is None:uv=[((color*64+32)/1024,1-32/2048)]*len(p)
        if self.detailed and not mapped:uv=[(u*.5,v) for u,v in uv]
        for i in range(1,len(p)-1):
            for j in [0,i,i+1]:self.v.append([*p[j],*n,*uv[j]])
    def flat(self,geom,z,c):
        if self.detailed:
            mat=10 if c==0 and z>1 else 11 if z<1 else c
            x0,y0,x1,y1=geom.bounds
            for x in np.arange(math.floor(x0/6)*6,x1,6):
                for y in np.arange(math.floor(y0/6)*6,y1,6):
                    g=geom.intersection(box(x,y,x+6,y+6))
                    for poly in parts(g):
                        for t in constrained_delaunay_triangles(poly).geoms:
                            pts=list(orient(t,1).exterior.coords)[:-1]
                            self.face([(*p,z) for p in pts],mat,[material_uv(mat,(p[0]-x)/6,(p[1]-y)/6) for p in pts],True)
            return
        for poly in parts(geom):
            for tri in constrained_delaunay_triangles(poly).geoms:
                pts=list(orient(tri,1).exterior.coords)[:-1]
                self.face([(*p,z) for p in pts],c,[(p[0]/24,p[1]/24) for p in pts] if self.texture=='apron.png' else None)
    def extrude(self,g,z0,z1,c,roof=None):
        for poly in parts(g):
            poly=orient(poly,1)
            for ring in [poly.exterior,*poly.interiors]:
                for a,b in zip(ring.coords,list(ring.coords)[1:]):self.face([(*a,z0),(*b,z0),(*b,z1),(*a,z1)],c)
            if roof is not None:self.flat(poly,z1,roof)
    def label(self,s,center,width=12,height=2,z=.03,heading=0):
        x,y=center;u0,v0,u1,v1=uvs[s]
        f,r=m.m.vectors(heading);c=np.array([x,y])
        self.face([(*(c+r*a*width/2+f*b*height/2),z) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    def animated(self,commands,draw):
        if len(self.v)>self.last:self.ops.append('TRIS %d %d'%(self.last,len(self.v)-self.last))
        start=len(self.v);draw();self.ops.extend(['ANIM_begin',*commands,'TRIS %d %d'%(start,len(self.v)-start),'ANIM_end']);self.last=len(self.v)
    def flood(self,x,y,z,dx,dy,intensity=18000):
        self.extrude(box(x-.17,y-.17,x+.17,y+.17),z-.13,z+.13,1,1)
        # Native X-Plane 12 photometric spill / billboard, mounted on the facade.
        down=-1.0 if dx==dy==0 else -.8
        self.lights.append(f'LIGHT_PARAM spot_params_sp_pm {x-self.o[0]:.3f} {z:.3f} {self.o[1]-y:.3f} 1 0.94 0.86 1 {intensity}cd {dx*.6:.3f} {down} {-dy*.6:.3f} 0.45')
        self.lights.append(f'LIGHT_PARAM spot_params_bb_pm {x-self.o[0]:.3f} {z:.3f} {self.o[1]-y:.3f} 1 0.94 0.86 {intensity/10:g}cd {dx*.6:.3f} {down} {-dy*.6:.3f} 0.5')
    def save(self):
        rel='objects/nrt_test/'+self.name+'.obj';p=PACK/rel
        texture=self.texture.replace('.png','.dds') if self.texture!='atlas.png' else self.texture
        rows=['I','800','OBJ','TEXTURE ../../textures/nrt_test/'+texture]
        if self.detailed:rows+=['TEXTURE_NORMAL ../../textures/nrt_test/buildings_NML.png','TEXTURE_LIT ../../textures/nrt_test/buildings_LIT.dds','GLOBAL_specular 1.0']
        if getattr(self,'lit',None):rows+=['TEXTURE_LIT ../../textures/nrt_test/'+self.lit,'GLOBAL_luminance '+str(self.luminance)]
        if self.draped:
            rows+=['TEXTURE_DRAPED ../../textures/nrt_test/'+texture,f'ATTR_layer_group_draped {self.layer[0]} {self.layer[1]}','ATTR_LOD_draped 5000','GLOBAL_no_shadow']
            if self.normal:rows+=['TEXTURE_DRAPED_NORMAL 1.0 ../../textures/nrt_test/'+self.normal,'SPECULAR 1.0']
            if self.name=='apron_material':rows+=['DECAL_LIB lib/g10/decals/apt_concrete_1.dcl']
            if self.name in ['paint','ramp_safety']:rows+=['DECAL_LIB lib/g10/decals/apt_markings2.dcl','WEATHER_TRANSPARENT']
        rows+=['POINT_COUNTS %d 0 0 %d'%(len(self.v),len(self.v))]
        rows+=['VT '+' '.join(f'{x:.6f}' for x in v) for v in self.v]
        # OBJ8 front faces are CLOCKWISE, unlike the authoring triangles.
        # Draped geometry is extracted by X-Plane; ATTR_no_cull on ordinary
        # geometry does not repair its winding. Match Terminal B/D labels.
        indices=[j for i in range(0,len(self.v),3) for j in (i,i+2,i+1)] if self.clockwise else list(range(len(self.v)))
        for i in range(0,len(indices),10):
            q=indices[i:i+10];rows+=['IDX10 '+' '.join(map(str,q))] if len(q)==10 else ['IDX '+str(j) for j in q]
        rows+=['ATTR_no_cull']
        if self.blended:rows+=['ATTR_blend','ATTR_no_shadow']
        if self.draped:rows+=['ATTR_draped']
        if self.name in ['ramp_wear','taxi_wear']:rows+=['WEATHER_TRANSPARENT']
        rows+=self.ops
        if len(self.v)>self.last:rows+=['TRIS %d %d'%(self.last,len(self.v)-self.last)]
        rows+=self.lights
        p.write_text('\n'.join(rows)+'\n')
        placements.append({'resource':rel,'origin':self.o.tolist(),'heading':0,'triangles':len(self.v)//3})
        meshes.append(self)
        return rel

def parts(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [p for child in getattr(g,'geoms',[]) for p in parts(child)]
def lines(g):
    if g.is_empty:return []
    if g.geom_type in ['LineString','LinearRing']:return [LineString(g)]
    return [p for child in getattr(g,'geoms',[]) for p in lines(child)]
def bridge(mesh,a,b):
    poly=LineString([a,b]).buffer(1.6,cap_style=2)
    mesh.extrude(poly,3.72,4.0,0,0);mesh.extrude(poly,4.0,6.6,2);mesh.extrude(poly,6.6,6.85,0,0)
    for p in [a,b]:mesh.extrude(Point(p).buffer(.6,quad_segs=8),0,3.72,3,3)
    ring=Point(b).buffer(1.70,quad_segs=12)
    mesh.extrude(ring,3.65,4.3,0,0);mesh.extrude(ring,4.3,6.95,2);mesh.extrude(ring,6.95,7.2,0,0)

# Native animated tunnels; fixed links end at their 4 m rotunda floor.
# Both NRT7 bridges serve main deck port doors (A380 M1L/M2L, 747 L1/L2).
jetways=[]
for ident,n,off,size,park,length,cab,door in [
    ('9A','NRT9',[22,-7],1,270,14,270,1),
    ('9B','NRT9',[29,-3],2,0,17,270,2),
    ('8','NRT8',[18,-6],0,270,11,270,1)]:
    b=m.S[n]['nose']+off;a=np.array([b[0],m.fbo.bounds[3]])
    mesh=Mesh('fixed_'+ident,b);bridge(mesh,a,b);mesh.save()
    jetways.append(dict(id=ident,stand=n,base=b.tolist(),root=a.tolist(),size=size,serialized_size=size+(10 if door==2 else 0),heading=park,length=length,cabin=cab,door=door,floor=4,range=[[11,23],[14,29],[17,38]][size]))

mesh=Mesh('cargo',list(m.cargo.centroid.coords)[0]);mesh.extrude(m.cargo,0,12,0,0)
mesh.extrude(m.cargo.buffer(-.5),12,12.8,1,1);architectural(mesh,m,'cargo',uvs);mesh.save()
mesh=Mesh('fbo',list(m.fbo.centroid.coords)[0]);mesh.extrude(m.fbo,0,9.5,0,0)
x0,y0,x1,y1=m.fbo.bounds
mesh.extrude(box(x0,y1-.1,x1,y1+.08),3.3,6.8,2,2);mesh.extrude(m.fbo.buffer(.2),9.5,10,1,1);architectural(mesh,m,'fbo',uvs);mesh.save()
from hangars import build_hangars
animation_info=build_hangars(Mesh,m,PACK,placements,uvs)
from tower_wear import build_rooftop_cab,build_floor_wear,native_grime
tower_info=build_rooftop_cab(Mesh,m,ROOT)
floor_wear_info=build_floor_wear(Mesh,m)
native_wear=native_grime(m)
from mx_detail import build_signs,taxi_wear,maintenance_equipment,service_lights
sign_info=build_signs(Mesh,PACK)
taxi_wear_info=taxi_wear(Mesh,m,PACK)
equipment=maintenance_equipment(m)
service_lights(Mesh,m)
for name in ['signs','signs_LIT','taxi_wear']:
    q=subprocess.run([str(dds),'--png2dxt5' if name=='taxi_wear' else '--png2dxt1',str(PACK/'textures/nrt_test'/(name+'.png')),str(PACK/'textures/nrt_test'/(name+'.dds'))],capture_output=True,text=True)
    (ROOT/'qa'/('dds_'+name+'.txt')).write_text(q.stdout+q.stderr);assert q.returncode==0

# Original dimensioned proxy for the optional 747-8I parked-maintenance case.
# It is deliberately labelled; no copyrighted aircraft add-on is converted.
mx=m.S['MX'];proxy=Mesh('mx_7478I_proxy',mx['nose']);f,r=m.m.vectors(mx['heading'])
def pp(x,z,y):return [*(mx['nose']+r*x-f*z),y]
stations=[(0,.05,4.8),(3,2.3,4.8),(8,3.25,5.2),(56,3.25,5.2),(68,1.8,6),(76.25,.02,7)]
for a,b in zip(stations,stations[1:]):
    for i in range(20):
        t=i*math.tau/20;u=(i+1)*math.tau/20
        proxy.face([pp(a[1]*math.cos(t),a[0],a[2]+a[1]*math.sin(t)),pp(b[1]*math.cos(t),b[0],b[2]+b[1]*math.sin(t)),pp(b[1]*math.cos(u),b[0],b[2]+b[1]*math.sin(u)),pp(a[1]*math.cos(u),a[0],a[2]+a[1]*math.sin(u))],0)
for sign in [-1,1]:
    proxy.face([pp(sign*2.4,28,4.4),pp(sign*34.2,45,5.8),pp(sign*34.2,48,5.8),pp(sign*2.4,48,4.4)],3)
    proxy.face([pp(sign*1.5,62,7.2),pp(sign*11,70,8),pp(sign*11,73,8),pp(sign*1.5,70,7.2)],3)
    for xx,zz in [(12,36),(23,41)]:
        a=mx['nose']+r*(sign*xx)-f*zz
        proxy.extrude(Point(a).buffer(1.7,quad_segs=8),1.7,4.9,3,3)
proxy.face([pp(0,61,7),pp(0,70,19.4),pp(0,74,19.4),pp(0,74,7)],9)
for xx,zz in [(-5,39),(5,39),(-2,43),(2,43),(0,7.74)]:
    proxy.extrude(Point(mx['nose']+r*xx-f*zz).buffer(.65,quad_segs=6),0,2.8,7,7)
proxy_resource=proxy.save();proxy_placement=placements.pop()

# Draped operational labels, nose-wheel stop bars and cargo loader reservations.
paint=Mesh('paint',[2700,500],True)
# Retain a clear truck-side frontage for the next ATS arrangement. Aviation-only
# hardstanding and a circulation reservation; no SCS models or functions copied.
truckcourt=m.TRUCKCOURT
tx0,ty0,tx1,ty1=truckcourt.bounds
for dx in [30,38]:paint.flat(LineString([(tx0+dx,ty0+2),(tx0+dx,ty1-2)]).buffer(.12).intersection(truckcourt),0,5)
for n,s in m.S.items():
    if n=='MXOPEN':continue
    k=s['aircraft'];ng=s['nose']-m.GEAR[k][1]*m.direction(s['heading']);right=m.m.vectors(s['heading'])[1]
    paint.flat(LineString([ng-3.5*right,ng+3.5*right]).buffer(.12,cap_style=2),0,4)
    paint.label(m.DISPLAY.get(n,n),m.TURN_LABELS[n],13,2.2,heading=s['heading'])
    if n in m.CARGO_SMALL:paint.label('MAX 75F',m.TURN_LABELS[n]-3*m.direction(s['heading']),16,2,heading=s['heading'])
    if n=='NRT8':
        paint.label('MAX A300',m.TURN_LABELS[n]-3*m.direction(s['heading']),16,2,heading=s['heading'])
        ng2=s['nose']-m.GEAR['737-800'][1]*m.direction(s['heading'])
        paint.flat(LineString([ng2-3.5*right,ng2+3.5*right]).buffer(.12,cap_style=2),0,4)
        paint.label('A300',ng+right*7,7,1.2,heading=180);paint.label('737',ng2+right*7,7,1.2,heading=180)
    if n=='NRT9':
        ng2=s['nose']-m.GEAR['747-8I'][1]*m.direction(s['heading'])
        paint.flat(LineString([ng2-3.5*right,ng2+3.5*right]).buffer(.12,cap_style=2),0,4)
        paint.label('A380',ng+right*7,7,1.2);paint.label('747-8I',ng2+right*8,8,1.2)
for n,g in m.loadzones.items():
    paint.flat(LineString(g.exterior.coords).buffer(.14),0,4)
    paint.label('NOSE LOAD',np.array(g.centroid.coords[0])+[-4,0],17,2.2,heading=90)
for n,g in m.GSE_POCKETS.items():
    paint.flat(LineString(g.exterior.coords).buffer(.1),0,5)
    paint.label(n,list(g.centroid.coords)[0],8,1.5)
for n,g in m.GSE_BAYS:paint.flat(LineString(g.exterior.coords).buffer(.08),0,5)
for n,p in m.helis:
    c=m.xy(p);paint.flat(LineString(box(*(list(c-20)+list(c+20))).exterior.coords).buffer(.15),0,5)
    # The native apt.dat helipad supplies its H and circle; do not double-paint it.
    paint.label(n,c+[0,-17],12,2)
    paint.label('CHINOOK',c+[0,17],13,2)
pb=dict(m.CARGO_PB)
for n,k in [('NRT9','A380'),('NRT8','737-800'),('NRT11','Bizjet32'),('NRT12','Bizjet32')]:
    p,h,_=m.PATHS[k,n+' departure'][0];ng=p+m.GEAR[k][0]*m.direction(h);pb[n]=[ng.tolist(),h]
# Remove test-only pavement banners and the obsolete A380 size-reference box.
paint.flat(LineString(m.OPEN_PAINT.exterior.coords).buffer(.15,cap_style=2,join_style=2),0,6)
paint.save()
ramp_details(Mesh,m,PACK)
pave=Mesh('apron_material',[2700,500],True);pave.texture='apron.png';pave.normal='apron_NML.png';pave.layer=('taxiways',1)
pave.flat(m.apron.union(truckcourt).difference(unary_union([m.hangar,m.cargo,m.fbo,*m.PRIVATE_HANGARS.values()])),0,0);pave.save()

# Start from the actual public tile, not the former private campus.
raw=(ROOT/'reference/public_south.dsf.txt').read_text();d=ag.parse_dsf(ROOT/'reference/public_south.dsf.txt')
portal=box(2795,680,2860,733)
site=unary_union([m.apron,m.hangar,m.fbo,m.cargo,portal,*m.PRIVATE_HANGARS.values()])
removed=[];clipped=[]
for e in d['entities']:
    if e['kind']=='object' and site.buffer(3).covers(e['geom']):
        # All such stock fixtures are enumerated in build evidence.
        raw=raw.replace('\n'.join(e['lines'])+'\n','',1);removed.append(dict(resource=e['resource'],bounds=list(e['geom'].bounds)))
    if e['kind']=='polygon' and e['resource'].endswith('Fence_Facades/Fence.fac'):
        original=LineString(e['loops'][0]);cut=original.difference(site.buffer(3))
        if original.equals(cut):continue
        rows=[]
        for path in lines(cut):
            if path.length<.1:continue
            rows += [f"BEGIN_POLYGON {e['index']} {e['param']} 3",'BEGIN_WINDING']
            rows += [f'POLYGON_POINT {m.m.ll(*p)[0]:.9f} {m.m.ll(*p)[1]:.9f} 0' for p in path.coords]
            rows += ['END_WINDING','END_POLYGON']
        raw=raw.replace('\n'.join(e['lines']),'\n'.join(rows),1);clipped.append(e['resource'])
defs=[];commands=[]
def objdef(resource):
    if resource not in d['objects']:d['objects'].append(resource);defs.append('OBJECT_DEF '+resource)
    return d['objects'].index(resource)
def objcmd(item):
    i=objdef(item['resource']);lo,la=m.m.ll(*item['origin']);return f"OBJECT {i} {lo:.9f} {la:.9f} {item['heading']}"
for item in placements:commands.append(objcmd(item))
for item in native_wear:commands.append(objcmd(item))
for item in equipment:commands.append(objcmd(item))
from ramp_masts import placements as mast_placements
masts=mast_placements()
for item in masts:commands.append(objcmd(item))
fidx=len(d['polygons']);defs.append('POLYGON_DEF lib/airport/Common_Elements/Fence_Facades/Fence.fac')
for path in m.fence_parts:
    commands += [f'BEGIN_POLYGON {fidx} 3 3','BEGIN_WINDING']
    commands += [f'POLYGON_POINT {m.m.ll(*m.xy(p))[0]:.9f} {m.m.ll(*m.xy(p))[1]:.9f} 0' for p in path]
    commands += ['END_WINDING','END_POLYGON']

a380path=CS/'MisterX_Library/Airport/Aircraft/Airbus_A380_800/Lufthansa.obj'
vs=np.array([list(map(float,r.split()[1:4])) for r in a380path.read_text().splitlines() if r.startswith('VT')]);bb=[vs.min(axis=0).tolist(),vs.max(axis=0).tolist()]
# OBJ forward is -Z. Heading 270 rotates its nose toward west.
zmin=vs[:,2].min();a380_origin=mx['nose']+m.direction(270)*zmin
a380item={'resource':'MisterX_Library/Airport/Aircraft/Airbus_A380_800/Lufthansa.obj','origin':a380_origin.tolist(),'heading':270}
a380cmd=objcmd(a380item);b747cmd=objcmd(proxy_placement)
# Exclude lower-priority auto-gen over the new test campus; keep roads untouched.
ex=[]
for bounds in [(2400,268,3172,598),(2822,598,3074,765)]:
    w,s=m.m.ll(bounds[0],bounds[1]);e,n=m.m.ll(bounds[2],bounds[3])
    for typ in ['obj','fac','for']:ex.append(f'PROPERTY sim/exclude_{typ} {w:.9f}/{s:.9f}/{e:.9f}/{n:.9f}')
ix=raw.find('FILTER 0');assert ix>=0
raw=raw[:ix]+'\n'.join(ex+defs)+'\n'+raw[ix:]
raw+='\n'+'\n'.join(commands)+'\n'

# Public apt.dat with only the east NB opening repaired and new test additions.
apt=(ROOT/'reference/public_apt.dat').read_text().rstrip();assert apt.endswith('99');apt=apt[:-2].rstrip()+'\n'
apt=apt.replace(apt.splitlines()[1],'1200 NRT R10 isolated visual finish R06',1)
features=ag.parse_apt(ROOT/'reference/public_apt.dat');removed_apt=[];boundary=[]
portal_clear=box(2762,682.32515,2860,730.32515)
for feat in features:
    if feat['code']!=120 or 'geom' not in feat:continue
    rows=feat['lines'];first=rows[0]
    if first=='120 Linear Feature 91' and feat['geom'].distance(Point([2823.386936,706.32515]))<25:boundary=rows;continue
    cut=first in ['120 Linear Feature 9','120 Linear Feature 16'] and len(rows)<=5 and feat['geom'].intersects(portal_clear)
    road_cuts=[s for s in styled_segments(rows) if s['attrs']==[74] and s['geom'].intersects(portal_clear)]
    if road_cuts:
        rep=rows.copy()
        for seg in reversed(road_cuts):
            assert seg['straight'];cp=list(seg['geom'].intersection(portal_clear).coords);extra=[]
            for p,att in [(cp[0],''),(cp[-1],' 74')]:
                lo,la=m.m.ll(*p);extra.append(f'111 {la:.9f} {lo:.9f}'+att)
            rep[seg['index']+1:seg['index']+1]=extra
    elif cut:
        rep=[];attrs=rows[1].split()[3:]
        for path in lines(feat['geom'].difference(portal_clear)):
            rep.append(first+' / test opening')
            for i,p in enumerate(path.coords):
                lo,la=m.m.ll(*p);end=i==len(path.coords)-1
                rep.append(f'{115 if end else 111} {la:.9f} {lo:.9f}'+(' '+' '.join(attrs) if not end else ''))
    else:continue
    apt=apt.replace('\n'.join(rows),'\n'.join(rep),1);removed_apt.append(rows)
assert boundary,'Original nonmovement boundary must remain'
for row in apt.splitlines():
    v=row.split()
    if len(v)>=7 and v[0]=='20' and v[6]=='{no-entry}' and abs(float(v[2])+95.312542)<.00001 and 29.99074<float(v[1])<29.99094:
        apt=apt.replace(row+'\n','',1);removed_apt.append([row])
new=[]
oldpave=unary_union([f['geom'] for f in features if f['code'] in [100,110] and 'geom' in f])
# Native hard pavement. Add small wheel-path margins on the existing R09 apron.
apron=m.apron.union(m.hangar).union(m.cargo).union(truckcourt).union(portal.intersection(box(2795,685,2860,728)))
for poly in parts(apron.difference(oldpave)):
    new.append('110 2 0.25 0 NRT R10 Test Apron')
    for ring in [orient(poly,1).exterior,*orient(poly,1).interiors]:
        pts=list(ring.coords)[:-1]
        for i,p in enumerate(pts):
            lo,la=m.m.ll(*p);new.append(f'{113 if i==len(pts)-1 else 111} {la:.9f} {lo:.9f}')
# Published R09 backbone is the visible guidance line. Type-specific final stop bars
# are nose-wheel targets. A long-wheelbase taxi trial must check real oversteer.
network=m.LINE_NETWORK
for path in lines(network):
    if path.length<.2:continue
    pts=list(path.simplify(.04).coords);new.append('120 NRT R10 common taxi line')
    for i,p in enumerate(pts):
        lo,la=m.m.ll(*p);new.append(f'{115 if i==len(pts)-1 else 111} {la:.9f} {lo:.9f}'+(' 51' if i<len(pts)-1 else ''))
# Flight-setup starts are gates (nose-wheel reference), with auto-population disabled.
starts=[]
def start(name,ng,h,size='F'):
    lo,la=m.m.ll(*ng);starts.append(dict(name=name,nose_gear=list(ng),heading=h,size=size))
    return [f'1300 {la:.9f} {lo:.9f} {h:.5f} gate heavy|jets {name}',f'1301 {size} none']
new+=start('NRT TEST ENTRY - NB eastbound',[2670,706.32515],90)
for n,s in m.S.items():
    if n in ['MX','MXOPEN'] or n in m.PRIVATE_HANGARS:continue
    types=['A380','747-8I'] if n=='NRT9' else ['A300-600','737-800'] if n=='NRT8' else [s['aircraft']]
    for k in types:
        ng=s['nose']-m.GEAR[k][1]*m.direction(s['heading'])
        new+=start(n+' TEST - '+k,ng,s['heading'],'F' if k in ['A380','747-8I','747-8F'] else 'E' if k=='777F' else 'D' if k in ['757F','A300-600'] else 'C')
for n,(ng,h) in pb.items():new+=start(n+' TEST EXIT - after pushback',ng,h,'D' if n in m.CARGO_SMALL else 'C' if n in ['NRT11','NRT12','NRT8'] else 'F')
# Native 40 m heli surfaces and helicopter-only setup positions.
for n,p in m.helis:
    c=m.xy(p);lo,la=m.m.ll(*c)
    new.append(f'102 {n} {la:.9f} {lo:.9f} 0 40 40 2 0 0 0.25 1')
    new += [f'1300 {la:.9f} {lo:.9f} 0 misc helos {n} TEST - Chinook', '1301 B none']
    starts.append(dict(name=n+' TEST - Chinook',nose_gear=c.tolist(),heading=0,size='B'))
for n,g in m.PRIVATE_HANGARS.items():
    c=[g.bounds[2]+45,g.centroid.y]
    new+=start(m.DISPLAY[n]+' TEST HOLD - open doors then tow',c,270,'D')
    ss=m.S[n];ng=ss['nose']-m.GEAR[ss['aircraft']][1]*m.direction(270)
    new+=start(m.DISPLAY[n]+' TEST - 757-300 or A321',ng,270,'D')
new+=start('NRT MX OPEN TEST - open parking',m.OPEN_NG,270,'F')
new+=start('NRT MH1 TEST HOLD - open all doors then tow',[2570,540],270)
for j in jetways:
    lo,la=m.m.ll(*j['base']);new.append(f"1500 {la:.9f} {lo:.9f} {j['heading']} 1 {j['serialized_size']} {j['heading']} {j['length']} {j['cabin']}")
aptbase=apt+'\n'.join(new)+'\n'
for mode,extra in [('A380_MX',a380cmd),('7478I_MX',b747cmd),('CLEAR_MX','')]:
    dest=PACK/'Test modes'/mode;dest.mkdir(exist_ok=True)
    src=PACK/'Source'/('south_'+mode+'.dsf.txt');src.write_text(raw+extra+'\n')
    p=subprocess.run([str(TOOL),'--text2dsf',str(src),str(dest/'south.dsf')],capture_output=True,text=True)
    (ROOT/'qa'/('compile_'+mode+'.txt')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
    a=aptbase
    if mode=='CLEAR_MX':
        for k in ['A380','747-8I']:a+='\n'.join(start('NRT MH1 TEST - '+k,mx['nose']-m.GEAR[k][1]*m.direction(270),270))+'\n'
    (dest/'apt.dat').write_text(a+'99\n')
shutil.copy2(PACK/'Test modes/CLEAR_MX/south.dsf',PACK/'Earth nav data/+20-100/+29-096.dsf')
shutil.copy2(PACK/'Test modes/CLEAR_MX/apt.dat',PACK/'Earth nav data/apt.dat')
(PACK/'ACTIVE_MODE.txt').write_text('CLEAR_MX\n')
manifest=dict(name=NAME,revision='R06',layout='R10',jetways=jetways,placements=placements,starts=starts,pushback_exits=pb,removed_stock=removed,clipped_fences=clipped,removed_apt=removed_apt,original_boundary=boundary,a380_mesh_bounds_xyz=bb,a380_placement=a380item,proxy_747=proxy_placement,base=str(BASE),open_parking=dict(start_count=1,nosegear=m.OPEN_NG.tolist(),red_square_bounds=list(m.OPEN_PAINT.bounds),red_square_size_m=88,yellow_leadin=False),status='Offline build; no simulator run or acceptance',animations=animation_info,remarks=['Aircraft movements are manual test routes; no new AI taxi/service network is claimed.','Visible common lines and detached ramp lead-ins follow R09 geometry. Long wheelbase final alignment needs simulator testing.','A380 interior static is MisterX, referenced in place. 747-8I occupancy is a labelled original dimensions proxy.','New buildings are simplified test geometry in R09 footprints with animated doors.','Jetways 9A/9B are main deck L1/L2 only. Native runtime docking depends on aircraft door data.'])
manifest['remarks']=['Approved R09 stand, hangar, jetway and common-line coordinates retained.','Lee Road centerline allowance is 16 m using existing OSM reference, not surveyed road width.','Nose loading and all 12 equipment bays retained; equipment column separation reduced.','Original tiled building, normal/specular, night, apron and wear materials; diffuse/LIT compressed by Laminar DDSTool.','Paint uses documented ATTR_layer_group_draped plus explicit drawing range, native decals and weather transparency.','Native 51 black-bordered yellow guidance, photometric facade lights and native helipad markings.','No new AI routing or automated pushback is claimed.','Actual visibility, weather/night appearance and OpenSAM/jetway operation require the next simulator test.']
manifest['materials']='R10 original materials; native X-Plane shader and light support'
manifest['repair']='Ground markings 01: clockwise draped triangles matched to Terminal B/D; original R10 retained'
manifest['remarks'].append('Four ground objects have corrected clockwise face indices; normals, UVs, textures, geometry, routes and placements are unchanged. Runtime confirmation remains pending.')
manifest.update(layout='R11',revision='R07',tower=tower_info,floor_wear=floor_wear_info,native_wear=native_wear)
manifest['remarks']=['Accepted R10 aircraft routes, starts, jetways, buildings and all signage retained.','Original NRT rooftop apron-control cab adapted to the FBO roof.','Stronger rubber alpha without mip fading; native Laminar stand grime and additional hangar-floor wear.','Ground markings retain the clockwise fix. No signage changes in this revision.','Runtime appearance awaits simulator testing.']
manifest.update(layout='R12',revision='R08',signs=sign_info,taxi_wear=taxi_wear_info,equipment=equipment)
manifest['remarks']=['Aircraft routes, starts, ground paint, tower and doors retained.','Dedicated tire paths along the backbone and detached lead-ins.','Native maintenance equipment at the west sides and rear service pockets.','Building signs are separate high-resolution, night-lit boards; MH1 sign clears the raised door stack.','Corrected facade light placement and added side/interior night-only work lighting.','Offline appearance and placement checked; simulator confirmation remains pending.']
manifest.update(layout='R14',revision='R10',masts=masts,helipad_lighting=dict(tall_mast_setback_from_reserved_area_m=100,removed_mast='M09',native_perimeter_lights=True,additional_tall_fixtures=False))
manifest['remarks']=['R13 routes, starts, ground paint, wear, equipment, signs, wall/interior lights and door animation preserved.','FBO west mast M09 removed; twelve native circular LED masts remain at their approved coordinates.','Every remaining tall mast assembly is at least 100 m beyond both 46 m helipad planning reserve squares.','Helipad lighting remains the native ground-level perimeter lights. No high fixtures added at the pads.','This setback is a scenery design choice, not an assessed helicopter approach surface.']
manifest.update(layout='R15',revision='R11',tire_stand_paths=json.loads((ROOT/'output/Tire_Stand_Paths.json').read_text()))
manifest['remarks']=['Original tire artwork revised using installed KIAH AEP skid/grunge references; no AEP artwork redistributed or new dependency added.','Four irregular streak variants at fixed 64 m longitudinal scale, with mixed fleet turn cut-in and aircraft-scaled stand tracks.','R14 routes, starts, geometry, ground paint, equipment, lighting and helipad clearances retained.','Exterior tire wear is illustrative; X-Plane appearance still needs user testing.']
(PACK/'Build_Evidence.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'output/Build_Evidence.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'built':str(PACK),'new_objects':len(placements),'new_triangles':sum(x['triangles'] for x in placements),'modes':3,'jetways':len(jetways),'test_starts':len(starts),'stock_removed':removed,'fences_clipped':len(clipped)},indent=2))
