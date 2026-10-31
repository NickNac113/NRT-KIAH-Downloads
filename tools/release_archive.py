"""Keep GitHub release versions immutable; use the workflow's short-lived GH_TOKEN."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import tempfile


def run(*args, **kw):
    return subprocess.run(['gh', *args], check=True, **kw)


def archive(site, publish=False):
    site = Path(site).resolve()
    manifest = json.loads((site / 'downloads/release-manifest.json').read_text())
    repo = os.environ.get('GITHUB_REPOSITORY', 'NickNac113/NRT-KIAH-Downloads')
    if repo != 'NickNac113/NRT-KIAH-Downloads':
        raise ValueError('Unexpected release repository')
    tag = 'v' + manifest['version']
    existing = subprocess.run(['gh', 'api', f'repos/{repo}/releases/tags/{tag}'], capture_output=True, text=True)
    if existing.returncode == 0:
        with tempfile.TemporaryDirectory() as tmp:
            run('release', 'download', tag, '--repo', repo, '--pattern', 'release-manifest.json', '--dir', tmp)
            old = json.loads((Path(tmp) / 'release-manifest.json').read_text())
            if old != manifest:
                raise ValueError('This version already has different files. Increment release.json version.')
        print(tag + ' already archived; payload unchanged.')
        return
    if 'HTTP 404' not in existing.stderr:
        raise RuntimeError('Cannot check release archive: ' + existing.stderr)
    if not publish:
        print(tag + ' is new and may be published.')
        return
    files = [str(p) for p in sorted((site / 'downloads').iterdir()) if p.is_file()]
    flags = ['--prerelease'] if manifest.get('prerelease', True) else []
    run('release', 'create', tag, *files, '--repo', repo, '--target', os.environ['GITHUB_SHA'], '--title', f'NRT KIAH {manifest["version"]} ({manifest.get("source_revision", "member release")})', '--notes-file', str(site / 'release-notes.md'), *flags)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--site', type=Path, required=True)
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--check', action='store_true')
    choice.add_argument('--publish', action='store_true')
    a = p.parse_args()
    archive(a.site, a.publish)
