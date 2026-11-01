KIAH R03 HF06 - JETWAY JOINTS, B NORTH TAXI LANE, EA VATSIM VARIANT
24 October 2026
STAGED FOR REVIEW. NOT INSTALLED. SIMULATOR TEST PENDING.

CHANGES FROM HF05
* Add circular fixed connectors at the native moving pivots of all 32 rebuilt
  fixed jetway extensions. The original fixed bridge/sign geometry is retained.
  All 116 animated jetway records remain identical to HF05.
* Replace the angled circulation line near B15/B16/B17 with a straight lane
  between the two B piers and rounded arrival/departure connections to NB.
  Native paint and aircraft routes share the same points. NB's existing
  eastbound direction is retained. The inner endpoint moves 10 m east to
  provide clearance behind B11. Route category C remains (36 m wingspan).
* Remove the two rows of 11 red barriers from EA, and add aircraft links through
  NB, EC, ED and EE. Pavement, painted centerline and signs remain in place.
  This is the user's requested VATSIM variant despite the real-world closure.
  EA is bidirectional category E in this simulator package. That is a modeling
  choice, not a claim about current real-world or ZHOU direction restrictions.

REFERENCE AND CONFIDENCE
The United Terminal B gallery image c04-op1.jpg supports a straighter central
lane with rounded outer connections. The linked rendering was uploaded in
October 2024. It is a design reference, not a surveyed as-built paint chart.
The exact lane location and 30 m connection radius are our modeled solution.
https://www.iahbunited.com/gallery?pgid=ln2798ht2-ed8e1d6d-e544-45b0-b04e-0dcfa765ef2b

AEP: WHAT HAPPENED AND HOW FUTURE REFINEMENTS ARE PROTECTED
AEP supplies both library material replacements and separate airport overlays.
Its Houston overlay contains an older rounded asphalt footprint and snow layer.
Our earlier polygon-exclusion records used the wrong coordinate separators and
winding. The offline audit had accepted that wrong format, so its prior success
did not prove X-Plane would suppress the overlay. HF05 corrected our exclusions
to WED's exporter format and removed underlying obsolete native asphalt.
The user has now confirmed the unwanted surfaces are gone with AEP enabled.

HF06 preserves every HF05 exclusion property exactly. It does not change or
redistribute AEP assets. The included read-only compatibility check validates
exclusion syntax and reviewed coverage, AEP asset/configuration fingerprints,
and KIAH's priority above AEP. A changed AEP version triggers review rather than
being silently accepted. AEP's actively written runtime log is ignored.
Any future terminal/apron footprint change also needs a spatial overlay audit;
an unchanged compatibility baseline alone cannot approve a new work area.
See Sources/HF06_Repair/AEP_Compatibility_Workflow.txt.

VALIDATION AND LIMITS
20/20 targeted offline checks pass. Runtime edits are limited to 32 fixed
connector objects, apt.dat and two DSF tiles. All other DSF placements match the
source exactly after decoding. Runways, pavement, signs, service routes, starts,
and moving jetways remain unchanged. EA's route and B's revised lane connect.

The B lane was checked with sampled generic aircraft outlines: 36 m span and
40 m, 45 m, then 56 m length. For the longer checks, category-C parked outlines
were stretched as well. The 56 m case has 6.56 m minimum sampled separation
from modeled parked aircraft. This checks the revised lane, not simultaneous
compatibility of every neighboring gate or every aircraft type. Aircraft
steering, tail swing between samples, terrain, pushback and jetway docking
still need X-Plane tests. These are custom checks, not WED validation.

PREVIEW METHOD
The before/after D5 views and B overview render actual exported custom objects
and stock animated jetway meshes in their parked state. Surface materials,
lighting and retained building massing are simplified. AEP surface effects,
terrain relief, traffic and service equipment are omitted. The route maps
come from final native airport data. No preview is an HF06 simulator screenshot.

FIRST TESTS AFTER APPROVED INSTALL
1. At D5, inspect the fixed/moving joint parked, then dock and retract. Also
   inspect a B gate and one of A20/C12/C14/C15 for the same repaired connection.
2. Taxi the B central lane in your A321 or comparable aircraft, checking the
   B15/B16/B17 side and opposite B8 side. Test the rounded connections with NB.
   Use separate clearance tests for a long 757; the static proxy is not a live
   handling test. Inspect behind B11 during pushback and taxi.
3. With AEP enabled, check that the obsolete rounded asphalt island and its
   markings/lights remain absent after a complete scenery load.
4. Inspect EA at NB and EE: both red barricade rows should be gone. Taxi via
   EC/ED as appropriate for the simulation; follow the online controller.

INSTALLATION AND PROVENANCE
This is a complete successor for the single existing R03 KIAH add-on slot.
After approval, back up HF05 and replace that slot while X-Plane is closed.
Do not enable two KIAH revisions together. No install, restart or scenery
reload was performed to prepare this revision. HF05 remains installed.
Sources contains historical notes and audit copies, not a portable rebuild.
Run revise_b_lane.py in the preserved HF06 workspace for the complete rebuild;
repair_hf06.py alone is an intermediate step and does not include the B revision.
The compatibility_guard.py utility is portable with its adjacent baseline JSON.

TECHNICAL REFERENCES
https://github.com/X-Plane/xptools/blob/master/src/WEDImportExport/WED_DSFExport.cpp#L1447-L1480
https://developer.x-plane.com/?article=customizable-jetways
https://houston.center/brief/kiah
The Houston guide does not independently establish today's EA closure status.
The user's explicit VATSIM preference is the authority for opening EA here.
