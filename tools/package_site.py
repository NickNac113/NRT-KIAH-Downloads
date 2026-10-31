"""Verify the published depot and build the static site and deterministic install ZIP."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import html
import json
import shutil
import zipfile
import zlib


def safe_path(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or any(c in value for c in '\\:|\r\n') or any(x in ('', '.', '..') or x.startswith('.') for x in value.split('/')):
        raise ValueError('Unsafe release path')
    if value.lower() in ('scenery_packs.ini', 'skunkcrafts_updater_ignore.txt') or p.parts[0].lower() == 'skunkcrafts':
        raise ValueError('User state cannot be published')
    return value


def package(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    if out.exists() or out == root or out.is_relative_to(root / 'depot'):
        raise ValueError('Site output must be a new directory outside the depot')
    data = json.loads((root / 'release-manifest.json').read_text())
    if data['preview_only'] or data['not_for_publication'] or data['local_only_assets']:
        raise ValueError('Cannot publish local-only output')
    depot = root / 'depot'
    cfg = dict(line.split('|', 1) for line in (depot / 'skunkcrafts_updater.cfg').read_text().splitlines() if line)
    expected_cfg = dict(name=data['product'], module=data['module_url'].rstrip('/'), version=data['version'], locked='false', zone='custom')
    if cfg != expected_cfg:
        raise ValueError('Updater configuration differs from manifest')
    crcmap = dict(s.rsplit('|', 1) for s in (depot / 'skunkcrafts_updater_whitelist.txt').read_text().splitlines() if s)
    sizes = dict(s.rsplit('|', 1) for s in (depot / 'skunkcrafts_updater_sizeslist.txt').read_text().splitlines() if s)
    paths = {r['path'] for r in data['files']}
    if paths != set(crcmap) or paths != set(sizes) or len(paths) != len(data['files']):
        raise ValueError('Release inventory differs')
    if len({p.lower() for p in paths}) != len(paths):
        raise ValueError('Case-colliding release paths')
    for record in data['files']:
        rel = safe_path(record['path'])
        content = (depot / rel).read_bytes()
        if hashlib.sha256(content).hexdigest() != record['sha256'] or len(content) != record['size'] or len(content) != int(sizes[rel]):
            raise ValueError('Payload mismatch: ' + rel)
        if int(crcmap[rel]) != record['crc32'] or record['crc32'] not in (-1, zlib.crc32(content) & 0xffffffff):
            raise ValueError('CRC mismatch: ' + rel)
    for rel in (depot / 'skunkcrafts_updater_blacklist.txt').read_text().splitlines():
        safe_path(rel)
        if rel.lower() in {p.lower() for p in paths} or rel.startswith('skunkcrafts_updater_'):
            raise ValueError('Unsafe blacklist overlap')
    metadata = {'skunkcrafts_updater.cfg', 'skunkcrafts_updater_whitelist.txt', 'skunkcrafts_updater_sizeslist.txt', 'skunkcrafts_updater_blacklist.txt'}
    inventory = set()
    for p in depot.rglob('*'):
        if p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Linked depot item')
        if p.is_file():
            inventory.add(p.relative_to(depot).as_posix())
    if inventory != paths | metadata:
        raise ValueError('Unexpected depot files')
    safe_path(data['folder'])
    if '/' in data['folder']:
        raise ValueError('Invalid scenery folder')
    out.mkdir(parents=True)
    shutil.copytree(depot, out / 'depot')
    downloads = out / 'downloads'
    downloads.mkdir()
    zipname = f'{data["folder"]}-{data["version"]}.zip'
    zipfile_path = downloads / zipname
    with zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for rel in [*(r['path'] for r in data['files']), 'skunkcrafts_updater.cfg']:
            zi = zipfile.ZipInfo(f'Custom Scenery/{data["folder"]}/{rel}', (2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            archive.writestr(zi, (depot / rel).read_bytes())
    checksum = hashlib.sha256(zipfile_path.read_bytes()).hexdigest() + '  ' + zipname + '\n'
    # ZIPs are rebuilt on Linux and Windows. Compare payload CRCs above on all platforms;
    # each archive publishes its own SHA256 because zlib implementations can vary.
    (downloads / 'SHA256SUMS.txt').write_text(checksum, encoding='utf-8')
    shutil.copyfile(root / 'release-manifest.json', downloads / 'release-manifest.json')
    (out / '.nojekyll').write_text('')
    install = html.escape((depot / 'INSTALL.txt').read_text())
    ver = html.escape(data['version'])
    revision = html.escape(data.get('source_revision', ''))
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NRT KIAH Downloads</title><style>body{{margin:0;background:#10252e;color:#e6f1f0;font:17px/1.65 system-ui}}main{{max-width:960px;margin:auto;padding:60px 24px}}h1{{font-size:48px;line-height:1.1}}h2{{margin-top:40px}}a{{color:#80e2d1}}.button{{display:inline-block;background:#8de4c9;color:#10252e;padding:14px 24px;border-radius:8px;font-weight:700;text-decoration:none}}.muted{{color:#b9cbcc}}pre{{white-space:pre-wrap;font:16px/1.65 system-ui;background:#183540;padding:24px;border-radius:8px}}code{{overflow-wrap:anywhere}}nav{{display:flex;gap:20px;align-items:center;flex-wrap:wrap}}</style><main>
<p class="muted">NRT / X-PLANE 12 / MEMBER SCENERY</p><h1>KIAH Campus</h1><p>Version {ver} · {revision}</p>
<nav><a class="button" href="downloads/{zipname}">Download scenery ({zipfile_path.stat().st_size / 1000000:.1f} MB)</a><a href="https://github.com/NickNac113/NRT-KIAH-Downloads/releases">Version archives</a><a href="downloads/SHA256SUMS.txt">SHA-256</a></nav>
<p class="muted">Includes the SkunkCrafts connection. Libraries and plugins are installed separately. Read the installation notes for this build's test status.</p><p>Need the updater? <a href="https://1228098873.rsc.cdn77.org/updater/SkunkcraftsUpdater-windows.zip">SkunkCrafts for Windows (developer download)</a> · <a href="https://github.com/lzamouth/sku_client/blob/master/docs/USER_GUIDE.md">Updater guide</a></p>
<h2>Install once, update in place</h2><pre>{install}</pre><h2>Update feed</h2><p>SkunkCrafts reads the configuration included with your download. Future published versions appear when you check for updates.</p><p><a href="depot/skunkcrafts_updater.cfg">View updater configuration</a> · <a href="depot/changelog.txt">Changelog</a> · <a href="depot/ASSET_NOTICES.txt">Asset notices</a></p></main></html>'''
    (out / 'index.html').write_text(page, encoding='utf-8')
    (out / 'release-notes.md').write_text(f'NRT KIAH Campus {data["version"]}\n\n'+(depot / 'changelog.txt').read_text()+'\n\nInstall instructions and test status: https://nicknac113.github.io/NRT-KIAH-Downloads/\n', encoding='utf-8')
    print(json.dumps(dict(version=data['version'], files=len(paths), archive=zipname, bytes=zipfile_path.stat().st_size)))
    return data


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    package(a.root, a.out)
