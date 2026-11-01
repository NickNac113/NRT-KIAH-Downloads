from common import *
import shutil
src=(PREV/'work/prepare_previews.py').read_text()
head=src[:src.index('for tag,pack,d,a in ')]
head=head.replace("STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03'","STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF04'")
head=head.replace("plan,before,oldapt,oldscene=pickle.loads((ROOT/'work/current.pkl').read_bytes())","plan,oldapt,before=pickle.loads((ROOT/'work/current.pkl').read_bytes())")
head=head.replace("scene=json.loads((ROOT/'work/scene-hf03.json').read_text())",'from common import SOURCE, visible_surfaces')
head=head.replace('crop=box(-1600,-1100,2200,1100)','crop=box(-750,300,30,850)')
loop=src[src.index('    for i,e in enumerate(d[\'entities\']):'):src.index('# Show the B5 aircraft clearance envelope')]
loop=loop.replace("for i,b in enumerate(x for x in a if x['code']==1500):active_jetway(b,tag,i)","for i,b in enumerate(x for x in a if x['code']==1500):\n        if crop.buffer(60).contains(Point(xy(float(b['parts'][2]),float(b['parts'][1])))):active_jetway(b,tag,i)")
body='''
for tag,pack,d,a in [('Before',SOURCE,before,oldapt),('After',STAGE,before,parse_apt(STAGE/'Earth nav data/apt.dat'))]:
    paved={};markings={};lights=[]
    # apt.dat pavement is first-wins; remove hidden portions before meshing.
    for i,surf,g in visible_surfaces(a):
        mat='asphalt' if surf==1 or 20<=surf<40 else 'concrete'
        if not g.is_empty:paved.setdefault(mat,[]).append(g)
    for b in a:
        if b['code'] not in (110,120):continue
        # Pavement-attached markings are just as visible as standalone lines.
        for line,styles in sampled_apt_segments(b):
            if not line.intersects(crop):continue
            for st in styles:
                code=int(st)
                if code==102:
                    for dist in np.arange(0,line.length,16):
                        p=line.interpolate(dist)
                        if crop.contains(p):lights.append(p.buffer(.52))
                if code>=100:continue
                col='white' if code in (20,21,22,24,25,70,71,72,74,75) else 'red' if code in (19,59) else 'yellow'
                g=line.intersection(crop)
                if code in (3,53):g=unary_union([g.offset_curve(.24),g.offset_curve(-.24)])
                if not g.is_empty:markings.setdefault(col,[]).append(g.buffer(.11,cap_style=2,join_style=2))
    for mat,gs in paved.items():flat(tag+' visible native pavement '+mat,unary_union(gs),.005,tag,mat)
    for col,gs in markings.items():flat(tag+' native paint '+col,unary_union(gs),.06,tag,col)
    if lights:flat(tag+' illustrative blue edge-light locations',unary_union(lights),.15,tag,'blue')
'''
tail="""
with gzip.open(ROOT/'work/native-review-context.json.gz','wt',compresslevel=3) as f:json.dump(out,f,separators=(',',':'))
(ROOT/'work/native-review-inputs.json').write_text(json.dumps({tag:hashlib.sha256((pack/'Earth nav data/apt.dat').read_bytes()).hexdigest() for tag,pack in [('Before',SOURCE),('After',STAGE)]},indent=2))
print(json.dumps(dict(mesh_batches=len(out),parked_jetways=animation_counts,triangles=sum(len(x['faces']) for x in out)),indent=2))
"""
(ROOT/'work/prepare_previews.py').write_text(head+body+loop+tail)
for name in ('stock-sign-atlas.png','stock-dir-atlas.png','scene-hf03.json'):shutil.copy2(PREV/'work'/name,ROOT/'work'/name)
render=(PREV/'work/render_hf03.py').read_text()
render=render.replace("BEFORE=pathlib.Path(r'X:\\X-Plane 12\\Custom Scenery\\KIAH_2026-10-24_Review_R03')",f'BEFORE=pathlib.Path({str(SOURCE)!r})')
render=render.replace("AFTER=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03'","AFTER=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF04'")
render=render.replace("(ROOT.parent/'KIAH_R03_HF02_Repair/work/scene-hf02.json')","(ROOT/'work/scene-hf03.json')")
render=render.replace("'cyan':(.02,.65,.9)","'cyan':(.02,.65,.9),'blue':(.025,.12,.95)")
start=render.index('views=[');end=render.index('requested=sys.argv',start)
render=render[:start]+'''views=[
 ('01_B_North_Before','Before',(-15,1040,420),(-410,565,4),700,1800,1200),
 ('02_B_North_After','After',(-15,1040,420),(-410,565,4),700,1800,1200),
 ('03_B5_Island_Before','Before',(-105,780,170),(-385,625,3),510,1800,1050),
 ('04_B5_Island_After','After',(-105,780,170),(-385,625,3),510,1800,1050)]
'''+render[end:]
render=render[:render.index('manifest=dict(')]+"""
manifest=dict(game_capture=False,renderer='Blender Cycles; actual custom OBJ8 assets and stock parked jetway meshes.',scope='Native first-wins pavement layering, including paint/light attributes attached to 110 pavement boundaries and separate 120 markings. Simplified surface materials and line widths. Blue dots illustrate edge-light paths with approximate spacing; actual lamp assets and exact spacing are not simulated. Gray retained building massing is simplified. Terrain relief, AEP effects, equipment and traffic are omitted. No docking simulation.',airport_data_inputs=json.loads((ROOT/'work/native-review-inputs.json').read_text()))
(OUT/'Preview_Method.json').write_text(json.dumps(manifest,indent=2))
"""
(ROOT/'work/render_hf04.py').write_text(render)
