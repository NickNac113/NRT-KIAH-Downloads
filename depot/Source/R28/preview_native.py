"""Extract installed stock art for local preview only. Never copy art to package."""
from common import *
import gzip,re
from functools import lru_cache
from shapely import constrained_delaunay_triangles,make_valid
OUT=[];STATS={};REGION=box(-740,300,110,785)

def texture(path):
    path=Path(path)
    if not path.exists():path=path.with_suffix('.dds')
    return str(path.resolve()) if path.exists() else None

def addmesh(name,verts,faces,tag='R28',mat='context',uvs=None,texture=None,cull=False,lit=None):
    if len(faces):OUT.append(dict(name=name,vertices=np.asarray(verts).tolist(),faces=np.asarray(faces).tolist(),material=mat,uvs=None if uvs is None else np.asarray(uvs).tolist(),texture=texture,lit=lit,cull=cull))

def flat(name,g,z,mat='concrete',tex=None,scale=30):
    g=make_valid(g)
    vs=[];fs=[];uv=[]
    for part in ([g] if g.geom_type=='Polygon' else getattr(g,'geoms',[])):
        if part.geom_type!='Polygon' or part.area<1e-6:continue
        for tri in constrained_delaunay_triangles(part).geoms:
            ps=list(orient(tri,1).exterior.coords)[:3];k=len(vs)
            vs.extend((x,y,z) for x,y in ps);fs.append((k,k+1,k+2));uv.extend((x/scale,y/scale) for x,y in ps)
    addmesh(name,vs,fs,mat=mat,uvs=uv if tex else None,texture=tex)

@lru_cache(None)
def read_fac(path):
    path=Path(path);d=dict(floors=[],objects=[],shaders={},ring=1,no_wall=False,no_roof=False,scale=30)
    shader=None;floor=None;seg=None;mesh=None;wall=None
    for row in path.read_text().splitlines():
        t=row.split('#')[0].split()
        if not t:continue
        op=t[0]
        if op.startswith('SHADER_'):shader=op[7:].lower();d['shaders'][shader]={}
        elif op in ('TEXTURE','TEXTURE_LIT') and shader:d['shaders'][shader][op]=texture(path.parent/t[1].replace('\\','/'))
        elif op=='ROOF_SCALE':d['scale']=float(t[1])
        elif op=='RING':d['ring']=int(t[1])
        elif op=='NO_WALL_MESH':d['no_wall']=True
        elif op=='NO_ROOF_MESH':d['no_roof']=True
        elif op=='OBJ':d['objects'].append(str((path.parent/t[1]).resolve()))
        elif op=='FLOOR':
            floor=dict(name=t[1],heights=[],segments={},walls=[]);d['floors'].append(floor)
        elif op=='ROOF_HEIGHT':floor['heights'].append(float(t[1]))
        elif op in ('SEGMENT','SEGMENT_CURVED'):
            seg=dict(meshes=[],attachments=[])
            if op=='SEGMENT':floor['segments'][int(t[1])]=seg
        elif op=='MESH':mesh=dict(v=[],ix=[]);seg['meshes'].append(mesh)
        elif op=='VERTEX':mesh['v'].append(list(map(float,t[1:9])))
        elif op=='IDX':mesh['ix']+=list(map(int,t[1:]))
        elif op=='ATTACH_GRADED':seg['attachments'].append(list(map(float,t[1:6])))
        elif op=='WALL':wall=dict(name=' '.join(t[5:]),spellings=[]);floor['walls'].append(wall)
        elif op=='SPELLING':wall['spellings'].append(list(map(int,t[1:])))
    for f in d['floors']:
        for seg in f['segments'].values():
            zz=[v[2] for m in seg['meshes'] for v in m['v']]
            seg['length']=max(zz)-min(zz)
    return d

