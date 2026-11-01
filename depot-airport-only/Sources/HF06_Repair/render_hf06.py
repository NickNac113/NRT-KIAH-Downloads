"""Read OBJ8 clockwise front faces and reproduce one-sided visibility.
The exported OBJ8 files, not intermediate author meshes, are the preview input.
Actual stock animated jetways are evaluated at their native parked state.
"""
import bpy, pathlib, json, gzip, math, sys, hashlib, numpy as np
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
OLD=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\work')
AFTER=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
BEFORE=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\outputs\KIAH_2026-10-24_Review_R03_HF05')
OUT=ROOT/'previews-final';OUT.mkdir(exist_ok=True)
infos={'Before':json.loads((ROOT/'work/scene-hf03.json').read_text()),'After':json.loads((ROOT/'work/scene-hf03.json').read_text())}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def material(name,color,rough=.7):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m
mats={k:material(k,v) for k,v in {'concrete':(.42,.44,.43),'asphalt':(.13,.15,.15),'runway':(.28,.30,.29),'context':(.48,.51,.51),'grass':(.17,.23,.16),'yellow':(.85,.55,.055),'white':(.83,.83,.8),'red':(.65,.12,.08),'cyan':(.02,.65,.9),'blue':(.025,.12,.95)}.items()}
atlasmat=material('Native atlas - clockwise front faces only',(1,1,1),.65)
n=atlasmat.node_tree.nodes;link=atlasmat.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(AFTER/'textures/terminal_atlas.png'));tex.interpolation='Linear';link.new(tex.outputs['Color'],p.inputs['Base Color'])
# Use explicit geometric back-face rejection for each orthographic camera.
# A transparency shader is not used: stacked coplanar back faces can exhaust
# Cycles transparent-ray depth and misleadingly produce black silhouettes.
native_data={};groups={'Before':[],'After':[]};textures={}

def obj_mesh(name,vertices,faces,mat):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat);return ob
with gzip.open(ROOT/'work/native-review-context.json.gz','rt') as f:context=json.load(f)
for d in context:
    if d.get('texture'):
        key=d['texture']
        if key not in textures:
            mat=material(pathlib.Path(key).stem,(1,1,1));p=mat.node_tree.nodes.get('Principled BSDF');tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(key);mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha']);textures[key]=mat
        mat=textures[key]
    else:mat=mats[d['material']]
    ob=obj_mesh(d['name'],d['vertices'],d['faces'],mat);groups[d['tag']].append(ob)
    if d.get('uvs'):
        uv=ob.data.uv_layers.new(name='Native UV')
        for poly in ob.data.polygons:
            for li in poly.loop_indices:uv.data[li].uv=d['uvs'][ob.data.loops[li].vertex_index]
    if d.get('cull'):native_data[ob.name]=(np.array(d['vertices']),np.array(d['faces']),d['uvs'],mat)
del context
obj_mesh('Ground',[(-7000,-7000,-.12),(7000,-7000,-.12),(7000,7000,-.12),(-7000,7000,-.12)],[(0,1,2,3)],mats['grass'])

def load_native(pack,m,tag):
    path=pack/'objects'/pathlib.Path(m['path']).name;vs=[];uvs=[];ix=[]
    for line in path.read_text().splitlines():
        t=line.split()
        if not t:continue
        if t[0]=='VT':
            x,y,z=map(float,t[1:4]);vs.append((x+m['origin'][0],-z+m['origin'][1],y+(.07 if m.get('draped') else 0)));uvs.append(tuple(map(float,t[7:9])))
        elif t[0] in ('IDX','IDX10'):ix.extend(map(int,t[1:]))
    # OBJ8 clockwise -> Blender counterclockwise. Axis conversion has det +1.
    faces=[(ix[i],ix[i+2],ix[i+1]) for i in range(0,len(ix),3)]
    ob=obj_mesh(tag+' '+path.stem,vs,faces,atlasmat);uv=ob.data.uv_layers.new(name='Native UV')
    for poly in ob.data.polygons:
        for li in poly.loop_indices:uv.data[li].uv=uvs[ob.data.loops[li].vertex_index]
    native_data[ob.name]=(np.array(vs),np.array(faces),uvs,atlasmat)
    return ob
for tag,pack in [('Before',BEFORE),('After',AFTER)]:groups[tag]+=[load_native(pack,m,tag) for m in infos[tag]['models']]
bpy.ops.object.light_add(type='SUN',location=(0,0,2000));sun=bpy.context.object;sun.rotation_euler=(math.radians(28),math.radians(-24),math.radians(-35));sun.data.energy=2.3;sun.data.angle=math.radians(5)
world=bpy.data.worlds.new('Daylight');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.52,.66,.79,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.transparent_max_bounces=32;s.render.threads_mode='FIXED';s.render.threads=8
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    usable=False
    for device in prefs.devices:device.use=device.type!='CPU';usable=usable or device.use
    if usable:s.cycles.device='GPU'
except Exception:pass
s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.clip_end=20000
views=[
 ('01_D5_Before','Before',(320,553,11),(311.2,569.8,5),13,1400,1000),
 ('02_D5_After','After',(320,553,11),(311.2,569.8,5),13,1400,1000),
 ('04_B_North_After','After',(-30,1050,590),(-400,565,4),700,1800,1200)]
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for name,tag,pos,target,scale,w,h in views:
    if requested and name not in requested:continue
    for group,objects in groups.items():
        for ob in objects:ob.hide_render=group!=tag
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    toward_camera=(Vector(pos)-Vector(target)).normalized()
    for ob in groups[tag]:
        if ob.name not in native_data:continue
        vs,faces,uvs,mat=native_data[ob.name]
        normals=np.cross(vs[faces[:,1]]-vs[faces[:,0]],vs[faces[:,2]]-vs[faces[:,0]])
        visible=faces[normals@np.array(toward_camera)>1e-8]
        oldmesh=ob.data;mesh=bpy.data.meshes.new(ob.name+' front faces');mesh.from_pydata(vs.tolist(),[],visible.tolist());mesh.update();mesh.materials.append(mat);ob.data=mesh;bpy.data.meshes.remove(oldmesh)
        uv=mesh.uv_layers.new(name='Native UV')
        for poly in mesh.polygons:
            for li in poly.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/(name+'.png'))
    print('RENDERING',name,flush=True);bpy.ops.render.render(write_still=True);print('FINISHED',name,flush=True)

manifest=dict(game_capture=False,renderer='Blender Cycles; actual custom OBJ8 assets and stock parked jetway meshes.',scope='Native first-wins pavement layering, including paint/light attributes attached to 110 pavement boundaries and separate 120 markings. Simplified surface materials and line widths. Blue dots illustrate edge-light paths with approximate spacing; actual lamp assets and exact spacing are not simulated. Gray retained building massing is simplified. Terrain relief, AEP effects, equipment and traffic are omitted. No docking simulation.',airport_data_inputs=json.loads((ROOT/'work/native-review-inputs.json').read_text()))
(OUT/'Preview_Method.json').write_text(json.dumps(manifest,indent=2))
