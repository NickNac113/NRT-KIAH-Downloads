R29.1 / 0.29.1 - Terminal B North obsolete-island cleanup

Earth nav data/apt.dat is the complete editable airport input for this variant.
Source/Native/+29-096.txt is the matching editable placement source; rebuild
with Source/rebuild_dsf.py and Laminar DSFTool into a separate output folder.

Four legacy native concrete surfaces are clipped only inside the rebuilt
B North apron. Thirty redundant HF04 island-shaped concrete cover patches
are removed; the current continuous B apron supplies that entire surface.
The three HF05 asphalt cut-outs remain unchanged. Nine original attributed
edges outside the cut-out retain their exact marking/light coordinates.

Two rectangular polygon/line exclusions supplement the original HF06
footprints wholly within the rebuilt apron. Binary DSF placement commands
are unchanged. Current taxi guidance, routes, stands, jetways and all other
terminal/campus geometry remain unchanged from R29.

RepairSummary.json records both channel file hashes and the bounded scope.
All 66 independent geometry/export checks passed. This is offline evidence;
the appearance of the cleared apron still requires a member simulator test.
