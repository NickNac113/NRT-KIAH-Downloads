"""Original NRT truck service shop, generated from dimensional primitives.

No imported truck-simulator mesh, texture, prefab or material is used by this
authoring script. R21 is read-only; a filtered successor is created once.
"""
from pathlib import Path
import ast, hashlib, json, math, shutil, subprocess, sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
CAMPUS = ROOT.parents[1]
PREVIOUS = ROOT.parent / 'KIAH_R21_Jet_Center_R17'
OLD = PREVIOUS / 'package/KIAH_NRT_R21_Jet_Center_R17'
NAME = 'KIAH_NRT_R22_Original_Garage_R18'
PACK = ROOT / 'package' / NAME
OUT = ROOT / 'output'
QA = ROOT / 'qa'
TOOL = Path('C:/Users/Nick/Documents/Codex/2026-10-24/cou/work/xptools-24-5/tools/DSFTool.exe')
ORIGIN = np.array([3080., 727.])
BOUNDS = [3065.3, 693.2, 3095.1, 760.8]
BAY_CENTERS = [704., 720., 736.]
PORTAL_X = 3094.85
DOOR_HEIGHT = 5.8
DOOR_WIDTH = 8.0
REFS = [f'nrt/kiah/r22/truck_garage/bay_{i}_open' for i in range(1, 4)]
LON0, LAT0 = -95.341444444, 29.984444444
phi = math.radians(LAT0)
SX = 111412.84*math.cos(phi)-93.5*math.cos(3*phi)+.118*math.cos(5*phi)
SY = 111132.92-559.82*math.cos(2*phi)+1.175*math.cos(4*phi)-.0023*math.cos(6*phi)
def ll(x, y): return x/SX+LON0, y/SY+LAT0
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    r = subprocess.run(list(map(str,args)), capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stdout+r.stderr)
    return r.stdout+r.stderr

placements = []
meshes = []
sign_crop = {}