@lru_cache(None)
def read_obj(path):
    path=Path(path);v=[];ix=[];cmd=[];tex=None;lit=None;active_lod=True
    for r in path.read_text(errors='replace').splitlines():
        t=r.split()
        if not t:continue
        if t[0]=='VT':v.append(list(map(float,t[1:9])))
        elif t[0] in ('IDX','IDX10'):ix.extend(map(int,t[1:]))
        elif t[0] in ('TEXTURE','TEXTURE_LIT') and len(t)>1:
            p=texture(path.parent/t[1].replace('\\','/'))
            if t[0]=='TEXTURE':tex=p
            else:lit=p
        elif t[0]=='ATTR_LOD':
            # Additive LOD ranges may both start at zero (fan + AC housing).
            active_lod=float(t[1])<=0<float(t[2])
        elif t[0]=='TRIS' and active_lod:cmd.append(tuple(map(int,t[1:3])))
    ids=[j for start,count in cmd for j in ix[start:start+count]]
    return np.array(v),np.array(ids,dtype=int),tex,lit

def obj(name,path,origin,heading=0,up=0):
    v,ids,tex,lit=read_obj(str(path))
    if not len(ids):return
    a=math.radians(heading);m=np.array([[math.cos(a),math.sin(a)],[-math.sin(a),math.cos(a)]])
    en=v[:,[0,2]]*np.array([1,-1]);en=en@m.T+np.array(origin)
    vs=np.column_stack((en,v[:,1]+up));faces=ids.reshape(-1,3)[:,[0,2,1]]
    addmesh(name,vs,faces,uvs=v[:,6:8],texture=tex,lit=lit,cull=True)

def facade_mesh(item):
    path=EXPORTS[item['resource']];d=read_fac(str(path));floor=min(d['floors'],key=lambda f:abs(max(f['heights'])-item['height']))
    pts=np.array(item['points']);end=np.roll(pts,-1,axis=0) if d['ring'] else pts[1:]
    mat=d['shaders'].get('wall',{})
    for wi,(a,b) in enumerate(zip(pts,end)):
        delta=b-a;length=np.linalg.norm(delta)
        if length<.001:continue
        direction=delta/length;outside=np.array([direction[1],-direction[0]])
        wall=floor['walls'][item['walls'][wi]]
        spellings=wall['spellings']
        choices=[]
        for s in spellings:
            n=sum(floor['segments'][j]['length'] for j in s)
            if n>0:choices.append((abs(math.log(length/n)),s,n))
        longest=max(choices,key=lambda x:x[2])
        if length>longest[2]:
            rep=max(1,round(length/longest[2]))
            choices=[(0,longest[1]*rep,longest[2]*rep)]
        _,spelling,total=min(choices,key=lambda x:x[0]);factor=length/total;offset=0
        for j in spelling:
            seg=floor['segments'][j]
            if not d['no_wall']:
                for k,m in enumerate(seg['meshes']):
                    v=np.array(m['v']);ids=np.array(m['ix']).reshape(-1,3)[:,[0,2,1]]
                    en=a+np.outer((-v[:,2]+offset)*factor,direction)+np.outer(v[:,0],outside)
                    addmesh(item['name']+f' wall {wi}/{j}/{k}',np.column_stack((en,v[:,1])),ids,uvs=v[:,6:8],texture=mat.get('TEXTURE'),lit=mat.get('TEXTURE_LIT'),cull=True)
            for oi,x,y,z,heading in seg['attachments']:
                en=a+direction*((-z+offset)*factor)+outside*x
                rotation=math.degrees(math.atan2(outside[0],outside[1]))+heading
                obj(item['name']+' roof attachment',d['objects'][int(oi)],en,rotation,y)
            offset+=seg['length']
    if d['ring'] and not d['no_roof']:
        roof=d['shaders'].get('roof',{});flat(item['name']+' roof',Polygon(pts),max(floor['heights']),'roof',roof.get('TEXTURE'),d['scale'])
    STATS.setdefault('native_facades',[]).append(dict(name=item['name'],resource=item['resource'],floor=floor['name'],height=max(floor['heights'])))

scope=dict(np=np,math=math,LIB=LIB,xy=ag.xy,addmesh=addmesh,templates={},animation_counts={})
extract_functions('X:/X-Plane 12/Output/KIAH_R03_HF06_Repair/work/prepare_previews.py',{'rotation','trans','lerp','active_jetway'},scope)
segments=extract_functions('X:/X-Plane 12/Output/KIAH_R03_HF02_Repair/work/repair_airport_details.py',{'sampled_apt_segments'},dict(np=np,math=math,LineString=LineString,xy=ag.xy))['sampled_apt_segments']

