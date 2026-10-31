"""Package the original-garage successor for local review; never publish/install."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'package/KIAH_NRT_R22_Original_Garage_R18';OUT=ROOT/'output'
OLDROOT=ROOT.parent/'KIAH_R21_Jet_Center_R17'
validation=json.loads((OUT/'Validation.json').read_text());assert all(q['passed'] for q in validation['checks'])
guide='''NRT KIAH R22 - Original truck service garage

R22 replaces the inherited ATS/SCS T02 garage with an original NRT service shop.
Its geometry, materials, normal maps, night maps and sectional-door animation
were generated from dimensional primitives and new procedural textures.
All 27 old OBJ components and all 54 associated PNG/DDS texture files are omitted.
The cargo-building recess, truck court and existing road/parking access remain.

The three bays have 8.0 m wide by 5.8 m high openings. A straight aligned
24.5 x 2.6 m tractor/trailer reference fits inside each clear work bay. Turning
into those bays has not been tested in a truck simulator. This is X-Plane scenery.
A dispatch/driver office, rear workbenches/tool cabinets, skylights, roof plant,
protective bollards and facade/workshop lights complete the original building.

DOORS
OpenSAM loads the three truck doors open by default. Each has an independent
Close NRT Truck Bay 1 / 2 / 3 checkbox. Door sections move up and back along an
overhead track. MH1, MH2 and the private-aircraft hangar retain their prior controls.

RETAINED FROM R21
The private terminal, BBJ2-sized aircraft canopy, enlarged private hangar, both
new aircraft starts and landscaped passenger/delivery court are included.
All 15 main NRT starts, aircraft taxi lines, helipads and jetways are unchanged.
R21 and its prior delivery ZIP are preserved for rollback on the source PC.

INSTALL ON YOUR X-PLANE PC
1. Extract the entire ZIP into an ordinary temporary folder.
2. Close X-Plane, then run Install R22.cmd.
3. Enter the folder containing X-Plane.exe.
4. Keep MisterX Library, OpenSAM and openSAM_Library installed as before.
The installer verifies file hashes and preserves previous scenery folders.
It backs up scenery_packs.ini before selecting R22 and disabling old NRT versions.
Rollback: close X-Plane and restore the recorded scenery_packs.before-NRT-R22
backup as scenery_packs.ini. No simulator install was performed during authoring.

IN-SIM CHECK
Inspect the cargo-side garage in daylight and at night. Confirm the three truck
doors load open, each Close control operates independently, the floor and truck
court match the terrain, and the cargo recess has no gaps. Existing aircraft
hangar, jetway, canopy and arrival-court tests remain applicable.
Export checks and offline material previews are not simulator acceptance.

DISTRIBUTION STATUS
The known T02 garage blocker is removed. Garage_Provenance.json identifies the
original replacement and its source. Inherited Gateway notices/COPYING remain.
No plugins or shared scenery libraries are bundled. The member update tooling
is staged separately; the GitHub repository, download access and live depot URL
have not been selected. This ZIP has no live SkunkCrafts connection and is a
versioned test install, not a published member update.
'''
(PACK/'README_R22.txt').write_text(guide,encoding='utf-8');(OUT/'Install_and_Test.txt').write_text(guide,encoding='utf-8')
for suffix in ['ps1','cmd']:
    s=(OLDROOT/f'Install R21.{suffix}').read_text(encoding='utf-8').replace('R21','R22').replace('Jet_Center_R17','Original_Garage_R18')
    (ROOT/f'Install R22.{suffix}').write_text(s,encoding='utf-8')
# Keep the tested harness but aim it exclusively at this revision's mock folder.
h=(OLDROOT/'qa/test_installer.ps1').read_text(encoding='utf-8').replace('R21','R22').replace('Jet_Center_R17','Original_Garage_R18')
(ROOT/'qa/test_installer.ps1').write_text(h,encoding='utf-8')
src=PACK/'Source/R22';src.mkdir(exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,src/p.name)
shutil.copy2(ROOT/'qa/R22_South.txt',src/'South.dsf.txt')
old_source=(PACK/'Source/README.txt').read_text(encoding='utf-8')
if 'R22 original garage' not in old_source:
    (PACK/'Source/README.txt').write_text(old_source+'\nR22 original garage: Source/R22/build_r22.py generates the new garage geometry, materials and door controls without any imported donor assets. Source/R22/South.dsf.txt is the exact compiled native DSF input. validate_r22.py and render_r22.py reopen exported geometry. Historical R21/R17 authoring files may mention predecessors; no T02 garage mesh or texture is included in this package.\n',encoding='utf-8')
note=dict(revision='R22',garage_replacement='original generated NRT geometry/materials',known_t02_blocker_resolved=True,
          donor_runtime_files_remaining=0,source='Source/R22/build_r22.py',provenance='Garage_Provenance.json',
          notices_preserved=['COPYING','Gateway-original-README.txt'],live_updater_configured=False,
          scope='This records the garage replacement and does not replace the inherited scenery licenses or establish a public download destination.')
(PACK/'Garage_Replacement_Record.json').write_text(json.dumps(note,indent=2));(OUT/'Garage_Replacement_Record.json').write_text(json.dumps(note,indent=2))
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NRT R22 | Original truck garage</title><style>body{margin:0;background:#eef2eb;color:#183c45;font:18px/1.6 system-ui}main{max-width:1380px;padding:40px 30px;margin:auto}h1{font-size:52px;line-height:1.1}img{width:100%;border-radius:7px}.note{background:#dce9df;padding:18px 24px;border-left:4px solid #16858c}nav{display:flex;gap:14px;flex-wrap:wrap}a{color:#087c82}nav a{background:#183c45;color:white;padding:12px 18px;border-radius:6px;text-decoration:none}table{border-collapse:collapse;margin:28px 0}th,td{padding:10px 25px;border-bottom:1px solid #c2d5ca;text-align:left}h2{margin-top:40px}.small{font-size:14px;color:#587276}</style><main><p>NRT / KIAH / R22</p><h1>An original NRT truck workshop.</h1><p>The inherited Truck Simulator garage has been replaced with a new three-bay service building designed for this campus. It occupies the existing cargo-building recess and retains the truck court and access.</p><nav><a href="../NRT_KIAH_R22_Test.zip">R22 test build</a><a href="Install_and_Test.txt">Install and test guide</a><a href="Validation.json">Export checks</a><a href="Garage_Replacement_Record.json">Replacement record</a></nav><p class="note"><b>Built and checked offline; not installed or published.</b> The images reopen the exported geometry and textures. Terrain, nighttime lighting and OpenSAM operation still need a simulator check.</p><img src="Garage_Open.png" alt="Original recessed NRT truck service building with three open workshop bays and dispatch office"><table><tr><th>Service bays</th><td>Three, each with an 8.0 m wide × 5.8 m high opening</td></tr><tr><th>Interior</th><td>27.7 m clear depth, rear workbenches/tool cabinets and overhead lighting</td></tr><tr><th>Doors</th><td>Articulated sectional doors; open by default with independent OpenSAM Close controls</td></tr><tr><th>Office</th><td>Glazed dispatch/driver area with covered pedestrian entrance</td></tr></table><h2>Open and closed</h2><img src="Garage_Interior.png" alt="Ground-facing view into three open service bays"><img src="Garage_Closed.png" alt="The same original workshop with all three sectional doors closed"><h2>Fits the retained truck court</h2><img src="Garage_Court.png" alt="Garage recessed into the cargo hall beside the preserved truck court"><p>The replacement stays inside the existing recess, clear of the marked service forecourt and through lane. The prior truck-parking reverse envelopes still clear it. A straight aligned 24.5 × 2.6 m truck envelope fits each bay; turning into the workshop has not been validated in a truck simulator.</p><h2>The borrowed content is gone</h2><p>All 27 inherited garage models and their 54 PNG/DDS texture files are excluded. The new mesh, material maps, signs and door motion are generated from original authoring source included with R22. A file-hash scan also checks that the old assets were not retained under other names.</p><p>The known garage-specific member-distribution blocker is resolved. Existing Gateway license notices are preserved. The GitHub/SkunkCrafts tooling will use R22, but the repository, download access and live update URL remain unset.</p><p class="small">R21's private terminal, aircraft canopy, large private hangar, landscaped arrival court, aircraft starts, jetways and helipads are retained. R21 remains available for rollback. <a href="https://developer.x-plane.com/article/obj8-file-format-specification/">Laminar OBJ8 reference</a></p></main></html>'''
(OUT/'Review.html').write_text(html,encoding='utf-8')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(OUT/'Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
archive=ROOT/'NRT_KIAH_R22_Test.zip'
if archive.exists():raise RuntimeError('Do not overwrite a delivered archive')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in sorted(hashes):z.write(PACK/rel,'package/'+PACK.name+'/'+rel)
    for rel in ['Install R22.ps1','Install R22.cmd','output/Package_Hashes.json','output/Install_and_Test.txt']:z.write(ROOT/rel,rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,h in hashes.items():assert hashlib.sha256(z.read('package/'+PACK.name+'/'+rel)).hexdigest()==h
receipt=dict(package=str(PACK),files=len(hashes),archive=str(archive),archive_bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),export_checks=validation['passed'],garage_donor_assets=0,installed=False,runtime_tested=False,published=False)
(OUT/'Delivery_Receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
