"""Seal HF03 for review; never changes the live airport or scenery order."""
from pathlib import Path
import json, hashlib, shutil, zipfile, html
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF03'
PRE=ROOT/'previews-final'
LIVE=Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((ROOT/'HF03_Validation.json').read_text())
assert report['passed']==report['total']==23
assert all(sha(LIVE/p)==h for p,h in json.loads((ROOT/'live_before.json').read_text()).items())
assert sha(LIVE.parent/'scenery_packs.ini')=='c1c9bce079f40d1d3f238ffec043cdb8b7dc773875e30764c0745d46ad3c6bd8'
method=json.loads((PRE/'Preview_Method.json').read_text())
assert method['airport_data_inputs']['After']==sha(STAGE/'Earth nav data/apt.dat')
assert all(sha(STAGE/'objects'/p)==h for p,h in method['inputs']['After'].items())
assert len(list(PRE.glob('*.png')))==16

notes='''KIAH R03 HF03 - PARKED JETWAY AND OVERLAY REPAIR
24 October 2026
STAGED FOR REVIEW. NOT INSTALLED. SIMULATOR ACCEPTANCE PENDING.

The user's B5 screenshots showed a parked jetway intruding into the aircraft.
HF03 retracts and turns the 32 rebuilt moving jetways away from the stands.
It also repairs related service paths and conflicts with inherited scenery.
The installed HF02 airport and scenery order remain unchanged.

CHANGES
* Revised the parked heading, extension and cabin heading of 32 rebuilt arms.
  Installation points, bridge sizes and styles are unchanged. Total moving
  jetway definitions: 116. All 84 retained arms remain byte-identical to HF02.
* Detoured seven original ground-service edges around low stairs/wheel geometry.
  Added 34 service nodes, yielding 622 service edges. Existing service network
  connectivity and all 119 service starts/destinations are preserved.
* Removed 31 inherited gate-label polygons and cleaned old paint, surface
  polygons and obsolete equipment around the rebuilt apron and terminal areas.
  Ground gate numbers remain on the apron; elevated signs supplement them.
* Added local exclusions for 1,419 conflicting lower-layer AEP primitives:
  1,191 objects, 160 lines and 68 polygons. These include old gate glyphs,
  paint and weathering. AEP itself has not been edited or redistributed.
* Removed disconnected old terminal/walkway fragments, six clipped garage
  fragments and fences/objects crossing the replacement buildings. Trimmed
  nine inherited surface polygons. Continuous pavement under buildings remains.
* Locally excluded 11 lower-layer road segments that intersect replacement
  buildings or taxiway bridge areas. This removes those road segments and
  their traffic; it does not construct replacement tunnels or a new road mesh.
* Added interpreted metal battens, plinth, roof seams and edge trim to the
  United maintenance hangar shell. Its footprint, 22 m interpreted height,
  east opening and retained stock interior framework are preserved.

VALIDATION
23/23 targeted offline checks pass. Native scenery compilation and decode
succeed. All 38 custom models have valid outward clockwise faces.
The 32 corrected parked meshes stay within stock motion limits and clear the
modeled conservative aircraft envelopes by at least 4.4 m. They also clear the
modeled terminal outlines, neighboring moving arms and authored fixed bridges.
Every service centerline clears the low geometry of those 32 parked arms by
at least 2.35 m. This is a centerline measurement, not a swept truck simulation.
All 988 aircraft taxi edges, aircraft route nodes, 240 starts, five runways and
flow rules are unchanged. Offline connectivity does not prove AI behavior.
All targeted AEP primitives and road segments meet the native exclusion rules.
Installed package hashes and scenery order are unchanged.

LIMITS AND OPEN TESTS
* Docking, retraction, vehicle turning, terrain fit and live overlay suppression
  still require X-Plane testing. No simulator has been launched for HF03.
* Seventeen inherited jetway records retain historical attitudes outside the
  nominal model ranges used by this audit; they were not changed in this fix.
  Retained arms, including HF02's seven extra source arms, need docking tests.
* The red east-side EA barricade row shown in the screenshots is preserved.
  It is separate from the reopened west/15L corridor. This repair does not
  certify current closure status from a fresh primary FAA NOTAM source.
* Earlier C29/E6 evidence limits, alternative/MARS stand restrictions and the
  C14 wide final-maneuver test remain applicable. HF03 is a repair of the
  existing airport build, not independent certification of today's layout.
* The hangar's exterior treatment is interpreted, not a survey-grade replica.

PREVIEWS
The before/after views render actual HF02/HF03 custom OBJ8 geometry and textures
and actual stock animated jetway meshes at their native parked positions.
Gray retained buildings/connections are simplified massing. Pavement/paint
comes from native airport data but uses simplified materials and line styles.
Cyan B5 shapes are a conservative A321-sized clearance guide, not a rendered
aircraft. Old AEP glyph meshes appear in the before views; most AEP weathering,
terrain relief, equipment and the hangar interior framework are omitted.
These are offline previews, not X-Plane screenshots. Shadows are illustrative.
The route and cleanup maps show staged data, not simulated moving traffic.

FIRST TESTS AFTER AN APPROVED INSTALL
1. B5 with the ToLiss A321: before requesting docking, check the parked arm is
   clear of the fuselage. Then dock and retract it. Check the ground B5 label.
2. B6/B8 and D4/D6: request ground services and inspect turns around the jetway
   stairs/wheels; check that vehicles do not cut through the terminal or aircraft.
3. B1-B4 and D West: look for obsolete B83/C19/C24 labels, doubled lead-ins and
   old apron weathering crossing the new stand layout.
4. B lobby and the international terminal: inspect the removed garage/facade
   fragments and verify traffic no longer passes through replacement buildings.
5. East taxiway bridge: inspect the crossing previously occupied by road traffic.
6. United Maintenance 3: inspect metal walls, roof, open east doorway and terrain.
7. C30/C40 and a widebody gate: test retained moving jetways and pushback.
8. Continue the R03 aircraft taxi tests, including the reopened west taxiways.

INSTALLATION HOLD
This is a full successor airport. After approval, replace the single active
R03 folder using a backup and hash verification. Do not enable HF02 and HF03
as two competing KIAH airports. No install or simulator reload occurred here.

PROVENANCE
Historical R02/R03/Gateway/Houston Airports/FAA source notes remain under Sources.
HF03 notes and validation take precedence for the current repair status.
Build scripts need preserved workspace inputs and dependencies; they are
included for traceability, not as a standalone portable one-click rebuild.
No commercial AEP assets or SimHeaven road tiles are included in this package.

Technical references consulted:
https://developer.x-plane.com/article/dsf-usage-in-x-plane/
https://developer.x-plane.com/?article=customizable-jetways
https://developer.x-plane.com/article/guide-to-ramp-starts/
'''
hist=STAGE/'Sources/R03_HF02_historical_notes.txt'
if not hist.exists(): shutil.copy2(STAGE/'README.txt',hist)
(STAGE/'README.txt').write_text(notes,encoding='utf-8')
(PRE/'Repair_Notes.txt').write_text(notes,encoding='utf-8')
src=STAGE/'Sources/HF03_Repair';src.mkdir(exist_ok=True)
for name in ['repair_hf03.py','jetway_repair.py','repair_service_paths.py','validate_hf03.py','setup_previews.py','prepare_previews.py','render_hf03.py','review_maps.py','package_review.py','jetways.json','service-repair.json','scene-hf03.json','cleanup-mask.json']:
    shutil.copy2(ROOT/'work'/name,src/name)
