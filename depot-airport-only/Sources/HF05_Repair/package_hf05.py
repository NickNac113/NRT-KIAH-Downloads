from hf05_common import *
import zipfile,html
PRE=ROOT/'previews-final'
report=json.loads((ROOT/'HF05_Validation.json').read_text())
assert report['passed']==report['total']==15
inputs=json.loads((ROOT/'work/native-review-inputs.json').read_text())
assert inputs['Before']==sha(SOURCE/'Earth nav data/apt.dat')
assert inputs['After']==sha(STAGE/'Earth nav data/apt.dat')
method=dict(revision='KIAH R03 HF05',
    images={
      '00_User_HF04_Screenshot.png':'Unmodified user-supplied X-Plane screenshot of installed HF04. Runtime before evidence.',
      '02_B_North_After.png':'Offline Blender render of staged HF05 native pavement, actual custom OBJ8 models, stock parked jetway meshes and retained markings.',
      '04_B5_Island_After.png':'Offline Blender render of staged HF05 pier tips and apron.',
      '05_AEP_Overlay_Audit.png':'Geometry audit map of the installed AEP asphalt overlay footprint, HF04 cleanup boundary and retained native airport layout.'},
    renderer='Blender Cycles for after views; matplotlib for source audit map.',
    scope='After views are geometry previews, not simulator screenshots. Surface colours, line widths and lighting are approximate. Gray retained building massing is simplified. AEP material replacements and visual effects, terrain relief, equipment and traffic are not rendered. No docking or vehicle simulation. The separately decoded final DSF exclusions were checked against the installed AEP overlay primitives. Exclusions remove whole overlay primitives, not just the portion within a mask; retained native airport pavement remains outside the local asphalt cut.',
    airport_data_inputs=inputs,
    final_south_dsf_sha256=sha(STAGE/'Earth nav data/+20-100/+29-096.dsf'),
    acceptance='Offline checks only; X-Plane visual test pending.')
