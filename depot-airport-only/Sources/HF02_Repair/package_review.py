"""Seal the staged review and package. Does not install or change scenery order."""
from pathlib import Path
import json,hashlib,shutil,zipfile,html
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF02'
PRE=ROOT/'previews-final'
LIVE=Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((ROOT/'HF02_Final_Validation.json').read_text())
assert report['passed']==report['total']==19
assert all(sha(LIVE/p)==h for p,h in json.loads((ROOT/'live_before.json').read_text()).items())
method=json.loads((PRE/'Preview_Method.json').read_text())
assert method['airport_data_inputs']['After']==sha(STAGE/'Earth nav data/apt.dat')
assert all(sha(STAGE/'objects'/p)==h for p,h in method['inputs']['After'].items())
assert len(list(PRE.glob('*.png')))==11
readme='''KIAH R03 HF02 - VISUAL AND JETWAY REPAIR REVIEW
24 October 2026
STAGED ONLY. NOT INSTALLED. X-PLANE ACCEPTANCE PENDING.

This successor repairs the defects reported during the R03 simulator test.
R03/HF01 and the installed airport are preserved. No simulator control or
scenery-order change was performed for this review.

REPAIRS
* Restored 84 omitted moving jetway definitions at surviving fixed connections.
  77 records match the installed current Global Airports exactly. Seven extra
  source arms preserve the compiled Gateway placement with translated current
  size codes. Those extra arms need particular docking review. Twenty-seven
  obsolete arms whose fixed bases were removed are not restored.
* Corrected absolute parked tunnel headings on the 32 new moving jetways.
  The staged airport now contains 116 moving-jetway definitions. This is a
  definition count, not a claim that all 116 have docked successfully.
* Corrected outward-facing triangles on all 37 existing custom models and the
  apron-facing direction/texture reading of the 32 elevated gate signs.
* Reversed 55 incorrectly clipped retained terminal/garage/bridge outlines.
* Added an exterior shell to the United maintenance hangar, whose retained
  source contained only an interior framework. The original footprint is
  preserved; the 22 m shell height/detail is interpreted. East doorway stays
  open. The stock interior framework remains in the native scenery.
* Added/corrected 81 ground gate identifiers. Elevated signs are supplementary;
  ground identifiers and lead-ins remain on the apron. Separated the D16 and
  D16A380 markings, removed stale renumbered labels and obsolete D9B marking.
* Removed 34 inherited equipment placements in rebuilt areas, trimmed five old
  surface polygons, removed 26 old painted-line blocks and clipped 32 others.
  Added continuous hard surface under custom buildings and fixed tunnels.

VALIDATION
19/19 targeted offline checks pass. Native DSF compilation and decode succeed.
38 custom models / 12,134 triangles have outward clockwise OBJ8 front faces.
Ground identifiers are on pavement, outside terminal footprints and do not
overlap. Native parked headings/lengths reach their designed endpoints; actual
parked moving meshes clear neighboring new fixed and moving bridge envelopes.
All aircraft starts, aircraft/service route records, runways and flow rules are
unchanged. Installed package hashes and the northern DSF are unchanged.

PREVIEW LIMITS
The images render the staged custom OBJ8 files and actual stock animated
jetway meshes evaluated at their native parked positions. Gray retained
buildings/connections are simplified massing. Pavement and painted paths come
from native airport data but use simplified colors/line styles. No aircraft,
traffic, terrain relief or library hangar framework is simulated. Lighting and
shadows are illustrative. These are offline previews, not X-Plane screenshots.

FIRST SIMULATOR TESTS AFTER AN APPROVED INSTALL
1. C30 or C40: confirm restored moving arm is visible; spawn a compatible
   aircraft, set parking brake, engines off, then request normal jetway docking.
2. B5: inspect roof/walls and readable sign; verify apron B5 paint and parked
   arm direction. Dock/retract the jetway, then request ground services.
3. B3/B4 and B15/B16: inspect the fanned stands and neighboring bridge clearance.
4. D14-D16 and D West: inspect gate numbers, overlapping old paint, pavement
   layering and bridge positions; test one widebody docking/pushback.
5. United Maintenance 3: inspect shell from both sides, doorway and terrain fit.
6. Repeat R03 aircraft taxi and service-route tests, including reopened west
   taxiways. C14 wide's 334 m final maneuver remains a specific test item.

INSTALLATION HOLD
The review package is a full successor airport, not an additional overlay.
Once approved it should replace the active R03 package as a single airport,
with a backup and hash check. Do not enable both airport revisions together.
This document does not authorize installation or simulator reload.

PROVENANCE AND LIMITS
Retains R03/HF01's airport header repair and the R02 Gateway/Houston Airports/FAA
source attribution, route decisions and C29/E6 evidence limitations. This fix
does not independently certify every real-world airport change as of today.
Historical source notes are retained under Sources; current HF02 notes and
validation take precedence for repair status. Rebuild scripts require the
preserved original workspace inputs/dependencies and repair-stage paths.

Technical references:
https://developer.x-plane.com/article/obj8-file-format-specification/
https://developer.x-plane.com/article/dsf-usage-in-x-plane/
https://developer.x-plane.com/article/airport-data-apt-dat-12-00-file-format-specification/
https://github.com/X-Plane/xptools/blob/master/src/WEDEntities/WED_FacadePlacement.cpp
'''
hist=STAGE/'Sources/R03_HF01_historical_notes.txt'
if not hist.exists():shutil.copy2(STAGE/'README.txt',hist)
(STAGE/'README.txt').write_text(readme,encoding='utf-8')
(PRE/'Repair_Notes.txt').write_text(readme,encoding='utf-8')
src=STAGE/'Sources/HF02_Repair';src.mkdir(exist_ok=True)
for name in ['prepare_hf02.py','repair_airport_details.py','sign_groups.py','validate_hf02.py','prepare_previews.py','validate_native_jetway_shapes.py','render_hf02.py','package_review.py']:
    shutil.copy2(ROOT/'work'/name,src/name)
