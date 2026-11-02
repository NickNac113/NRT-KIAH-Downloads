NRT KIAH 0.28.2 / R28.2 - FBO night glazing and native jetway guidance

Main: corrects the repeating illuminated/dark window checkerboard across the
FBO/headquarters. All glazing panes now use consistent, subdued illumination
with a slight vertical falloff. Opaque materials remain unlit. Daytime color,
normal/roughness maps, geometry, signs, lights and aircraft paths are unchanged.
The same original NRT material is used by the fixed FBO jetway links/portals.

Airport Only: has no fictional FBO material. Its airport geometry is unchanged;
the shared version advances with updated native-jetway operating instructions.

Terminal B already uses native X-Plane 12 animated jetways. To let X-Plane
manage them, open OpenSAM > Settings, uncheck Manage XP12 Jetways, and FULLY
RESTART X-Plane. This setting is global. Keep OpenSAM/openSAM_Library installed
for the NRT hangar-door controls. See JETWAYS.txt for details and limitations.

Main source: Source/R28_2/build_night_materials.py. Requires Pillow and Laminar
Research DDSTool; generates only the night atlas into a new staging folder.
Historical R25 source is preserved. No plugin or simulator preferences ship
with this update. Offline material/package checks are not in-simulator visual
acceptance. Check dusk/night lighting and native jetway docking in X-Plane.