class Mesh:
    """Small OBJ8 writer with tiled materials and articulated door batches."""
    def __init__(self, name, signage=False):
        self.name=name; self.v=[]; self.ops=[]; self.last=0; self.lights=[]; self.signage=signage
    def face(self, p, mat=0, uv=None):
        if uv is None and len(p)==4:
            a,b,c,d=map(lambda q:np.array(q,float),p)
            nu=max(1,math.ceil(np.linalg.norm(b-a)/6)); nv=max(1,math.ceil(np.linalg.norm(d-a)/6))
            col,row=mat%4,mat//4
            for j in range(nv):
                for i in range(nu):
                    q=[a+(b-a)*u+(d-a)*v for u,v in [(i/nu,j/nv),((i+1)/nu,j/nv),((i+1)/nu,(j+1)/nv),(i/nu,(j+1)/nv)]]
                    tex=[((col*512+1+u*510)/2048,1-(row*512+1+(1-v)*510)/1024) for u,v in [(0,0),(1,0),(1,1),(0,1)]]
                    self.face(q,mat,tex)
            return
        q=np.array([[x-ORIGIN[0],z,ORIGIN[1]-y] for x,y,z in p])
        n=np.cross(q[1]-q[0],q[2]-q[0]); n/=max(np.linalg.norm(n),1e-9)
        for i in range(1,len(p)-1):
            for k in [0,i,i+1]: self.v.append([*q[k],*n,*uv[k]])
    def box(self,b,z0,z1,mat=0,roof=None):
        x0,y0,x1,y1=b
        p=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for a,b in zip(p,p[1:]+p[:1]):self.face([(*a,z0),(*b,z0),(*b,z1),(*a,z1)],mat)
        self.face([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],mat if roof is None else roof)
        self.face([(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0)],mat)
    def rod(self,a,b,w=.08,mat=1):
        a=np.array(a,float);b=np.array(b,float);v=(b-a)/np.linalg.norm(b-a)
        r=np.cross(v,[0,0,1]);r=r/max(np.linalg.norm(r),1e-9) if np.linalg.norm(r)>.01 else np.array([1.,0,0])
        r*=w/2;u=np.cross(v,r);q=[r+u,-r+u,-r-u,r-u]
        for j in range(4):self.face([a+q[j],b+q[j],b+q[(j+1)%4],a+q[(j+1)%4]],mat)
    def animated(self,commands,draw):
        if len(self.v)>self.last:self.ops.append(f'TRIS {self.last} {len(self.v)-self.last}')
        start=len(self.v);draw();self.ops+=['ANIM_begin',*commands,f'TRIS {start} {len(self.v)-start}','ANIM_end'];self.last=len(self.v)
    def light(self,x,y,z,dx=0,dy=0,cd=1800):
        self.lights += [f'LIGHT_PARAM spot_params_sp_pm {x-ORIGIN[0]:.4f} {z:.4f} {ORIGIN[1]-y:.4f} 1 .94 .86 1 {cd}cd {dx} -.9 {-dy} .55',
                        f'LIGHT_PARAM spot_params_bb_pm {x-ORIGIN[0]:.4f} {z:.4f} {ORIGIN[1]-y:.4f} 1 .94 .86 {cd/10:g}cd {dx} -.9 {-dy} .55']
    def save(self):
        stem='r22_garage_signs' if self.signage else 'r22_garage_materials'
        rows=['I','800','OBJ',f'TEXTURE ../../textures/nrt_test/{stem}.dds',f'TEXTURE_LIT ../../textures/nrt_test/{stem}_LIT.dds']
        if not self.signage:rows += [f'TEXTURE_NORMAL ../../textures/nrt_test/{stem}_NML.png','GLOBAL_specular 1.0']
        rows += [f'POINT_COUNTS {len(self.v)} 0 0 {len(self.v)}']
        rows += ['VT '+' '.join(f'{v:.6f}' for v in p) for p in self.v]
        # Reverse the authoring winding for OBJ8, and keep interior faces visible.
        ids=[j for i in range(0,len(self.v),3) for j in (i,i+2,i+1)]
        for i in range(0,len(ids),10):
            v=ids[i:i+10];rows += ['IDX10 '+' '.join(map(str,v))] if len(v)==10 else ['IDX '+str(k) for k in v]
        rows += ['ATTR_no_cull',*self.ops]
        if len(self.v)>self.last: rows += [f'TRIS {self.last} {len(self.v)-self.last}']
        rows += self.lights
        rel='objects/nrt_test/'+self.name+'.obj';(PACK/rel).write_text('\n'.join(rows)+'\n')
        placements.append(dict(resource=rel,origin=ORIGIN.tolist(),heading=0,triangles=len(self.v)//3));meshes.append(self)

def make_textures():
    """Seeded paint/metal/concrete maps; no photograph or donor texture input."""
    rng=np.random.default_rng(22018); yy,xx=np.mgrid[:512,:512]
    diffuse=Image.new('RGB',(2048,1024)); normal=Image.new('RGBA',(2048,1024));lit=Image.new('RGB',(2048,1024))
    colors=[[196,204,202],[26,52,61],[40,79,92],[129,137,135],[76,90,95],[154,172,178],[214,168,40],[122,48,40]]
    for i,base in enumerate(colors):
        noise=rng.normal(0,.9,(512,512)); height=np.zeros_like(noise); gloss=np.full_like(noise,48)
        if i in (0,1):
            seam=xx%24<2;noise-=seam*13;height+=seam*.7
            noise-=((np.sin(xx*.09)+1)*.8)*(yy/512)
        elif i==2:
            frames=(xx%128<4)|(yy%256<4);noise=noise*.1+(1-yy/512)*10-frames*24;gloss[:]=160;height-=frames*.4
        elif i==3:
            noise+=rng.normal(0,1,(512,512));noise-=(yy%256<2)*13;height+=noise*.015;gloss[:]=20
        elif i==4:
            seam=xx%64<3;height+=seam;noise-=seam*18;gloss[:]=55
        elif i==5:
            seam=yy%64<2;height-=seam*.6;noise-=seam*16;gloss[:]=65
        else:gloss[:]=45
        rgb=np.clip(np.array(base)[None,None,:]+noise[:,:,None],0,255).astype('uint8')
        dx=np.gradient(height,axis=1)*.3;dy=np.gradient(height,axis=0)*.3
        ns=np.stack([-dx,dy,np.ones_like(dx)],2);ns/=np.linalg.norm(ns,axis=2)[:,:,None]
        nm=np.dstack([(ns*.5+.5)*255,gloss]).clip(0,255).astype('uint8')
        location=(i%4*512,i//4*512);diffuse.paste(Image.fromarray(rgb),location);normal.paste(Image.fromarray(nm),location)
        if i==2:
            glow=np.full((512,512,3),[24,29,27],dtype='uint8');glow[frames]=[1,2,2];lit.paste(Image.fromarray(glow),location)
    tex=PACK/'textures/nrt_test'
    diffuse.save(tex/'r22_garage_materials.png');normal.save(tex/'r22_garage_materials_NML.png');lit.save(tex/'r22_garage_materials_LIT.png')
    signs=Image.new('RGB',(2048,1024),(22,47,55));d=ImageDraw.Draw(signs)
    names=['NRT  |  TRUCK SERVICE','01','02','03','DISPATCH / DRIVERS','PARTS / WORKSHOP','NRT']
    for i,s in enumerate(names):
        y=i*128;fs=96
        while ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs).getlength(s)>1950:fs-=1
        text_width=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs).getlength(s)
        sign_crop[i]=((1024-text_width/2-30)/2048,(1024+text_width/2+30)/2048)
        d.rectangle([0,y+118,2047,y+125],fill=(36,141,158))
        d.text((1024,y+60),s,font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',fs),anchor='mm',fill=(231,237,230))
    signs.save(tex/'r22_garage_signs.png')
    Image.fromarray((np.asarray(signs)*.40).astype('uint8')).save(tex/'r22_garage_signs_LIT.png')
    for name in ['r22_garage_materials','r22_garage_materials_LIT','r22_garage_signs','r22_garage_signs_LIT']:
        (QA/(name+'_dds.txt')).write_text(run([TOOL.with_name('DDSTool.exe'),'--png2dxt1',tex/(name+'.png'),tex/(name+'.dds')]))

def east_sign(mesh,row,x,y,z,width,height):
    left,right=sign_crop[row]
    uv=[(left,1-(row+1)*128/1024),(right,1-(row+1)*128/1024),(right,1-row*128/1024),(left,1-row*128/1024)]
    mesh.face([(x,y-width/2,z),(x,y+width/2,z),(x,y+width/2,z+height),(x,y-width/2,z+height)],uv=uv)

def build_model():
    shell=Mesh('r22_nrt_truck_garage');doors=Mesh('r22_nrt_truck_doors');sign=Mesh('r22_nrt_truck_signs',True)
    x0,y0,x1,y1=BOUNDS
    # Hollow service hall, not a filled box. Low painted masonry base and metal cladding.
    for b in [(x0,y0,x0+.35,y1),(x0,y0,x1,y0+.35),(x0,y1-.35,x1,y1)]:
        shell.box(b,0,1.1,3);shell.box(b,1.1,8.5,0)
    # End walls/pier zones between the three genuine door openings.
    front_segments=[(y0,700),(708,716),(724,732),(740,748)]
    for a,b in front_segments:
        shell.box([x1-.35,a,x1,b],0,1.1,3);shell.box([x1-.35,a,x1,b],1.1,8.5,0)
    shell.box([x1-.35,700,x1,740],5.82,8.5,0)
    shell.box([x0,y0,x1,y1],8.5,8.85,4)
    shell.box([x1-.04,y0,x1+.12,748],7.05,8.48,1)
    # Deep dispatch/driver room in the northern end, parts store behind it.
    shell.box([x0,747.65,x1,748],0,7.9,0)
    shell.box([3082.0,748,3082.25,y1],0,8.5,0)
    shell.box([x1-.35,748,x1,y1],0,.9,3)
    shell.box([x1-.35,748,x1,y1],.9,6.65,2)
    shell.box([x1-.35,748,x1,y1],6.65,8.5,1)
    shell.box([x1+.02,752.1,x1+.10,754.2],.12,2.8,1)
    shell.box([x1+.11,752.22,x1+.15,754.08],.75,2.63,2)
    shell.box([x1,748.1,x1+2.3,760.4],0,.12,3)
    shell.box([x1-.2,749,x1+2.1,759.6],3.15,3.40,1)
    # Perimeter frame, gutters/downpipes and modest roof plant.
    for y in [y0+.6,748,y1-.6]:
        shell.rod([x1+.15,y,.25],[x1+.15,y,8.5],.13,1)
    shell.box([x1,y0,x1+.18,y1],8.25,8.55,1)
    for y in [702,720,738]:
        shell.box([3071,y-2.2,3079,y+2.2],8.87,9.03,2)
        shell.box([3067,y-1,3069,y+1],8.87,9.8,4)
        for z in np.arange(9.03,9.65,.18):shell.box([3068.99,y-.9,3069.03,y+.9],z,z+.04,1)
    # Wall columns and high beams remain outside the vehicle clear boxes.
    for y in [697,712,728,745]:
        shell.box([3065.8,y-.18,3066.12,y+.18],.12,8.48,1)
        shell.box([3066,y-.12,3094.6,y+.12],7.6,7.95,1)
    shell.box([x0+.35,y0+.35,x1-.35,y1-.35],.005,.035,3)
    for n,cy in enumerate(BAY_CENTERS):
        # Equipment stays at the rear wall or side of each work bay.
        shell.box([3066.1,cy-3.3,3066.8,cy+1.8],.12,.95,1)
        shell.box([3066.0,cy-3.4,3067.0,cy+1.9],.95,1.06,3)
        shell.box([3066.05,cy+2.2,3066.95,cy+3.5],.12,1.8,7)
        for z in [.45,.85,1.25]:shell.box([3066.96,cy+2.35,3066.99,cy+3.35],z,z+.04,3)
        for y in [cy-4.45,cy+4.45]:
            shell.box([3095.2,y-.12,3095.44,y+.12],.05,1.05,6)
            shell.box([3095.18,y-.14,3095.46,y+.14],.55,.72,1)
            # Door vertical tracks and horizontal ceiling tracks.
            shell.rod([3094.45,y,.15],[3094.45,y,5.7],.07,3)
            shell.rod([3087.9,y,6.25],[3094.45,y,6.25],.07,3)
        shell.box([3094.8,cy-4.15,3095.35,cy+4.15],5.83,6.12,1)
        east_sign(sign,n+1,3095.24,cy,6.35,1.2,.48)
        shell.box([3095.2,cy-.4,3095.65,cy+.4],6.75,6.88,1)
        shell.light(3095.7,cy,6.65,.5,0,2600)
        for x in [3073,3083]:
            shell.box([x-.25,cy-1.3,x+.25,cy+1.3],7.35,7.47,0)
            shell.light(x,cy,7.27,0,0,1600)
        # Ten articulated sections follow a curved overhead track. A closed
        # panel becomes horizontal above the clear opening when fully open.
        for j in range(10):
            z0=j*.58+.02;z1=(j+1)*.58-.005;zc=(z0+z1)/2
            pivot=np.array([PORTAL_X-ORIGIN[0],zc,ORIGIN[1]-cy]);keys=[];rot=[]
            for state in np.linspace(0,1,25):
                travel=zc+6.5*state;arc=(travel-5.5)/.6
                if travel<=5.5:xp=PORTAL_X;zp=travel;angle=0
                elif arc<=math.pi/2:xp=PORTAL_X-.6*(1-math.cos(arc));zp=5.5+.6*math.sin(arc);angle=math.degrees(arc)
                else:xp=PORTAL_X-.6-(travel-5.5-.6*math.pi/2);zp=6.1;angle=90
                keys.append(f'ANIM_trans_key {state:.6f} {xp-PORTAL_X:.6f} {zp-zc:.6f} 0');rot.append(f'ANIM_rotate_key {state:.6f} {angle:.6f}')
            fixed=lambda q:'ANIM_trans '+' '.join(f'{v:.6f}' for v in [*q,*q])+ ' 0 0'
            cmd=['ANIM_trans_begin '+REFS[n],*keys,'ANIM_trans_end',fixed(pivot),'ANIM_rotate_begin 0 0 1 '+REFS[n],*rot,'ANIM_rotate_end',fixed(-pivot)]
            def panel(z0=z0,z1=z1,j=j,cy=cy):
                doors.box([PORTAL_X-.065,cy-4,PORTAL_X+.065,cy+4],z0,z1,5)
                if j in [4,5]:
                    for y in np.arange(cy-3.6,cy+3.2,1.3):doors.box([PORTAL_X+.067,y,PORTAL_X+.082,y+.95],z0+.10,z1-.10,2)
            doors.animated(cmd,panel)
    east_sign(sign,0,3095.24,722,7.38,30,.85)
    east_sign(sign,4,3095.24,754,6.94,11,.65)
    shell.light(3097.25,753.5,3.05,0,0,1000)
    for m in [shell,doors,sign]:m.save()

def copy_successor():
    if PACK.exists():raise RuntimeError('Preserve existing R22 build; use a successor or explicit QA archive.')
    for p in [OUT,QA,ROOT/'reference']:p.mkdir(parents=True,exist_ok=True)
    oldhash={p.relative_to(OLD).as_posix():sha(p) for p in OLD.rglob('*') if p.is_file()}
    (ROOT/'reference/R21_Hashes.json').write_text(json.dumps(oldhash,indent=2))
    removed=[]
    for p in OLD.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(OLD)
        if p.name.startswith('garage_t02_') or p.name in ['PERSONAL_TEST_ONLY.txt','Garage_Provenance.json','README_R21.txt']:
            removed.append(dict(path=rel.as_posix(),sha256=sha(p)));continue
        q=PACK/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    (OUT/'Removed_Donor_Assets.json').write_text(json.dumps(removed,indent=2))
    return removed

def update_dsf():
    source=ROOT/'reference/R21_South.txt'
    (QA/'Decompile_R21.txt').write_text(run([TOOL,'--dsf2text',OLD/'Earth nav data/+20-100/+29-096.dsf',source]))
    rows=source.read_text().splitlines();defs=[s.split(' ',1)[1] for s in rows if s.startswith('OBJECT_DEF ')]
    mapping={};kept=[]
    for i,r in enumerate(defs):
        if Path(r).name.startswith('garage_t02_'):continue
        mapping[i]=len(kept);kept.append(r)
    newdefs=[q['resource'] for q in placements];output=[];definitions=False;removed=0
    for s in rows:
        t=s.split()
        if t and t[0]=='OBJECT_DEF':
            if not definitions:output+=['OBJECT_DEF '+r for r in kept+newdefs];definitions=True
            continue
        if t and t[0] in ['OBJECT','OBJECT_MSL','OBJECT_AGL']:
            oldindex=int(t[1])
            if oldindex not in mapping:removed+=1;continue
            t[1]=str(mapping[oldindex]);s=' '.join(t)
        output.append(s)
    output += ['FILTER 0']
    for i,p in enumerate(placements):
        lo,la=ll(*p['origin']);output += [f'OBJECT {len(kept)+i} {lo:.9f} {la:.9f} 0']
    path=QA/'R22_South.txt';path.write_text('\n'.join(output)+'\n')
    target=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile_R22.txt').write_text(run([TOOL,'--text2dsf',path,target]))
    (QA/'Decompile_R22.txt').write_text(run([TOOL,'--dsf2text',target,QA/'R22_Roundtrip.txt']))
    return removed

def update_xml():
    for name in ['sam.xml','opensam.xml']:
        root=ET.parse(PACK/name).getroot();root.set('name','NRT KIAH R22 Original Garage')
        for i,ref in enumerate(REFS):
            r=ET.SubElement(root.find('datarefs'),'dataref',name=ref,autoplay='false',randomize_phase='false',augment_wind_speed='false')
            ET.SubElement(r,'animation',t='0',v='1');ET.SubElement(r,'animation',t='18',v='0')
            ET.SubElement(root.find('gui'),'checkbox',label=f'Close NRT Truck Bay {i+1}',title='Close sectional workshop door',instance='truck_service',dataref=ref)
        lo,la=ll(*ORIGIN)
        ET.SubElement(root.find('objects'),'instance',id='truck_service',latitude=f'{la:.9f}',longitude=f'{lo:.9f}',elevation='29',heading='0')
        ET.indent(root);ET.ElementTree(root).write(PACK/name,encoding='utf-8',xml_declaration=True)

def main():
    removed=copy_successor();make_textures();build_model();count=update_dsf();update_xml()
    spec=dict(name='Original NRT Truck Service',revision='R22',origin=ORIGIN.tolist(),bounds_en=BOUNDS,height_m=9.8,
        service_bays=[dict(id=f'B{i+1}',center_y=y,door_width_m=8,door_height_m=5.8,clear_interior_depth_m=27.7,clear_work_width_m=12,
                           clear_box=[3067.1,y-3.9,3094.8,y+3.9],dataref=REFS[i]) for i,y in enumerate(BAY_CENTERS)],
        office='Dispatch and driver room in the north end; parts/workbench space at the rear.',doors='Original articulated overhead sectional doors, open on load with OpenSAM, independent Close controls.',
        geometry_source='Generated dimensional primitives in Source/R22/build_r22.py; no imported mesh.',
        texture_source='Original seeded metal/paint/concrete/normal/night materials and NRT text atlas generated in the same source; no imported images.',
        input_geometry_or_texture_files=[],inherited_donor_runtime_files_removed=len([r for r in removed if Path(r['path']).name.startswith('garage_t02_')]),
        legacy_donor_instances_removed=count,new_placements=placements,runtime_tested=False)
    (PACK/'Garage_Provenance.json').write_text(json.dumps(spec,indent=2));(OUT/'Garage_Specification.json').write_text(json.dumps(spec,indent=2))
    b=json.loads((PACK/'Build_Evidence.json').read_text());b.update(name=NAME,layout='R22',revision='R18',garage=spec,runtime_tested=False)
    b['placements']=[p for p in b['placements'] if not Path(p['resource']).name.startswith('garage_t02_')]
    b['new_placements'] += placements
    for s in b['landside']['solids']:
        if s['name']=='T02 garage':s.update(name='Original NRT truck service',wkt=f'POLYGON (({BOUNDS[0]} {BOUNDS[1]}, {BOUNDS[2]} {BOUNDS[1]}, {BOUNDS[2]} {BOUNDS[3]}, {BOUNDS[0]} {BOUNDS[3]}, {BOUNDS[0]} {BOUNDS[1]}))')
    b['landside']['notes']=[s for s in b['landside']['notes'] if 'garage' not in s.lower()]
    b['landside']['notes'] += ['R22 replaces the T02 donor with original NRT geometry and materials. Cargo recess, marked court, parking, docks and roads are retained.']
    b['garage_replacement']=dict(removed_assets=removed,original=True,original_donor_copied=False)
    (PACK/'Build_Evidence.json').write_text(json.dumps(b,indent=2))
    src=PACK/'Source/R22';src.mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,src/p.name)
    (OUT/'Build_Summary.json').write_text(json.dumps(dict(package=NAME,removed_donor_instances=count,original_triangles=sum(p['triangles'] for p in placements),source_preserved=True),indent=2))
    print((OUT/'Build_Summary.json').read_text())

if __name__=='__main__':main()