for name in ['HF02_Final_Validation.json','HF02_Detail_Validation.json']:
    shutil.copy2(ROOT/name,src/name);shutil.copy2(ROOT/name,PRE/name)
shutil.copy2(ROOT/'work/current-global-KIAH-apt.dat',src/'current-global-KIAH-reference.dat')
shutil.copy2(ROOT/'work/scene-hf02.json',src/'scene-hf02.json')
shutil.copy2(ROOT/'work/sign-tiles-hf02.json',src/'sign-tiles-hf02.json')
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
receipt=dict(revision='KIAH R03 HF02',status='STAGED - NOT INSTALLED',checks='19/19 offline',archive=archive.name,sha256=sha(archive),files=len(manifest)+1,live_package_unchanged=True)
(PRE/'Package_Receipt.json').write_text(json.dumps(receipt,indent=2))
views=[
 ('B5 - roof, signs and jetway','02_B5_After.png','01_B5_Before.png','The repaired roof and exterior walls are visible, both sign types read from the apron, and the moving arm uses its intended parked heading.'),
 ('Terminal B North','04_B_North_After.png','03_B_North_Before.png','Full repaired concourse geometry, 22 new jetways and apron labels. Retained gray buildings are simplified context.'),
 ('Retained C gates - moving arms restored','09_Retained_C_After.png','08_Retained_C_Before.png','The moving portions are restored at the existing fixed connections. Their actual stock meshes are shown at the parked state; docking remains to be tested.'),
 ('D West','05_D_West_After.png',None,'Repaired walls and roof with moving bridges and stand labels. MARS alternatives remain manual placements.'),
 ('International terminal','06_International_After.png',None,'Custom terminal repairs and native parked jetways. Gray retained facade massing is illustrative.'),
 ('D East apron markings','11_D_East_Apron_After.png',None,'Updated ground identifiers, including separated D16 and D16A380 labels. Paint widths, surface texture and weathering are simplified in this review.'),
 ('United maintenance hangar','10_United_Maintenance_After.png',None,'New exterior shell around the existing footprint, with the east doorway open. The retained interior framework is omitted from this offline view.'),
 ('Terminal complex overview','07_Terminal_Complex_After.png',None,'Review the combined building and jetway layout. Traffic behavior and automatic docking are not simulated.')]
