"""Prepare the reversible local R26 installer, manifest and test notes."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R25_Realism_R22';PACK=ROOT/'package/KIAH_NRT_R26_Lighting_Access_R23';OUT=ROOT/'output'
validation=json.loads((OUT/'Validation.json').read_text())
assert all(c['passed'] for c in validation['checks'])
assert not (ROOT/'NRT_KIAH_R26_Test.zip').exists(),'Sealed revision; use a successor'
for name in ['Install R25.ps1','Install R25.cmd']:
    txt=(PREV/name).read_text().replace('R25','R26').replace('Realism_R22','Lighting_Access_R23')
    (ROOT/name.replace('R25','R26')).write_text(txt,encoding='utf-8')
for name in ['Check OpenSAM.ps1','Check OpenSAM.cmd']:shutil.copy2(PREV/name,ROOT/name)
test=(PREV/'qa/test_installer.ps1').read_text().replace('R25','R26').replace('Realism_R22','Lighting_Access_R23')
(ROOT/'qa/test_installer.ps1').write_text(test,encoding='utf-8')
readme=f'''NRT KIAH R26 - Work lighting, pedestrian separation and service access (R23)

CURRENT REVISION. Earlier README files describe historical revisions.
Isolated local test package. No SkunkCrafts feed or public release changed.
No library or plugin binaries bundled. AEP is NOT required.

REQUIRES
X-Plane 12, MisterX_Library and openSAM_Library, plus openSAM for the
existing door controls and arrival guidance.

CHANGES
- 22 new building-mounted, directional, night-only work lights: terminal,
  NRT11, pedestrian doorway and the hangar apron. Nine existing canopy
  lamps upgraded at their original 15.7 m mounting height.
- NRT9 moves 4 m east with its start, yellow stand line, stop markings,
  ground label and stand outline. The building-side walking corridor
  stays in place; 4.47 m outside a full-width parked A380 rectangle.
  NRT8 and NRT9 rectangles retain 14.09 m separation.
- Native connected airport service roads to the terminal and cargo apron;
  59 nodes and 59 edges, with a six-metre marked corridor. A small native
  concrete connector bridges the measured grass gap beside the old road.
  No service-vehicle spawn/destination removed; crew-car loop retained.

RETAINED
One ground-lit helipad, no additional mast or beacon. Secure ramp fences,
blast fences, pull-through canopy, enlarged NRT11 (nose east; maximum
66 m wingspan AND 50 m length), other starts and main taxi routes retained.
119 native jetway records and fixed links unchanged. Six default-open
independent OpenSAM controls retained; truck doors remain fixed open.

INSTALL
Extract this complete ZIP. Close X-Plane and run Install R26.cmd.
Choose the folder containing X-Plane.exe. The installer validates hashes,
copies this isolated revision, backs up scenery_packs.ini and selects R26.
Previous scenery folders and libraries remain preserved.
Then start X-Plane and load KIAH. A full restart is required.

ROLL BACK
With X-Plane closed, restore the installer-created
scenery_packs.before-NRT-R26-*.ini backup as scenery_packs.ini. Do not
delete predecessor packages or libraries. The previous selection returns.

TEST SEQUENCE
1. Dusk/night: brightness at the aircraft noses, NRT11, canopy and hangars;
   compare frame time from the same camera. Helipad remains ground-lit.
2. NRT9: parked large-aircraft walking clearance and both jetway connections.
3. Call service vehicles at NRT1-9 and follow their route from NB. Check
   the connector and final approach to the aircraft on the apron.
4. Existing canopy arrival guidance, door controls and crew-car circuit.

LIMITS OF VERIFICATION
{validation['passed']} offline exported-file, geometry, dependency and preservation
checks pass. Actual X-Plane light appearance and frame time remain untested.
The native service-road additions address a plausible cause of the grass
crossings. X-Plane still chooses its final approach away from the network;
this is not a claim that every service-vehicle behavior is resolved.
Actual add-on docking after the four-metre NRT9 shift must be tested.

REVIEW
Open the PNG files and output/Review.txt. No HTML is required.
Lighting_Service_Plan shows fixture locations and ground aim, not simulated
illumination. The model previews show actual exported fixture geometry;
they do not render native jetway arms or X-Plane lighting/weather.
'''
(PACK/'README_R26.txt').write_text(readme);(OUT/'Install_and_Test.txt').write_text(readme)
dest=PACK/'Source/R26';dest.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,dest/p.name)
shutil.copy2(ROOT/'qa/R26_South.txt',dest/'South.dsf.txt')
(dest/'README.txt').write_text('Private-workspace authoring records. Rebuilds require predecessor helpers and Laminar tools. No third-party library contents copied. Runtime acceptance remains separate.\n')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(OUT/'Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
(ROOT/'STATUS.txt').write_text(f'R26 built; {validation["passed"]} offline checks passed. PNG and actual-export review ready. Installer/archive checks pending. Not installed or published.\n')
print(json.dumps(dict(prepared=True,files=len(hashes),installed=False,published=False)))
