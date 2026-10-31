"""Actual OBJ8 exports, with schematic aircraft and ground context."""
from pathlib import Path
import ast,json,math,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'package/KIAH_NRT_R23_Jet_Center_Refinement_R19';OUT=ROOT/'output'
tree=ast.parse((ROOT.parent/'KIAH_R17_Native_Surface_R13/source/obj_reader.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'OBJ_reader','exec'))
renderer=(ROOT.parent/'KIAH_R21_Jet_Center_R17/source/render_exports.py').read_text(encoding='utf-8').replace(' • ',' / ')
tree=ast.parse(renderer)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render'],type_ignores=[]),'renderer','exec'))
B=json.loads((PACK/'Build_Evidence.json').read_text());scene=[];cache={}
keep={'mh2_accordion_hangar','mx_stepped_hangar','fbo_ground_tower','fixed_8','fixed_9A','fixed_9B','r21_private_hangar','r21_arrival_landscape','r21_planting_bed','r21_arrival_paint','r23_jet_center','r23_identity','r23_ground_ids','r23_ramp_details'}
pl={q['resource']:q for q in B['placements']+B['new_placements']}
for p in pl.values():
    if Path(p['resource']).stem not in keep:continue
    vals={r:1 for r in ['nrt/kiah/r10/mx/outer_open','nrt/kiah/r10/mx/middle_open','nrt/kiah/r10/mx/tail_open','nrt/kiah/r10/mh2/accordion_open','nrt/kiah/r21/private_hangar/doors_open']}
    tri,uv,tex=readobj(PACK/p['resource'],p['origin'],vals=vals,full=True)
    if 'ATTR_draped' in (PACK/p['resource']).read_text():tri[:,:,2]+=.04
    cache[tex]=np.asarray(Image.open(tex).convert('RGBA'));scene.extend((t,u,tex,None) for t,u in zip(tri,uv))
concept=json.loads((ROOT.parents[1]/'feasibility/KIAH_R21_Jet_Center_Concept_R01/output/scene.json').read_text())
for m in concept['meshes']:
    v=np.array(m['v']);mn=v.min(0);mx=v.max(0)
    landscape=mn[0]>2704 and mx[0]<2717 and mn[1]>306 and mx[1]<319 and mx[2]>.3 and m['c'][1]>m['c'][0]*1.3
    vehicle=mn[0]>2707 and mx[0]<2754 and mn[1]>322 and mx[1]<330 and mn[2]>=.4 and mx[2]<=2
    if landscape or vehicle:
        for j in range(1,len(v)-1):scene.append((v[[0,j,j+1]],None,None,m['c']))
def flat(points,z,col):
    v=np.array([[x,y,z] for x,y in points])
    for j in range(1,len(v)-1):scene.append((v[[0,j,j+1]],None,None,col))
flat([(2395,270),(2900,270),(2900,590),(2395,590)],-.01,[.63,.65,.62])
flat([(2692,292),(2735,292),(2735,330),(2692,330)],.005,[.25,.29,.28])
flat([(2720,257),(2880,257),(2880,334),(2720,334)],.004,[.25,.29,.28])
for x in np.arange(2400,2900,6):flat([(x,270),(x+.04,270),(x+.04,590),(x,590)],0,[.45,.48,.46])
for y in np.arange(276,590,6):flat([(2395,y),(2900,y),(2900,y+.04),(2395,y+.04)],0,[.45,.48,.46])
# Native 102 helipad, represented once at the authored coordinates.
for a in np.linspace(0,2*math.pi,120,endpoint=False):
    points=[(2675+r*math.cos(t),480+r*math.sin(t)) for r,t in [(19.7,a),(20,a),(20,a+2*math.pi/120),(19.7,a+2*math.pi/120)]];flat(points,.02,[.9,.91,.86])
for bounds in [(2672.6,476.5,2673.2,483.5),(2676.8,476.5,2677.4,483.5),(2673.2,479.7,2676.8,480.3)]:
    x0,y0,x1,y1=bounds;flat([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],.02,[.9,.91,.86])
flat([(2647.9,303),(2648.1,303),(2648.1,376),(2647.9,376)],.02,[.85,.65,.12])
# Move the original dimensional BBJ2 reference from west-facing to south-facing.
for m in concept['meshes']:
    if m['group']!='aircraft:BBJ2 / 737-800':continue
    v=np.array(m['v']);x=v[:,0]-2630.25;y=v[:,1]-320
    v[:,0]=2648-y;v[:,1]=303+x
    for j in range(1,len(v)-1):scene.append((v[[0,j,j+1]],None,None,m['c']))
render('Arrival_Export.png','R23 | One NRT Jet Center, from the arrival court',[2803,242,53],[2721,334,5],160)
render('Canopy_Export.png','R23 | Side-entry canopy and passenger doorway',[2540,241,33],[2655,319,6],112)
render('Airside_Export.png','R23 | Continuous FBO facade and covered arrival',[2775,539,97],[2740,360,7],300)
print(json.dumps(dict(renders=3,triangles=len(scene),runtime=False)))
