"""R21 private jet center. File-based successor; never installs or modifies R20."""
from pathlib import Path
import ast, hashlib, json, math, re, shutil, subprocess, sys, types
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]; CAMPUS=ROOT.parents[1]
sys.path.insert(0,str(CAMPUS/'tools/python_geometry'))
from shapely import constrained_delaunay_triangles, wkt
from shapely.geometry import Polygon, Point, LineString, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
LEGACY=ROOT.parent/'KIAH_R17_Native_Surface_R13/source'
sys.path.insert(0,str(LEGACY))
import airport_geometry as ag
from materials import material_uv as _material_uv, TILES
OLD=ROOT.parent/'KIAH_R20_Open_Hangars_R16/package/KIAH_NRT_R20_Open_Hangars_R16'
NAME='KIAH_NRT_R21_Jet_Center_R17'; PACK=ROOT/'package'/NAME
OUT=ROOT/'output'; QA=ROOT/'qa'
TOOL=Path('C:/Users/Nick/Documents/Codex/2026-10-24/cou/work/xptools-24-5/tools/DSFTool.exe')
CONCEPT=CAMPUS/'feasibility/KIAH_R21_Jet_Center_Concept_R01'
D=json.loads((CONCEPT/'output/Concept_Measurements.json').read_text())
B=json.loads((OLD/'Build_Evidence.json').read_text())
H=box(*D['hangar']['bounds']); MAIN=box(*D['terminal']['main']); WING=box(*D['terminal']['side_wing']); ROOF=box(*D['canopy']['roof_bounds'])
MEDIAN=box(*D['landside']['median']); COURT=box(*D['landside']['forecourt']); DELIVERY=box(*D['landside']['delivery_bay'])
BUILDINGS=unary_union([H,MAIN,WING]); LAND=box(2692,292,2735,330).union(DELIVERY)
REWORK=unary_union([box(2433,283,2560,434),box(2609,292,2673,402),MAIN,WING,LAND])
SPINE=D['context']['spine_x']
placements=[];meshes=[];uvs={};checks=[];changes=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:raise AssertionError(name)
def run(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p.stdout+p.stderr
def direction(h):return np.array([math.sin(math.radians(h)),math.cos(math.radians(h))])
def vectors(h):f=direction(h);return f,np.array([f[1],-f[0]])
m=types.SimpleNamespace(m=types.SimpleNamespace(vectors=vectors))
def material_uv(c,u,v):return _material_uv(c,u,v) if c in TILES else ((c*64+32)/2048,1-32/2048)
# Reuse the established OBJ8 material/animation writer, without executing legacy builds.
tree=ast.parse((LEGACY/'build_test.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Mesh' or isinstance(n,ast.FunctionDef) and n.name in ['parts','lines']],type_ignores=[]),'R21_mesh_helpers','exec'))
def save(mesh):
    rel=mesh.save();p=PACK/rel;s=p.read_text()
    if mesh.draped:s=s.replace('ATTR_draped','WEATHER_TRANSPARENT\nATTR_draped')
    p.write_text(s);return rel
def block(mesh,b,z0,z1,c,roof=None):mesh.extrude(box(*b),z0,z1,c,c if roof is None else roof)
def rod(mesh,a,b,w=.12,c=3):
    a=np.array(a,float);b=np.array(b,float);v=b-a;v/=np.linalg.norm(v);r=np.cross(v,[0,0,1])
    if np.linalg.norm(r)<.01:r=np.array([1.,0,0])
    r=r/np.linalg.norm(r)*w/2;u=np.cross(v,r);q=[r+u,-r+u,-r-u,r-u]
    for i in range(4):mesh.face([a+q[i],b+q[i],b+q[(i+1)%4],a+q[(i+1)%4]],c)
