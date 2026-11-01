from hf05_common import *
for row in (SOURCE/'SHA256SUMS.txt').read_text().splitlines():
    h,p=row.split('  ',1);assert sha(SOURCE/p)==h,p
assert snapshot_tree(LIVE)==snapshot_tree(SOURCE),'Installed HF04 differs from sealed source'
assert not STAGE.exists(),'Use a new successor instead of overwriting a stage'
(ROOT/'live_before.json').write_text(json.dumps(snapshot_tree(LIVE),indent=2))
(ROOT/'ini_before.sha256').write_text(sha(LIVE.parent/'scenery_packs.ini'))
protected=[LIVE.parent/'AEP/Library.txt',LIVE.parent/'AEP Overlays/Earth nav data/+20-100/+29-096.dsf',LIVE.parent/'AEP Overlays/Earth nav data/+30-100/+30-096.dsf']
(ROOT/'aep_before.json').write_text(json.dumps({str(p):sha(p) for p in protected if p.exists()},indent=2))
shutil.copytree(SOURCE,STAGE)

# Remove the source asphalt rather than relying on drawing order of a cover.
edits=[];rows=[];geometries={}
for i,a in enumerate(oldapt):
    if a['code']==110 and (int(a['parts'][1])==1 or 20<=int(a['parts'][1])<40) and smooth_pavement(a).intersection(mask).area>.01:
        assert all(len(l.split())==(5 if l.split()[0] in ('112','114') else 3) for l in a['lines'][1:]),'Do not drop attached edge attributes'
        before=precise_pavement(a);after=polys_only(before.difference(mask))
        assert after.is_valid
        header=a['lines'][0]+' HF05 clipped at rebuilt B North apron'
        replacement=native_area(after,header);rows+=replacement
        edits.append(dict(source_index=i,name=a['lines'][0],removed_sqm=before.intersection(mask).area,pieces=len(polygon_parts(after)),native_vertices=sum(l.startswith(('111 ','113 ')) for l in replacement)))
        geometries[i]=(before,after)
    else:rows+=a['lines']
(STAGE/'Earth nav data/apt.dat').write_text('\n'.join(rows)+'\n')

# Match WED's actual exporter: bbox;lon/lat,lon/lat,... . The documentation
# example differs; previous checks incorrectly accepted comma-only points.
# Reverse CW rings without changing any exclusion footprint.
rewrites=[]
for src in sorted((SOURCE/'Earth nav data').rglob('*.dsf')):
    tile=src.stem;before=ROOT/'work'/f'{tile}-before.txt';after=ROOT/'work'/f'{tile}-hf05.txt'
    dsf_decode(src,before);result=[];counts=collections.Counter()
    for row in before.read_text().splitlines():
        if row.startswith('PROPERTY sim/exclude_') and ';' in row:
            prefix,data=row.rsplit(' ',1);extent,coords=data.split(';')
            kind,g=parse_exclusion(row,strict=False)
            oldpoints=list(zip(*[iter(coords.split(','))]*2)) if '/' not in coords else [p.split('/') for p in coords.split(',')]
            if not g.exterior.is_ccw:oldpoints.reverse()
            replacement=prefix+' '+extent+';'+','.join(x+'/'+y for x,y in oldpoints)
            k,newg=parse_exclusion(replacement)
            assert k==kind and newg.equals(g) and newg.exterior.is_ccw
            assert len(replacement.split(' ',2)[2])<512
            row=replacement;counts[k]+=1
        result.append(row)
    after.write_text('\n'.join(result)+'\n')
    dest=STAGE/src.relative_to(SOURCE)
    if not counts:shutil.copy2(before,ROOT/'work'/f'{tile}-roundtrip.txt')
    rewrites.append(dict(tile=tile,corrected=dict(counts),total=sum(counts.values())))

# Patch only PROP strings in the original binary, preserving all packed
# placement coordinates and commands exactly; refresh the DSF checksum.
subprocess.run([sys.executable,str(ROOT/'work/preserve_dsf_binary.py')],check=True)

(ROOT/'work/repair-geometry.pkl').write_bytes(pickle.dumps(geometries))
report=dict(revision='KIAH R03 HF05',status='STAGED - NOT INSTALLED',
    native_asphalt=edits,exclusion_syntax_repairs=rewrites,
    source='https://github.com/X-Plane/xptools/blob/master/src/WEDImportExport/WED_DSFExport.cpp#L1447-L1480',
    finding='AEP supplies a legacy asphalt overlay over B North and replacement native pavement materials. HF04 still retained the underlying asphalt. Existing polygon exclusions used comma-only coordinates, unlike WED exporter lon/lat pairs; old offline audit accepted this malformed representation.',
    method='Clip the underlying asphalt at the existing HF04 cleanup mask. Rewrite existing polygon exclusion coordinates to WED syntax and CCW orientation, without changing footprints, types or order. Leave AEP installed and enabled.',
    limitations='No simulator reload or acceptance test. Curves of the one clipped native asphalt polygon are adaptively flattened at 0.5 mm geometric tolerance. Surface colour in offline previews is approximate.')
(ROOT/'HF05_Changes.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
