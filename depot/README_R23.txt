HISTORICAL NOTES - retained from the previous member release.
For this package use README.txt and INSTALL.txt. The test installers and
review outputs mentioned below are not included in the member ZIP.

NRT KIAH Campus 0.23.0 (R23)

See INSTALL.txt for the stable NRT_KIAH_Campus folder and SkunkCrafts updates.
See ASSET_NOTICES.txt and COPYING for asset provenance and inherited notices.
Keep MisterX Library, OpenSAM and openSAM_Library installed separately.

R23 CHANGES
The FBO/private terminal and aircraft canopy share one exterior design with
original material maps, glazing, stone base, shade details and entrance lights.
The canopy start faces south and enters from the north side, with the left
passenger door toward the doorway under the canopy. Use tow-in/tow-out for the
BBJ2. All canopy departures back out north; the south perimeter has no exit.
A native OpenSAM marshaller placement serves the detached stand guidance.

NRT10 is the single retained 40 m helipad with ground-level lighting and a
46 m reserve outline. Its internal native pad identifier is H2. The unrelated
airport H1 remains. The second campus pad and old paint/label fragments were
removed. The private-hangar label faces the approaching apron. The fence
crossing the passenger arrival court was removed. Native weather-aware concrete
and surface details accompany a native crew-car route from the parking aisle,
around the landscaped median, to the arrival curb. The delivery area remains.

OPENsam AND SIMULATOR TEST STATUS
All eight existing door controls and 119 native airport jetway records remain.
Hangars are configured open by default. Runtime discovery of NRT by OpenSAM
still needs a full simulator restart test; this release does not claim the
reported missing controls or jetways are fixed. SkunkCrafts updates scenery
files only. It does not change scenery_packs.ini or plugin settings.

After updating with X-Plane closed, relaunch and load KIAH. If controls or
jetways remain absent, run Check OpenSAM.cmd in this folder and enter the
X-Plane root. The checker reads configuration and Log.txt without writing.
It distinguishes OpenSAM discovery from X-Plane merely loading the scenery.

SIMULATOR CHECKS
1. View the hangars, then verify and test the eight Close controls: MH1 outer,
   middle and tail; MH2; private hangar; and three truck-garage doors.
2. Inspect terminal B and FBO animated jetways, including NRT8 single and
   NRT9 dual. Fixed rotundas alone are not a pass.
3. Approach NRT CANOPY from the north with the beacon on. For a ground-only
   marshaller test, use OpenSAM Activate or select the canopy in its stand
   menu. Confirm the stop and left passenger-door alignment. The Lineage is
   the alignment datum; different add-ons may need a small stop adjustment.
4. Inspect the single NRT10 pad, removed artifacts, corrected hangar label,
   passenger court, crew-car route, wet pavement and night lighting.

Offline checks verify export integrity and planning clearances: minimum BBJ2
roof gap 1.5 m and sampled approach-box gap to fixed structures 5.45 m. These
checks do not establish steering, tug behavior or simulator acceptance.