(PRE/'Preview_Method.json').write_text(json.dumps(method,indent=2))
notes='''KIAH R03 HF05 - AEP OVERLAY AND SOURCE ASPHALT REPAIR
24 October 2026
STAGED FOR REVIEW. NOT INSTALLED. X-PLANE TEST PENDING.

FINDINGS
The installed AEP Houston overlay contains the old rounded asphalt footprint
across the rebuilt B North apron, plus a matching snow layer. AEP also replaces
native pavement materials. HF04 removed the old edge markings and lights but
kept the original asphalt under its concrete cover.

Our previous polygon exclusions used comma-only coordinate values. The actual
WED exporter writes longitude/latitude pairs separated by commas. The earlier
offline exclusion audit accepted the wrong representation and therefore did
not establish that X-Plane would apply those exclusions. This repair corrects
our airport package. No AEP assets or library mappings are changed.

CHANGES
* Remove 41,407.789 square metres from the one underlying legacy asphalt
  polygon within the existing HF04 B North cleanup boundary. This includes
  areas already hidden under concrete; it is not an exposed-area measurement.
  Retain the remainder as three polygons. The former asphalt area is concrete.
* Correct all 4,732 existing polygonal exclusion records in the southern DSF
  to the syntax emitted by WED, with counter-clockwise point order. Their
  footprints, categories and property order are unchanged. This restores the
  intended exclusions authored in earlier revisions across the airport, so
  the effect is broader than the small B North pavement cut.
* Patch only the DSF property payload and checksum. All packed placement,
  resource and command data is preserved exactly. Re-encoding the full DSF
  was rejected because it slightly quantized object headings.

AEP EFFECT
Both AEP legacy asphalt and asphalt-snow overlay primitives intersecting the
repair are covered by the corrected polygon exclusions. All 30 AEP overlay
primitives touching that area are covered by the intended categories.
X-Plane exclusions remove a whole primitive when a qualifying point is inside;
they do not clip only the overlap. The native active pavement outside the
repair is retained. AEP remains enabled and supplies its normal replacements
where not excluded. This does not disable AEP globally.

PRESERVED AND VERIFIED
15/15 targeted offline checks pass. The only changed runtime files are apt.dat
and the southern DSF. All other airport records, all five runways, 988 aircraft
taxi edges, 622 service edges, 1,450 shared nodes, 240 aircraft starts, 119
service starts/destinations, 116 animated jetways, custom models and textures
are preserved. Both DSF tiles decode successfully and all placements compare
exactly. The northern DSF is byte-identical to HF04.

The clipped asphalt curves were flattened with a 0.5 mm geometric tolerance.
An independent finer sampling measured maximum outside-boundary difference
of 0.4083 mm. Removed asphalt is covered by concrete. HF04's removal of the old
edge paint and lights is retained.

The installed HF04 package, scenery order, AEP Library.txt and Houston AEP
overlay DSFs remain untouched. These are custom offline checks, not WED
validation or simulator acceptance.

PREVIEWS
The user screenshot is the actual HF04 before state. HF05 after views render
native airport geometry, actual custom terminal models and stock jetway meshes
in their parked positions. Surface appearance and lighting are approximate.
They do not render AEP textures/effects, terrain relief, equipment or traffic.
The AEP footprint map is a separate source-geometry audit. No image is presented
as an HF05 X-Plane screenshot. See Preview_Method.json for exact input hashes.

FIRST TESTS AFTER AN APPROVED INSTALL
1. With AEP enabled, load B5 and inspect the same view as the submitted
   screenshot. Look for a continuous concrete apron where the dark rounded
   island borders remained in HF04.
2. Inspect the other B pier tip at B17/B18 and the junction with NB. Retained
   gate markings, active taxiway centerlines and the grass island should remain.
3. Inspect D/E, terminal roads and the United maintenance hangar as a regression
   check because previously intended airport exclusions now use corrected syntax.
4. Check the local surface boundary in daylight and at dusk. Report any remaining
   dark patch, missing pavement or stray edge lights. Docking and AI/service
   runtime limitations from earlier revisions still apply.

INSTALLATION
This is a complete successor for the existing single R03 KIAH add-on slot.
After approval, back up HF04 and replace that slot while retaining scenery
priority. Do not enable both packages as competing KIAH airports. No install,
simulator restart or scenery reload was performed to prepare this review.

PROVENANCE
Earlier revision records remain under Sources as historical material. HF05
notes and validation supersede older claims about the exclusion check.
Build helpers are audit copies requiring preserved local workspace inputs;
they are not a portable build system. repair_hf05.py invokes the property-only
DSF patch before validation. No third-party AEP resources are redistributed.

PRIMARY TECHNICAL REFERENCES
Actual WED exporter, polygon exclusion formatting:
https://github.com/X-Plane/xptools/blob/master/src/WEDImportExport/WED_DSFExport.cpp#L1447-L1480
The developer article's coordinate example differs from the exporter. HF05
follows the exporter and still requires a simulator test.
https://developer.x-plane.com/article/dsf-usage-in-x-plane/
https://developer.x-plane.com/article/dsf-file-format-specification/
'''
hist=STAGE/'Sources/R03_HF04_historical_notes.txt'
if not hist.exists():shutil.copy2(SOURCE/'README.txt',hist)
(STAGE/'README.txt').write_text(notes,encoding='utf-8')
(PRE/'Repair_Notes.txt').write_text(notes,encoding='utf-8')
src=STAGE/'Sources/HF05_Repair';src.mkdir(exist_ok=True)
for name in ('hf05_common.py','repair_hf05.py','preserve_dsf_binary.py','validate_hf05.py','prepare_previews.py','render_hf05.py','aep_preview_map.py','package_hf05.py'):
    shutil.copy2(ROOT/'work'/name,src/name)
for name in ('HF05_Changes.json','HF05_Validation.json'):
    shutil.copy2(ROOT/name,src/name);shutil.copy2(ROOT/name,PRE/name)
