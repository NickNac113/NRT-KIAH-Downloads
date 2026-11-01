NRT KIAH R27 - Member release 0.27.0

CURRENT REVISION. Earlier README files are historical records. This cumulative
release includes R25, R26 and R27. No library or plugin binaries are bundled.
AEP is NOT required.

CHANGES SINCE THE LAST MEMBER RELEASE
- Native light concrete and asphalt, restrained wheel tracks and surface
  details. Headquarters and canopy share glazing, panel, roof and night maps.
- NRT8/NRT9 fixed jetway links meet recessed openings in the terminal facade.
- NRT11 remains nose EAST. Its bay is now 54 m long x 71 m wide; aircraft
  planning limits apply TOGETHER: 66 m / 216.5 ft wingspan and 50 m / 164 ft
  length. Limits are painted on the approach side. Push back or tow out.
- Secure ramp fencing separates the aircraft area from public parking.
- Building-mounted work lights cover the terminal, NRT11, walk and hangars.
  Canopy lights improved; one stock mast matching NRT8 added at NRT9/NRT11.
  The new mast is 43.3 m outside the helipad reserved square.
- NRT9 stand moved 4 m east for walking clearance. Both native jetways,
  fixed links, wall openings and red movement boxes now match that shift.
- Connected native service roads, a paved connector and seven local service
  parking positions with a holding destination. Additional access nodes
  address dispatch distance and long service-road segments beside NB.
- Modeled floors under the canopy and Indoor Parking use the dry MH1/MH2
  floor treatment; guidance stays above them. Exterior wet pavement retained.

OPERATIONS
One ground-lit NRT10 helipad, no beacon. Use the marked walk only when aircraft
are stationary and rotors stopped. The canopy pull-through and NRT11 approach
share space: one aircraft movement at a time. G650/Lineage are the canopy turn
targets; BBJ2 remains tow-in/tow-out. Aircraft fit and steering require testing.

Six OpenSAM controls remain, all default OPEN: MH1 Outer/Middle/Tail, MH2,
Indoor Parking Left and Right. Truck doors remain fixed open. All 119 native
airport/FBO jetway records remain. Main starts and aircraft taxi routes retained.

INSTALL AND UPDATE
Close X-Plane. Update NRT KIAH Campus with SkunkCrafts, or extract the member ZIP
to the stable Custom Scenery/NRT_KIAH_Campus folder for a first installation.
Keep MisterX Library, OpenSAM and openSAM_Library installed separately.
Disable older versioned NRT/KIAH scenery entries while the stable folder is
active; retain their folders for rollback. Fully restart X-Plane after updating.
See INSTALL.txt for priority, dependency and rollback instructions.

CHECK IN X-PLANE
1. Request catering, baggage and fuel at NRT9, then cargo and canopy; follow
   dispatch/return paths beside NB and inspect the new local service parking.
2. Test both NRT9 jetways against your normal aircraft and check the walk.
3. In rain, check canopy/Indoor Parking floors, thresholds and guidance.
4. At night, check the corner mast, work lights, helipad and frame time.
5. Confirm canopy guidance, six door controls and the crew-car circuit.
Use Check OpenSAM.cmd for read-only diagnostics if needed.

VERIFICATION LIMITS
R27 passed 149 offline checks and 8 mock installer checks. The release matches
the sealed runtime assets. Simulator acceptance remains pending for this build.
The previous service graph was already connected; these changes address
dispatch distance and access choices, not a proven single cause. Native AI
can leave the road graph on its final approach, so grass shortcuts must be
rechecked in X-Plane. No rain-particle occlusion is claimed. Wet-floor behavior,
jetway docking and night appearance need a fresh simulator session.