def main():
    apt=ag.parse_apt(PACK/'Earth nav data/apt.dat');dsf=ag.parse_dsf(ROOT/'qa/R28_Roundtrip.txt')
    flat('Ground',REGION.buffer(400),-.04,'grass')
    covered=Polygon()
    for i,q in enumerate(apt):
        if q['code']!=110:continue
        g=smooth_pavement(q)
        if not g.intersects(REGION):continue
        surface=int(q['parts'][1])%100
        if surface in (0,3,4,5,13,15):continue
        g=g.intersection(REGION);visible=g.difference(covered);covered=covered.union(g)
        flat('Native pavement '+str(i),visible,0,'asphalt' if surface==1 or 20<=surface<40 else 'concrete')
    paint={}
    for q in apt:
        if q['code'] not in (110,120):continue
        for line,styles in segments(q):
            if not line.intersects(REGION):continue
            for st in styles:
                code=int(st)
                if code>=100:continue
                color='white' if code in (20,21,22,24,25,70,71,72,74,75) else 'red' if code in (19,59) else 'yellow'
                geom=line.intersection(REGION)
                if code in (3,53):geom=unary_union([geom.offset_curve(.24),geom.offset_curve(-.24)])
                paint.setdefault(color,[]).append(geom.buffer(.10,cap_style=2,join_style=2))
                if code>=50:paint.setdefault('black',[]).append(geom.buffer(.18,cap_style=2,join_style=2))
    for col,gs in paint.items():flat('Native paint '+col,unary_union(gs),.012 if col=='black' else .022,col)
    for i,q in enumerate(dsf['entities']):
        if q['geom'].is_empty or not q['geom'].intersects(REGION):continue
        res=q['resource']
        if res.endswith('.fac') and res in EXPORTS and '/Terminal_kit/' in res and any(t in res for t in ('term_building','term_bridge','term_roof')):
            p=[list(map(float,r.split()[1:])) for r in q['lines'] if r.startswith('POLYGON_POINT ')]
            f=facade(res,[ag.xy(*r[:2]) for r in p],[int(r[2]) if len(r)>2 else 0 for r in p],float(q['param']),f'{i} '+Path(res).stem)
            facade_mesh(f)
        elif q['kind']=='object':
            path=PACK/res if (PACK/res).exists() else EXPORTS.get(res)
            if path and path.exists():obj(f'{i} '+Path(res).stem,path,q['geom'].coords[0],float(q['coords'][2]))
        elif res.endswith('.pol') and any(s in res for s in ('DrapedLocSigns','DrapedDirSigns')):
            p=[list(map(float,r.split()[1:])) for r in q['lines'] if r.startswith('POLYGON_POINT ')]
            if len(p)==4 and all(len(r)==4 for r in p):
                name='DrapedLocSigns' if 'LocSigns' in res else 'DrapedDirSigns'
                addmesh('Ground sign '+str(i),[(*ag.xy(*r[:2]),.035) for r in p],[(0,1,2),(0,2,3)],uvs=[r[2:] for r in p],texture=texture(LIB/'Common_Elements'/(name+'.png')))
    for i,q in enumerate(apt):
        if q['code']==1500 and REGION.contains(Point(ag.xy(float(q['parts'][2]),float(q['parts'][1])))):scope['active_jetway'](q,'R28',i)
    STATS['jetways']=scope['animation_counts'];STATS['mesh_batches']=len(OUT);STATS['triangles']=sum(len(d['faces']) for d in OUT)
    merged={}
    for d in OUT:
        key=(d['material'],d['texture'],d['lit'],bool(d['uvs']))
        if key not in merged:merged[key]={**d,'vertices':[],'faces':[],'uvs':[] if d['uvs'] else None}
        batch=merged[key];offset=len(batch['vertices']);batch['vertices']+=d['vertices'];batch['faces'] += [[i+offset for i in f] for f in d['faces']]
        if d['uvs']:batch['uvs']+=d['uvs']
    with gzip.open(ROOT/'qa/Preview_Meshes.json.gz','wt',compresslevel=2) as f:json.dump(list(merged.values()),f,separators=(',',':'))
    (ROOT/'qa/Preview_Inputs.json').write_text(json.dumps(STATS,indent=2));print(json.dumps({k:v for k,v in STATS.items() if k!='native_facades'},indent=2))
if __name__=='__main__':main()