shutil.copy2(PRE/'Preview_Method.json',src/'Preview_Method.json')
manifest={p.relative_to(STAGE).as_posix():sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'}
(STAGE/'SHA256SUMS.txt').write_text(''.join(f'{h}  {p}\n' for p,h in manifest.items()))
archive=ROOT/(STAGE.name+'.zip')
assert not archive.exists(),'Do not overwrite a sealed archive'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(STAGE.rglob('*')):
        if p.is_file():z.write(p,STAGE.name+'/'+p.relative_to(STAGE).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for p,h in manifest.items():assert hashlib.sha256(z.read(STAGE.name+'/'+p)).hexdigest()==h
receipt=dict(revision='KIAH R03 HF05',status='STAGED - NOT INSTALLED',checks='15/15 targeted offline',archive=archive.name,sha256=sha(archive),files=len(manifest)+1,
    predecessor='KIAH R03 HF04',installed_package_unchanged=True,scenery_order_unchanged=True,aep_unchanged=True,
    runtime_file_changes=['Earth nav data/apt.dat','Earth nav data/+20-100/+29-096.dsf'],simulator_acceptance='Pending')
(PRE/'Package_Receipt.json').write_text(json.dumps(receipt,indent=2))
views=[
 ['B5 and pier tips','04_B5_Island_After.png','HF05 OFFLINE PREVIEW','The obsolete source asphalt has been cut out of the rebuilt apron. Gate lead-ins and parked jetways are preserved. Colours and lighting are approximate.'],
 ['B North overview','02_B_North_After.png','HF05 OFFLINE PREVIEW','Continuous concrete around both rebuilt pier tips. The separate grass island between the active taxiways remains.'],
 ['AEP overlay source','05_AEP_Overlay_Audit.png','SOURCE GEOMETRY AUDIT','Orange shows the old AEP asphalt overlay footprint. The corrected existing exclusions target this overlay. Cyan outlines the local source-pavement cleanup; exclusion removes a whole overlay primitive, including portions outside that outline.'],
 ['Your HF04 screenshot','00_User_HF04_Screenshot.png','USER SCREENSHOT · HF04','Your unmodified screenshot shows the rounded dark bands remaining after HF04. This is the runtime before view; the HF05 previews use different camera angles.']]
table=''.join(f'<tr><td>Pass</td><td>{html.escape(c["check"])}</td></tr>' for c in report['checks'])
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KIAH HF05 — AEP and apron repair</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111b23;color:#e8eef2;font:16px/1.55 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:36px;margin:6px 0}h2{font-size:23px}.status{color:#ffd18a;font-size:13px;font-weight:700;letter-spacing:.1em}p{max-width:1140px;color:#c7d4dc}.stats{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0}.stats>div{background:#20313d;border-radius:8px;padding:14px 22px}.stats b{display:block;font-size:24px;color:#9ce0d4}.viewer{padding:18px;background:#1e2d38;border-radius:12px}.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0}button{font:inherit;border:1px solid #527182;background:#14232e;color:#d9ecf3;padding:8px 15px;border-radius:6px;cursor:pointer}button.active{background:#34766c}button:focus-visible{outline:3px solid #ffd18a}.label{font-size:12px;letter-spacing:.08em;color:#ffd18a;margin:12px 0}img{width:100%;display:block;border-radius:6px}figure{margin:0}figcaption{margin:12px 0;color:#d0dce3}a{color:#9ce0d4}li{margin-bottom:8px}details{padding:18px 0}summary{cursor:pointer;font-weight:bold}table{border-collapse:collapse;width:100%;margin-top:12px}td{padding:8px;border-bottom:1px solid #36505f}td:first-child{color:#9ce0d4;width:60px}footer{color:#a3b7c3;border-top:1px solid #36505f;margin-top:25px;padding-top:16px}.links{display:flex;gap:22px;flex-wrap:wrap}</style></head><body><main>
<div class="status">STAGED · NOT INSTALLED · SIMULATOR TEST PENDING</div><h1>KIAH R03 HF05</h1>
<p>AEP contains the old asphalt overlay seen around the B North pier tips. HF05 corrects our airport’s exclusions and removes the underlying legacy asphalt, addressing both sources of the remaining dark bands.</p>
<div class="stats"><div><b>AEP stays enabled</b>no AEP files changed</div><div><b>15 / 15</b>targeted offline checks passed</div><div><b>116 jetways</b>positions and records preserved</div></div>
<section class="viewer"><h2 id="title">B5 and pier tips</h2><div class="controls"><button class="view active" data-i="0">B5 and pier tips</button><button class="view" data-i="1">B North overview</button><button class="view" data-i="2">AEP overlay source</button><button class="view" data-i="3">Your HF04 screenshot</button></div><div id="label" class="label">HF05 OFFLINE PREVIEW</div><figure><a id="full" href="04_B5_Island_After.png" target="_blank"><img id="picture" src="04_B5_Island_After.png" alt="HF05 B5 apron geometry preview"></a><figcaption id="caption"></figcaption></figure></section>
<p>The after views use the staged airport geometry with approximate surface colours. They are not X-Plane screenshots and do not reproduce AEP’s material effects. The corrected exclusions were checked separately against the installed AEP overlay. Visual confirmation in X-Plane is still needed.</p>
<h2>What changed</h2><ul><li>Removed the old source asphalt within the existing B North cleanup area, leaving concrete apron.</li><li>Corrected the format of the airport’s existing polygon exclusions. The previous offline audit accepted the wrong format, so it did not prove those exclusions worked.</li><li>Preserved the exclusion boundaries, buildings, gate markings, aircraft routes, service routes and jetway positions. HF04’s light and marking cleanup remains.</li></ul>
<p>The exclusion correction applies to previously authored exclusions across the airport. It can affect more than B North. AEP’s old overlays are removed as whole pieces; native active pavement outside the local cleanup remains.</p>
<h2>First checks after installation</h2><ol><li>Load B5 with AEP enabled and compare the rounded dark bands with your screenshot.</li><li>Inspect B17/B18, the connection to NB, and the retained grass island and taxiway markings.</li><li>Recheck D/E, terminal roads and the United maintenance hangar because the correction also restores other intended exclusions.</li></ol>
<details><summary>Validation details</summary><table>CHECKTABLE</table></details><div class="links"><a href="Repair_Notes.txt">Repair notes</a><a href="HF05_Validation.json">Validation report</a><a href="Preview_Method.json">Preview method</a><a href="Package_Receipt.json">Package receipt</a></div>
<footer>24 October 2026 · Complete successor for the existing KIAH add-on slot. Installed HF04, scenery order and AEP remain untouched. No restart or scenery reload performed.</footer></main>
<script>const views=VIEWDATA;function show(i){const v=views[i];document.getElementById('title').textContent=v[0];document.getElementById('picture').src=v[1];document.getElementById('picture').alt=v[0];document.getElementById('full').href=v[1];document.getElementById('label').textContent=v[2];document.getElementById('caption').textContent=v[3];for(const b of document.querySelectorAll('.view'))b.classList.toggle('active',Number(b.dataset.i)===i)}for(const b of document.querySelectorAll('.view'))b.onclick=()=>show(Number(b.dataset.i));show(0);</script></body></html>'''
(PRE/'Review.html').write_text(page.replace('CHECKTABLE',table).replace('VIEWDATA',json.dumps(views)),encoding='utf-8')
for file in re.findall(r'(?:href|src)="([^"#]+)"',page):
    if not file.startswith('http'):assert (PRE/file).is_file(),file
for v in views:assert (PRE/v[1]).is_file()
assert snapshot_tree(LIVE)==json.loads((ROOT/'live_before.json').read_text())
assert sha(LIVE.parent/'scenery_packs.ini')==(ROOT/'ini_before.sha256').read_text()
assert all(sha(pathlib.Path(p))==h for p,h in json.loads((ROOT/'aep_before.json').read_text()).items())
print(json.dumps(receipt,indent=2))
