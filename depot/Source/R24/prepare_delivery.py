"""Prepare a reversible isolated test installer; no live installation."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R23_Jet_Center_Refinement_R19';PACK=ROOT/'package/KIAH_NRT_R24_Pullthrough_Refinements_R21';OUT=ROOT/'output'
assert all(c['passed'] for c in json.loads((OUT/'Validation.json').read_text())['checks'])
for name in ['Install R23.ps1','Install R23.cmd']:
    txt=(PREV/name).read_text().replace('R23','R24').replace('Jet_Center_Refinement_R19','Pullthrough_Refinements_R21')
    (ROOT/name.replace('R23','R24')).write_text(txt,encoding='utf-8')
for name in ['Check OpenSAM.ps1','Check OpenSAM.cmd']:shutil.copy2(PREV/name,ROOT/name)
test=(PREV/'qa/test_installer.ps1').read_text().replace('R23','R24').replace('Jet_Center_Refinement_R19','Pullthrough_Refinements_R21')
(ROOT/'qa/test_installer.ps1').write_text(test,encoding='utf-8')
readme='''NRT KIAH R24 - Pull-through and campus refinements (R21)

CURRENT REVISION. Older README_R22/R23 files are historical records.
This package is an isolated test revision; no plugin binaries or libraries are bundled.

CHANGES
- Approved canopy pull-through entry and forward exit in native yellow guidance.
  Stop and passenger doorway moved 11 m north. G650 and Lineage are the turn
  targets; BBJ2 remains tow-in/tow-out. One movement at a time; yield at the spine.
- Both main headquarters signs read NRT VIRTUAL HEADQUARTERS.
- Former private hangar is INDOOR PARKING. Roof matches MH2 (20.6 m main roof,
  20.78 m skylights), with a 16 m clear opening. Unified walls remove overlapping
  corner faces. Left/south and right/north doors are independently controlled,
  as viewed facing the east hangar entrance. Both default open.
- Six OpenSAM controls: MH1 outer/middle/tail, MH2, Indoor Parking Left/Right.
  Truck doors are fixed open and have no OpenSAM controls or animation datarefs.
- Former arrival-court fence fabric AND metal framework removed. Guardhouse,
  vehicle entry barrier and surrounding security perimeter retained.
- Old red open-parking square removed across and behind the hangar footprint.
- Native 5 m blast fencing faces the apron and follows the complete south, east
  and northeast cargo fence sections. Vehicle entrances remain open.
- NRT11 is a single small GA/small business-jet stand on the former second-pad
  area: 20 m (about 66 ft) maximum wingspan, 22 m planning length, nose east.
  Per the latest instruction, the upper canopy branch bends gently into a
  straight eastbound final approach. Push back or tow out; the white bay is a planning
  envelope and aircraft/add-on fit needs testing.
- Flush pedestrian markings follow the stepped headquarters wall and pass
  east of the GA bay, with a branch approaching its north edge and a continued
  route to the hold point outside NRT10. Neither aircraft entry
  line crosses this walk. Use only with aircraft stationary and rotors stopped.
  No walking-agent simulation is added. One NRT helipad remains, ground lit.
  No beacon, per Nick's instruction.
- Native airport/FBO jetways (119 records), service routes, MH1/MH2 animation,
  ground tower and north airport tile retained.

INSTALL
Extract the complete ZIP. With X-Plane closed, run Install R24.cmd and provide
the folder containing X-Plane.exe on the test PC. The installer verifies every
package hash, preserves old folders, backs up scenery_packs.ini and selects the
isolated R24 above earlier NRT scenery. Keep MisterX_Library and openSAM_Library
installed. Fully relaunch X-Plane after installation and load KIAH.

TEST
1. NRT CANOPY: taxi G650 or Lineage down the entry line, park at the moved stop,
   verify marshaller/L1 position, then follow the forward exit. Check steering,
   wing/tail tracking and canopy columns. BBJ2 is excluded from this turn test.
2. NRT INDOOR PARKING: outward-facing start retained. Operate left and right
   controls separately; confirm default-open behavior on a fresh scenery load.
3. Inspect corners, red-paint removal behind the hangar, court fencing and each
   blast fence run. Taxi a suitable small GA jet into NRT11 from the upper
   branch, then check the pedestrian route around the building and hold point.
4. Confirm terminal and FBO jetways still load and move with your aircraft.
5. Run Check OpenSAM.cmd after the session if diagnostics are needed.

VALIDATION LIMITS
Offline exported-file and geometry checks pass. Live X-Plane taxi steering,
surface appearance, night lighting, marshalling and door operation have not
been accepted for R24. The aircraft sweep model uses conservative rectangles
and planning wheelbases; it is not aircraft operating approval.

This revision was not installed on the development PC or published to the
public SkunkCrafts feed. R23 remains the published release.
Rollback: close X-Plane and restore the saved scenery_packs.before-NRT-R24-*.ini
to scenery_packs.ini. The predecessor scenery folders were not changed.
'''
(PACK/'README_R24.txt').write_text(readme);(OUT/'Install_and_Test.txt').write_text(readme)
dest=PACK/'Source/R24';dest.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,dest/p.name)
shutil.copy2(ROOT/'qa/R24_South.txt',dest/'South.dsf.txt')
shutil.copy2(ROOT/'reference/Approved_Pullthrough.json',dest/'Approved_Pullthrough.json')
(dest/'README.txt').write_text('Authoring records; builds require the private workspace R23/R21/R17 helpers and Laminar tools. No third-party library assets copied. Approved route geometry is recorded in Approved_Pullthrough.json. Runtime testing is separate from these offline checks.\n')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(OUT/'Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
(ROOT/'STATUS.txt').write_text('R24 built and checked offline. Installer and archive verification pending. Not installed or published. User tests on the new X-Plane PC.\n')
print(json.dumps(dict(prepared=True,files=len(hashes),installed=False,published=False)))
