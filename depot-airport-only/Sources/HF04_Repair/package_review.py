from common import *
import shutil,zipfile,html
PRE=ROOT/'previews-final'
report=json.loads((ROOT/'HF04_Validation.json').read_text())
assert report['passed']==report['total']==12
method=json.loads((PRE/'Preview_Method.json').read_text())
assert method['airport_data_inputs']['After']==sha(STAGE/'Earth nav data/apt.dat')
assert method['airport_data_inputs']['Before']==sha(SOURCE/'Earth nav data/apt.dat')
assert len(list(PRE.glob('*.png')))==4
assert json.loads((ROOT/'live_before.json').read_text())=={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()}
assert sha(LIVE.parent/'scenery_packs.ini')==(ROOT/'ini_before.sha256').read_text()
notes='''KIAH R03 HF04 - B NORTH ISLAND CLEANUP
24 October 2026
STAGED FOR REVIEW. NOT INSTALLED. X-PLANE TEST PENDING.

HF03 was reported to look good except for the old island and taxiway markings
beside B5. HF04 addresses this local B North apron defect.

CHANGES
* Cover approximately 18,368 square metres of exposed legacy asphalt with
  light apron concrete, including a 1 cm overlap to avoid coordinate slivers.
* Remove obsolete island-edge paint and blue edge-light paths at the rebuilt
  B pier tips and where this apron now joins taxiway NB. Remove six small
  inherited marking fragments in the same local area.
* Edit 28 edge attributes across nine source records, removing approximately
  1,003 metres of obsolete edge/marking paths. This is path length, not a count
  of separate painted stripes or light fixtures.
* Preserve all original pavement geometry and Bezier curves. Where an edited
  painted edge crosses the repair boundary, retain its outside portion as a
  separate line; the original pavement boundary itself is unchanged.

PRESERVED
All five runways, 988 aircraft taxi edges, 622 service edges, 1,450 shared route
nodes, 240 aircraft starts, 119 service starts/destinations, 116 moving jetways,
flow rules and authored stand/GSE/circulation markings remain unchanged.
All DSFs, custom models, textures, buildings and exclusions are byte-identical
to the sealed HF03 package. This repair does not revise the airport layout.

CHECKS AND PREVIEWS
12/12 targeted offline checks passed against the written airport file.
They verify local surface coverage, removal of obsolete paint/light paths,
preservation outside the cleanup area, and unchanged operational records.
The original pavement nodes and curves were checked independently of style
attributes. Retained painted/light paths outside the repair agree within
4 mm at the source sampling and native output precision.
The installed HF03 package and scenery order are unchanged.

These are custom offline checks, not WED validation or simulator acceptance.
The previews render actual custom models and stock moving-jetway meshes at
their parked positions. Native pavement layering is resolved in file order.
Both pavement-attached edge markings and separate line features are included.
Materials, paint widths and lighting are approximate. Blue dots illustrate
light paths; actual fixture geometry and exact spacing are not simulated.
Retained buildings are simplified gray massing. AEP effects, terrain relief,
traffic and equipment are omitted. The views are not X-Plane screenshots.

AFTER AN APPROVED INSTALL
1. Load B5 and inspect the apron from the angle in your screenshot. The dark
   rounded islands, duplicate yellow borders and blue lights across the new
   apron should be gone.
2. Inspect the other B pier tip around B17/B18 and the junction with NB.
   Stand lead-ins, ground gate numbers and the active NB centerline remain.
3. Check the new-to-retained pavement boundary for a seam or stray lights,
   ideally in daylight and at dusk.
HF03's remaining docking, AI/service behavior and layout-evidence limitations
continue to apply; this local cleanup does not expand their acceptance.

INSTALLATION
This is a complete successor airport for the existing single R03 add-on slot.
After approval, back up HF03 and replace that slot, retaining its scenery order.
Do not enable HF03 and HF04 as competing KIAH airports. No installation or
simulator reload was performed while preparing this review.

PROVENANCE
HF03 and earlier source/repair records remain under Sources. HF04 records
describe the latest local repair and take precedence for its staged status.
Build helpers require preserved workspace inputs and are included for audit,
not as a standalone portable build system. No third-party AEP assets are copied.
Technical reference:
https://developer.x-plane.com/article/airport-data-apt-dat-12-00-file-format-specification/
'''
changes=json.loads((ROOT/'HF04_Changes.json').read_text())
count=len(set(x['block'] for x in changes['edited_edge_attributes']))
notes=notes.replace('across nine source records',f'across {count} source records')
hist=STAGE/'Sources/R03_HF03_historical_notes.txt'
if not hist.exists():shutil.copy2(SOURCE/'README.txt',hist)
(STAGE/'README.txt').write_text(notes,encoding='utf-8')
(PRE/'Repair_Notes.txt').write_text(notes,encoding='utf-8')
src=STAGE/'Sources/HF04_Repair';src.mkdir(exist_ok=True)
for name in ('common.py','repair_hf04.py','validate_hf04.py','setup_previews.py','prepare_previews.py','render_hf04.py','package_review.py'):
    shutil.copy2(ROOT/'work'/name,src/name)
