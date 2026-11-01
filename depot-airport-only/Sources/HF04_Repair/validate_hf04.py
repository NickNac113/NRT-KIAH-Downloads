from common import *
import collections
apt=parse_apt(STAGE/'Earth nav data/apt.dat')
checks=[]
def check(name,ok,detail=None):
    checks.append(dict(check=name,passed=bool(ok),detail=detail))
    if not ok:print('FAIL',name,detail)
mask,patch,changed=pickle.loads((ROOT/'work/repair-geometry.pkl').read_bytes())
runtime=[p for p in SOURCE.rglob('*') if p.is_file() and p.suffix.lower() in ('.dsf','.obj','.png','.dds','.pol','.lin','.fac')]
check('All DSFs, models, textures and library resources are byte-identical to HF03',all(sha(p)==sha(STAGE/p.relative_to(SOURCE)) for p in runtime),len(runtime))
stable_codes=sorted(set(a['code'] for a in oldapt)-{110,120})
check('All other airport records are byte-identical, including taxi/service routes, starts, jetways and flows',
      [a['lines'] for a in oldapt if a['code'] in stable_codes]==[a['lines'] for a in apt if a['code'] in stable_codes],
      {str(c):sum(a['code']==c for a in apt) for c in (100,1201,1202,1206,1300,1400,1401,1500)})
def protected(a):return a['code']==120 and a['lines'][0].startswith(('120 Stand ','120 GSE equipment bay ','120 R03 aircraft circulation '))
check('Every authored stand, equipment bay and R03 aircraft circulation marking is unchanged',
      [a['lines'] for a in oldapt if protected(a)]==[a['lines'] for a in apt if protected(a)])
def geomrows(a):
    return [a['lines'][0]]+[' '.join(s[:5] if s[0] in ('112','114','116') else s[:3]) for s in [l.split() for l in a['lines'][1:]]]
original=[a for a in oldapt if a['code']==110]
preserved=[a for a in apt if a['code']==110 and 'HF04' not in a['lines'][0]]
check('Every original pavement node, Bezier curve and surface definition is unchanged',
      [geomrows(a) for a in original]==[geomrows(a) for a in preserved])
patches=[a for a in apt if a['code']==110 and 'HF04' in a['lines'][0]]
decoded=unary_union([smooth_pavement(a) for a in patches])
check('Written replacement pavement is valid and confined to the reported legacy asphalt area',
      bool(patches) and all(smooth_pavement(a).is_valid for a in patches) and decoded.symmetric_difference(patch).area<3,
      dict(pieces=len(patches),area_sqm=decoded.area,quantization_difference_sqm=decoded.symmetric_difference(patch).area))
check('Replacement concrete is ordered before inherited pavement',
      next(a for a in apt if a['code']==110)['lines'][0].endswith('HF04 B North obsolete island asphalt replacement'))
before_asphalt=unary_union([g for i,s,g in visible_surfaces(oldapt) if s==1 or 20<=s<40])
after_asphalt=unary_union([g for i,s,g in visible_surfaces(apt) if s==1 or 20<=s<40])
remaining=after_asphalt.intersection(mask.buffer(-.002)).area
check('Obsolete asphalt island surfaces no longer show through inside the cleanup area',remaining<.1,remaining)
outside=before_asphalt.symmetric_difference(after_asphalt).difference(mask.buffer(.002)).area
check('Visible asphalt outside the local cleanup area is unchanged',outside<.1,outside)
def old_style_paths(items):
    result={}
    for a in items:
        if a['code'] not in (110,120) or protected(a):continue
        for g,s in sampled_apt_segments(a):
            for style in s:result.setdefault(style,[]).append(g)
    return {s:unary_union(gs) for s,gs in result.items()}
before_paths=old_style_paths(oldapt);after_paths=old_style_paths(apt)
inside={s:g.intersection(mask.buffer(-.003)).length for s,g in after_paths.items()}
check('No inherited edge paint or blue edge-light paths remain inside the cleanup area',sum(inside.values())<.01,inside)
outside_diffs={}
for s,g in before_paths.items():
    a=after_paths.get(s,LineString());region=mask.buffer(.005)
    outside_diffs[s]=g.difference(region).difference(a.buffer(.004)).length+a.difference(region).difference(g.buffer(.004)).length
check('Paint and light paths outside the cleanup area remain within 4 mm of HF03',sum(outside_diffs.values())<.01,outside_diffs)
check('Installed HF03 package is untouched',json.loads((ROOT/'live_before.json').read_text())=={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()})
check('Scenery order is untouched',sha(LIVE.parent/'scenery_packs.ini')==(ROOT/'ini_before.sha256').read_text())
report=dict(revision='KIAH R03 HF04',scope='Offline local pavement and edge-detail checks; simulator acceptance pending',passed=sum(x['passed'] for x in checks),total=len(checks),checks=checks)
(ROOT/'HF04_Validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert report['passed']==report['total']
