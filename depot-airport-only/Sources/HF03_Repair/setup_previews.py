from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];prev=root.parent/'KIAH_R03_HF02_Repair'
for name in ('stock-sign-atlas.png','stock-dir-atlas.png'):
 shutil.copy2(prev/'work'/name,root/'work'/name)
source=(prev/'work/prepare_previews.py').read_text()
source=source.replace('from sign_groups import *',"import pathlib,sys\nROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'\nsys.path.insert(0,str(PREV/'work'))\nfrom sign_groups import *\nROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF02_Repair'")
source=source.replace('R03_HF02\'','R03_HF03\'').replace("ROOT/'work/repair_airport_details.py'","PREV/'work/repair_airport_details.py'")
source=source.replace("plan,before,oldapt=pickle.loads((ROOT/'work/context.pkl').read_bytes())","plan,before,oldapt,oldscene=pickle.loads((ROOT/'work/current.pkl').read_bytes())")
source=source.replace('scene-hf02.json','scene-hf03.json')
insert='''
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
        elif r[0]=='TEXTURE':texture=(path.parent/r[1].replace('\\\\','/')).resolve()
    if not texture.exists():texture=texture.with_suffix('.dds')
    faces=[(ix[k],ix[k+2],ix[k+1]) for k in range(0,len(ix),3)]
    for tag in ('Before','After'):
        if tag=='After' and i in excluded:continue
        addmesh(f'{tag} old AEP glyph {i}',vs,faces,tag,'sign',uv,str(texture))
'''
source=source.replace("with gzip.open(ROOT/'work/native-review-context.json.gz'",insert+"\nwith gzip.open(ROOT/'work/native-review-context.json.gz'")
(root/'work/prepare_previews.py').write_text(source)
render=(prev/'work/render_hf02.py').read_text().replace('R03_HF02\'','R03_HF03\'').replace('scene-hf02.json','scene-hf03.json')
render=render.replace("(OLD/'generated/scene.json')","(ROOT.parent/'KIAH_R03_HF02_Repair/work/scene-hf02.json')")
render=render.replace("'red':(.65,.12,.08)","'red':(.65,.12,.08),'cyan':(.02,.65,.9)")
render=render.replace("mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);textures[key]=mat","mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha']);textures[key]=mat")
start=render.index('views=[');end=render.index('requested=sys.argv',start)
render=render[:start]+'''views=[
 ('01_B5_Before','Before',(-182,660,44),(-238,601,5),90,1500,1000),
 ('02_B5_After','After',(-182,660,44),(-238,601,5),90,1500,1000),
 ('03_B_North_Before','Before',(-50,1090,390),(-390,435,6),740,1700,1100),
 ('04_B_North_After','After',(-50,1090,390),(-390,435,6),740,1700,1100),
 ('05_D_West_Before','Before',(640,930,330),(295,485,4),500,1700,1100),
 ('06_D_West_After','After',(640,930,330),(295,485,4),500,1700,1100),
 ('07_B_Landside_Before','Before',(-650,-100,260),(-360,250,6),400,1600,1000),
 ('08_B_Landside_After','After',(-650,-100,260),(-360,250,6),400,1600,1000),
 ('09_International_Before','Before',(1200,-80,300),(800,250,6),500,1700,1100),
 ('10_International_After','After',(1200,-80,300),(800,250,6),500,1700,1100),
 ('11_Hangar_Before','Before',(1640,560,65),(1775,432,11),175,1600,1000),
 ('12_Hangar_After','After',(1640,560,65),(1775,432,11),175,1600,1000),
 ('13_B5_Top_Before','Before',(-240,605,150),(-240,605,0),80,1400,1000),
 ('14_B5_Top_After','After',(-240,605,150),(-240,605,0),80,1400,1000)]
''' + render[end:]
render=render.replace('Framework, equipment, terrain relief and aircraft omitted.', 'Framework, equipment and terrain relief omitted. Cyan B5 outline/cage is a conservative A321-sized clearance guide, not an aircraft rendering. Old AEP glyph meshes included; other AEP effects omitted.')
(root/'work/render_hf03.py').write_text(render)
print('HF03 preview scripts prepared')
