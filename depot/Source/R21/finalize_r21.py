from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1];CAMPUS=ROOT.parents[1];PACK=ROOT/'package/KIAH_NRT_R21_Jet_Center_R17';OUT=ROOT/'output'
CONCEPT=CAMPUS/'feasibility/KIAH_R21_Jet_Center_Concept_R01';UPDATER=CAMPUS/'distribution/NRT_KIAH_Updater_R01'
validation=json.loads((OUT/'Validation.json').read_text());assert all(x['passed'] for x in validation['checks'])
guide='''NRT KIAH R21 - Private Jet Center / personal test

The private-terminal addition and aircraft awning replace NRT11/NRT12 parking.
MH3 and the old open maintenance parking become one enlarged private hangar.
There are 15 main NRT starting positions, including:
  NRT PRIVATE HANGAR - centered, facing east toward the FBO.
  NRT CANOPY - under the aircraft awning, facing west toward the taxi spine.
The canopy clear box is 48 m wide x 46 m deep x 14 m high below the structure.
The BBJ2/737-800 exterior envelope fits including its tail; plan to tow it.
Reference aircraft in the preview images are not static aircraft in the scenery.

Passenger cars approach from the existing car park, loop around a planted
median and stop at the covered entrance. A 7 m native oak, low shrubs, benches,
an NRT flagpole and low entrance lights furnish the court. The separate 18 x 9 m
delivery bay is for vans/rigid service trucks. The cargo yard handles semis.
The security fence opening is rerouted around the new public court.

MH1, MH2, existing FBO/roof tower, NRT8/9 jetways, cargo, and both helipads stay.
Hangars remain open by default with OpenSAM active. Use the Close NRT Private
Hangar checkbox to close/reopen the new sliding doors. MH1/MH2 controls stay.

INSTALL ON YOUR NEW PC
1. Extract the entire ZIP into an ordinary temporary folder.
2. Close X-Plane. Run Install R21.cmd and enter the folder containing X-Plane.exe.
3. Keep your existing MisterX Library, OpenSAM and openSAM_Library. Launch KIAH.
The installer verifies hashes, preserves older scenery folders, and backs up
scenery_packs.ini before selecting R21. To roll back, close X-Plane and restore
that recorded scenery_packs.before-NRT-R21-*.ini backup as scenery_packs.ini.
No changes were installed on the source PC by this build task.

CHECK IN X-PLANE
- Both new start locations and aircraft/tug passage around canopy posts.
- New hangar loads open; manual close/reopen completes without gaps.
- Old MH3 and former open-parking paint are gone; MH1/MH2 remain correct.
- Passenger loop, tree, flag, delivery bay and rerouted fence align with terrain.
- Native wet pavement, vegetation seasons and nighttime light levels.
- NRT8/9 jetways and both helipads still work as before.
Offline export checks and render previews are not a simulator acceptance test.

MEMBER DISTRIBUTION
This package retains the converted ATS T02 garage. Its provenance records it
as a personal-test adaptation, not a redistributable original asset. Do not
publish this ZIP to members until that asset is replaced or cleared.
The separate NRT_KIAH_Updater_R01 tooling prepares a stable-folder release and
SkunkCrafts depot after repository/access/URL and asset review are settled.
'''
(OUT/'Install_and_Test.txt').write_text(guide,encoding='utf-8');(PACK/'README_R21.txt').write_text(guide,encoding='utf-8')
for f in ['Jet_Center_Plan.png','Arrival_Court_Plan.png','Concept_Measurements.json']:
    shutil.copy2(CONCEPT/'output'/f,OUT/f)
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NRT R21 Jet Center</title><style>body{margin:0;background:#eff3ec;color:#193e47;font:18px/1.6 system-ui}main{max-width:1400px;margin:auto;padding:40px 30px}h1{font-size:54px;line-height:1.1}h2{margin-top:42px}img{width:100%;border-radius:8px}a{color:#087a7d}.note{padding:18px 24px;background:#dce9e1;border-left:4px solid #17878b}.caption{font-size:14px;color:#60777a}.links{display:flex;gap:14px;flex-wrap:wrap}.links a{background:#193e47;color:white;padding:12px 18px;border-radius:6px;text-decoration:none}table{border-collapse:collapse}td,th{padding:12px 24px;border-bottom:1px solid #bed1c7;text-align:left}</style><main><p>NRT / KIAH / R21 PERSONAL TEST</p><h1>A proper arrival at the Jet Center.</h1><p>A covered passenger pull-up from the existing parking lot, a planted median with a feature tree and NRT flagpole, and a separate delivery bay. The private terminal, aircraft canopy and enlarged private hangar are built into an isolated scenery package.</p><p class="note"><b>Built and checked offline; not installed.</b> R20 is preserved. These images reopen the exported building meshes. The simulator still needs to confirm terrain, lighting, wet surfaces, jetways and towing.</p><div class="links"><a href="../NRT_KIAH_R21_Personal_Test.zip">Personal test ZIP</a><a href="Install_and_Test.txt">Install and test guide</a><a href="Validation.json">Export checks</a></div><h2>Arrivals and deliveries</h2><img src="Arrival_Export.png" alt="Exported terminal entrance with covered curb, landscaped island, tree, benches and flagpole"><p>The one-way passenger loop is separated from aircraft access. A rounded path checked with a 5.4 × 2.0 m car envelope clears the modelled obstacles by at least 2.8 m; this is a static envelope check, not vehicle steering simulation. The 18 × 9 m delivery bay serves vans and rigid trucks. The existing cargo court remains the semi-trailer area.</p><img src="Arrival_Court_Plan.png" alt="Arrival loop and separate delivery bay"><h2>Covered private-jet arrival</h2><img src="Canopy_Export.png" alt="Exported canopy with BBJ2 reference silhouette"><table><tr><th>Canopy clear dimensions</th><td>48 m width × 46 m depth × 14 m height</td></tr><tr><th>NRT CANOPY start</th><td>Facing west toward the taxi spine</td></tr><tr><th>Reference aircraft</th><td>G650, Lineage 1000E and BBJ2 envelopes fit; BBJ2 tow-in/tow-out</td></tr></table><h2>The enlarged private hangar</h2><img src="Hangar_Export.png" alt="Exported private hangar with doors open"><p>MH3 and the old MX open-parking area are replaced by a 78 × 150 m private hangar, with one centered outward-facing start. Its sliding doors load open with OpenSAM and retain a manual Close control. MH1 and MH2 stay in place.</p><h2>Whole site</h2><img src="Jet_Center_Plan.png" alt="Measured site layout"><p class="caption">The plan retains its concept-stage notes. The R21 package is now built; the plan’s diagram aircraft remain reference shapes and are not installed as statics.</p><h2>Member updates</h2><p>The GitHub-ready tooling creates a first-install ZIP and individual-file SkunkCrafts depot, and its seven release tests pass. Repository, download access and the production URL remain unset. The inherited T02 garage is explicitly marked personal-use in its provenance; replace it or obtain redistribution clearance before publishing to members. This personal test ZIP is not a member release.</p><p>Built with native X-Plane weather-aware pavement and vegetation, OBJ8 animation/photometric lights, and Laminar DSFTool/DDSTool. No separate WED project was requested. <a href="https://developer.x-plane.com/article/airport-pavement-and-fx/">Native pavement reference</a> · <a href="https://github.com/lzamouth/sku_client/blob/master/docs/PUBLISHING.md">SkunkCrafts publishing guide</a></p></main></html>'''
(OUT/'Review.html').write_text(html,encoding='utf-8')
author=PACK/'Source/R21';author.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,author/p.name)
helpers=PACK/'Source/R17_Helpers';helpers.mkdir(exist_ok=True)
for f in ['build_test.py','materials.py','airport_geometry.py','obj_reader.py']:
    shutil.copy2(ROOT.parent/'KIAH_R17_Native_Surface_R13/source'/f,helpers/f)
(PACK/'Source/README.txt').write_text('R21 authoring sources and R17 helper provenance are provided. Rebuilding requires the preserved R20 package as baseline, the R21 concept measurements, Python with numpy/Pillow/Shapely, and Laminar xptools. Native library resources are referenced from X-Plane, not copied into this package. Full predecessor source is retained in the source workspace.\n')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(OUT/'Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
zipname=ROOT/'NRT_KIAH_R21_Personal_Test.zip'
assert not zipname.exists(),'Preserve an existing delivery archive'
with zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in PACK.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
    for rel in ['Install R21.ps1','Install R21.cmd','output/Package_Hashes.json','output/Install_and_Test.txt']:
        z.write(ROOT/rel,rel)
with zipfile.ZipFile(zipname) as z:
    assert z.testzip() is None
    for rel,expected in hashes.items():assert hashlib.sha256(z.read('package/'+PACK.name+'/'+rel)).hexdigest()==expected
receipt=dict(package=str(PACK),files=len(hashes),archive=str(zipname),archive_bytes=zipname.stat().st_size,sha256=hashlib.sha256(zipname.read_bytes()).hexdigest(),export_checks=validation['passed'],installed=False,runtime_tested=False,member_release=False)
(OUT/'Delivery_Receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
