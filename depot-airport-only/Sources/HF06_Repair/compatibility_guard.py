"""Read-only KIAH/AEP preflight. Python standard library only.
Usage: python compatibility_guard.py --package PATH --xplane PATH
A changed AEP installation or exclusion footprint requires a fresh overlay audit.
Do not regenerate the baseline merely to make this check pass.
"""
import argparse,hashlib,json,pathlib,struct,sys

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atoms(raw,start=0,end=None):
    end=len(raw) if end is None else end
    while start<end:
        size=struct.unpack_from('<I',raw,start+4)[0]
        assert size>=8 and start+size<=end
        yield raw[start:start+4],raw[start+8:start+size]
        start+=size
    assert start==end
def properties(path):
    raw=path.read_bytes()
    assert raw[:8]==b'XPLNEDSF' and hashlib.md5(raw[:-16]).digest()==raw[-16:]
    head=next(p for k,p in atoms(raw,12,len(raw)-16) if k==b'DAEH')
    props=next(p for k,p in atoms(head) if k==b'PORP').decode().split('\0')[:-1]
    assert len(props)%2==0
    return list(zip(props[::2],props[1::2]))
def exclusions(path):return [(k,v) for k,v in properties(path) if k.startswith('sim/exclude_')]
def exclusion_digest(rows):return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
def valid_exclusion(value):
    bbox,sep,ring=value.partition(';');w,s,e,n=map(float,bbox.split('/'))
    assert w<e and s<n
    if sep:
        pts=[tuple(map(float,p.split('/'))) for p in ring.split(',')]
        assert len(pts)>=3 and all(len(p)==2 for p in pts)
        assert all(w-1e-9<=x<=e+1e-9 and s-1e-9<=y<=n+1e-9 for x,y in pts)
        # Local origin avoids cancellation in geographic coordinates.
        p=[(x-w,y-s) for x,y in pts]
        assert sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))>0
    return bool(sep)
def audit(package,xplane,baseline):
    errors=[];counts={}
    for rel,expected in baseline['exclusions'].items():
        try:
            rows=exclusions(package/rel)
            counts[rel]=dict(total=len(rows),polygon=sum(valid_exclusion(v) for k,v in rows))
            if exclusion_digest(rows)!=expected:errors.append('Exclusion coverage changed: '+rel+'; re-audit lower overlays before release.')
        except Exception as exc:errors.append('Invalid DSF exclusions: '+rel+' '+str(exc))
    for name,expected in baseline['aep_files'].items():
        root=xplane/'Custom Scenery'/name
        ignored={'plugins/AEP-Live/AEP-Live Log.txt'} if name=='AEP' else set()
        expected={k:v for k,v in expected.items() if k not in ignored}
        actual={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in ignored}
        changed=sorted(k for k in set(expected)|set(actual) if expected.get(k)!=actual.get(k))
        if changed:errors.append(f'{name}: {len(changed)} added, removed or changed files; re-audit before testing a new refinement. First files: '+', '.join(changed[:6]))
    ini=xplane/'Custom Scenery/scenery_packs.ini'
    rows=[l.strip() for l in ini.read_text(encoding='utf-8-sig').splitlines() if l.startswith('SCENERY_PACK ')]
    matches=[i for i,l in enumerate(rows) if '/KIAH_2026-10-24_Review_R03/' in l.replace('\\','/')]
    if len(matches)!=1:errors.append('Expected exactly one enabled installed KIAH add-on.')
    elif any(i<matches[0] for i,l in enumerate(rows) if l.rstrip('/').endswith(('/AEP','/AEP Overlays'))):errors.append('AEP must remain below the installed KIAH package.')
    return dict(passed=not errors,errors=errors,exclusions=counts,ignored_runtime_log='AEP/plugins/AEP-Live/AEP-Live Log.txt',scope='Exclusion syntax and baseline coverage, AEP asset/configuration changes, installed scenery priority. A changed terminal footprint needs a fresh spatial overlay audit even if this check passes.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=pathlib.Path,required=True);p.add_argument('--xplane',type=pathlib.Path,required=True)
    args=p.parse_args();baseline=json.loads(pathlib.Path(__file__).with_name('AEP_Compatibility_Baseline.json').read_text())
    report=audit(args.package,args.xplane,baseline);print(json.dumps(report,indent=2));sys.exit(0 if report['passed'] else 1)
