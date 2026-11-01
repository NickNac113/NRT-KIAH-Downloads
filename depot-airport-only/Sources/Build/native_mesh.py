from layout_plan import *
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
from PIL import Image,ImageDraw,ImageFont

TILES={'roof':(0,0,512,512),'glass':(512,0,1024,256),'concrete':(1024,0,1280,256),'metal':(1280,0,1536,256),'yellow':(1536,0,1792,256),'dark':(1792,0,2048,256),'hvac':(1024,256,1280,512),'white':(1280,256,1536,512),'orange':(1536,256,1792,512)}
COLORS={'roof':(190,199,200),'glass':(35,65,79),'concrete':(156,160,156),'metal':(216,222,220),'yellow':(239,186,56),'dark':(25,31,34),'hvac':(101,118,120),'white':(225,230,229),'orange':(232,109,48)}
SIGN_TILES={}
def atlas(names,path):
    im=Image.new('RGB',(2048,2048),(40,46,50));lit=Image.new('RGB',(2048,2048));d=ImageDraw.Draw(im);ld=ImageDraw.Draw(lit)
    for n,t in TILES.items():d.rectangle(t,fill=COLORS[n])
    d.rectangle(TILES['glass'],fill=(43,70,82));ld.rectangle(TILES['glass'],fill=(71,93,98))
    for x in range(516,1024,64):
        d.line([(x,0),(x,255)],fill=(154,171,177),width=4);ld.line([(x,0),(x,255)],fill=(18,23,26),width=5)
    for y in (6,128,249):d.line([(512,y),(1023,y)],fill=(152,166,171),width=5);ld.line([(512,y),(1023,y)],fill=(16,20,22),width=5)
    for x in range(0,512,32):d.line([(x,0),(x,511)],fill=(172,183,185),width=1)
    for y in range(0,512,128):d.line([(0,y),(511,y)],fill=(162,173,175),width=2)
    for y in range(260,512,8):d.line([(1030,y),(1274,y)],fill=(55,65,67),width=2)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',44)
    for i,n in enumerate(sorted(set(names))):
        col=i%16;row=i//16;x=col*128;y=1024+row*64
        if y+64>2048:raise ValueError('sign atlas capacity')
        t=(x+2,y+2,x+126,y+62);SIGN_TILES[n]=t
        d.rectangle(t,fill=(23,30,34),outline=(236,186,61),width=3)
        sz=44 if len(n)<=3 else 30;ff=font.font_variant(size=sz)
        d.text((x+64,y+32),n,fill=(246,207,95),font=ff,anchor='mm');ld.text((x+64,y+32),n,fill=(142,123,72),font=ff,anchor='mm')
    path.mkdir(parents=True,exist_ok=True);im.save(path/'terminal_atlas.png');lit.save(path/'terminal_atlas_LIT.png')
    return dict(SIGN_TILES)
def uv_rect(tile):
    x1,y1,x2,y2=tile
    return [(x1/2048,1-y2/2048),(x2/2048,1-y2/2048),(x2/2048,1-y1/2048),(x1/2048,1-y1/2048)]
