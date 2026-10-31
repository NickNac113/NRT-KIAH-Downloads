"""Review actual exported meshes. Native pavement/light shading is illustrative."""
from pathlib import Path
import importlib.util,sys,ast,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
s=importlib.util.spec_from_file_location('r24',ROOT/'source/build_r24.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
PACK=b.PACK;g=b.g;scene=[];cache={}
tree=ast.parse((g.LEGACY/'obj_reader.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'))
tree=ast.parse((ROOT.parent/'KIAH_R21_Jet_Center_R17/source/render_exports.py').read_text(encoding='utf-8').replace(' • ',' / '))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render'],type_ignores=[]),'renderer','exec'))
data=g.ag.parse_dsf(ROOT/'qa/R24_Roundtrip.txt')
keep={'mh2_accordion_hangar','mx_stepped_hangar','fbo_ground_tower','fixed_8','fixed_9A','fixed_9B','r21_arrival_landscape','r21_planting_bed','r21_arrival_paint','landside_security','landside_fence','landside_paint','landside_curbs'}
vals={r.get('name'):1 for r in __import__('xml.etree.ElementTree',fromlist=['parse']).parse(PACK/'sam.xml').findall('datarefs/dataref')}
hangar_entry=None
for q in data['entities']:
    if q['kind']!='object' or not q['resource'].startswith('objects/nrt_test/'):continue
    stem=Path(q['resource']).stem
    if stem not in keep and not stem.startswith('r24_'):continue
    origin=[q['geom'].x,q['geom'].y]
    tri,uv,tx=readobj(PACK/q['resource'],origin,vals=vals,full=True)
    if 'ATTR_draped' in (PACK/q['resource']).read_text():tri[:,:,2]+=.04
    cache[tx]=np.asarray(Image.open(tx).convert('RGBA'))
    start=len(scene);scene.extend((v,u,tx,None) for v,u in zip(tri,uv))
    if stem=='r24_indoor_parking':hangar_entry=(start,len(scene),q,origin)
def flat(points,z,col):
    v=np.array([[x,y,z] for x,y in points])
    for j in range(1,len(v)-1):scene.append((v[[0,j,j+1]],None,None,col))
def poly(geom,z,col):
    for p in g.parts(geom):
        for tri in g.constrained_delaunay_triangles(p).geoms:flat(list(tri.exterior.coords)[:-1],z,col)
flat([(2395,270),(2900,270),(2900,600),(2395,600)],-.01,[.63,.65,.62])
poly(g.LAND,.005,[.25,.29,.28]);poly(b.box(2735,277,2888,334),.004,[.25,.29,.28])
for x in np.arange(2400,2900,6):flat([(x,270),(x+.04,270),(x+.04,600),(x,600)],0,[.45,.48,.46])
for y in np.arange(276,600,6):flat([(2395,y),(2900,y),(2900,y+.04),(2395,y+.04)],0,[.45,.48,.46])
for tag in ['arrival','departure']:poly(b.LineString(b.PROPOSAL[tag]).buffer(.12,cap_style=2),.05,[.85,.65,.12])
poly(b.LineString([(g.SPINE,291),(g.SPINE,475)]).buffer(.12),.05,[.85,.65,.12])
poly(b.LineString(b.GA_ROUTE).buffer(.12),.05,[.85,.65,.12])
poly(b.Point(b.HELI).buffer(20,quad_segs=70).difference(b.Point(b.HELI).buffer(19.7,quad_segs=70)),.03,[.9,.91,.86])
for bounds in [(2672.6,476.5,2673.2,483.5),(2676.8,476.5,2677.4,483.5),(2673.2,479.7,2676.8,480.3)]:poly(b.box(*bounds),.03,[.9,.91,.86])
render('Canopy_Pullthrough.png','R24 | Approved canopy pull-through',[2510,242,73],[2637,352,4],207)
render('Headquarters_Arrival.png','R24 | NRT Virtual Headquarters - arrival court',[2803,242,53],[2721,334,5],160)
render('Indoor_Parking_Open.png','R24 | Indoor Parking - matched MH2 roofline',[2678,275,63],[2464,385,8],220)
# A separate pose demonstrates the left/right controls in the actual OBJ.
start,end,q,origin=hangar_entry
partial=dict(vals);partial[b.REF_LEFT]=0;partial[b.REF_RIGHT]=1
tri,uv,tx=readobj(PACK/q['resource'],origin,vals=partial,full=True)
scene[start:end]=[(v,u,tx,None) for v,u in zip(tri,uv)]
render('Indoor_Parking_Split.png','R24 | Left doors closed / right doors open',[2660,359,40],[2474,359,9],171)
print(json.dumps(dict(renders=4,triangles=len(scene),runtime_tested=False)))
