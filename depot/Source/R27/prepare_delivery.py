"""Prepare the reversible local R27 installer, manifest and test notes."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R26_Lighting_Access_R23';PACK=ROOT/'package/KIAH_NRT_R27_Shelter_Service_R24';OUT=ROOT/'output'
validation=json.loads((OUT/'Validation.json').read_text())
assert all(c['passed'] for c in validation['checks'])
assert not (ROOT/'NRT_KIAH_R27_Test.zip').exists(),'Sealed revision; use a successor'
for name in ['Install R26.ps1','Install R26.cmd']:
    txt=(PREV/name).read_text().replace('R26','R27').replace('Lighting_Access_R23','Shelter_Service_R24')
    (ROOT/name.replace('R26','R27')).write_text(txt,encoding='utf-8')
for name in ['Check OpenSAM.ps1','Check OpenSAM.cmd']:shutil.copy2(PREV/name,ROOT/name)
test=(PREV/'qa/test_installer.ps1').read_text().replace('R26','R27').replace('Lighting_Access_R23','Shelter_Service_R24')
(ROOT/'qa/test_installer.ps1').write_text(test,encoding='utf-8')
readme=f'''NRT KIAH R27 - Shelter, service access, corner mast and NRT9 jetways (R24)

CURRENT REVISION. Earlier README files describe historical revisions.
Isolated local test package. No public SkunkCrafts feed changed.
No library or plugin binaries bundled. AEP is NOT required.

REQUIRES
X-Plane 12, MisterX_Library and openSAM_Library, plus openSAM for the
existing door controls and arrival guidance.

CHANGES
- Seven local native service-vehicle parking positions and one holding
  destination east of HQ; a connected paved road west of HQ; additional
  access nodes on the long NB service-road segments.
- Both NRT9 native jetways, fixed connections, facade portals and red
  movement boxes shift 4 m east to match the stand already moved in R26.
- Stock pole mast matching NRT8 at the HQ corner beside NRT9/NRT11.
  43.3 m outside the helipad reserved square; ground pad lights retained.
- Modeled canopy and Indoor Parking floors matching the dry MH1/MH2
  floor material, with guidance above them. Exterior wet pavement retained.

RETAINED
All aircraft/heli starts and aircraft taxi lines. One ground-lit helipad,
secure ramp fences, blast fences, pull-through canopy, enlarged NRT11
(nose east; maximum 66 m wingspan AND 50 m length), six default-open
independent OpenSAM door controls. Truck doors stay fixed open.
Other airport jetways, predecessor packages and public payload unchanged.

INSTALL
Extract this complete ZIP. Close X-Plane and run Install R27.cmd.
Choose the folder containing X-Plane.exe. The installer verifies hashes,
copies this isolated revision, backs up scenery_packs.ini and selects R27.
Previous scenery folders and installed libraries remain preserved.
Then start X-Plane and load KIAH. A full restart is required.

ROLL BACK
With X-Plane closed, restore the installer-created
scenery_packs.before-NRT-R27-*.ini backup as scenery_packs.ini. Do not
delete predecessor packages or libraries. The previous selection returns.

TEST SEQUENCE
1. At NRT9, request catering, baggage and fuel. Observe dispatch and return
   beside NB, then repeat at cargo and canopy. Check the staging positions.
2. Test both NRT9 jetways against your normal aircraft.
3. Wet weather: canopy and Indoor Parking floors, thresholds and guidance.
4. Night: corner pole spill, walking path, pad clearance and frame time.
5. Existing door controls, canopy arrival guidance and crew-car circuit.

LIMITS OF VERIFICATION
{validation['passed']} offline exported-file, geometry, graph, dependency and
preservation checks pass. Native AI may leave the road graph for its final
approach. The old local graph was already connected; this test addresses
vehicle dispatch distance and access-node spacing, not a proven root cause.
Actual vehicle behavior, docking, night appearance and wet-weather floor
behavior remain untested in X-Plane. No rain-particle occlusion is claimed.

REVIEW
Open output/R27_Repair_Plan.png and output/Review.txt. No HTML is required.
The three model previews use actual exported meshes; they do not simulate
X-Plane lighting/weather or native animated jetway arms.
'''
(PACK/'README_R27.txt').write_text(readme);(OUT/'Install_and_Test.txt').write_text(readme)
dest=PACK/'Source/R27';dest.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,dest/p.name)
shutil.copy2(ROOT/'qa/R27_South.txt',dest/'South.dsf.txt')
(dest/'README.txt').write_text('Private-workspace authoring records. Rebuilds require predecessor helpers and Laminar tools. No third-party library contents copied. Runtime acceptance remains separate.\n')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(OUT/'Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
(ROOT/'STATUS.txt').write_text(f'R27 built; {validation["passed"]} offline checks passed. Installer/archive checks pending. Not installed or published.\n')
print(json.dumps(dict(prepared=True,files=len(hashes),installed=False,published=False)))
