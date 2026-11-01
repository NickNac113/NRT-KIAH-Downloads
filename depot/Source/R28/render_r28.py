"""Local renders of exported OBJ8 geometry and installed native facade meshes."""
import bpy,sys,json,gzip,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.7
    return m

mats={k:material(k,v) for k,v in dict(concrete=(.56,.57,.55),asphalt=(.15,.16,.16),context=(.5,.52,.52),grass=(.22,.28,.16),roof=(.55,.56,.54),yellow=(.9,.59,.05),white=(.9,.9,.86),red=(.65,.13,.08),black=(.045,.046,.04)).items()}
textures={};emissions=[]

def texmat(d):
    key=(d['texture'],d.get('lit'))
    if key in textures:return textures[key]
    m=material(Path(key[0]).stem,(1,1,1));n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(key[0],check_existing=True);l.new(t.outputs['Color'],p.inputs['Base Color']);l.new(t.outputs['Alpha'],p.inputs['Alpha'])
    if key[1]:
        t2=n.new('ShaderNodeTexImage');t2.image=bpy.data.images.load(key[1],check_existing=True);l.new(t2.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=0;emissions.append(p)
    textures[key]=m;return m

# Ground in these offline renders is a restrained material approximation.
# The package retains X-Plane's native concrete/weather system unchanged.
m=mats['concrete'];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
axes=[]
for axis in ['X','Y']:
    mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=1/5;l.new(sep.outputs[axis],mul.inputs[0])
    fract=n.new('ShaderNodeMath');fract.operation='PINGPONG';fract.inputs[1].default_value=.5;l.new(mul.outputs[0],fract.inputs[0])
    less=n.new('ShaderNodeMath');less.operation='LESS_THAN';less.inputs[1].default_value=.0025;l.new(fract.outputs[0],less.inputs[0]);axes.append(less)
mx=n.new('ShaderNodeMath');mx.operation='MAXIMUM';l.new(axes[0].outputs[0],mx.inputs[0]);l.new(axes[1].outputs[0],mx.inputs[1])
mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.57,.575,.55,1);mix.inputs[2].default_value=(.24,.26,.25,1);l.new(mx.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],p.inputs['Base Color'])
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=30;l.new(geo.outputs['Position'],noise.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])

with gzip.open(ROOT/'qa/Preview_Meshes.json.gz','rt') as f:data=json.load(f)
for d in data:
    mat=texmat(d) if d.get('texture') else mats.get(d['material'],mats['context'])
    mesh=bpy.data.meshes.new(d['name']);mesh.from_pydata(d['vertices'],[],d['faces']);mesh.update()
    ob=bpy.data.objects.new(d['name'],mesh);bpy.context.collection.objects.link(ob);mesh.materials.append(mat)
    if d.get('uvs'):
        layer=mesh.uv_layers.new(name='Native UV')
        for poly in mesh.polygons:
            for li in poly.loop_indices:layer.data[li].uv=d['uvs'][mesh.loops[li].vertex_index]
del data
bpy.ops.object.light_add(type='SUN',location=(0,0,1000));sun=bpy.context.object;sun.rotation_euler=(math.radians(25),math.radians(-30),math.radians(-25));sun.data.energy=2.6;sun.data.angle=.06
world=bpy.data.worlds.new('Sky');bpy.context.scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.65,.75,.88,1);bg.inputs[1].default_value=.55
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.cycles.transparent_max_bounces=64;s.cycles.max_bounces=8
s.render.threads_mode='FIXED';s.render.threads=8
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    if any(d.use for d in prefs.devices):s.cycles.device='GPU'
except Exception:pass
s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.clip_end=5000
views=[
    ('Terminal_B_Overview',(-900,1080,600),(-390,500,3),740,1800,1200,False),
    ('Terminal_B_Gate_Detail',(-410,585,25),(-490,551,7),100,1800,1100,False),
    ('Terminal_B_Evening',(-410,585,25),(-490,551,7),100,1800,1100,True),
    ('Terminal_B_Passenger_Windows',(-442,516,7),(-489.6,522,7),25,1500,950,True)]
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for name,pos,target,scale,w,h,dusk in views:
    if requested and name not in requested:continue
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    sun.data.energy=.16 if dusk else 2.6;bg.inputs[1].default_value=.18 if dusk else .55
    for p in emissions:p.inputs['Emission Strength'].default_value=.65 if dusk else 0
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(ROOT/'output'/(name+'.png'))
    print('RENDERING',name,flush=True);bpy.ops.render.render(write_still=True);print('FINISHED',name,flush=True)
(ROOT/'qa/Preview_Method.json').write_text(json.dumps(dict(game_capture=False,method='Exported custom OBJ8 meshes; stock terminal-kit facade segments, textures and roof attachments; stock animated jetways evaluated parked.',limits='Facade spelling choice approximates X-Plane. Ground material, paint widths and lighting are review approximations. Simulator weather, terrain, animated traffic and docking are not simulated. No AEP assets used.'),indent=2))
