R29 / 0.29.0 C/D native material pass

Editable final source: Source/Native/+29-096.txt and objects/bridge_C12.obj,
bridge_C14.obj, bridge_C15.obj and bridge_D1.obj through bridge_D6.obj.
Rebuild the native placement with Source/rebuild_dsf.py and Laminar DSFTool.
All referenced terminal-kit resources come from X-Plane; none of their
textures or artwork are redistributed. Materials.json records the 38 added
facades and nine edited fixed links. Local plan coordinates are metres east
and north of longitude -95.341444444, latitude 29.984444444; the native text
contains the final geographic coordinates used for compilation.

D_West and International_Processor OBJ placements are replaced by native
terminal facades. Their old source files remain for historical reference.
Fixed-link glass skins are replaced; support and jetway pivot geometry is
retained. Four sign vertices per link are raised 1.1 m above the new link
roof. Airport starts, pavement, routes, animated jetways and OpenSAM XML
are unchanged from 0.28.2. This is not a remodel of original Terminal C.

Confirmed HF05/HF06 pavement clipping and all 4741 original exclusion
records are preserved in both variants. The Main variant retains six
additional campus exclusions. See SCENERY_ORDER.txt if old pavement returns.
