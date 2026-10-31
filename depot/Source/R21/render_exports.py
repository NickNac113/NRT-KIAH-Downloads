"""Offline textured views of exported OBJ meshes. Native shaders are not simulated."""
from pathlib import Path
import ast,json,math,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];CAMPUS=ROOT.parents[1];PACK=ROOT/'package/KIAH_NRT_R21_Jet_Center_R17';OUT=ROOT/'output'
tree=ast.parse((ROOT.parent/'KIAH_R17_Native_Surface_R13/source/obj_reader.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'OBJ_reader','exec'))
B=json.loads((PACK/'Build_Evidence.json').read_text());scene=[];cache={}
keep={'mh2_accordion_hangar','mx_stepped_hangar','fbo','fbo_ground_tower','fixed_8','fixed_9A','fixed_9B'}
for placement in B['placements']+B['new_placements']:
    name=Path(placement['resource']).stem
    if name not in keep and not name.startswith('r21_'):continue
    if name=='r21_stand_ids':continue
    p=PACK/placement['resource'];vals={r:1 for r in ['nrt/kiah/r10/mx/outer_open','nrt/kiah/r10/mx/middle_open','nrt/kiah/r10/mx/tail_open','nrt/kiah/r10/mh2/accordion_open','nrt/kiah/r21/private_hangar/doors_open']}
    tris,uvs,tex=readobj(p,placement['origin'],vals=vals,full=True)
    cache.setdefault(tex,np.asarray(Image.open(tex).convert('RGBA')))
    scene.extend((t,uv,tex,None) for t,uv in zip(tris,uvs))
concept=json.loads((CAMPUS/'feasibility/KIAH_R21_Jet_Center_Concept_R01/output/scene.json').read_text())
# Context planes and tree/vehicles are illustrative; all buildings above are reopened exports.
for m in concept['meshes']:
    v=np.array(m['v']);mn=v.min(0);mx=v.max(0)
    ground=mx[2]<=.14
    landscape=mn[0]>2704 and mx[0]<2717 and mn[1]>306 and mx[1]<319 and mx[2]>.3 and m['c'][1]>m['c'][0]*1.3
    vehicle=mn[0]>2707 and mx[0]<2754 and mn[1]>322 and mx[1]<330 and mn[2]>=.4 and mx[2]<=2
    if ground or landscape or vehicle or m['group']=='aircraft:BBJ2 / 737-800':
        for j in range(1,len(v)-1):scene.append((v[[0,j,j+1]],None,None,m['c']))
def render(filename,title,eye,target,span):
    width,height=1600,960;eye=np.array(eye,float);target=np.array(target,float);fw=target-eye;fw/=np.linalg.norm(fw);rt=np.cross(fw,[0,0,1]);rt/=np.linalg.norm(rt);up=np.cross(rt,fw);scale=width/span
    pixels=np.full((height,width,3),[221,229,227],np.uint8);depth=np.full((height,width),np.inf)
    for v,uv,tx,col in scene:
        pos=v-target;pt=np.column_stack([pos@rt*scale+width/2,-pos@up*scale+height*.54]);zs=(v-eye)@fw
        if pt[:,0].max()<0 or pt[:,0].min()>width or pt[:,1].max()<0 or pt[:,1].min()>height:continue
        x0=max(0,int(np.floor(pt[:,0].min())));x1=min(width-1,int(np.ceil(pt[:,0].max())));y0=max(0,int(np.floor(pt[:,1].min())));y1=min(height-1,int(np.ceil(pt[:,1].max())))
        den=(pt[1,1]-pt[2,1])*(pt[0,0]-pt[2,0])+(pt[2,0]-pt[1,0])*(pt[0,1]-pt[2,1])
        if abs(den)<1e-9:continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        a=((pt[1,1]-pt[2,1])*(xx-pt[2,0])+(pt[2,0]-pt[1,0])*(yy-pt[2,1]))/den;b=((pt[2,1]-pt[0,1])*(xx-pt[2,0])+(pt[0,0]-pt[2,0])*(yy-pt[2,1]))/den;c=1-a-b;zz=a*zs[0]+b*zs[1]+c*zs[2]
        old=depth[y0:y1+1,x0:x1+1];mask=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(zz<old)
        if not mask.any():continue
        normal=np.cross(v[1]-v[0],v[2]-v[0]);normal/=max(np.linalg.norm(normal),1e-9);shade=.67+.33*abs(np.dot(normal,[.35,-.45,.82]))
        if tx:
            tex=cache[tx];h,w=tex.shape[:2];u=a*uv[0,0]+b*uv[1,0]+c*uv[2,0];vv=a*uv[0,1]+b*uv[1,1]+c*uv[2,1]
            colors=tex[np.clip(((1-vv)*h).astype(int),0,h-1),np.clip((u*w).astype(int),0,w-1)];mask&=colors[:,:,3]>128;rgb=np.clip(colors[:,:,:3]*shade,0,255).astype(np.uint8)
            pixels[y0:y1+1,x0:x1+1][mask]=rgb[mask]
        else:pixels[y0:y1+1,x0:x1+1][mask]=[int(x*shade*255) for x in col]
        old[mask]=zz[mask]
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im);d.rectangle([0,0,width,95],fill='#f1f4ed');d.rectangle([0,height-60,width,height],fill='#f1f4ed')
    d.text((35,20),title,font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',32),fill='#163943')
    d.text((35,62),'Reopened X-Plane OBJ exports • Offline material preview',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',20),fill='#587078')
    d.text((35,height-43),'Ground, vegetation and aircraft are reference context. X-Plane lighting and weather still need an in-sim check.',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19),fill='#163943')
    im.save(OUT/filename)
render('Arrival_Export.png','NRT Jet Center | Arrivals from the car park',[2788,238,54],[2710,322,4],99)
render('Canopy_Export.png','NRT Jet Center | Covered private-jet arrival',[2525,240,40],[2654,326,7],137)
render('Hangar_Export.png','NRT Jet Center | Private hangar, doors open',[2665,274,66],[2470,365,8],205)
print(json.dumps(dict(triangles=len(scene),renders=3,source='reopened exported OBJ8 meshes',runtime=False)))
