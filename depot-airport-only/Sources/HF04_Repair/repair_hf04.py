from common import *
import shutil,collections
if STAGE.exists():assert (ROOT/'HF04_Changes.json').is_file(),'Refuse to overwrite an unrelated stage'
for line in (SOURCE/'SHA256SUMS.txt').read_text().splitlines():
    h,p=line.split('  ',1);assert sha(SOURCE/p)==h,p
live_hashes={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()}
assert live_hashes=={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()},'Live package differs from sealed HF03'
(ROOT/'live_before.json').write_text(json.dumps(live_hashes,indent=2))
(ROOT/'ini_before.sha256').write_text(sha(LIVE.parent/'scenery_packs.ini'))
if not STAGE.exists():shutil.copytree(SOURCE,STAGE)

# Preserve all original pavement nodes and curves. Detach only the paint/light
# attributes on intersecting edges, and retain their outside portions as lines.
def indexed_segments(a):
    ring=[]
    for idx,row in enumerate(a['lines'][1:],1):
        s=row.split();code=int(s[0]);p=np.array(xy(float(s[2]),float(s[1])))
        curved=code in (112,114,116);h=np.array(xy(float(s[4]),float(s[3]))) if curved else p
        ring.append((idx,p,h,s[5:] if curved else s[3:]))
        if code in (113,114,115,116):
            closed=code in (113,114)
            for (idx,p,h,style),(_,q,k,_) in zip(ring,ring[1:]+(ring[:1] if closed else [])):
                if not style:continue
                steps=max(1,min(100,math.ceil((np.linalg.norm(h-p)+np.linalg.norm(q-h)+np.linalg.norm(k-q))/2)))
                ps=[(1-t)**3*p+3*(1-t)**2*t*h+3*(1-t)*t*t*(2*q-k)+t**3*q for t in np.linspace(0,1,steps+1)]
                if math.dist(ps[0],ps[-1])>.001:yield idx,LineString(ps),style
            ring=[]

asphalt=unary_union([g for i,s,g in visible_surfaces(oldapt) if s==1 or 20<=s<40])
# A 1 cm overlap on adjoining concrete prevents sub-millimetre quantization
# slivers at the native coordinate precision. The local boundary is unchanged.
patch=polys_only(make_valid(asphalt.intersection(mask).buffer(.01).intersection(mask)))
patch_rows=apt_area(patch,'HF04 B North obsolete island asphalt replacement',50)
changed=[];out=[];extras=[];inserted=False
for i,a in enumerate(oldapt):
    if a['code']==110 and not inserted:out+=patch_rows;inserted=True
    rows=list(a['lines'])
    if a['code'] in (110,120) and not (a['code']==120 and a['lines'][0].startswith(('120 Stand ','120 GSE equipment bay ','120 R03 aircraft circulation '))):
        for idx,g,style in indexed_segments(a):
            inside=g.intersection(mask)
            if inside.length<.001:continue
            # Geometry stays native, including the exact original Bezier nodes.
            s=rows[idx].split();rows[idx]=' '.join(s[:5] if s[0] in ('112','114','116') else s[:3])
            outside=g.difference(mask)
            extras+=emit_apt_line(outside,style,f'HF04 preserved outer edge from {i}:{idx}')
            changed.append(dict(block=i,node=idx,name=a['lines'][0],style=style,removed_m=inside.length,preserved_m=outside.length))
    out+=rows
# The parser preserves file header and footer as ordinary records. Insert the
# detached outside paint before the final 99 marker, never after end-of-file.
end=next((i for i,s in enumerate(out) if s.strip()=='99'),len(out))
out[end:end]=extras
(STAGE/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n',encoding='utf-8')
report=dict(revision='KIAH R03 HF04',status='STAGED - NOT INSTALLED',
    scope='B North legacy islands between the rebuilt pier tips and taxiway NB',
    replacement_surface_sqm=patch.area,cleanup_area_sqm=mask.area,
    edited_edge_attributes=changed,removed_edge_total_m=sum(x['removed_m'] for x in changed),
    unchanged='All pavement geometry, aircraft/service routes, starts, flows, jetways, DSFs, objects and textures; only local surface and edge paint/light treatment changed.',
    outside_edges='Clipped outside portions are retained as sampled 120 line records; original pavement geometry remains byte-equivalent without edge attributes.')
(ROOT/'HF04_Changes.json').write_text(json.dumps(report,indent=2))
(ROOT/'work/repair-geometry.pkl').write_bytes(pickle.dumps((mask,patch,changed)))
print(json.dumps({k:v for k,v in report.items() if k!='edited_edge_attributes'},indent=2))
print('Edges edited:',len(changed),'blocks:',dict(collections.Counter(x['name'] for x in changed)))