cards=''.join(f'<button class="view" data-index="{i}">{html.escape(v[0])}</button>' for i,v in enumerate(views))
table=''.join(f'<tr><td>Pass</td><td>{html.escape(x["check"])}</td></tr>' for x in report['checks'])
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KIAH R03 HF02 repair review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#11191f;color:#e9eef1;font:16px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:34px;margin:8px 0}h2{font-size:23px}p{max-width:1000px;color:#becbd2}.status{color:#ffc56c;font-weight:700;letter-spacing:.08em;font-size:13px}.stats{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.stats div{background:#213039;padding:16px 24px;border-radius:8px}.stats strong{font-size:27px;color:#8ed5d0;display:block}.viewer{background:#1d2a32;padding:18px;border-radius:12px}nav{display:flex;flex-wrap:wrap;gap:8px;margin:15px 0}button,a{color:#a5e4df}button{border:1px solid #4c636f;background:#14222a;padding:10px 14px;border-radius:5px;cursor:pointer}button.active{background:#34716f;color:#fff}.controls{display:flex;gap:9px;align-items:center;margin-bottom:14px}.controls span{margin-left:auto;color:#ffc56c}img{width:100%;display:block;background:#26343c;border-radius:6px}figcaption{padding:14px 0;color:#cfdae0}figure{margin:0}summary{cursor:pointer;font-weight:bold;padding:16px 0}table{border-collapse:collapse;width:100%}td{border-bottom:1px solid #33444e;padding:8px}td:first-child{color:#83c9b6;width:70px}li{margin-bottom:8px}.links{display:flex;gap:25px;flex-wrap:wrap}footer{border-top:1px solid #394950;margin-top:25px;padding-top:14px;color:#9eafb9;font-size:14px}</style>
<main><div class="status">STAGED REPAIR · NOT INSTALLED</div><h1>KIAH R03 HF02</h1><p>Repairs for the missing jetways, see-through buildings, hangar shell and apron markings reported in your X-Plane test. The active R03 airport and scenery order remain unchanged.</p>
<div class="stats"><div><strong>84</strong>moving jetways restored</div><div><strong>32</strong>new parked headings corrected</div><div><strong>81</strong>ground identifiers</div><div><strong>19 / 19</strong>offline checks passed</div></div>
<section class="viewer"><h2 id="title"></h2><nav>CARDS</nav><div class="controls"><button id="after">Staged repair</button><button id="before">Installed R03</button><span>OFFLINE MODEL PREVIEW</span></div><figure><a id="full" target="_blank"><img id="picture" alt=""></a><figcaption id="caption"></figcaption></figure></section>
<p><b>Preview method:</b> actual custom model files and stock moving-jetway meshes at their parked positions. Gray retained buildings and fixed connections are simplified. Native pavement/paint geometry uses simplified materials and line styles. Aircraft, vehicles, terrain relief and the hangar's retained interior framework are omitted. These are not simulator screenshots; docking and traffic are not validated by the images.</p>
<h2>What changed</h2><ul><li>Restored moving sections at surviving gate connections and corrected the new bridges' absolute parked headings. Total: 116 definitions. Seventy-seven restored records match current Global Airports; seven additional source arms use translated size codes and need special docking review.</li><li>Fixed the front faces on 37 original custom models, 55 retained building outlines, and the reading direction of elevated gate signs.</li><li>Added the United maintenance hangar's exterior shell while retaining its open doorway and stock interior. Its 22 m height and exterior detail are interpreted.</li><li>Repaired ground gate labels, removed conflicting old paint/equipment in rebuilt areas, and added hard surface under buildings and fixed tunnels. Ground numbers remain on the apron; elevated signs supplement them.</li></ul>
<h2>First tests after an approved install</h2><ol><li><b>C30 or C40:</b> confirm the restored arm appears, then request docking with a compatible parked aircraft.</li><li><b>B5:</b> inspect roof, walls, both gate signs and parked direction. Dock/retract, then call ground services.</li><li><b>B3/B4, B15/B16 and D14–D16:</b> check neighboring bridges, ground markings, pushback and widebody clearances.</li><li><b>United Maintenance 3:</b> inspect the building from both sides, doorway and ground fit.</li></ol>
<details><summary>19 passed offline checks</summary><table>TABLE</table></details><p>Aircraft and service route records, starts, runways and flow rules are unchanged. Runtime route behavior remains pending. Prior C29/E6 evidence limitations and the manual C14 wide maneuver checkpoint still apply.</p>
<div class="links"><a href="Repair_Notes.txt">Full repair notes and test list</a><a href="HF02_Final_Validation.json">Validation report</a><a href="Preview_Method.json">Preview provenance</a><a href="Package_Receipt.json">Package receipt</a></div>
<footer>24 October 2026 · No installation, scenery-order change or simulator reload performed. This is a repair successor to R03, not another overlay to enable alongside it.</footer></main>
<script>const views=VIEWS;let selected=0;let mode='after';function show(){let v=views[selected];if(!v[2])mode='after';let file=mode==='after'?v[1]:v[2];document.querySelector('#title').textContent=v[0];let im=document.querySelector('#picture');im.src=file;im.alt=v[0]+' — '+(mode==='after'?'staged repair':'installed R03 geometry');document.querySelector('#full').href=file;document.querySelector('#caption').textContent=(mode==='before'?'Before: installed native geometry, rendered offline. ':'Staged repair: ')+v[3];document.querySelector('#before').hidden=!v[2];document.querySelector('#before').classList.toggle('active',mode==='before');document.querySelector('#after').classList.toggle('active',mode==='after');document.querySelectorAll('.view').forEach((b,i)=>b.classList.toggle('active',i===selected));}document.querySelectorAll('.view').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.index);mode='after';show();});document.querySelector('#after').onclick=()=>{mode='after';show();};document.querySelector('#before').onclick=()=>{mode='before';show();};show();</script></html>'''
page=page.replace('CARDS',cards).replace('TABLE',table).replace('VIEWS',json.dumps(views))
(PRE/'Review.html').write_text(page,encoding='utf-8')
print(json.dumps(receipt,indent=2))
