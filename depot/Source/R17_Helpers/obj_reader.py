from probe import *
from PIL import Image
def rotation(axis,ang):
    x,y,z=np.array(axis)/np.linalg.norm(axis);c=math.cos(math.radians(ang));s=math.sin(math.radians(ang));C=1-c
    q=np.eye(4);q[:3,:3]=[[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]];return q
def translate(v):q=np.eye(4);q[:3,3]=v;return q
def readobj(path,origin,heading=0,vals=None,full=False):
    rows=[r.split() for r in path.read_text().splitlines()];verts=np.array([list(map(float,r[1:])) for r in rows if r and r[0]=='VT']);idx=[int(v) for r in rows if r and r[0] in ['IDX','IDX10'] for v in r[1:]]
    counts=next(r for r in rows if r and r[0]=='POINT_COUNTS');assert int(counts[1])==len(verts) and int(counts[4])==len(idx)
    tex=next(r[1] for r in rows if r and r[0] in ['TEXTURE','TEXTURE_DRAPED']);tx=(path.parent/tex).resolve()
    if not tx.exists():tx=tx.with_suffix('.dds')
    assert tx.exists(),tx
    im=Image.open(tx).convert('RGB');w,h=im.size
    mat=rotation([0,1,0],-heading);stack=[];active=True;i=0;tri=[];colors=[];uvs=[];vals=vals or {}
    while i<len(rows):
        r=rows[i];i+=1
        if not r:continue
        k=r[0]
        if k=='ATTR_LOD':active=float(r[1])<=0<float(r[2])
        elif k=='ANIM_begin':stack.append(mat.copy())
        elif k=='ANIM_end':mat=stack.pop()
        elif k=='ANIM_trans':mat=mat@translate(list(map(float,r[1:4])))
        elif k in ['ANIM_trans_begin','ANIM_rotate_begin']:
            keys=[];end='ANIM_trans_end' if k=='ANIM_trans_begin' else 'ANIM_rotate_end'
            while i<len(rows) and rows[i][0]!=end:
                if rows[i][0].endswith('_key'):keys.append(list(map(float,rows[i][1:])))
                i+=1
            i+=1;keys.sort();value=vals.get(r[-1],vals.get(r[-1].rsplit('/',1)[-1],0))
            v=[float(np.interp(value,[a[0] for a in keys],[a[j] for a in keys])) for j in range(1,len(keys[0]))]
            mat=mat@(translate(v) if k=='ANIM_trans_begin' else rotation(list(map(float,r[1:4])),v[0]))
        elif k=='TRIS' and active:
            start,count=map(int,r[1:3]);assert start+count<=len(idx)
            for j in range(start,start+count,3):
                vv=verts[idx[j:j+3]];p=(mat@np.column_stack([vv[:,:3],np.ones(3)]).T).T
                p=np.array([[v[0]+origin[0],origin[1]-v[2],v[1]] for v in p]);tri.append(p)
                uv=vv[:,6:8].mean(axis=0);pixel=im.getpixel((max(0,min(w-1,int(uv[0]*w))),max(0,min(h-1,int((1-uv[1])*h)))))
                colors.append(np.array(pixel)/255)
                uvs.append(vv[:,6:8])
    assert not stack
    if full:return np.array(tri),np.array(uvs),str(tx)
    return np.array(tri),np.array(colors)
