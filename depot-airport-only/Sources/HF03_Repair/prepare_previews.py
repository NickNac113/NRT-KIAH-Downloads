"""Build review geometry from the staged native airport and stock jetway OBJs.
Native animated meshes are evaluated at their parked state. Retained facades
are massing proxies; paint follows native control points with simplified width.
"""
import pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
sys.path.insert(0,str(PREV/'work'))
from sign_groups import *
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'
import math,gzip,importlib.util,ast,hashlib
from route_common import smooth_pavement
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03'
LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
LIB=LIVE.parents[1]/'Resources/default scenery/airport scenery'
# Load only the Bezier helper, without executing the repair builder.
tree=ast.parse((PREV/'work/repair_airport_details.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='sampled_apt_segments'],type_ignores=[]),'helper','exec'))
spec=importlib.util.spec_from_file_location('preview_native',STAGE/'Sources/Build/native_mesh.py');nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(nm)
plan,before,oldapt,oldscene=pickle.loads((ROOT/'work/current.pkl').read_bytes())
scene=json.loads((ROOT/'work/scene-hf03.json').read_text())
crop=box(-1600,-1100,2200,1100)
out=[];counts={}

def addmesh(name,verts,faces,tag,mat,uvs=None,texture=None,cull=False):
    if not faces:return
    out.append(dict(name=name,vertices=verts,faces=faces,tag=tag,material=mat,uvs=uvs,texture=texture,cull=cull))

def flat(name,g,z,tag,mat):
    vs=[];fs=[]
    for part in polygon_parts(polys_only(make_valid(g))):
        if part.area<.00001:continue
        for tri in constrained_delaunay_triangles(part).geoms:
            pts=list(orient(tri,sign=1).exterior.coords)[:3];k=len(vs)
            vs += [(x,y,z) for x,y in pts];fs.append((k,k+1,k+2))
    addmesh(name,vs,fs,tag,mat)

def simple_solid(name,g,z0,z1,tag,mat):
    m=nm.Mesh(name);m.extrude(g,z0,z1)
    addmesh(name,[v[:3] for v in m.vertices],m.faces,tag,mat)

templates={};animation_counts={}
def rotation(axis,degrees):
    u=np.array(axis,dtype=float);u/=np.linalg.norm(u);a=math.radians(degrees);c=math.cos(a);s=math.sin(a)
    x,y,z=u;cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    m=np.eye(4);m[:3,:3]=c*np.eye(3)+(1-c)*np.outer(u,u)+s*cross;return m
def trans(v):
    m=np.eye(4);m[:3,3]=v;return m
def lerp(keys,value):
    keys=sorted(keys,key=lambda k:k[0]);t=[k[0] for k in keys];vals=np.array([k[1:] for k in keys])
    return [float(np.interp(value,t,vals[:,i])) for i in range(vals.shape[1])]

def active_jetway(a,tag,index):
    s=a['parts'];style=int(s[4]);size=int(s[5])%10
    filename=f"jetway_{['1s','1g','2s','2g'][style]}_3t_{['11-23','14-29','17-38','20-47'][size]}.obj"
    path=LIB/'Ramp_Equipment/jetways'/filename
    if filename not in templates:
        rows=[l.split() for l in path.read_text().splitlines() if l.split()];v=[];uv=[];ix=[];cmd=[];lod=False
        for row in rows:
            if row[0]=='VT':v.append([*map(float,row[1:4]),1]);uv.append(list(map(float,row[7:9])))
            elif row[0] in ('IDX','IDX10'):ix.extend(map(int,row[1:]))
            elif row[0]=='TEXTURE':texture=path.parent/row[1].replace('\\','/')
            elif row[0]=='ATTR_LOD':
                if lod:break
                lod=True
            elif lod:cmd.append(row)
        if not texture.exists():texture=texture.with_suffix('.dds')
        templates[filename]=(np.array(v),np.array(uv),np.array(ix),cmd,str(texture.resolve()))
    v,uv,ix,cmd,texture=templates[filename];stack=[];m=np.eye(4);vs=[];us=[];fs=[];i=0
    base=(float(s[6])-float(s[3])+180)%360-180
    cabin=(float(s[8])-float(s[6])+180)%360-180
    vals={'jw_base_rotation':base,'jw_tunnel_pitch':0,'jw_tunnel_extension':float(s[7]),'jw_cabin_rotation':cabin,'jw_bogie_elevation':0,'jw_bogie_rotation':0,'jw_bogie_bogie_tilt':0,'jw_wheel_left':0,'jw_wheel_right':0,'jw_stairs_angle':-35,'jw_stairs_bogie_angle':35}
    origin=xy(float(s[2]),float(s[1]));world=trans((origin[0],0,-origin[1]))@rotation((0,1,0),-float(s[3]))
    while i<len(cmd):
        r=cmd[i];op=r[0]
        if op=='ANIM_begin':stack.append(m.copy())
        elif op=='ANIM_end':m=stack.pop()
        elif op in ('ANIM_rotate_begin','ANIM_trans_begin'):
            keys=[];ref=r[-1].split('/')[-1];axis=list(map(float,r[1:4])) if op=='ANIM_rotate_begin' else None
            i+=1
            while not cmd[i][0].endswith('_end'):
                if cmd[i][0].endswith('_key'):keys.append(list(map(float,cmd[i][1:])))
                i+=1
            value=lerp(keys,vals.get(ref,0));m=m@(rotation(axis,value[0]) if axis is not None else trans(value))
        elif op=='ANIM_trans':
            a0=list(map(float,r[1:4]));a1=list(map(float,r[4:7]));assert a0==a1;m=m@trans(a0)
        elif op=='ANIM_rotate':
            assert float(r[4])==float(r[5]);m=m@rotation(list(map(float,r[1:4])),float(r[4]))
        elif op=='TRIS':
            start,count=map(int,r[1:3]);ids=ix[start:start+count];ps=v[ids]@(world@m).T;offset=len(vs)
            vs.extend(np.column_stack((ps[:,0],-ps[:,2],ps[:,1])).tolist());us.extend(uv[ids].tolist())
            fs.extend((offset+j,offset+j+2,offset+j+1) for j in range(0,count,3))
        i+=1
    assert not stack
    addmesh(f'{tag} native moving jetway {index}',vs,fs,tag,'jetway',us,texture,True)
    animation_counts[tag]=animation_counts.get(tag,0)+1

for tag,pack,d,a in [('Before',LIVE,before,oldapt),('After',STAGE,parse_dsf(ROOT/'work/roundtrip-south.txt'),parse_apt(STAGE/'Earth nav data/apt.dat'))]:
    paved={};markings={}
    for b in a:
        if b['code'] in (100,110):
            if b['code']==100:g=b['geom'];mat='runway'
            else:
                g=smooth_pavement(b);surf=int(b['parts'][1])%100
                if surf in (0,3,4,5,13,15):continue
                mat='asphalt' if surf==1 or 20<=surf<40 else 'concrete'
            if g.intersects(crop):paved.setdefault(mat,[]).append(g.intersection(crop))
        if b['code']==120 and b.get('geom') is not None and b['geom'].intersects(crop):
            for line,style in sampled_apt_segments(b):
                code=int(style[0])
                if code>=100:continue
                col='white' if code in (20,21,22,24,25,70,71,72,74,75) else 'red' if code in (19,59) else 'yellow'
                line=line.intersection(crop)
                if not line.is_empty:markings.setdefault(col,[]).append(line.buffer(.11,cap_style=2,join_style=2))
    for mat,gs in paved.items():flat(tag+' native pavement '+mat,unary_union(gs),.005 if mat!='runway' else .015,tag,mat)
    for col,gs in markings.items():flat(tag+' native paint '+col,unary_union(gs),.06,tag,col)
    for i,e in enumerate(d['entities']):
        if e['geom'].is_empty or not e['geom'].intersects(crop):continue
        res=e['resource']
        if res.endswith('.fac'):
            if 'Jetways/' in res:
                for loop in e['loops']:
                    if len(loop)>1:
                        simple_solid(f'{tag} fixed library tunnel {i}',LineString(loop).buffer(1.4,cap_style=2),4.25,7.15,tag,'context')
                        for p in (loop[0],loop[-1]):simple_solid(f'{tag} library tunnel pillar {i}',Point(p).buffer(.45),0,4.25,tag,'context')
            elif any(t in res.lower() for t in ('term_building','term_roof','term_bridge','garage','hangar')) and 'parts/interior' not in res:
                g=e['geom'];h=min(55,max(4,float(e['param'])));z0=max(0,h-3) if 'bridge' in res else 0
                simple_solid(f'{tag} retained massing {i}',g,z0,h,tag,'context')
        elif any(t in res for t in ('DrapedLocSigns.pol','DrapedDirSigns.pol')):
            points=[]
            for l in e['lines']:
                if l.startswith('POLYGON_POINT'):points.append(list(map(float,l.split()[1:])))
            if len(points)==4 and all(len(p)==4 for p in points):
                texture=LIB/'Common_Elements'/('DrapedLocSigns.png' if 'LocSigns' in res else 'DrapedDirSigns.png')
                # Use verified local PNG conversions of stock sign textures.
                texture=ROOT/'work'/('stock-sign-atlas.png' if 'LocSigns' in res else 'stock-dir-atlas.png')
                addmesh(f'{tag} retained ground sign {i}',[(*xy(*p[:2]),.065) for p in points],[(0,1,2),(0,2,3)],tag,'sign',[p[2:] for p in points],str(texture))
    for i,b in enumerate(x for x in a if x['code']==1500):active_jetway(b,tag,i)

# Show the B5 aircraft clearance envelope, not a claimed simulator aircraft.
from layout_plan import heading_vec
_,_,planes=pickle.loads((ROOT/'work/jetways.pkl').read_bytes())
b5=next(r for r in scene['new_stands'] if r['name']=='B5')
p=np.array(b5['pos']);f=heading_vec(b5['heading']);right=np.array([f[1],-f[0]])
corners=[p+right*x+f*y for x,y in [(-2.6,6),(2.6,6),(2.6,-38.5),(-2.6,-38.5)]]
for tag in ('Before','After'):
    flat(tag+' B5 conservative aircraft outline',planes[4].boundary.buffer(.22),.1,tag,'cyan')
    m=nm.Mesh('B5 fuselage clearance cage')
    for a,b in zip(corners,corners[1:]+corners[:1]):
        m.link(a,b,.08,1.55,1.63,'white');m.link(a,b,.08,5.5,5.58,'white')
    for p in corners:m.box(*p,1.55,.08,.08,4.03,'white')
    addmesh(tag+' A321-sized fuselage clearance guide',[v[:3] for v in m.vertices],m.faces,tag,'cyan')

# Actual small AEP glyph meshes explain the remaining old identifiers.
# Assets are read for local previews only and are not copied into this package.
aep=pickle.loads((ROOT/'work/aep.pkl').read_bytes())
excluded={h['index'] for h in json.loads((ROOT/'work/aep-exclusion-audit.json').read_text())}
aeproot=LIVE.parent/'AEP';exports={}
for line in (aeproot/'library.txt').read_text(errors='replace').splitlines():
    s=line.split(None,2)
    if len(s)==3 and s[0].startswith('EXPORT'):exports[s[1]]=s[2].strip()
for i,e in enumerate(aep['entities']):
    if e['kind']!='object' or '/Draped_Signs/Taxi_Small/' not in e['resource'] or not e['geom'].intersects(crop):continue
    path=aeproot/exports[e['resource']];vs=[];uv=[];ix=[];s=e['lines'][0].split();angle=math.radians(float(s[4]));c=math.cos(angle);sn=math.sin(angle);origin=xy(float(s[2]),float(s[3]))
    for line in path.read_text().splitlines():
        r=line.split()
        if not r:continue
        if r[0]=='VT':
            x,y,z=map(float,r[1:4]);vs.append((origin[0]+c*x-sn*z,origin[1]-sn*x-c*z,.085));uv.append(list(map(float,r[7:9])))
        elif r[0] in ('IDX','IDX10'):ix.extend(map(int,r[1:]))
        elif r[0]=='TEXTURE':texture=(path.parent/r[1].replace('\\','/')).resolve()
    if not texture.exists():texture=texture.with_suffix('.dds')
    faces=[(ix[k],ix[k+2],ix[k+1]) for k in range(0,len(ix),3)]
    for tag in ('Before','After'):
        if tag=='After' and i in excluded:continue
        addmesh(f'{tag} old AEP glyph {i}',vs,faces,tag,'sign',uv,str(texture))

with gzip.open(ROOT/'work/native-review-context.json.gz','wt',compresslevel=3) as f:json.dump(out,f,separators=(',',':'))
(ROOT/'work/native-review-inputs.json').write_text(json.dumps({tag:hashlib.sha256((pack/'Earth nav data/apt.dat').read_bytes()).hexdigest() for tag,pack in [('Before',LIVE),('After',STAGE)]},indent=2))
print(json.dumps(dict(mesh_batches=len(out),parked_jetways=animation_counts,triangles=sum(len(x['faces']) for x in out)),indent=2))
