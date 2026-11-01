KIAH NRT R28 - TERMINAL B REFINEMENT
2026-11-01

CURRENT STATUS: Local review/test build. Not installed or published.
This is a cumulative successor to R27. Earlier README files describe historic
revisions; this file defines the status of the R28 review package.

CHANGES
- Native X-Plane terminal glass, interior passenger artwork and matching roofs.
- 22 matching fixed glass corridors; existing animated jetway positions retained.
- 12 roof HVAC units, six skylights; U-shaped B North footprint retained.
- ND/NG paint aligned to aircraft network; duplicate B-side branches removed.
- Smooth R1 arrival/departure paint at NB.
- No redesign of B South, neighboring terminal placements or NRT campus.

267 offline checks passed. Simulator testing and live jetway docking are pending.
No AEP dependency. Existing MisterX Library, openSAM_Library and openSAM
requirements remain. Native library assets are referenced, not bundled.

MANUAL TEST INSTALL (WHEN READY)
1. Fully exit X-Plane. Preserve your current scenery folder and scenery_packs.ini.
2. Copy KIAH_NRT_R28_Terminal_B_R25 into X-Plane 12/Custom Scenery/.
3. In scenery_packs.ini enable this folder at the same priority as your current
   cumulative NRT KIAH revision. Disable the previous cumulative revision and any
   NRT_KIAH_Campus duplicate. Do not run two cumulative revisions together.
4. Keep required libraries enabled. Launch X-Plane, load KIAH and follow the
   review sequence in Review/Review.txt.
5. To revert, exit X-Plane, disable R28 and restore the previous scenery entry.

This review folder intentionally has no new updater configuration. Do not
overwrite your member install with this review package. Publication will be a
separate release after simulator review.
