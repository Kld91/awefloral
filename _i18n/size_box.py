# -*- coding: utf-8 -*-
"""Finds where the arrangement sits in each product photo (img/p/<code>-1.webp) and prints SZBOX for index.html: usage python3 _i18n/size_box.py SITE_DIR"""
import numpy as np, sys, json, re
from PIL import Image, ImageFilter, ImageCms
srgb=ImageCms.createProfile('sRGB'); lab=ImageCms.createProfile('LAB')
T=ImageCms.buildTransformFromOpenProfiles(srgb,lab,'RGB','LAB')
def box(path):
    W,H=300,225
    im=Image.open(path).convert('RGB').resize((W,H)).filter(ImageFilter.GaussianBlur(1.5))
    L=np.asarray(ImageCms.applyTransform(im,T)).astype(float)
    edge=np.concatenate([L[:,:10],L[:,-10:]],axis=1); bg=np.median(edge,axis=1)
    D=np.abs(L-bg[:,None,:]); d=0.35*D[:,:,0]+1.6*D[:,:,1]+1.6*D[:,:,2]
    m=d>30
    xs=np.where(m.mean(0)>0.035)[0]; ys=np.where(m.mean(1)>0.035)[0]
    if not len(xs) or not len(ys): return None
    x0,x1,y0,y1=xs[0],xs[-1]+1,ys[0],ys[-1]+1
    # clear glass: vertical edges (horizontal lightness change) under the flowers, in the middle 60% of the box
    gx=np.abs(np.diff(L[:,:,0],axis=1))
    cx0=int(x0+0.2*(x1-x0)); cx1=int(x1-0.2*(x1-x0))
    for y in range(y1,H):
        if (gx[y,cx0:cx1]>6).sum()>=2: y1=y+1
    return [round(float(v),3) for v in (x0/W,y0/H,x1/W,y1/H)]
if __name__=='__main__':
    R=sys.argv[1]
    s=open(R+'/index.html',encoding='utf-8').read()
    sp=json.loads(re.search(r'const SPECS = (\{.*?\});',s).group(1))
    out={}
    for k,v in sp.items():
        if v[0] and v[1]:
            b=box(f'{R}/img/p/{k[1:]}-1.webp')
            if b: out[k]=b
    print(json.dumps(out))
