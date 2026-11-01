"""Stage the OBJ8 face/sign repair. Never write to Custom Scenery."""
from pathlib import Path
import hashlib, json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
LIVE=Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF02'
OLDWORK=Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\work')
sys.path.insert(0,str(OLDWORK/'pydeps'))
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_obj(p):
    lines=p.read_text().splitlines();verts=[];indices=[];vlines=[]
    for k,line in enumerate(lines):
        s=line.split()
        if s and s[0]=='VT':verts.append(list(map(float,s[1:])));vlines.append(k)
        elif s and s[0] in ('IDX','IDX10'):indices.extend(map(int,s[1:]))
    return lines,np.array(verts),np.array(indices).reshape(-1,3),vlines

def audit(p):
    lines,v,f,_=read_obj(p)
    cr=np.cross(v[f[:,1],:3]-v[f[:,0],:3],v[f[:,2],:3]-v[f[:,0],:3])
    area=np.linalg.norm(cr,axis=1)
    dot=np.einsum('ij,ij->i',cr,v[f[:,0],3:6])
    return dict(model=p.name,triangles=len(f),clockwise_outward=int(sum(dot < -1e-7)),
                counterclockwise_outward=int(sum(dot > 1e-7)),degenerate=int(sum(area < 1e-7)),
                roof_area_m2=float(sum(area[(v[f[:,0],4]>.99)&(v[f[:,0],1]>3)])/2))

def main():
    assert not STAGE.exists(),'Refuse to replace an existing repair stage'
    live_hashes={p.relative_to(LIVE).as_posix():sha(p) for p in LIVE.rglob('*') if p.is_file()}
    shutil.copytree(LIVE,STAGE)
    (ROOT/'live_before.json').write_text(json.dumps(live_hashes,indent=2))
    scene=json.loads((OLDWORK/'generated/scene.json').read_text())
    jets={j['name']:j for j in scene['jetways']}
    before=[];after=[];signs=[]
    for p in sorted((STAGE/'objects').glob('*.obj')):
        before.append(audit(p))
        lines,v,faces,vlines=read_obj(p)
        native=faces[:,[0,2,1]].copy()
        if p.stem.startswith('bridge_'):
            name=p.stem.removeprefix('bridge_');j=jets[name]
            # The last quad is the identifier panel. Its original normal and
            # horizontal texture axis faced the terminal, not the apron.
            first=len(v)-4
            assert np.all(faces[-2:]>=first)
            assert np.all(faces[:-2]<first)
            v[first:,3:6]*=-1
            v[first:,6]=v[first:,6].min()+v[first:,6].max()-v[first:,6]
            native[-2:]=faces[-2:]
            for i in range(first,len(v)):
                x,y,z,nx,ny,nz,u,t=v[i]
                lines[vlines[i]]=f'VT {x:.4f} {y:.4f} {z:.4f} {nx:.5f} {ny:.5f} {nz:.5f} {u:.7f} {t:.7f}'
            out=np.array(j['base'])-np.array(j['door']);out/=np.linalg.norm(out)
            normal=v[-1,[3,5]]*np.array([1,-1])
            normal_dot=float(np.dot(out,normal))
            # Camera is on the apron looking toward the sign. Its screen-right
            # is (-out_y, out_x); texture U must increase toward screen-right.
            camera_right=np.array([-out[1],out[0]])
            edge=(v[first+1,[0,2]]-v[first,[0,2]])*np.array([1,-1])
            readable=float(np.dot(edge,camera_right)*(v[first+1,6]-v[first,6]))
            assert normal_dot>.999 and readable>0
            signs.append(dict(gate=name,normal_points_to_apron=normal_dot,readable_horizontal_axis=readable))
        flat=native.flatten().tolist();newix=[]
        for i in range(0,len(flat),10):
            a=flat[i:i+10]
            newix.extend(['IDX10 '+' '.join(map(str,a))] if len(a)==10 else ['IDX '+str(n) for n in a])
        begin=next(i for i,l in enumerate(lines) if l.startswith(('IDX ','IDX10 ')))
        end=begin
        while end<len(lines) and lines[end].startswith(('IDX ','IDX10 ')):end+=1
        lines[begin:end]=newix
        p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        after.append(audit(p))
        # All positions, dimensions and texture files remain unchanged.
        _,oldv,_,_=read_obj(LIVE/'objects'/p.name)
        assert np.array_equal(oldv[:,:3],v[:,:3])
    assert len(after)==37 and len(signs)==32
    assert all(a['clockwise_outward']==a['triangles'] and a['degenerate']==0 for a in after)
    source=STAGE/'Sources/Build/native_mesh.py';text=source.read_text()
    old='        for i in range(0,len(self.indices),10):\n            ix=self.indices[i:i+10]'
    new='        # OBJ8 front faces are CLOCKWISE; authoring/Blender faces stay CCW.\n        native_indices=[n for i in range(0,len(self.indices),3) for n in (self.indices[i],self.indices[i+2],self.indices[i+1])]\n        for i in range(0,len(native_indices),10):\n            ix=native_indices[i:i+10]'
    assert text.count(old)==1;text=text.replace(old,new)
    old="m.face([(*(c-right),7.2),(*(c+right),7.2),(*(c+right),9),(*(c-right),9)],j['name'])"
    new="m.face([(*(c+right),7.2),(*(c-right),7.2),(*(c-right),9),(*(c+right),9)],j['name'])"
    assert text.count(old)==1;text=text.replace(old,new)
    source.write_text(text,encoding='utf-8')
    builder=STAGE/'Sources/Build/build_native.py';text=builder.read_text()
    text=text.replace('orient(p,sign=-1).exterior.coords','orient(p,sign=1).exterior.coords')
    text=text.replace('{j["size"]} 0 {j["length"]:.2f}', '{j["size"]} {j["heading"]:.2f} {j["length"]:.2f}')
    builder.write_text(text,encoding='utf-8')
    report=dict(revision='R03 HF02',status='STAGED - NOT INSTALLED',
        rule='OBJ8 uses clockwise front faces viewed from the outside',
        source='https://developer.x-plane.com/article/obj8-file-format-specification/',
        before=before,after=after,signs=signs,
        total_triangles=sum(a['triangles'] for a in after),
        apt_unchanged=sha(STAGE/'Earth nav data/apt.dat')==sha(LIVE/'Earth nav data/apt.dat'),
        dsfs_unchanged=all(sha(p)==sha(LIVE/p.relative_to(STAGE)) for p in (STAGE/'Earth nav data').rglob('*.dsf')),
        textures_unchanged=all(sha(p)==sha(LIVE/p.relative_to(STAGE)) for p in (STAGE/'textures').glob('*')),
        live_unchanged=all(sha(LIVE/p)==h for p,h in live_hashes.items()))
    assert all(report[k] for k in ['apt_unchanged','dsfs_unchanged','textures_unchanged','live_unchanged'])
    (ROOT/'HF02_Validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('before','after','signs')},indent=2))

if __name__=='__main__':main()
