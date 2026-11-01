CURRENT R28 EDITABLE PLACEMENT
Source/Native/+29-096.txt and +30-096.txt describe the compiled DSF placements
for this variant. Source/rebuild_dsf.py rebuilds them into a new folder using
Laminar DSFTool; OBJ8, apt.dat, XML and textures are also editable inputs.
Source/R28 contains the Terminal B authoring scripts and variant preparation.
Historical generation scripts require their recorded predecessor inputs and
workspace paths; they are not a portable complete authoring environment.

HISTORICAL AUTHORING NOTES
R21 authoring sources and R17 helper provenance are provided. Rebuilding requires the preserved R20 package as baseline, the R21 concept measurements, Python with numpy/Pillow/Shapely, and Laminar xptools. Native library resources are referenced from X-Plane, not copied into this package. Full predecessor source is retained in the source workspace.

R22 original garage: Source/R22/build_r22.py generates the new garage geometry, materials and door controls without any imported donor assets. Source/R22/South.dsf.txt is the exact compiled native DSF input. validate_r22.py and render_r22.py reopen exported geometry. Historical R21/R17 authoring files may mention predecessors; no T02 garage mesh or texture is included in this package.
