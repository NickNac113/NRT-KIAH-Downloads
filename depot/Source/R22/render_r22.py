"""Offline material previews of the actual exported replacement garage."""
from pathlib import Path
import ast,json,math,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];CAMPUS=ROOT.parents[1]
PACK=ROOT/'package/KIAH_NRT_R22_Original_Garage_R18';OUT=ROOT/'output'
sys.path.insert(0,str(CAMPUS/'tools/python_geometry'))
sys.path.insert(0,str(ROOT.parent/'KIAH_R17_Native_Surface_R13/source'))
import airport_geometry as ag
for name in ['obj_reader.py']:
    t=ast.parse((ROOT.parent/'KIAH_R17_Native_Surface_R13/source'/name).read_text())
    exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'))
t=ast.parse((ROOT.parent/'KIAH_R21_Jet_Center_R17/source/render_exports.py').read_text(encoding='utf-8'))
f=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='render'][0]
for node in ast.walk(f):
    if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('Ground, vegetation'):
        node.value='Original garage meshes and materials reopened from the package. Pavement is context; lighting needs X-Plane.'
    if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('Reopened X-Plane'):
        node.value='Reopened X-Plane OBJ exports | Offline material preview'
# Modest roof occlusion makes the hollow interior legible in this offline
# preview. This is a simple roof-shadow approximation, not the X-Plane shader.
for node in ast.walk(f):
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='shade' for t in node.targets):
        node.value=ast.BinOp(left=node.value,op=ast.Mult(),right=ast.parse("0.48 if 'r22_garage_materials' in (tx or '') and 3065.7 < v[:,0].mean() < 3094.7 and 693.5 < v[:,1].mean() < 760.5 and v[:,2].mean() < 8.4 else 1",mode='eval').body)
ast.fix_missing_locations(f)
exec(compile(ast.Module(body=[f],type_ignores=[]),'material_preview','exec'))
dsf=ag.parse_dsf(ROOT/'qa/R22_Roundtrip.txt');scene=[];cache={}
keep={'cargo','cargo_recess_walls','landside_paint','landside_stencils','landside_curbs','landside_security','landside_signboards','landside_lights','landside_fence'}
for item in dsf['entities']:
    if item['kind']!='object':continue
    name=Path(item['resource']).stem
    if name not in keep and not name.startswith('r22_'):continue
    tris,uvs,tex=readobj(PACK/item['resource'],list(item['geom'].coords)[0],heading=item['coords'][2],vals={f'nrt/kiah/r22/truck_garage/bay_{i}_open':1 for i in range(1,4)},full=True)
    cache.setdefault(tex,np.asarray(Image.open(tex).convert('RGBA')))
    for tri,uv in zip(tris,uvs):
        if tri[:,0].max()<3055 or tri[:,0].min()>3156 or tri[:,1].max()<670 or tri[:,1].min()>770:continue
        scene.append((tri,uv,tex,None))
def ground(b,z,color):
    x0,y0,x1,y1=b;v=np.array([[x0,y0,z],[x1,y0,z],[x1,y1,z],[x0,y1,z]])
    scene.extend((v[list(q)],None,None,color) for q in [(0,1,2),(0,2,3)])
ground([3000,630,3190,800],-.06,[.39,.48,.35])
ground([3065,693,3145,761],-.025,[.31,.34,.34])
ground([3095,550,3145,693],-.025,[.31,.34,.34])
ground([3146,550,3160,780],-.04,[.52,.54,.50])
render('Garage_Open.png','NRT | Original truck service workshop',[3170,661,38],[3090,724,4],98)
render('Garage_Court.png','NRT | Recessed workshop and retained truck court',[3215,665,110],[3100,716,1],142)
render('Garage_Interior.png','NRT | Open bays and workshop interior',[3154,705,10],[3087,721,3],70)
# Closed-door comparison uses only new door geometry while everything else stays.
scene=[q for q in scene if 'r22_garage_materials' not in (q[2] or '')]
# Reload all three new meshes with closed doors (shell/signs share no animation).
for p in json.loads((PACK/'Garage_Provenance.json').read_text())['new_placements']:
    tri,uv,tex=readobj(PACK/p['resource'],p['origin'],full=True)
    cache.setdefault(tex,np.asarray(Image.open(tex).convert('RGBA')))
    if p['resource'].endswith('signs.obj'):continue
    scene.extend((t,u,tex,None) for t,u in zip(tri,uv))
render('Garage_Closed.png','NRT | Independent sectional doors, closed',[3170,661,38],[3090,724,4],98)
print(json.dumps(dict(images=['Garage_Open.png','Garage_Court.png','Garage_Interior.png','Garage_Closed.png'],runtime=False)))
