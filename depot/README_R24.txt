NRT KIAH R24 - Pull-through and campus refinements (R21)

CURRENT REVISION. Older README_R22/R23 files are historical records.
Member release 0.24.0; no plugin binaries or libraries are bundled.

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
Close X-Plane and update NRT KIAH Campus with SkunkCrafts. First installations
use the member ZIP and stable Custom Scenery/NRT_KIAH_Campus folder. See
INSTALL.txt for dependencies, scenery priority, rollback and restart guidance.
Keep MisterX Library, OpenSAM and openSAM_Library installed separately.

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

Member distribution uses the stable SkunkCrafts feed. Earlier versioned test
folders remain separate and must be disabled while this package is active.
The next-revision ramp-security perimeter is not part of this release.