for name in ['HF03_Changes.json','HF03_Validation.json']:
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
receipt=dict(revision='KIAH R03 HF03',status='STAGED - NOT INSTALLED',checks='23/23 offline',archive=archive.name,sha256=sha(archive),files=len(manifest)+1,live_package_unchanged=True,scenery_order_unchanged=True)
(PRE/'Package_Receipt.json').write_text(json.dumps(receipt,indent=2))
views=[
 ('B5 parked clearance','02_B5_After.png','01_B5_Before.png','The parked bridge retracts and turns away from the cyan A321-sized clearance guide. Docking has not been simulated.'),
 ('B5 from above','14_B5_Top_After.png','13_B5_Top_Before.png','Compare the parked moving arm against the conservative fuselage guide. Ground numbers stay on the apron; elevated signs supplement them.'),
 ('Terminal B North','04_B_North_After.png','03_B_North_Before.png','Corrected parked bridges and removal of inherited labels and paint around the rebuilt concourses.'),
 ('D West apron','06_D_West_After.png','05_D_West_Before.png','Retracted parked arms and cleanup of old stand markings. The gray retained structures are simplified context.'),
 ('B landside cleanup','08_B_Landside_After.png','07_B_Landside_Before.png','Old garage, walkway and terminal fragments around the new B lobby have been removed. Retained context is simplified.'),
 ('International terminal','10_International_After.png','09_International_Before.png','Cleanup of clipped garage and building fragments. Ground textures and retained buildings are simplified in this view.'),
 ('United maintenance hangar','12_Hangar_After.png','11_Hangar_Before.png','Added metal battens, plinth, edge trim and roof seams. The east opening is retained on the opposite side. Exterior detail is interpreted.'),
 ('Service path repairs','15_Service_Path_Repair.png',None,'Seven original service edges detour around low parked jetway geometry. Aircraft taxi routes are unchanged. Vehicle driving still needs an X-Plane test.'),
 ('Road and overlay cleanup','16_Overlay_Road_Repair.png',None,'Local exclusions suppress conflicting AEP apron features and 11 road segments. The removed road segments are not replaced with tunnels.')]
