"""R23 isolated successor. Native X-Plane surfaces, service routes and OpenSAM DGS.
Does not install, launch a simulator, or alter any predecessor.
"""
from pathlib import Path
import importlib.util, json, math, re, shutil, sys, hashlib, xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r21',ROOT.parent/'KIAH_R21_Jet_Center_R17/source/build_r21.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
np=g.np; Image=g.Image; ImageDraw=g.ImageDraw; ImageFont=g.ImageFont
box=g.box;Point=g.Point;Polygon=g.Polygon;LineString=g.LineString;union=g.unary_union
OLDROOT=ROOT.parent/'KIAH_R22_Original_Garage_R18';OLD=OLDROOT/'package/KIAH_NRT_R22_Original_Garage_R18'
NAME='KIAH_NRT_R23_Jet_Center_Refinement_R19';PACK=ROOT/'package'/NAME;OUT=ROOT/'output';QA=ROOT/'qa'
g.PACK=PACK;g.OUT=OUT;g.QA=QA;g.placements=[];g.meshes=[];g.changes=[];g.checks=[]
BASE=json.loads((OLD/'Build_Evidence.json').read_text())
PLACES=json.loads((QA/'R22_Placements.json').read_text());g.B={'placements':list(PLACES.values())}
FBO=box(2724.61,333.92,2881.97,419.39)
FOOT=union([g.MAIN,g.WING,FBO]);CANOPY=box(2620,292,2674,348)
NG=[2648.,303.];HEAD=180.;DOOR=[2673.7,303.86];HELI=[2675.,480.]
CLEAN=union([box(2512,278,2562,441),box(2600,275,2692,444),box(2649,454,2701,506)])
COLS=[box(x-.65,y-.65,x+.65,y+.65) for x in [2622,2672] for y in [294,346]]
retired=[];native=[];surfaces=[];details=[]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    for p in [OUT,QA,PACK/'objects/nrt_test',PACK/'textures/nrt_test']:p.mkdir(parents=True,exist_ok=True)
    # Re-running a candidate restores its inputs, never a sealed predecessor.
    if (ROOT/'NRT_KIAH_R23_Test.zip').exists():raise RuntimeError('Sealed delivery exists; create a successor')
    for p in OLD.rglob('*'):
        if p.is_file():
            q=PACK/p.relative_to(OLD);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    (ROOT/'reference/R22_Hashes.json').write_text(json.dumps({p.relative_to(OLD).as_posix():sha(p) for p in OLD.rglob('*') if p.is_file()},indent=2))

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
    tex=PACK/'textures/nrt_test';im.save(tex/'r23_materials.png');nm.save(tex/'r23_materials_NML.png');lit.save(tex/'r23_materials_LIT.png')
    for name in ['r23_materials','r23_materials_LIT']:g.dds(tex/(name+'.png'))
    def uv(c,u,v):
        c={10:4,11:6}.get(c,c%8)
        return ((c%4*512+1+u*510)/2048,1-(c//4*512+1+(1-v)*510)/1024)
    g.material_uv=uv
    names=['NRT PRIVATE HANGAR','NRT CANOPY','NRT10','NRT JET CENTER','ARRIVALS','PRIVATE AVIATION','NRT']
    for ground in [False,True]:
        a=Image.new('RGBA',(2048,1024),(0,0,0,0));d=ImageDraw.Draw(a)
        for i,text in enumerate(names):
            y=i*144;d.rectangle((0,y,2047,y+143),fill=(220,172,36,255) if ground else (25,51,57,255))
            size=100
            while ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size).getlength(text)>1920:size-=1
            d.text((1024,y+72),text,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size),anchor='mm',fill=(25,30,27,255) if ground else (238,236,224,255))
            g.uvs[text]=(0,1-(y+144)/1024,1,1-y/1024)
        stem='r23_ground_ids' if ground else 'r23_identity';a.save(tex/(stem+'.png'));g.dds(tex/(stem+'.png'),True)
        if not ground:
            Image.fromarray((np.asarray(a)*np.array([.4,.4,.4,1])).astype('uint8')).save(tex/(stem+'_LIT.png'));g.dds(tex/(stem+'_LIT.png'),True)

def save(m):
    rel=g.save(m)
    if m.detailed:
        p=PACK/rel;p.write_text(p.read_text().replace('buildings.dds','r23_materials.dds').replace('buildings_NML.png','r23_materials_NML.png').replace('buildings_LIT.dds','r23_materials_LIT.dds'))
    return rel