for name in ('HF04_Changes.json','HF04_Validation.json'):
    shutil.copy2(ROOT/name,src/name);shutil.copy2(ROOT/name,PRE/name)
shutil.copy2(PRE/'Preview_Method.json',src/'Preview_Method.json')
manifest={p.relative_to(STAGE).as_posix():sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'}
(STAGE/'SHA256SUMS.txt').write_text(''.join(f'{h}  {p}\n' for p,h in manifest.items()))
archive=ROOT/(STAGE.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(STAGE.rglob('*')):
        if p.is_file():z.write(p,STAGE.name+'/'+p.relative_to(STAGE).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for p,h in manifest.items():assert hashlib.sha256(z.read(STAGE.name+'/'+p)).hexdigest()==h
receipt=dict(revision='KIAH R03 HF04',status='STAGED - NOT INSTALLED',checks='12/12 targeted offline',archive=archive.name,sha256=sha(archive),files=len(manifest)+1,
             predecessor='KIAH R03 HF03',installed_package_unchanged=True,scenery_order_unchanged=True,
             runtime_file_changes=['Earth nav data/apt.dat'],simulator_acceptance='Pending')
(PRE/'Package_Receipt.json').write_text(json.dumps(receipt,indent=2))
views=[['B North apron','02_B_North_After.png','01_B_North_Before.png','The old island outlines become continuous concrete apron. The separate grass island between the active taxiways is retained.'],
       ['B5 and the pier tips','04_B5_Island_After.png','03_B5_Island_Before.png','The obsolete asphalt border, yellow edge paint and blue lights are removed beside the rebuilt stands. Gate lead-ins and the active circulation line remain.']]
table=''.join(f'<tr><td>Pass</td><td>{html.escape(x["check"])}</td></tr>' for x in report['checks'])
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KIAH HF04 — island cleanup</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111b23;color:#e8eef2;font:16px/1.55 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:36px;margin:6px 0}h2{font-size:23px}.status{color:#ffd18a;font-size:13px;font-weight:700;letter-spacing:.1em}p{max-width:1100px;color:#c7d4dc}.stats{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0}.stats>div{background:#20313d;border-radius:8px;padding:14px 22px}.stats b{display:block;font-size:26px;color:#9ce0d4}.viewer{padding:18px;background:#1e2d38;border-radius:12px}.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0}button{font:inherit;border:1px solid #527182;background:#14232e;color:#d9ecf3;padding:8px 15px;border-radius:6px;cursor:pointer}button.active{background:#34766c}button:focus-visible{outline:3px solid #ffd18a}.label{margin-left:auto;font-size:12px;letter-spacing:.08em;color:#ffd18a}img{width:100%;display:block;border-radius:6px}figure{margin:0}figcaption{margin:12px 0;color:#d0dce3}a{color:#9ce0d4}li{margin-bottom:7px}details{padding:18px 0}summary{cursor:pointer;font-weight:bold}table{border-collapse:collapse;width:100%;margin-top:12px}td{padding:8px;border-bottom:1px solid #36505f}td:first-child{color:#9ce0d4;width:60px}footer{color:#a3b7c3;border-top:1px solid #36505f;margin-top:25px;padding-top:16px}.links{display:flex;gap:22px;flex-wrap:wrap}</style></head>
<body><main><div class="status">STAGED · NOT INSTALLED</div><h1>KIAH R03 HF04</h1><p>A focused cleanup of the leftover islands and taxiway-edge markings beside B5 and the other B North pier. The old asphalt borders become apron concrete, and their obsolete paint and blue edge lights are removed.</p>
<div class="stats"><div><b>12 / 12</b>targeted checks passed</div><div><b>116</b>jetways preserved</div><div><b>988 + 622</b>aircraft + service edges unchanged</div></div>
<section class="viewer"><h2 id="title">B North apron</h2><div class="controls"><button class="view active" data-i="0">B North apron</button><button class="view" data-i="1">B5 and pier tips</button><span class="label">OFFLINE PREVIEW</span></div><div class="controls"><button id="after" class="active">Staged HF04</button><button id="before">HF03 before cleanup</button></div><figure><a id="full" href="02_B_North_After.png" target="_blank"><img id="picture" src="02_B_North_After.png" alt="HF04 B North apron cleanup"></a><figcaption id="caption"></figcaption></figure></section>
<p>These are offline views of the native airport geometry. Surface materials, line widths and lighting are approximate. Blue dots illustrate edge-light paths; gray retained buildings are simplified. Simulator appearance still needs a test.</p>
<h2>What changed</h2><ul><li>Replaced the exposed legacy asphalt with light apron concrete.</li><li>Removed island-edge paint and blue lights, including the obsolete border at the apron’s junction with NB.</li><li>Preserved the gate markings, parked jetway positions, buildings, active routes and scenery order.</li></ul>
<h2>First checks after installation</h2><ol><li>Load B5 and use the same camera angle as your screenshot. The rounded dark borders and blue lights across the apron should be gone.</li><li>Inspect B17/B18 and the connection to NB. Check the retained gate lead-ins and taxiway centerline.</li><li>Look for a surface seam or stray lights at the repair boundary, in daylight and at dusk.</li></ol>
<details><summary>Validation details</summary><table>TABLE</table></details><div class="links"><a href="Repair_Notes.txt">Repair notes</a><a href="HF04_Validation.json">Validation report</a><a href="Preview_Method.json">Preview method</a><a href="Package_Receipt.json">Package receipt</a></div>
<footer>24 October 2026 · HF04 is a complete successor for the existing KIAH add-on. Installed HF03 is untouched. No installation or simulator reload was performed.</footer></main>
<script>const views=VIEWS;let selected=0,mode='after';function show(){const v=views[selected],file=mode==='after'?v[1]:v[2];document.getElementById('title').textContent=v[0];document.getElementById('picture').src=file;document.getElementById('picture').alt=v[0]+' — '+(mode==='after'?'staged HF04':'HF03 before cleanup');document.getElementById('full').href=file;document.getElementById('caption').textContent=(mode==='after'?'HF04: ':'HF03 before cleanup: ')+v[3];for(const b of document.querySelectorAll('.view'))b.classList.toggle('active',Number(b.dataset.i)===selected);document.getElementById('after').classList.toggle('active',mode==='after');document.getElementById('before').classList.toggle('active',mode==='before')}for(const b of document.querySelectorAll('.view'))b.onclick=()=>{selected=Number(b.dataset.i);show()};document.getElementById('after').onclick=()=>{mode='after';show()};document.getElementById('before').onclick=()=>{mode='before';show()};show();</script></body></html>'''
(PRE/'Review.html').write_text(page.replace('TABLE',table).replace('VIEWS',json.dumps(views)),encoding='utf-8')
print(json.dumps(receipt,indent=2))