for _,after,before,_ in views:
    assert (PRE/after).is_file()
    if before: assert (PRE/before).is_file()
cards=''.join(f'<button class="view" data-index="{i}">{html.escape(v[0])}</button>' for i,v in enumerate(views))
table=''.join(f'<tr><td>Pass</td><td>{html.escape(x["check"])}</td></tr>' for x in report['checks'])
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KIAH R03 HF03 repair review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#11191f;color:#e9eef1;font:16px/1.5 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:34px;margin:8px 0}h2{font-size:23px}p{max-width:1100px;color:#becbd2}.status{color:#ffc56c;font-weight:700;letter-spacing:.08em;font-size:13px}.stats{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.stats div{background:#213039;padding:16px 24px;border-radius:8px}.stats strong{font-size:27px;color:#8ed5d0;display:block}.viewer{background:#1d2a32;padding:18px;border-radius:12px}nav{display:flex;flex-wrap:wrap;gap:8px;margin:15px 0}button,a{color:#a5e4df}button{border:1px solid #4c636f;background:#14222a;padding:10px 14px;border-radius:5px;cursor:pointer}button.active{background:#34716f;color:#fff}button:focus-visible{outline:3px solid #ffc56c}.controls{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:14px}.controls span{margin-left:auto;color:#ffc56c;font-size:13px}img{width:100%;display:block;background:#26343c;border-radius:6px}figcaption{padding:14px 0;color:#cfdae0}figure{margin:0}summary{cursor:pointer;font-weight:bold;padding:16px 0}table{border-collapse:collapse;width:100%}td{border-bottom:1px solid #33444e;padding:8px}td:first-child{color:#83c9b6;width:70px}li{margin-bottom:8px}.links{display:flex;gap:25px;flex-wrap:wrap}footer{border-top:1px solid #394950;margin-top:25px;padding-top:14px;color:#9eafb9;font-size:14px}</style></head>
<body><main><div class="status">STAGED REPAIR · NOT INSTALLED</div><h1>KIAH R03 HF03</h1><p>The B5 bridge was intersecting the aircraft while parked. This repair retracts and turns the rebuilt jetways, adjusts nearby service paths, and cleans up old markings, building fragments and conflicting roads. Your installed HF02 airport remains unchanged.</p>
<div class="stats"><div><strong>32</strong>parked jetways corrected</div><div><strong>7</strong>service sections rerouted</div><div><strong>11</strong>road segments excluded</div><div><strong>23 / 23</strong>offline checks passed</div></div>
<section class="viewer"><h2 id="title">B5 parked clearance</h2><nav aria-label="Preview views">CARDS</nav><div class="controls"><button id="after">Staged HF03</button><button id="before">Installed HF02</button><span>OFFLINE MODEL PREVIEW</span></div><figure><a id="full" href="02_B5_After.png" target="_blank"><img id="picture" src="02_B5_After.png" alt="Staged B5 parked jetway clearance"></a><figcaption id="caption"></figcaption></figure></section>
<p><b>What the images show:</b> actual custom models and stock moving-jetway meshes at their parked positions. Cyan shapes mark a conservative A321-sized clearance guide. Gray retained buildings are simplified, and surface materials and paint styles are approximate. These are not X-Plane screenshots. Docking, traffic and vehicle turning still need simulator testing.</p>
<h2>Repair details</h2><ul><li><b>Parked jetways:</b> revised 32 parked poses while preserving installation points and bridge sizes. All 116 moving-jetway definitions remain; the 84 retained arms are unchanged.</li><li><b>Service paths:</b> seven short sections now avoid the retracted stairs and wheels. Minimum modeled centerline clearance is 2.35 m. All 988 aircraft taxi edges and 240 aircraft starts are unchanged.</li><li><b>Apron and landside:</b> removed inherited stand labels, paint and disconnected building/garage fragments. Local exclusions target 1,419 conflicting AEP objects, lines and polygons. AEP itself is untouched.</li><li><b>Road conflicts:</b> excluded 11 road segments crossing replacement buildings or taxiway bridge areas. This removes those road segments and traffic, without constructing replacement tunnels.</li><li><b>Hangar:</b> added modest metal wall and roof detail while preserving the open east doorway. Its exterior treatment remains interpreted.</li></ul>
<h2>First tests after an approved install</h2><ol><li><b>B5 with your A321:</b> check the parked arm before requesting docking, then dock and retract it.</li><li><b>B6/B8 and D4/D6:</b> call ground services and watch their turns around the jetway stairs and aircraft.</li><li><b>B North and D West:</b> check for old B83/C19/C24 labels, doubled lead-ins and old paint across new stands.</li><li><b>Landside and east taxiway bridge:</b> check the removed fragments and traffic conflicts; inspect the maintenance hangar from both sides.</li><li><b>C30/C40 and a widebody gate:</b> test retained jetways and pushback, then continue the aircraft taxi-route tests.</li></ol>
<details><summary>23 passed offline checks</summary><table>TABLE</table></details>
<p>Retained jetway docking and runtime route behavior remain open tests. The east-side EA barricades are preserved; they are separate from the reopened west/15L corridor. Earlier C29/E6 evidence limits and the C14 wide maneuver checkpoint still apply.</p>
<div class="links"><a href="Repair_Notes.txt">Full repair notes</a><a href="HF03_Validation.json">Validation report</a><a href="Preview_Method.json">Preview method</a><a href="Package_Receipt.json">Package receipt</a></div>
<footer>24 October 2026 · HF03 is staged only. No installation, scenery-order change or simulator reload was performed. This is a full successor airport, not a second overlay to enable alongside HF02.</footer></main>
<script>const views=VIEWS;let selected=0;let mode='after';function show(){let v=views[selected];if(!v[2])mode='after';let file=mode==='after'?v[1]:v[2];document.querySelector('#title').textContent=v[0];let im=document.querySelector('#picture');im.src=file;im.alt=v[0]+' — '+(mode==='after'?'staged HF03':'installed HF02');document.querySelector('#full').href=file;document.querySelector('#caption').textContent=(mode==='before'?'Before: installed HF02 geometry rendered offline. ':'Staged HF03: ')+v[3];document.querySelector('#before').hidden=!v[2];document.querySelector('#before').classList.toggle('active',mode==='before');document.querySelector('#after').classList.toggle('active',mode==='after');document.querySelectorAll('.view').forEach((b,i)=>{b.classList.toggle('active',i===selected);b.setAttribute('aria-pressed',i===selected?'true':'false')});}document.querySelectorAll('.view').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.index);mode='after';show();});document.querySelector('#after').onclick=()=>{mode='after';show();};document.querySelector('#before').onclick=()=>{mode='before';show();};show();</script></body></html>'''
page=page.replace('CARDS',cards).replace('TABLE',table).replace('VIEWS',json.dumps(views))
(PRE/'Review.html').write_text(page,encoding='utf-8')
print(json.dumps(receipt,indent=2))
