"""Reversible R25 test installer and documentation; does not install."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R24_Pullthrough_Refinements_R21';PACK=ROOT/'package/KIAH_NRT_R25_Realism_R22';OUT=ROOT/'output'
assert all(c['passed'] for c in json.loads((OUT/'Validation.json').read_text())['checks'])
assert (OUT/'pdf/NRT_R25_Realism_Review.pdf').is_file()
assert not (ROOT/'NRT_KIAH_R25_Test.zip').exists(),'Sealed delivery; create a successor'
for name in ['Install R24.ps1','Install R24.cmd']:
    txt=(PREV/name).read_text().replace('R24','R25').replace('Pullthrough_Refinements_R21','Realism_R22')
    (ROOT/name.replace('R24','R25')).write_text(txt,encoding='utf-8')
for name in ['Check OpenSAM.ps1','Check OpenSAM.cmd']:shutil.copy2(PREV/name,ROOT/name)
test=(PREV/'qa/test_installer.ps1').read_text().replace('R24','R25').replace('Pullthrough_Refinements_R21','Realism_R22')
(ROOT/'qa/test_installer.ps1').write_text(test,encoding='utf-8')
readme='''NRT KIAH R25 - Maintained ramp and private-terminal realism (R22)

CURRENT REVISION. Older README files are historical records.
This isolated test package has no updater configuration: the public 0.24.0
SkunkCrafts feed is unchanged. No library or plugin binaries are bundled.

REQUIRES
X-Plane 12, existing MisterX_Library and openSAM_Library, plus openSAM for
door controls/marshalling. AEP is NOT required. The dependency check resolved
every active DSF asset using only stock Laminar + these existing libraries.

FINISH PASS
- Native new light concrete and plain asphalt, with duplicate small slab
  overlays removed. The base uses Laminar's material, decal and weather system.
- Heavy blanket rubber/grime retired. Six native narrow wheel-track runs,
  flush drainage, clear stop bars and a coherent apron instead.
- HQ and aircraft canopy share clean panel joints, blue-grey glazing, stone
  base, bronze details and a standing-seam roof. Separate normal/metalness,
  gloss and night maps. New entrance handles, doors, benches and planters.
- NRT8 and both NRT9 fixed links rebuilt to matching finishes. Recessed
  openings cut through the facade; rails and glass no longer cross them.
  Three fixed links align with their native jetway bases within 3.3 cm.
- Sparse native/library activity: pilot, security worker, stowed GPU,
  cone stack and wall-side fire extinguisher. No extra traffic plugin.

NRT11
54 m long x 71 m wide painted bay. Aircraft planning limits apply TOGETHER:
  MAX WINGSPAN 216.5 FT / 66 M
  MAX LENGTH 164 FT / 50 M
The stand remains nose EAST with a straight final approach. Identification
and limits are on the approach side, using the NRT8 wording placement.
The old 20 m side strip and small bay are removed. North boarding approach
retained; its hold point is pulled back to maintain wing clearance.
Departure uses PUSHBACK OR TOW. The shared canopy/NRT11 approach is one
aircraft movement at a time. No random AI fleet is assigned to this bay.

GEOMETRY EVIDENCE
The conservative 50 x 66 m rectangle passes the exported arrival route.
Minimum modelled arrival gap to exported walking corridor: 2.83 m.
G650 canopy sweep with the full NRT11 envelope occupied: 3.33 m minimum.
51 m length reduces that canopy gap below the 2.5 m working reserve;
68 m span reduces the walking-route gap below the reserve.
These are planning rectangles and wheelbases, not aircraft operating approval.
Actual add-on nosewheel/CG positions and steering must be tested.

OPERATIONS RETAINED
- Approved canopy pull-through and doorway stop. G650 / Lineage turn targets;
  BBJ2 remains tow-only, as previously agreed.
- 119 native airport/FBO jetway records, crew-car service route, ground tower.
- Six default-open OpenSAM controls: MH1 Outer/Middle/Tail, MH2,
  Indoor Parking Left/Right. Truck doors remain fixed open.
- One ground-lit NRT10 helipad, no beacon. Marked pedestrian path is ground
  paint, not walking agents; board with aircraft stopped and rotors stopped.
- Accepted security/blast fences, hangar geometry and all other main starts.

INSTALL ON THE TEST PC
Extract the complete ZIP. Close X-Plane, run Install R25.cmd and enter the
folder containing X-Plane.exe. The installer validates package hashes, preserves
previous folders, saves scenery_packs.ini, and selects the isolated R25 package.
Fully exit/relaunch X-Plane after installation, then load KIAH.
To return to the member feed, close X-Plane and restore the installer-created
scenery_packs.before-NRT-R25-*.ini backup as scenery_packs.ini. Prior folders
are preserved. This package does not replace the stable updater folder.

REVIEW SEQUENCE
1. Dry daylight without AEP: pavement scale, surface restraint, joint direction,
   three jetway wall openings, signs and approach-side NRT11 limits.
2. Wet/overcast: water response and transition beneath the canopy.
3. Dusk/night: glass/sign brightness, doorway/canopy spill and ground-lit pad.
4. Operations: G650/Lineage canopy movement with NRT11 occupied, NRT11 tow,
   marshaller alignment, terminal/FBO jetways, crew car and six door controls.
5. Same-view performance: frame time and VRAM, then screenshot review before
   a separate release instruction. Run Check OpenSAM.cmd after testing if needed.

VISUAL REVIEW
Open output/pdf/NRT_R25_Realism_Review.pdf or the individual PNGs. HTML is not
required. Images reopen actual OBJ meshes, with stock diffuse pavement context.
The offline renderer does not simulate native jetway arms, pavement FX, weather,
PBR reflections or X-Plane lights. Their appearance is a simulator test.

STATUS
235 exported-file, resource, geometry and preservation checks pass.
No live X-Plane appearance, motion or performance acceptance is claimed.
Built locally; not installed on the development PC or published to SkunkCrafts.
The approved follow-up passes for maintenance/cargo detail and broader edges/
lighting remain later review stages.
'''
(PACK/'README_R25.txt').write_text(readme);(OUT/'Install_and_Test.txt').write_text(readme)
dest=PACK/'Source/R25';dest.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,dest/p.name)
shutil.copy2(ROOT/'qa/R25_South.txt',dest/'South.dsf.txt')
(dest/'README.txt').write_text('Authoring records for the isolated review. Builds require private workspace predecessor helpers and Laminar tools. No third-party library contents copied. Runtime acceptance is separate.\n')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(OUT/'Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
(ROOT/'STATUS.txt').write_text('R25 built; 235 offline checks passed. PDF and image review ready. Isolated installer and archive checks pending. Not installed or published; public release is 0.24.0 / R24.\n')
print(json.dumps(dict(prepared=True,files=len(hashes),installed=False,published=False)))