def sign(mesh,text,x0,x1,y,z,h):
    u0,v0,u1,v1=uvs[text]
    mesh.face([(x0,y,z),(x1,y,z),(x1,y,z+h),(x0,y,z+h)],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
def east_sign(mesh,text,x,cy,z,w,h):
    u0,v0,u1,v1=uvs[text]
    mesh.face([(x,cy-w/2,z),(x,cy+w/2,z),(x,cy+w/2,z+h),(x,cy-w/2,z+h)],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
def dds(path,alpha=False):run([TOOL.with_name('DDSTool.exe'),'--png2dxt5' if alpha else '--png2dxt1',path,path.with_suffix('.dds')])

def make_textures():
    names=['NRT PRIVATE HANGAR','NRT CANOPY','NRT JET CENTER','ARRIVALS','DELIVERIES','NRT']
    im=Image.new('RGBA',(2048,1024),(0,0,0,0));draw=ImageDraw.Draw(im)
    for i,s in enumerate(names):
        y=i*144;draw.rectangle((0,y,2047,y+143),fill=(22,48,58,255))
        fs=100
        while ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs).getlength(s)>1960:fs-=1
        draw.text((1024,y+72),s,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs),anchor='mm',fill=(236,237,224,255))
        uvs[s]=(0,1-(y+144)/1024,1,1-y/1024)
    p=PACK/'textures/nrt_test/r21_identity.png';im.save(p);dds(p,True)
    lit=Image.fromarray((np.asarray(im).astype(float)*np.array([.45,.45,.45,1])).astype('uint8'));p=p.with_name('r21_identity_LIT.png');lit.save(p);dds(p,True)
    ground=Image.new('RGBA',im.size,(0,0,0,0));draw=ImageDraw.Draw(ground)
    for i,s in enumerate(names[:2]):
        y=i*144;draw.rectangle((0,y,2047,y+143),fill=(219,172,35,255))
        draw.text((1024,y+72),s,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',100),anchor='mm',fill=(32,35,31,255))
    p=p.with_name('r21_ground_ids.png');ground.save(p);dds(p,True)
    rng=np.random.default_rng(21);noise=rng.normal(0,4,(512,512,1));soil=np.clip(np.array([78,66,47])[None,None,:]+noise,0,255).astype('uint8')
    p=p.with_name('r21_planting.png');Image.fromarray(soil).save(p);dds(p)

def new_meshes():
    # Roof and walls surround a real empty interior. The old MH3 is not stretched.
    g=Mesh('r21_private_hangar',[2473,359])
    for b in [(2434,284,2435,434),(2434,284,2512,285),(2434,433,2512,434)]:block(g,b,0,18,0)
    for b in [(2510,284,2512,290),(2510,428,2512,434)]:block(g,b,0,18,1)
    block(g,[2510,290,2512,428],14,18,1);block(g,H.bounds,18,18.6,0,10)
    # Clear span trusses. Their lowest points remain above the 14 m door.
    for x in [2440,2462,2484,2507]:
        rod(g,[x,285,16.2],[x,433,16.2],.30)
        for y in np.arange(286,430,8):
            rod(g,[x,y,16.2],[x,y+4,17.9],.14);rod(g,[x,y+4,17.9],[x,y+8,16.2],.14)
    for x in [2447,2470,2493]:
        for y in [310,344,378,412]:block(g,[x-5,y-1.2,x+5,y+1.2],18.61,18.8,2)
    # Sliding multi-leaf doors stack at the two end pockets. 138 m clear when open.
    dr='nrt/kiah/r21/private_hangar/doors_open'
    for side in [-1,1]:
        for j in range(12):
            y0=359+side*j*5.75;y1=359+side*(j+1)*5.75;ya,yb=sorted([y0,y1]);target=(284.01+j*.01) if side<0 else (428.0+j*.01)
            delta=target-ya
            commands=['ANIM_trans_begin '+dr,'ANIM_trans_key 0 0 0 0',f'ANIM_trans_key 1 {-j*.10:.4f} 0 {-delta:.4f}','ANIM_trans_end']
            def panel(ya=ya,yb=yb):
                block(g,[2510.8,ya,2511.05,yb],.05,13.98,8)
                block(g,[2511.055,ya+.1,2511.09,yb-.1],5.5,7,2)
            g.animated(commands,panel)
    for y in [300,328,356,384,412]:
        g.flood(2508,y,16,0,0,9000)
    save(g)

    g=Mesh('r21_terminal_canopy',[2674,330])
    for b in [MAIN,WING]:
        # Weathered cladding on service face, glazed arrival and apron elevations.
        x0,y0,x1,y1=b.bounds;block(g,b.bounds,0,9.3,2);block(g,[x0-.8,y0-.8,x1+.8,y1+.8],9.3,10,0,10)
        for y in np.arange(y0,y1,4):block(g,[x0-.08,y,x0+.12,y+.16],0,9.3,1)
        for x in np.arange(x0,x1,4):block(g,[x,y0-.08,x+.16,y0+.12],0,9.3,1)
        block(g,[x0-.09,y0,x0+.13,y1],4.5,4.7,1);block(g,[x0,y0-.1,x1,y0+.13],4.5,4.7,1)
    for b in D['canopy']['columns']:block(g,b,0,15.8,1)
    for b in [[2620,292,2674,294],[2620,346,2674,348],[2620,294,2621.2,346],[2672.8,294,2674,346]]:block(g,b,14,16.1,1)
    block(g,ROOF.bounds,16.1,16.8,0,10)
    for x in [2628,2641,2654,2667]:
        rod(g,[x,294,14.1],[x,346,14.1],.18)
        for y in range(294,344,4):rod(g,[x,y,14.1],[x,y+2,15.9],.09);rod(g,[x,y+2,15.9],[x,y+4,14.1],.09)
    for x in [2630,2650,2668]:
        for y in [302,320,338]:g.flood(x,y,15.0,0,0,6500)
    block(g,[2696,324.2,2724,330.1],4.8,5.15,0,10)
    for x in [2697,2723]:block(g,[x-.12,327.8,x+.12,328.05],.15,4.8,1)
    for x in [2700,2710,2720]:g.flood(x,328,4.55,0,0,700)
    block(g,[2706,329.65,2710,329.85],.15,3.2,2)
    for x in [2706,2708,2710]:rod(g,[x,329.6,.15],[x,329.6,3.2],.07,3)
    save(g)

    g=Mesh('r21_arrival_landscape',[2711,312.5])
    # Native asphalt stays at ground level; only curbs and footways are raised.
    curb=MEDIAN.difference(MEDIAN.buffer(-.3));g.extrude(curb,.02,.20,0,0)
    soil=MEDIAN.buffer(-.3);g.extrude(soil,.02,.17,3)
    walkway=unary_union([box(2692,292,2694,330),box(2692,327.3,2725,330)])
    # Level gap at the entry provides a flush route from the car-park crossing.
    walkway=walkway.difference(box(2721.5,327.3,2725,329.5))
    g.extrude(walkway,.02,.15,0,11)
    for x in [2698,2702,2716,2721]:
        block(g,[x-.10,328.6,x+.10,328.8],.15,1.1,1);g.flood(x,328.7,.98,0,0,45)
    # An original 9 m flag pole avoids the 20 m stock pole beside aircraft facilities.
    fx,fy=D['landside']['flagpole'];rod(g,[fx,fy,.2],[fx,fy,9],.10,3)
    block(g,[fx-.30,fy-.30,fx+.30,fy+.30],.15,.26,0)
    # Benches on the median, clear of the pedestrian and driving lanes.
    for y in [309,316.5]:
        block(g,[2706,y-.3,2708,y+.3],.48,.58,1)
        block(g,[2706,y+.25,2708,y+.35],.5,1.15,1)
        for x in [2706.2,2707.8]:block(g,[x-.08,y-.22,x+.08,y+.22],.2,.48,3)
    save(g)

    g=Mesh('r21_planting_bed',[2711,312.5]);g.detailed=False;g.texture='r21_planting.png';g.normal=None
    x0,y0,x1,y1=soil.bounds;g.face([(x0,y0,.17),(x1,y0,.17),(x1,y1,.17),(x0,y1,.17)],uv=[(0,0),(1,0),(1,1),(0,1)]);save(g)

    g=Mesh('r21_identity',[2674,330]);g.detailed=False;g.texture='r21_identity.png';g.lit='r21_identity_LIT.dds';g.luminance=40;g.normal=None
    sign(g,'NRT JET CENTER',2697,2723,329.78,6.7,1.6)
    sign(g,'ARRIVALS',2702,2718,324.15,4.86,.25)
    east_sign(g,'NRT PRIVATE HANGAR',2512.08,359,15.1,28,1.9)
    # Label the flag on both sides, using the same brand artwork, never the old name.
    u0,v0,u1,v1=uvs['NRT'];fx,fy=D['landside']['flagpole']
    for reverse in [False,True]:
        q=[(fx,fy,7.3),(fx+2.8,fy+.18,7.1),(fx+2.8,fy+.18,8.5),(fx,fy,8.8)]
        uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
        g.face(q[::-1] if reverse else q,uv=uv[::-1] if reverse else uv)
    save(g)

    g=Mesh('r21_arrival_paint',[2711,312.5],True)
    # White edge lines, delivery envelope, pedestrian crossing, and loop direction arrows.
    g.flat(DELIVERY.boundary.buffer(.07),0,5)
    for y in np.arange(320.5,327,.8):g.flat(box(2727,y,2732,y+.35),0,5)
    for x,y,h in [(2720,301,270),(2700,315,0),(2714,323.5,90)]:
        f,r=vectors(h);c=np.array([x,y]);pts=[c+f*a+r*b for a,b in [(-2,-.10),(.5,-.10),(.5,-.7),(2,0),(.5,.7),(.5,.10),(-2,.10)]];g.flat(Polygon(pts),0,5)
    for y in [294,331.8]:g.flat(LineString([(2736,y),(2765,y)]).buffer(.06),0,5)
    save(g)
    g=Mesh('r21_stand_ids',[2674,330],True);g.texture='r21_ground_ids.png';g.normal=None
    for label,c,h in [('NRT PRIVATE HANGAR',[2542,359],90),('NRT CANOPY',[2613,320],270)]:g.label(label,c,16,2.1,heading=h)
    save(g)

def cut_obj(rel,region):
    """Clip static OBJ triangles in EN and preserve interpolated UVs and normals."""
    p=PACK/rel;rows=p.read_text().splitlines()
    check(rel+': static clipping only',not any(s.startswith('ANIM_') for s in rows))
    vs=np.array([list(map(float,s.split()[1:])) for s in rows if s.startswith('VT ')])
    ids=[int(a) for s in rows if s.startswith(('IDX ','IDX10 ')) for a in s.split()[1:]]
    origin=next(q['origin'] for q in B['placements'] if q['resource']==rel);new=[];removed=0
    for i in range(0,len(ids),3):
        vv=vs[ids[i:i+3]];en=np.column_stack([vv[:,0]+origin[0],origin[1]-vv[:,2]]);poly=Polygon(en)
        if poly.area<1e-10:
            if not region.intersects(LineString(en)):new.extend(vv);continue
            check(rel+': vertical clipping region is rectangular',region.equals(box(*region.bounds)))
            x0,y0,x1,y1=region.bounds;pending=list(vv);outside=[]
            # Preserve the fence below the new opening, even when one large triangle spans both.
            for axis,edge,sgn in [(0,x0-origin[0],1),(0,x1-origin[0],-1),(2,origin[1]-y1,1),(2,origin[1]-y0,-1)]:
                inside=[];out=[]
                for a,b in zip(pending,pending[1:]+pending[:1]):
                    da=(a[axis]-edge)*sgn;db=(b[axis]-edge)*sgn
                    (inside if da>=0 else out).append(a)
                    if (da>=0)!=(db>=0):v=a+(b-a)*da/(da-db);inside.append(v);out.append(v)
                if len(out)>=3:outside.append(out)
                pending=inside
                if len(pending)<3:break
            for q in outside:
                for j in range(1,len(q)-1):new.extend([q[0],q[j],q[j+1]])
            if len(pending)>=3:removed+=1
            continue
        cut=poly.difference(region)
        if abs(cut.area-poly.area)<1e-8:new.extend(vv);continue
        removed+=1
        mat=np.vstack([en.T,np.ones(3)])
        for piece in parts(cut):
            for tri in constrained_delaunay_triangles(piece).geoms:
                coords=list(tri.exterior.coords)[:-1]
                if np.cross(np.array(coords[1])-coords[0],np.array(coords[2])-coords[0])*np.cross(en[1]-en[0],en[2]-en[0])<0:coords.reverse()
                for x,y in coords:new.append(np.linalg.solve(mat,[x,y,1])@vv)
    header=[s for s in rows if not s.startswith(('VT ','IDX ','IDX10 ','POINT_COUNTS','TRIS '))]
    at=next((i for i,s in enumerate(header) if s.startswith('ATTR_')),len(header));payload=[f'POINT_COUNTS {len(new)} 0 0 {len(new)}']
    payload+=['VT '+' '.join(f'{v:.6f}' for v in q) for q in new]
    for i in range(0,len(new),10):
        ii=list(range(i,min(i+10,len(new))));payload+=['IDX10 '+' '.join(map(str,ii))] if len(ii)==10 else ['IDX '+str(j) for j in ii]
    p.write_text('\n'.join(header[:at]+payload+header[at:]+[f'TRIS 0 {len(new)}'])+'\n')
    changes.append(dict(resource=rel,triangles_clipped=removed))

def update_apt():
    blocks=ag.parse_apt(OLD/'Earth nav data/apt.dat');out=[];removed=[]
    retired={'NRT11','NRT12','NRT MH3','NRT MX OPEN'}
    for q in blocks:
        if q['code']==1300 and q['name'] in retired:removed.append(q['name']);continue
        if q['code']==120 and 'NRT' in q['lines'][0]:
            bb=q['geom'].bounds
            if (bb[0]>2600 and bb[2]<2670 and bb[3]<403) or (bb[0]>2450 and bb[2]<2561 and abs(bb[1]-407)<.1):continue
        out+=q['lines']
    check('Exactly four obsolete NRT starts removed',set(removed)==retired)
    out=[s for s in out if s.strip()!='99']
    for n,s in [('NRT PRIVATE HANGAR',D['hangar']['start']),('NRT CANOPY',D['canopy']['start'])]:
        lo,la=ag.ll(*s['ng']);out += [f'1300 {la:.9f} {lo:.9f} {s["heading"]:.5f} hangar jets {n}','1301 C general_aviation']
    for name,points in [('Private hangar detached guidance',[(2489.75,359),(2558,359)]),('Canopy detached guidance',[(2613,320),(2630.25,320)]),('Spine south extension',[(SPINE,321.87),(SPINE,291)])]:
        out.append('120 NRT R21 '+name)
        for i,(x,y) in enumerate(points):
            lo,la=ag.ll(x,y);out.append(f'{115 if i==len(points)-1 else 111} {la:.9f} {lo:.9f} 1')
    out.append('99');(PACK/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n')
    return removed

def update_xml():
    for filename in ['sam.xml','opensam.xml']:
        tree=ET.parse(OLD/filename);root=tree.getroot();root.set('name','NRT KIAH R21 Jet Center')
        for ref in root.findall('datarefs/dataref'):
            if 'mh3/' in ref.get('name',''):
                ref.set('name','nrt/kiah/r21/private_hangar/doors_open');ref.findall('animation')[1].set('t','60')
        for item in root.findall('objects/instance'):
            if item.get('id')=='mh3':
                lo,la=ag.ll(2473,359);item.set('id','private_hangar');item.set('longitude',f'{lo:.9f}');item.set('latitude',f'{la:.9f}')
        for item in root.findall('gui/checkbox'):
            if item.get('instance')=='mh3':item.set('instance','private_hangar');item.set('label','Close NRT Private Hangar');item.set('title','Close sliding hangar doors');item.set('dataref','nrt/kiah/r21/private_hangar/doors_open')
        ET.indent(tree);tree.write(PACK/filename,encoding='utf-8',xml_declaration=True)
        check(filename+': open by default and manual controls retained',all([a.get('v') for a in r.findall('animation')]==['1','0'] and r.get('autoplay')=='false' for r in root.findall('datarefs/dataref')))

def update_dsf():
    source=ROOT/'reference/R20_South.txt';data=ag.parse_dsf(source);raw=source.read_text();objdefs=data['objects'];polydefs=data['polygons'];defs=[];commands=[];retired=[]
    def polylines(resource,g,param=0):
        if resource not in polydefs:polydefs.append(resource);defs.append('POLYGON_DEF '+resource)
        ans=[]
        for p in parts(g):
            if p.area<.001:continue
            p=orient(p,1);ans.append(f'BEGIN_POLYGON {polydefs.index(resource)} {param} 2')
            for ring in [p.exterior,*p.interiors]:
                ans.append('BEGIN_WINDING')
                for x,y in list(ring.coords)[:-1]:lo,la=ag.ll(x,y);ans.append(f'POLYGON_POINT {lo:.9f} {la:.9f}')
                ans.append('END_WINDING')
            ans.append('END_POLYGON')
        return ans
    deleted={'objects/nrt_test/'+n+'.obj' for n in ['mh3_accordion_hangar','floor_wear_mh3','signs_mh3_accordion_hangar']}
    for q in data['entities']:
        r=q['resource'];remove=r in deleted
        if q['kind']=='object' and r.startswith('lib/'):
            if BUILDINGS.buffer(1).contains(q['geom']) or LAND.contains(q['geom']):remove=True
            if r.endswith('grunge_size_C.obj') and box(2609,292,2673,403).contains(q['geom']):remove=True
        if remove:raw=raw.replace('\n'.join(q['lines']),'');retired.append(dict(resource=r,bounds=list(q['geom'].bounds)));continue
        if q['kind']=='polygon' and '/pavement/' in r and q['geom'].intersects(BUILDINGS.union(LAND)):
            replacement=polylines(r,q['geom'].difference(BUILDINGS.union(LAND)))
            raw=raw.replace('\n'.join(q['lines']),'\n'.join(replacement))
    # Close the former hangar pavement holes by using the new interior footprint.
    commands+=polylines('lib/airport/ground/pavement/concrete_L/dirty.pol',H)
    commands+=polylines('lib/airport/ground/pavement/asphalt_D3/worn.pol',LAND.difference(MEDIAN))
    for item in placements:
        r=item['resource']
        if r not in objdefs:objdefs.append(r);defs.append('OBJECT_DEF '+r)
        lo,la=ag.ll(*item['origin']);commands.append(f'OBJECT {objdefs.index(r)} {lo:.9f} {la:.9f} 0')
    # Point-mode native vegetation with explicit height: one 7 m feature tree.
    for resource,pts in [('lib/vegetation/trees/deciduous/oak_medium.for',[(2711,312.5,7)]),('lib/vegetation/trees/deciduous/shrubs_small.for',[(2706,308,1),(2706,317,1),(2716,317,1)])]:
        if resource not in polydefs:polydefs.append(resource);defs.append('POLYGON_DEF '+resource)
        commands += [f'BEGIN_POLYGON {polydefs.index(resource)} 767 3','BEGIN_WINDING']
        for x,y,h in pts:lo,la=ag.ll(x,y);commands.append(f'POLYGON_POINT {lo:.9f} {la:.9f} {h}')
        commands += ['END_WINDING','END_POLYGON']
    # Rerouted security edge joins the actual R20 west car-park fence at x2720.
    fence='lib/airport/Common_Elements/Fence_Facades/Fence.fac'
    commands += [f'BEGIN_POLYGON {polydefs.index(fence)} 3 2','BEGIN_WINDING']
    for x,y in [(2692,292),(2720,292)]:lo,la=ag.ll(x,y);commands.append(f'POLYGON_POINT {lo:.9f} {la:.9f}')
    commands += ['END_WINDING','END_POLYGON']
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(commands)+'\n'
    src=QA/'R21_South.txt';src.write_text(raw)
    dst=PACK/'Earth nav data/+20-100/+29-096.dsf';(QA/'Compile.txt').write_text(run([TOOL,'--text2dsf',src,dst]))
    roundtrip=QA/'R21_Roundtrip.txt';(QA/'Decompile.txt').write_text(run([TOOL,'--dsf2text',dst,roundtrip]))
    return retired

def main():
    for d in [OUT,QA,ROOT/'reference']:d.mkdir(parents=True,exist_ok=True)
    check('New revision directory has no prior completed package',not PACK.exists())
    oldhash={p.relative_to(OLD).as_posix():sha(p) for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    (ROOT/'reference/R20_Hashes.json').write_text(json.dumps(oldhash,indent=2))
    for d in ['Earth nav data','objects','textures']:shutil.copytree(OLD/d,PACK/d)
    for n in ['COPYING','Gateway-original-README.txt','sam.xml','opensam.xml','Garage_Provenance.json']:shutil.copy2(OLD/n,PACK/n)
    make_textures();new_meshes()
    for rel in ['paint','ramp_safety','ramp_wear','taxi_wear']:
        cut_obj('objects/nrt_test/'+rel+'.obj',REWORK)
    for rel in ['landside_fence','landside_paint','landside_stencils','landside_curbs']:
        cut_obj('objects/nrt_test/'+rel+'.obj',box(2691,291.9,2735,334))
    removed=update_apt();update_xml();retired=update_dsf()
    check('R20 source preserved',all(sha(OLD/k)==v for k,v in oldhash.items()))
    check('North airport tile unchanged',sha(OLD/'Earth nav data/+30-100/+30-096.dsf')==sha(PACK/'Earth nav data/+30-100/+30-096.dsf'))
    for obj in ['mx_stepped_hangar','mh2_accordion_hangar','fbo','fbo_ground_tower','fixed_8','fixed_9A','fixed_9B']:
        rel='objects/nrt_test/'+obj+'.obj';check(obj+' retained exactly',sha(OLD/rel)==sha(PACK/rel))
    B.update(name=NAME,layout='R21',revision='R17',jet_center=D,new_placements=placements,retired_starts=removed,retired_dsf_entities=retired,clipped_objects=changes,runtime_tested=False)
    (PACK/'Build_Evidence.json').write_text(json.dumps(B,indent=2));(OUT/'Build_Checks.json').write_text(json.dumps(dict(checks=checks,passed=len(checks),runtime_tested=False),indent=2))
    (PACK/'PERSONAL_TEST_ONLY.txt').write_text('R21 local personal test. Includes the previously approved T02 garage adaptation. Its source provenance marks it not redistributable. Do not publish this package to members until that asset is replaced or cleared.\n')
    (OUT/'Package_Hashes.json').write_text(json.dumps({p.relative_to(PACK).as_posix():sha(p) for p in PACK.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(dict(package=str(PACK),checks=len(checks),new_objects=len(placements),clipped=changes),indent=2))
if __name__=='__main__':main()
