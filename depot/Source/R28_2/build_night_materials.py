"""R28.2 FBO night atlas; rebuilds only the original NRT emissive material.

Requires Pillow and Laminar Research's DDSTool. Output is staged in a new
directory; this tool never installs scenery or modifies plugin preferences.
"""
from pathlib import Path
import argparse
import subprocess

from PIL import Image, ImageDraw


def night_atlas():
    """All glazing panes have the same subdued light; opaque materials stay dark."""
    atlas = Image.new("RGB", (4096, 2048), (0, 0, 0))
    draw = ImageDraw.Draw(atlas)
    # Match R25's 1 m glazing bays and 2 m horizontal mullions exactly.
    # The original atlas switched five of eight panes off, repeating a coarse
    # checkerboard on every 4 m wall module. Use equal occupancy in all bays.
    for row in range(2):
        for y in range(6, 507):
            t = (y - 6) / 500
            rgb = tuple(round(a + (b - a) * t)
                        for a, b in zip((16, 17, 17), (12, 14, 15)))
            for col in range(4):
                x = 2048 + col * 256
                draw.line((x + 8, row * 512 + y,
                           x + 249, row * 512 + y), fill=rgb)
    return atlas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="New staging directory, outside installed scenery")
    parser.add_argument("--ddstool", required=True, type=Path)
    args = parser.parse_args()
    if not args.ddstool.is_file():
        parser.error("DDSTool executable not found")
    args.output.mkdir(parents=True, exist_ok=False)
    png = args.output / "r25_materials_LIT.png"
    dds = args.output / "r25_materials_LIT.dds"
    night_atlas().save(png, optimize=True)
    subprocess.run([str(args.ddstool.resolve()), "--png2dxt1",
                    str(png.resolve()), str(dds.resolve())], check=True)
    with Image.open(dds) as image:
        if image.size != (4096, 2048):
            raise RuntimeError("Unexpected DDS dimensions")
    print("Prepared PNG and mipmapped DDS night atlas:", args.output)


if __name__ == "__main__":
    main()
