"""Actual OBJ exports with stock texture context; not an X-Plane screenshot."""
from pathlib import Path
import importlib.util,sys,ast,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
s=importlib.util.spec_from_file_location('r25',ROOT/'source/build_r25.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;PACK=b.PACK;scene=[];cache={};groundtextures=set()
tree=ast.parse((g.LEGACY/'obj_reader.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'))
data=g.ag.parse_dsf(ROOT/'qa/R25_Roundtrip.txt');e=json.loads((PACK/'Build_Evidence.json').read_text())
vals={r.get('name'):1 for r in __import__('xml.etree.ElementTree',fromlist=['parse']).parse(PACK/'sam.xml').findall('datarefs/dataref')}
keep={'mh2_accordion_hangar','mx_stepped_hangar','fbo_ground_tower','r24_indoor_parking','r21_arrival_landscape','r21_planting_bed','r21_arrival_paint','landside_security','landside_fence','landside_paint','landside_curbs','paint','ramp_safety'}
for q in data['entities']:
    if q['kind']!='object':continue
    if q['resource'].startswith('objects/nrt_test/'):
        if Path(q['resource']).stem not in keep and not Path(q['resource']).stem.startswith('r25_'):continue
        p=PACK/q['resource']
    elif q['resource'] in b.LIBMAP and any(q['resource']==r['resource'] and q['geom'].distance(b.Point(r['origin']))<.25 for r in e['r25']['props']):p=Path(b.LIBMAP[q['resource']])
    else:continue
    tri,uv,tx=readobj(p,[q['geom'].x,q['geom'].y],heading=float(q['lines'][0].split()[-1]),vals=vals,full=True)
    if 'ATTR_draped' in p.read_text():tri[:,:,2]+=.04
    cache.setdefault(tx,np.asarray(Image.open(tx).convert('RGBA')))
    scene.extend((v,u,tx,None) for v,u in zip(tri,uv))
def flat(points,z,col):
    v=np.array([[x,y,z] for x,y in points],float)
    for j in range(1,len(v)-1):scene.append((v[[0,j,j+1]],None,None,col))
def poly(geom,z,col):
    for p in g.parts(geom):
        for tri in g.constrained_delaunay_triangles(p).geoms:flat(list(tri.exterior.coords)[:-1],z,col)
def ground(geom,tx,scale,z):
    tx=str(tx);groundtextures.add(tx);cache[tx]=np.asarray(Image.open(tx).convert('RGBA'))
    for p in g.parts(geom):
        for tri in g.constrained_delaunay_triangles(p).geoms:
            v=np.array([[x,y,z] for x,y in list(tri.exterior.coords)[:-1]])
            uv=np.column_stack([(v[:,0]-2400)/scale[0],(v[:,1]-270)/scale[1]])
            scene.append((v,uv,tx,None))
native=Path('X:/X-Plane 12/Resources/default scenery/sim objects/apt_pavement/textures')
flat([(2350,230),(2925,230),(2925,630),(2350,630)],-.02,[.28,.37,.23])
ground(b.box(2411.7,276.6,2890,595),native/'concrete_1a_ALB.dds',(22,44),0)
for q in data['entities']:
    if q['kind']=='polygon' and '/pavement/asphalt' in q['resource'] and b.box(2400,270,2900,600).covers(q['geom'].representative_point()):ground(q['geom'],native/'asphalt_5a_ALB.dds',(25,25),.01)
for tag in ['arrival','departure']:
    poly(b.Line(b.PROPOSAL[tag]).buffer(.22,cap_style=2),.045,[.11,.12,.11]);poly(b.Line(b.PROPOSAL[tag]).buffer(.12,cap_style=2),.05,[.88,.68,.13])
for line in [[(g.SPINE,291),(g.SPINE,475)],b.GA_ROUTE]:
    poly(b.Line(line).buffer(.22,cap_style=2),.045,[.11,.12,.11]);poly(b.Line(line).buffer(.12,cap_style=2),.05,[.88,.68,.13])
poly(b.Point(b.HELI).buffer(20,quad_segs=70).difference(b.Point(b.HELI).buffer(19.7,quad_segs=70)),.04,[.94,.94,.9])
for bounds in [(2672.6,476.5,2673.2,483.5),(2676.8,476.5,2677.4,483.5),(2673.2,479.7,2676.8,480.3)]:poly(b.box(*bounds),.04,[.94,.94,.9])
# Soft illustrative ground shadow from the actual geometry. X-Plane shader and
# dynamic light output are deliberately not represented as verified here.
shadow=Image.new('L',(2300,1600));sd=ImageDraw.Draw(shadow);shadowbox=(2350,230,2925,630)
for v,uv,tx,col in scene:
    if v[:,2].max()<.7:continue
    p=v[:,:2]-v[:,2,None]*np.array([.35,-.5])
    sd.polygon([((x-2350)*4,(630-y)*4) for x,y in p],fill=1)
shadow=np.asarray(shadow)
tree=ast.parse((ROOT.parent/'KIAH_R21_Jet_Center_R17/source/render_exports.py').read_text(encoding='utf-8'))
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render');code=ast.unparse(f)
code=code.replace('width, height = (1600, 960)','width, height = (1920, 1152)')
code=code.replace('width, height = (1600, 960)','width, height = (1920, 1152)')
# Wrap ground textures only; atlas UVs use normal clamping.
code=code.replace('colors = tex[',"\n            if tx in groundtextures:\n                u=u%1;vv=vv%1\n            colors = tex[")
code=code.replace('mask &= colors[:, :, 3] > 128',"mask &= colors[:, :, 3] > 128\n            if tx in groundtextures:\n                wx=a*v[0,0]+b*v[1,0]+c*v[2,0];wy=a*v[0,1]+b*v[1,1]+c*v[2,1]\n                sh=shadow[np.clip(((630-wy)*4).astype(int),0,1599),np.clip(((wx-2350)*4).astype(int),0,2299)]\n                shade=shade*(1-sh*.18)[:,:,None]")
code=code.replace('Reopened X-Plane OBJ exports • Offline material preview','Actual exported meshes / stock pavement texture context')
code=code.replace('Ground, vegetation and aircraft are reference context. X-Plane lighting and weather still need an in-sim check.','Offline preview: native jetway arms, pavement FX and X-Plane weather/lighting are not simulated.')
exec(code)
render('Headquarters_Arrival.png','R25 | A maintained arrival court',[2795,238,49],[2710,328,4],116)
render('Canopy_Finish.png','R25 | Shared materials from headquarters to canopy',[2520,235,55],[2656,337,5],155)
render('Jetway_Connections.png','R25 | Recessed terminal connections for NRT8 / NRT9',[2817,470,24],[2791,420,4.8],47)
render('NRT11_Export.png','R25 | Larger NRT11, nose east',[2590,455,95],[2680,408,0],145)
(OUT/'Render_Evidence.json').write_text(json.dumps(dict(renders=4,triangles=len(scene),actual_export_meshes=True,runtime_tested=False,notes=['Stock diffuse pavement texture context; no XP runway randomizer, wet shader, PBR reflection or animated jetway arms simulated.','Ground shadow is an offline visualization, not simulator acceptance.']),indent=2))
print(json.dumps(dict(renders=4,triangles=len(scene))))
