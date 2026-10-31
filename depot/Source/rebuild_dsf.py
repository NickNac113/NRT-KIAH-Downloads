"""Compile the editable placement snapshot into a new scenery folder using DSFTool.

Example: python Source/rebuild_dsf.py --dsftool /path/to/DSFTool --out /new/path/NRT_KIAH_Campus
OBJ8, apt.dat, XML and PNG assets are already editable and copied unchanged.
"""
from pathlib import Path
import argparse
import shutil
import subprocess

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dsftool', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    source = Path(__file__).resolve().parents[1]
    out = a.out.resolve()
    if out.exists() or out.is_relative_to(source):
        raise ValueError('Choose a new directory outside the source scenery')
    shutil.copytree(source, out)
    for cell, folder in [('+29-096', '+20-100'), ('+30-096', '+30-100')]:
        subprocess.run([str(a.dsftool.resolve()), '--text2dsf', str(source / 'Source/Native' / (cell + '.txt')), str(out / 'Earth nav data' / folder / (cell + '.dsf'))], check=True)
    print('Compiled editable placement snapshot:', out)