def model():
    m=g.Mesh('r23_jet_center',[2674,330])
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
    g.block(m,[2673.60,301.7,2673.78,306.1],.16,3.65,1)
    for ya,yb in [(301.9,303.76),(303.96,305.9)]:
        g.block(m,[2673.54,ya,2673.60,yb],.26,3.45,2)
        g.rod(m,[2673.49,(ya+yb)/2,1.1],[2673.49,(ya+yb)/2,1.75],.045,5)
    # Paver threshold is outside the maximum wing envelope and has no raised kerb across the boarding path.
    m.extrude(box(2668.5,300.8,2674,307.2),.005,.035,6,6)
    g.block(m,[2670.2,300.7,2674,307.3],4.4,4.65,1,0)
    for y in [300.7,307.3]:g.block(m,[2673.5,y-.15,2674,y+.15],.1,7.5,5)
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
    for y in [301.4,306.4]:m.flood(2673.2,y,4.1,-.1,0,400)
    # Landside entrance uses the same canopy edges, stone plinth and bronze soffit.
    g.block(m,[2696,324.2,2724,330.1],4.8,5.15,1,0)
    m.face([(2696,324.2,4.78),(2696,330.1,4.78),(2724,330.1,4.78),(2724,324.2,4.78)],5)
    for x in [2697,2723]:g.block(m,[x-.12,327.8,x+.12,328.05],.15,4.8,1)
    for x in [2706,2708,2710]:g.rod(m,[x,329.58,.15],[x,329.58,3.4],.09,5)
    for x in [2700,2710,2720]:m.flood(x,328,4.5,0,0,650)
    # Shallow repeated solar shades make the old terminal read as part of the new wing.
    for x in np.arange(2732,2880,12):g.block(m,[x,333.65,x+.18,333.93],.8,7.4,5)
    save(m)
    m=g.Mesh('r23_identity',[2674,330]);m.detailed=False;m.texture='r23_identity.png';m.normal=None;m.lit='r23_identity_LIT.dds';m.luminance=25
    g.sign(m,'NRT JET CENTER',2697,2723,329.78,7.7,1.2)
    g.sign(m,'ARRIVALS',2702,2718,324.15,4.86,.25)
    g.east_sign(m,'NRT PRIVATE HANGAR',2512.08,359,15.1,28,1.9)
    # West-facing sign: reverse its horizontal physical axis to avoid mirrored lettering.
    u0,v0,u1,v1=g.uvs['PRIVATE AVIATION'];m.face([(2673.52,312,7.7),(2673.52,298,7.7),(2673.52,298,8.65),(2673.52,312,8.65)],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    g.sign(m,'NRT JET CENTER',2801,2824,333.78,7.8,1.2)
    fx,fy=g.D['landside']['flagpole'];u0,v0,u1,v1=g.uvs['NRT']
    m.face([(fx,fy,7.3),(fx+2.8,fy+.18,7.1),(fx+2.8,fy+.18,8.5),(fx,fy,8.8)],uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    save(m)
    m=g.Mesh('r23_ground_ids',[2674,330],True);m.texture='r23_ground_ids.png';m.normal=None
    for text,c,w,h in [('NRT PRIVATE HANGAR',[2542,359],16,270),('NRT CANOPY',[2648,377],12,180),('NRT10',[2675,457.5],9,0)]:m.label(text,c,w,2.0,heading=h)
    save(m)
    m=g.Mesh('r23_ramp_details',[2674,330],True)
    m.flat(box(2652,457,2698,503).boundary.buffer(.065,cap_style=2,join_style=2),0,5)
    # Stop bar, unobstructed pedestrian path and small passenger walk boundary, no aircraft-type labels.
    m.flat(LineString([(2646,303),(2650,303)]).buffer(.10,cap_style=2),0,4)
    for y in [301.5,306.2]:m.flat(LineString([(2653.8,y),(2668.5,y)]).buffer(.04,cap_style=2),0,5)
    save(m)

def clean():
    for name in ['paint','ramp_safety','ramp_wear','taxi_wear']:
        g.cut_obj('objects/nrt_test/'+name+'.obj',CLEAN)
    # Remove complete old fence spans instead of clipping long faces halfway through the arrival court.
    g.cut_obj('objects/nrt_test/landside_fence.obj',box(2680,275,2742,343))

def arc(cx,cy,r,a,b,n=12):return [(cx+r*math.cos(t),cy+r*math.sin(t)) for t in np.linspace(math.radians(a),math.radians(b),n)]

VEHICLE=[(2724,300),(2706,300)]+arc(2706,306,6,-90,-180)[1:]+[(2700,317)]+arc(2706,317,6,180,90)[1:]+[(2724,323)]+arc(2724,317,6,90,0)[1:]+[(2730,310),(2730,306)]+arc(2724,306,6,0,-90)[1:]
APPROACH=[(g.SPINE,450)]+arc(g.SPINE+30,450,30,180,270)[1:]+[(2618,420)]+arc(2618,390,30,90,0)[1:]+[(2648,303)]

def apt():
    out=[];blocks=g.ag.parse_apt(OLD/'Earth nav data/apt.dat')
    for q in blocks:
        if q['code']==102 and q['parts'][1]=='NRT10B':continue
        if q['code']==102 and q['parts'][1]=='NRT10A':
            # Use a conventional unique helipad designator; the user-facing ramp name stays NRT10.
            out += [l.replace('102 NRT10A ','102 H2 ') for l in q['lines']];continue
        if q['code']==1300 and q['name'] in ['NRT10B','NRT CANOPY']:continue
        if q['code']==120 and 'Canopy detached guidance' in q['lines'][0]:continue
        out += [l.replace('NRT10A','NRT10') for l in q['lines'] if l.strip()!='99']
    lo,la=g.ag.ll(*NG);out += [f'1300 {la:.9f} {lo:.9f} 180.0 gate jets NRT CANOPY','1301 C general_aviation']
    out+=['120 NRT R23 canopy detached side-entry guidance']
    for i,(x,y) in enumerate([(2648,376),(2648,303)]):
        lo,la=g.ag.ll(x,y);out.append(f'{111 if i==0 else 115} {la:.9f} {lo:.9f}'+(' 51' if i==0 else ''))
    # A closed one-way native crew-car circuit, kept on the landside of the terminal.
    max_id=max(q['id'] for q in blocks if q['code']==1201);first=max_id+1
    path=VEHICLE[:-1] if np.linalg.norm(np.array(VEHICLE[0])-VEHICLE[-1])<.01 else VEHICLE
    out+=['1200']
    for i,(x,y) in enumerate(path):
        lo,la=g.ag.ll(x,y);out.append(f'1201 {la:.9f} {lo:.9f} both {first+i} NRT arrival {i}')
    for i in range(len(path)):out.append(f'1206 {first+i} {first+(i+1)%len(path)} oneway NRT arrivals')
    # The car starts in the existing parking-lot aisle and joins the loop via one short spur.
    spur=first+len(path);lo,la=g.ag.ll(2744,310)
    out += [f'1201 {la:.9f} {lo:.9f} both {spur} NRT car park',f'1206 {first+path.index((2730,310))} {spur} twoway NRT car park']
    for code,x,y,h,name in [(1400,2744,310,270,'NRT arrival car'),(1401,2711,323,90,'NRT terminal curb')]:
        lo,la=g.ag.ll(x,y);out.append(f'{code} {la:.9f} {lo:.9f} {h} crew_car'+(' 0' if code==1400 else '')+' '+name)
    out.append('99');(PACK/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n')
    for f in ['sam.xml','opensam.xml']:
        t=ET.parse(OLD/f);t.getroot().set('name','NRT KIAH R23 Jet Center');ET.indent(t);t.write(PACK/f,encoding='utf-8',xml_declaration=True)

def dsf():
    src=OLDROOT/'qa/R22_Roundtrip.txt';data=g.ag.parse_dsf(src);raw=src.read_text();objects=list(data['objects']);polygons=list(data['polygons']);defs=[];cmd=[]
    def definition(r,obj=False):
        array=objects if obj else polygons
        if r not in array:array.append(r);defs.append(('OBJECT_DEF ' if obj else 'POLYGON_DEF ')+r)
        return array.index(r)
    def poly(r,geom,param=0):
        rows=[];idx=definition(r)
        for p in g.parts(geom):
            if p.area<.001:continue
            p=g.orient(p,1);rows += [f'BEGIN_POLYGON {idx} {param} 2']
            for ring in [p.exterior,*p.interiors]:
                rows+=['BEGIN_WINDING']
                for x,y in list(ring.coords)[:-1]:lo,la=g.ag.ll(x,y);rows += [f'POLYGON_POINT {lo:.9f} {la:.9f}']
                rows+=['END_WINDING']
            rows+=['END_POLYGON']
        return rows
    def line(r,points,param=0):
        rows=[f'BEGIN_POLYGON {definition(r)} {param} 2','BEGIN_WINDING']
        for x,y in points:lo,la=g.ag.ll(x,y);rows += [f'POLYGON_POINT {lo:.9f} {la:.9f}']
        rows+=['END_WINDING','END_POLYGON'];return rows
    def obj(r,x,y,h=0):
        lo,la=g.ag.ll(x,y);cmd.append(f'OBJECT {definition(r,True)} {lo:.9f} {la:.9f} {h}');native.append(dict(resource=r,origin=[x,y],heading=h))
    removed={'objects/nrt_test/'+n+'.obj' for n in ['fbo','signs_fbo','r21_terminal_canopy','r21_identity','r21_stand_ids']}
    # Exactly replace the old pad-hole and the canopy surface with native weather-aware materials.
    paving=union([box(2665,399,2705,439),box(2620,292,2674,376)])
    for q in data['entities']:
        r=q['resource'];erase=r in removed
        if q['kind']=='object' and r.startswith(('lib/','MisterX_')):
            if FOOT.buffer(.2).contains(q['geom']) and not 'mast' in r.lower():erase=True
            if ('grunge' in r or 'taxiway_dirt' in r) and box(2600,275,2692,444).contains(q['geom']):erase=True
        if q['kind']=='polygon' and r.endswith('.fac') and 'Fence' in r:
            # R21 added a court fence plus a campus boundary that cut the passenger arrival.
            if box(2680,277,2742,343).intersects(q['geom']) and q['geom'].bounds[1]>277:erase=True
        if erase:
            raw=raw.replace('\n'.join(q['lines']),'');retired.append(dict(resource=r,bounds=list(q['geom'].bounds)));continue
        if q['kind']=='polygon' and '/pavement/' in r and q['geom'].intersects(paving.union(FOOT)):
            raw=raw.replace('\n'.join(q['lines']),'\n'.join(poly(r,q['geom'].difference(paving.union(FOOT)))))
    cmd+=poly('lib/airport/ground/pavement/concrete_L/worn.pol',paving.difference(FOOT))
    surfaces.append(dict(resource='lib/airport/ground/pavement/concrete_L/worn.pol',wkt=paving.difference(FOOT).wkt))
    # Small material variation, physical-size native seams and grated drainage beside the passenger wing.
    for x in [2632,2644,2656,2668]:cmd+=line('lib/airport/ground/pavement_FX/seams/concrete.lin',[(x,293),(x,347)])
    cmd+=line('lib/airport/ground/pavement_FX/drains/drain_1.lin',[(2673.1,309),(2673.1,329)])
    obj('openSAM/dgs/marshaller.agp',2648,286,0)
    # Public car court fence joins the terminal at its south wall, not across the entrance.
    cmd+=line('lib/airport/Common_Elements/Fence_Facades/Fence.fac',[(2692,276.6),(2692,291.9)],3)
    # Keep delivery parking separate from the one-way passenger route.
    obj('lib/airport/Ramp_Equipment/GPU_1.obj',2700,380,180)
    for p in g.placements:obj(p['resource'],*p['origin'],p['heading'])
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(cmd)+'\n'
    source=QA/'R23_South.txt';source.write_text(raw);dst=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile.txt').write_text(g.run([g.TOOL,'--text2dsf',source,dst]));(QA/'Decompile.txt').write_text(g.run([g.TOOL,'--dsf2text',dst,QA/'R23_Roundtrip.txt']))

def main():
    prepare();materials();model();clean();apt();dsf()
    evidence=dict(BASE);evidence.update(name=NAME,layout='R23',revision='R19',placements=list(PLACES.values()),new_placements=g.placements,retired_dsf_entities=retired,clipped_objects=g.changes,
        r23=dict(canopy_nosewheel=NG,heading=HEAD,passenger_door=DOOR,marshaller=[2648,286],helipad=HELI,canopy_clear_height_m=14,footprint_wkt=FOOT.wkt,columns=[list(c.bounds) for c in COLS],vehicle_route=VEHICLE,vehicle_spur=[[2730,310],[2744,310]],canopy_approach=APPROACH,native_additions=native,native_surfaces=surfaces,door_controls=8),runtime_tested=False)
    (PACK/'Build_Evidence.json').write_text(json.dumps(evidence,indent=2))
    (OUT/'Build_Checks.json').write_text(json.dumps(g.checks,indent=2))
    print(json.dumps(dict(package=str(PACK),new_objects=len(g.placements),retired=len(retired),native_additions=len(native),built=True)))
if __name__=='__main__':main()
