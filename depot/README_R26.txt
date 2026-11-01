HISTORICAL LOCAL TEST NOTES - superseded by member release 0.27.0.
For current installation and operations use INSTALL.txt and README_R27.txt.
The isolated test installers and review outputs mentioned below are not bundled.

NRT KIAH R26 - Work lighting, pedestrian separation and service access (R23)

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
295 offline exported-file, geometry, dependency and preservation
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