class Mesh:
    def __init__(self,name):self.name=name;self.vertices=[];self.indices=[];self.faces=[]
    def face(self,coords,mat='metal',uv=None):
        coords=np.array(coords,dtype=float);n=np.cross(coords[1]-coords[0],coords[2]-coords[0]);length=np.linalg.norm(n)
        if length<1e-8:return
        n/=length
        tile=SIGN_TILES.get(mat,TILES.get(mat,TILES['metal']));uv=uv or uv_rect(tile)
        offset=len(self.vertices)
        for p,u in zip(coords,uv):self.vertices.append([*p,*n,*u])
        for j in range(1,len(coords)-1):self.indices.extend([offset,offset+j,offset+j+1]);self.faces.append((offset,offset+j,offset+j+1))
    def flat(self,geom,z,mat='roof'):
        for part in polygon_parts(polys_only(make_valid(geom))):
            tris=constrained_delaunay_triangles(part)
            for tri in tris.geoms:
                q=orient(tri,sign=1);p=list(q.exterior.coords)[:3];tile=SIGN_TILES.get(mat,TILES.get(mat,TILES['roof']));u=uv_rect(tile)
                self.face([(x,y,z) for x,y in p],mat,u[:3])
    def extrude(self,geom,z0,z1,mat='metal',roof='roof',panels=False):
        for part in polygon_parts(polys_only(make_valid(geom))):
            part=orient(part,sign=1)
            for ring in [part.exterior,*part.interiors]:
                pts=list(ring.coords)
                for a,b in zip(pts,pts[1:]):
                    a=np.array(a);b=np.array(b);length=np.linalg.norm(b-a);count=max(1,math.ceil(length/6)) if panels else 1
                    for j in range(count):
                        s=a+(b-a)*j/count;t=a+(b-a)*(j+1)/count
                        self.face([(*s,z0),(*t,z0),(*t,z1),(*s,z1)],mat)
            if roof:self.flat(part,z1,roof)
    def box(self,x,y,z,sx,sy,sz,mat='metal'):
        self.extrude(box(x-sx/2,y-sy/2,x+sx/2,y+sy/2),z,z+sz,mat,mat)
    def link(self,a,b,width,z0,z1,mat='glass'):
        a=np.array(a);b=np.array(b);v=b-a;n=np.linalg.norm(v)
        if n<.05:return
        right=np.array([v[1],-v[0]])/n*width/2
        self.extrude(Polygon([a-right,b-right,b+right,a+right]),z0,z1,mat,'metal',True)
    def write(self,path,origin=(0,0),draped=False):
        lines=['A','800','OBJ','','TEXTURE ../textures/terminal_atlas.png','TEXTURE_LIT ../textures/terminal_atlas_LIT.png']
        if draped:lines+=['TEXTURE_DRAPED ../textures/terminal_atlas.png','LAYER_GROUP_DRAPED markings 2']
        lines+=['GLOBAL_specular 0.3',f'POINT_COUNTS {len(self.vertices)} 0 0 {len(self.indices)}','']
        for x,y,z,nx,ny,nz,u,v in self.vertices:lines.append(f'VT {x-origin[0]:.4f} {z:.4f} {-y+origin[1]:.4f} {nx:.5f} {nz:.5f} {-ny:.5f} {u:.7f} {v:.7f}')
        # OBJ8 front faces are CLOCKWISE; authoring/Blender faces stay CCW.
        native_indices=[n for i in range(0,len(self.indices),3) for n in (self.indices[i],self.indices[i+2],self.indices[i+1])]
        for i in range(0,len(native_indices),10):
            ix=native_indices[i:i+10]
            if len(ix)==10:lines.append('IDX10 '+' '.join(map(str,ix)))
            else:lines.extend('IDX '+str(n) for n in ix)
        if draped:lines+=['ATTR_draped']
        lines+=['ATTR_LOD 0 14000',f'TRIS 0 {len(self.indices)}','']
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(lines),encoding='utf-8')
        return {'path':str(path),'origin':list(origin),'vertices':len(self.vertices),'triangles':len(self.indices)//3,'draped':draped}

def terminal_mesh(name,geom,height):
    mesh=Mesh(name);g=geom.simplify(.18,preserve_topology=True)
    mesh.extrude(g,0,3.9,'concrete',None)
    mesh.extrude(g,3.9,height-1.2,'glass',None,True)
    mesh.extrude(g.buffer(.4,join_style=2),height-1.2,height,'metal','roof')
    # Exterior mullions and restrained service details are modeled, not surveyed.
    for part in polygon_parts(g):
        pts=list(part.exterior.coords)
        for a,b in zip(pts,pts[1:]):
            a=np.array(a);b=np.array(b);length=np.linalg.norm(b-a)
            for t in np.arange(0,length,12):
                p=a+(b-a)*t/max(length,.01);mesh.box(*p,3.9,.32,.32,height-3.9,'white')
    inside=g.buffer(-6);bounds=g.bounds
    for x in np.arange(math.ceil(bounds[0]/24)*24,bounds[2],24):
        for y in np.arange(math.ceil(bounds[1]/32)*32,bounds[3],32):
            q=box(x-2.5,y-4,x+2.5,y+4)
            if inside.covers(q):mesh.extrude(q,height,height+1.25,'hvac','hvac')
    # Roof seam ribs follow a regular construction rhythm; shape is kept lightweight.
    for x in np.arange(math.ceil(bounds[0]/10)*10,bounds[2],10):
        rib=g.buffer(-1).intersection(box(x-.06,bounds[1],x+.06,bounds[3]))
        mesh.extrude(rib,height,height+.08,'metal','metal')
    return mesh

def make_jetway(r,building):
    door=np.array(r['door']);f=heading_vec(r['heading']);left=np.array([-f[1],f[0]])
    base=door-f*8+left*8
    for k in range(60):
        if not building.buffer(1.8).contains(Point(base)):break
        base-=f
    target=np.array(r['pos'])-f*3+left*3
    v=target-base;length=np.linalg.norm(v);h=bearing(v)
    # Keep a valid parked state in the stock X-Plane articulation envelope.
    length=max(11,min(46,length));size=next((i for i,(lo,hi) in enumerate([(11,23),(14,29),(17,38),(20,47)]) if lo<=length<=hi),3)
    end=base+heading_vec(h)*length
    return dict(name=r['name'],door=door.tolist(),base=base.tolist(),end=end.tolist(),heading=h,length=length,size=size,cabin_heading=(h-45)%360)

def jetway_mesh(j,active=False):
    m=Mesh('jetway_'+j['name']);door=np.array(j['door']);base=np.array(j['base']);end=np.array(j['end'])
    if not active:
        m.link(door,base,3.0,4.3,7.2)
        m.box(*base,0,1.1,1.1,4.3,'metal')
        # Wall-mounted identifier, facing the ramp, above the fixed tunnel.
        v=base-door;length=np.linalg.norm(v);v=v/max(length,.01);right=np.array([v[1],-v[0]])*2.0;c=base+v*.12
        m.face([(*(c+right),7.2),(*(c-right),7.2),(*(c-right),9),(*(c+right),9)],j['name'])
    else:
        m.link(base,end,2.7,4.25,7.0)
        m.box(*end,0,1.4,1.1,4.3,'dark')
        m.extrude(Point(end).buffer(1.8,quad_segs=5),4.1,7.2,'white','metal')
    return m

def ground_sign(mesh,pos,h,text,width=6,height=2.6):
    f=heading_vec(h);right=np.array([f[1],-f[0]]);p=np.array(pos)
    mesh.face([(*(p-right*width/2-f*height/2),0),(*(p+right*width/2-f*height/2),0),(*(p+right*width/2+f*height/2),0),(*(p-right*width/2+f*height/2),0)],text)
