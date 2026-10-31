"""Original, deterministic aviation materials with physical-scale mapping.
No borrowed scenery texture assets. Shared 2K building sheet / 1K pavement.
"""
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

TILES={0:(0,0),1:(1,0),2:(0,1),3:(1,1),8:(0,2),9:(1,2),10:(0,3),11:(1,3)}

def build_textures(pack,atlas):
    out=pack/'textures/nrt_test';rng=np.random.default_rng(10106)
    sheet=Image.new('RGB',(2048,2048));sheet.paste(atlas.convert('RGB'),(0,0))
    normal=Image.new('RGBA',sheet.size,(128,128,255,40))
    lit=Image.new('RGB',sheet.size,(0,0,0))
    yy,xx=np.mgrid[:512,:512]
    for material,(col,row) in TILES.items():
        height=np.zeros((512,512));gloss=np.full((512,512),55.)
        fine=rng.normal(0,.9,(512,512));coarse=np.asarray(Image.fromarray(rng.integers(80,180,(16,16),dtype='uint8')).resize((512,512),Image.Resampling.BICUBIC)).astype(float)/20-6
        if material in [0,8,9]:
            base={0:[200,206,204],8:[148,166,172],9:[48,94,108]}[material]
            ribs=(xx%16<2);height+=ribs*.8
            noise=fine+coarse-ribs*10+(xx%16==2)*6
            if material==8:
                joint=yy%64<2;height-=joint*.8;noise-=joint*21
            # Faint rain streaks and atmospheric dirt, no baked directional light.
            noise-=((np.sin(xx*.155)+1)*1.5)*(yy/512)
            gloss[:]=70 if material==8 else 44
        elif material in [1,10]:
            base=[36,57,64] if material==1 else [184,191,190]
            seam=xx%64<3;height+=seam*1.3
            noise=fine+coarse-seam*13+(xx%64==3)*8
            noise-=(yy%256<2)*6;gloss[:]=65
        elif material==2:
            base=[36,70,86];frames=(xx%128<5)|(yy%128<5)
            height-=frames*.6;noise=fine*.15+(1-yy/512)*14
            noise-=frames*25;gloss[:]=165
        else:
            base=[119,126,125] if material==3 else [139,143,139]
            noise=fine*1.8+coarse*1.5
            height=fine*.03;gloss[:]=22
            noise-=(yy%256<3)*8
        rgb=np.clip(np.asarray(base)[None,None,:]+noise[:,:,None],0,255).astype('uint8')
        tile=Image.fromarray(rgb)
        if material in [0,8,9]:
            d=ImageDraw.Draw(tile)
            for y in [24,256,488]:
                for x in range(8,512,32):d.ellipse((x,y,x+1,y+1),fill=(87,99,103))
        gx=np.gradient(height,axis=1)*.32;gy=np.gradient(height,axis=0)*.32
        ns=np.stack([-gx,gy,np.ones_like(gx)],axis=2);ns/=np.linalg.norm(ns,axis=2)[:,:,None]
        rgba=np.dstack([(ns*.5+.5)*255,gloss]).clip(0,255).astype('uint8')
        pos=(1024+col*512,row*512);sheet.paste(tile,pos);normal.paste(Image.fromarray(rgba),pos)
        if material==2:
            light=np.zeros((512,512,3),dtype='uint8')
            light[:]=[60,63,54];light[frames]=[2,3,4]
            lit.paste(Image.fromarray(light),pos)
    sheet.save(out/'buildings.png');normal.save(out/'buildings_NML.png');lit.save(out/'buildings_LIT.png')
    # 24 m repeat contains sixteen 6 m slabs with restrained variation.
    n=1024;y,x=np.mgrid[:n,:n];noise=rng.normal(0,1.8,(n,n))
    cloud=np.asarray(Image.fromarray(rng.integers(80,180,(32,32),dtype='uint8')).resize((n,n),Image.Resampling.BICUBIC)).astype(float)/35-3.7
    slabs=rng.uniform(-3,3,(4,4))[y//256,x//256]
    joint=((x%256)<2)|((y%256)<2)
    a=np.clip(np.array([155,157,150])[None,None,:]+(noise+cloud+slabs-joint*30)[:,:,None],0,255).astype('uint8')
    pavement=Image.fromarray(a);d=ImageDraw.Draw(pavement)
    # Infrequent fine crack repairs, aligned to slabs rather than random scribbles.
    for pts in [[(256,335),(288,350),(311,369),(334,381)],[(780,768),(792,750),(812,742),(830,722)]]:d.line(pts,fill=(115,119,114),width=1)
    pavement.save(out/'apron.png')
    h=joint.astype(float)*-.25+noise*.004
    dx=np.gradient(h,axis=1);dy=np.gradient(h,axis=0)
    ns=np.stack([-dx,dy,np.ones_like(dx)],axis=2);ns/=np.linalg.norm(ns,axis=2)[:,:,None]
    Image.fromarray(np.dstack([(ns*.5+.5)*255,np.full((n,n),22)]).clip(0,255).astype('uint8')).save(out/'apron_NML.png')
    # Legible rubber with coherent grain. The old maximum was only 47/255 and
    # --fade_mips erased it further as the view pulled back. Preserve alpha mips.
    y,x=np.mgrid[:512,:512];fade=np.sin(np.pi*y/511)**.65
    grain=np.asarray(Image.fromarray(rng.integers(100,255,(64,64),dtype='uint8')).resize((512,512),Image.Resampling.BICUBIC))/255
    track=np.exp(-((x-197)/15)**2)+np.exp(-((x-315)/15)**2)
    shoulder=np.exp(-((x-197)/40)**2)+np.exp(-((x-315)/40)**2)
    grooves=.78+.22*np.sin(x*2.1)**2
    opacity=((track*155+shoulder*24)*fade*(.55+.45*grain)*grooves).clip(0,165)
    Image.fromarray(np.dstack([np.full((512,512,3),35),opacity]).astype('uint8')).save(out/'ramp_wear.png')

def material_uv(material,u,v):
    col,row=TILES[material]
    # Half-texel padding prevents neighbouring tiles leaking through at full res.
    return ((1024+col*512+.5+u*511)/2048,1-(row*512+.5+(1-v)*511)/2048)
