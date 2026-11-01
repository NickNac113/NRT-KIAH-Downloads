"""Stage R28 variants from immutable review inputs. Never alter installed scenery.

Airport Only starts with the public HF06 airport. Only the recorded R28 B changes
are applied. Campus apt.dat edits, exclusions, models and SAM XML never enter it.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess

from build_release import source_paths, reparse

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(folder):
    return {p.relative_to(folder).as_posix(): sha(p) for p in Path(folder).rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


def blocks(text):
    rows = text.splitlines()
    result = []
    for row in rows:
        parts = row.split()
        code = int(parts[0]) if parts and parts[0].isdigit() else -1
        if result and (code in range(111, 117) or code == 1301):
            result[-1].append(row)
        else:
            result.append([row])
    return result


def exact_block(items, header):
    found = [b for b in items if b[0] == header]
    if len(found) != 1:
        raise ValueError('Expected exactly one airport record: ' + header)
    return found[0]


def apt_delta(before, after):
    return Counter(tuple(b) for b in blocks(before)) - Counter(tuple(b) for b in blocks(after))


def prepare(baseline, review, dsftool, out):
    baseline, review, out = map(lambda p: Path(p).resolve(), (baseline, review, out))
    if out.exists() or out.is_relative_to(baseline) or out.is_relative_to(review):
        raise ValueError('Use a new staging directory outside both immutable inputs')
    if any(reparse(p) for p in baseline.rglob('*')):
        raise ValueError('Linked baseline entry')
    seal = json.loads((review / 'qa/Review_Package.json').read_text())
    r28 = review / 'package/KIAH_NRT_R28_Terminal_B_R25'
    r27 = review.parent / 'KIAH_R27_Shelter_Service_R24/package/KIAH_NRT_R27_Shelter_Service_R24'
    if snapshot(r28) != seal['package_hashes']:
        raise ValueError('Sealed R28 package differs')
    evidence = json.loads((review / 'qa/R28_Evidence.json').read_text())
    base_hashes = snapshot(baseline)
    out.mkdir(parents=True)
    main, airport = out / 'main', out / 'airport-only'
    shutil.copytree(ROOT / 'scenery', main)
    shutil.copytree(r28, main, dirs_exist_ok=True)
    # The sealed review carries local-test instructions. Retain the member
    # release's historical documentation and configured distribution record.
    for rel in ['Garage_Replacement_Record.json', *[f'README_R{n}.txt' for n in range(22, 28)]]:
        member = ROOT / 'scenery' / rel
        if member.exists():
            shutil.copyfile(member, main / rel)
    # Retain original editable authoring inputs and license notices; not obsolete hashes.
    shutil.copytree(baseline, airport, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'SHA256SUMS.txt'))
    (airport / 'README_HF06_HISTORICAL.txt').write_bytes((airport / 'README.txt').read_bytes())
    (airport / 'README.txt').write_text('KIAH Airport Only - R28 staging build\nSee INSTALL.txt and VARIANT.txt. Historical HF06 notes describe the predecessor only.\n')
    baseline_apt = (baseline / 'Earth nav data/apt.dat').read_text()
    old_apt = (r27 / 'Earth nav data/apt.dat').read_text()
    new_apt = (r28 / 'Earth nav data/apt.dat').read_text()
    base_blocks, old_blocks, new_blocks = map(blocks, (baseline_apt, old_apt, new_apt))
    changes = next(c for c in evidence['changes'] if c['change'] == 'Taxi guidance consolidation')
    # HF04 edge labels are not unique: match the complete record and its
    # occurrence count, retaining the other geometry with the same label.
    removed = apt_delta(old_apt, new_apt)
    added = apt_delta(new_apt, old_apt)
    allowed_old = set(changes['removed']) | set(changes['replaced'])
    available = Counter(tuple(b) for b in base_blocks)
    for record, count in removed.items():
        if record[0] not in allowed_old or available[record] < count:
            raise ValueError('Public baseline B record drifted: ' + record[0])
    for record in added:
        if not (record[0].startswith('120 R28 B North ') or
                (record[0].startswith('1202 ') and record[0].endswith(' NG'))):
            raise ValueError('Unrecorded B airport change: ' + record[0])
    pending = removed.copy()
    airport_blocks = []
    for block in base_blocks:
        record = tuple(block)
        if pending[record]:
            pending[record] -= 1
        elif block[0] != '99':
            airport_blocks.append(block)
    for block in new_blocks:
        record = tuple(block)
        if added[record]:
            airport_blocks.append(block)
            added[record] -= 1
    airport_apt = '\n'.join(row for block in airport_blocks + [['99']] for row in block) + '\n'
    if apt_delta(baseline_apt, airport_apt) != apt_delta(old_apt, new_apt) or apt_delta(airport_apt, baseline_apt) != apt_delta(new_apt, old_apt):
        raise ValueError('Airport Only must apply exactly the same B airport-record changes')
    (airport / 'Earth nav data/apt.dat').write_text(airport_apt)
    for change in evidence['changes']:
        resource = change.get('resource', '')
        if resource.startswith('objects/bridge_B'):
            if sha(baseline / resource) != sha(r27 / resource):
                raise ValueError('Public baseline B bridge drifted: ' + resource)
            shutil.copyfile(r28 / resource, airport / resource)

    def tool(*args):
        run = subprocess.run([str(dsftool), *map(str, args)], capture_output=True, text=True, check=True)
        return run.stdout + run.stderr

    south = 'Earth nav data/+20-100/+29-096.dsf'
    tool('--dsf2text', baseline / south, out / 'HF06_South.txt')
    raw = (out / 'HF06_South.txt').read_text()
    objects = re.findall(r'^OBJECT_DEF (.+)$', raw, re.M)
    index = objects.index('objects/B_North.obj')
    raw, count = re.subn(r'^OBJECT ' + str(index) + r' .+$', '# R28: native Terminal B facades replace the previous shell', raw, flags=re.M)
    if count != 1:
        raise ValueError('Expected one B shell placement in public baseline')
    definitions = re.findall(r'^POLYGON_DEF (.+)$', raw, re.M)
    added = []
    for f in evidence['facades']:
        if f['resource'] not in definitions:
            definitions.append(f['resource'])
            added.append('POLYGON_DEF ' + f['resource'])
    marker = raw.index('FILTER ')
    raw = raw[:marker] + '\n'.join(added) + '\n' + raw[marker:]
    phi = math.radians(29.984444444)
    sx = 111412.84*math.cos(phi)-93.5*math.cos(3*phi)+.118*math.cos(5*phi)
    sy = 111132.92-559.82*math.cos(2*phi)+1.175*math.cos(4*phi)-.0023*math.cos(6*phi)
    new = ['FILTER 0']
    for f in evidence['facades']:
        new += [f'BEGIN_POLYGON {definitions.index(f["resource"])} {f["height"]} 3', 'BEGIN_WINDING']
        for (x, y), wall in zip(f['points'], f['walls']):
            new.append(f'POLYGON_POINT {x/sx-95.341444444:.9f} {y/sy+29.984444444:.9f} {wall}')
        new += ['END_WINDING', 'END_POLYGON']
    raw += '\n' + '\n'.join(new) + '\n'
    native = airport / 'Source/Native'
    native.mkdir(parents=True)
    (native / '+29-096.txt').write_text(raw)
    tool('--text2dsf', native / '+29-096.txt', airport / south)
    tool('--dsf2text', airport / south, out / 'Airport_Only_Roundtrip.txt')
    north = 'Earth nav data/+30-100/+30-096.dsf'
    tool('--dsf2text', airport / north, native / '+30-096.txt')
    shutil.copyfile(ROOT / 'scenery/Source/rebuild_dsf.py', airport / 'Source/rebuild_dsf.py')
    shutil.copyfile(review / 'qa/R28_Roundtrip.txt', main / 'Source/Native/+29-096.txt')
    for dest in (main, airport):
        (dest / 'Source/R28').mkdir(parents=True)
        for p in (review / 'source').glob('*.py'):
            shutil.copyfile(p, dest / 'Source/R28' / p.name)
        shutil.copyfile(review / 'qa/R28_Evidence.json', dest / 'Source/R28/R28_Evidence.json')
        shutil.copyfile(Path(__file__), dest / 'Source/R28/prepare_r28_channels.py')
        shutil.copyfile(r28 / 'README_R28.txt', dest / 'README_R28_REVIEW_HISTORY.txt')
    runtime_delta = {south, 'Earth nav data/apt.dat'} | {c['resource'] for c in evidence['changes'] if c.get('resource', '').startswith('objects/bridge_B')}
    runtime = {r for r in base_hashes if r.startswith(('Earth nav data/', 'objects/', 'textures/'))}
    unchanged = [r for r in runtime if r not in runtime_delta]
    if not all(sha(airport / r) == base_hashes[r] for r in unchanged):
        raise ValueError('Unrelated public airport runtime asset changed')
    if re.search(r'(?mi)^1300 .*(?:NRT|MH1|MH2|Canopy|Indoor Parking)', airport_apt):
        raise ValueError('Fictional campus start leaked into Airport Only')
    if 'nrt_test' in raw or (airport / 'sam.xml').exists() or (airport / 'opensam.xml').exists():
        raise ValueError('Fictional campus objects or animation XML leaked into Airport Only')
    if snapshot(baseline) != base_hashes or snapshot(r28) != seal['package_hashes']:
        raise ValueError('Protected input changed')
    checks = dict(status='PASS - offline only', version='0.28.0', public_baseline='KIAH public HF06',
                  main_basis='Sealed R28 cumulative review', airport_record_delta_equal=True,
                  changed_airport_runtime_files=sorted(runtime_delta),
                  unchanged_airport_runtime_files=len(unchanged), native_B_facades=len(evidence['facades']),
                  main_native_jetways=sum(r.startswith('1500 ') for r in new_apt.splitlines()),
                  airport_only_native_jetways=sum(r.startswith('1500 ') for r in airport_apt.splitlines()),
                  fictional_starts_in_airport_only=0, public_baseline_preserved=True, sealed_review_preserved=True,
                  airport_only_hashes=snapshot(airport), main_hashes=snapshot(main))
    (out / 'Preparation.json').write_text(json.dumps(checks, indent=2))
    print(json.dumps({k: v for k, v in checks.items() if not k.endswith('_hashes')}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--dsftool', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    prepare(a.baseline, a.review, a.dsftool.resolve(), a.out)
