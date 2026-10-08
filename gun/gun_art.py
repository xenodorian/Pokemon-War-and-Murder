"""Art for the shot-to-Hell/Heaven feature: Heaven (cloud picture -> tiles + map), Arceus and Giratina overworld sprites.
Everything is deterministic so the build is reproducible."""
import sys,os,colorsys
import numpy as np
from PIL import Image
from scipy.cluster.vq import kmeans2
W='/home/claude/work/gun/'
BW,BH=16,28                      # Heaven size in 16x16 blocks (picture 384x672 = 4:7)
PX=2                             # chunky pixel size of the pixel-art look
NPAL=13                          # BG palette slots 0..12

def _q15(px,seed):
    """15 colour palette for an array of RGB pixels (n,3): k-means in RGB, deterministic"""
    px=px.astype(float)
    if len(np.unique(px,axis=0))<=15:
        u=np.unique(px,axis=0); return np.vstack([u,np.tile(u[-1],(15-len(u),1))])
    np.random.seed(seed)
    c,_=kmeans2(px,15,minit='++',seed=seed,iter=12)
    c=np.where(np.isnan(c),0,c)
    return c
def _nearest(px,pal):
    d=((px[:,None,:].astype(float)-pal[None,:,:])**2).sum(2); return d.argmin(1)

def heaven_pixels():
    """the cloud picture reduced to 'PX x PX' chunky pixels (RGB array BH*16 x BW*16)"""
    im=Image.open(W+'src23.png').convert('RGB')
    small=im.resize((BW*16//PX,BH*16//PX),Image.BOX)
    return np.array(small.resize((BW*16,BH*16),Image.NEAREST))

def convert_heaven(maxtiles=1000):
    """returns dict(pal=[13 x 16 RGB], tiles=[(palslot, bytes32)], grid=[BH*2*? ...] ) with a tile map per 8x8 cell.
    Tile choices are (index into tiles, hflip, vflip) per 8x8 cell, palette slot is stored with the tile."""
    img=heaven_pixels(); H,Wd=img.shape[:2]; tw,th=Wd//8,H//8
    cells=[img[ty*8:ty*8+8,tx*8:tx*8+8].reshape(64,3) for ty in range(th) for tx in range(tw)]
    feat=np.array([np.concatenate([c.mean(0),c.std(0)]) for c in cells])
    cen,lab=kmeans2(feat,NPAL,minit='++',seed=3,iter=25)
    # palettes
    pals=[]
    for k in range(NPAL):
        mem=[cells[i] for i in range(len(cells)) if lab[i]==k]
        px=np.vstack(mem) if mem else np.zeros((1,3))
        pals.append(_q15(px,k+7))
    tile_idx=[];recon=[]
    for i,c in enumerate(cells):
        k=lab[i]; ix=_nearest(c,pals[k]); tile_idx.append((k,ix))
    return img,cells,lab,pals,tile_idx,(tw,th)

def build_heaven():
    img,cells,lab,pals,tile_idx,(tw,th)=convert_heaven()
    # dedupe with flips
    def flips(ix):
        a=ix.reshape(8,8)
        return [(a,0,0),(a[:,::-1],1,0),(a[::-1,:],0,1),(a[::-1,::-1],1,1)]
    uniq={};tiles=[];cellref=[]
    for i,(k,ix) in enumerate(tile_idx):
        found=None
        for a,hf,vf in flips(ix):
            key=(k,a.tobytes())
            if key in uniq: found=(uniq[key],hf,vf); break
        if not found:
            key=(k,ix.reshape(8,8).tobytes()); uniq[key]=len(tiles); tiles.append((k,ix.reshape(8,8).copy())); found=(uniq[key],0,0)
        cellref.append(found)
    return dict(img=img,pals=pals,tiles=tiles,cellref=cellref,tw=tw,th=th,lab=lab)

def reduce_tiles(h,limit):
    """merge the closest tiles (same palette slot) until at most `limit` remain; returns a new h"""
    tiles=h['tiles']; n=len(tiles)
    if n<=limit: return h
    # k-means per palette slot, proportional quota, on the RGB reconstruction
    pals=h['pals']; groups={}
    for i,(k,a) in enumerate(tiles): groups.setdefault(k,[]).append(i)
    remap={}; newtiles=[]
    total=sum(len(v) for v in groups.values()); budget=limit
    for k,ids in sorted(groups.items()):
        q=max(1,int(round(len(ids)*limit/total)))
        q=min(q,len(ids))
        if len(ids)<=q:
            for i in ids: remap[i]=len(newtiles); newtiles.append(tiles[i])
            continue
        vec=np.array([pals[k][tiles[i][1].reshape(-1)].reshape(-1) for i in ids],float)
        cen,lb=kmeans2(vec,q,minit='++',seed=11,iter=15)
        for c in range(q):
            mem=[ids[j] for j in range(len(ids)) if lb[j]==c]
            if not mem: continue
            m=vec[[j for j in range(len(ids)) if lb[j]==c]].mean(0).reshape(64,3)
            ix=_nearest(m,pals[k]).reshape(8,8)
            for i in mem: remap[i]=len(newtiles)
            newtiles.append((k,ix))
    h2=dict(h); h2['tiles']=newtiles
    h2['cellref']=[(remap[t],hf,vf) for t,hf,vf in h['cellref']]
    return h2

def render_heaven(h):
    th,tw=h['th'],h['tw']; out=np.zeros((th*8,tw*8,3),np.uint8)
    for i,(t,hf,vf) in enumerate(h['cellref']):
        k,ix=h['tiles'][t]; a=ix
        if hf: a=a[:,::-1]
        if vf: a=a[::-1,:]
        ty,tx=divmod(i,tw); out[ty*8:ty*8+8,tx*8:tx*8+8]=h['pals'][k][a].astype(np.uint8)
    return out

def walk_mask(img):
    """per 16x16 block: True where the picture shows cloud (walkable), False for sky and sun"""
    m=np.zeros((BH,BW),bool)
    for by in range(BH):
        for bx in range(BW):
            blk=img[by*16:by*16+16,bx*16:bx*16+16].reshape(-1,3)/255.0
            hs=[colorsys.rgb_to_hsv(*p) for p in blk[::7]]
            v=np.mean([x[2] for x in hs]); s=np.mean([x[1] for x in hs])
            r,g,b=blk.mean(0)
            warm=r>b+0.05
            m[by,bx]=(v>0.64 and s<0.46) or (warm and v>0.62 and s<0.62 and by>=3)
    return m

# ---------------------------------------------------------------- sprites
def sprite64(src,box=64):
    """fit an 80x80 RGBA sprite into a box x box canvas (transparent background, bottom centred), quantised to 15 colours"""
    im=Image.open(src).convert('RGBA'); bb=im.getbbox(); im=im.crop(bb)
    s=min((box-2)/im.size[0],(box-2)/im.size[1]); nw,nh=max(1,round(im.size[0]*s)),max(1,round(im.size[1]*s))
    im=im.resize((nw,nh),Image.LANCZOS)
    out=Image.new('RGBA',(box,box),(0,0,0,0)); out.paste(im,((box-nw)//2,box-nh-1),im)
    a=np.array(out); alpha=a[:,:,3]>=140
    px=a[:,:,:3][alpha]
    pal=_q15(px,5); idx=np.zeros((box,box),int)
    ys,xs=np.nonzero(alpha); ix=_nearest(a[ys,xs,:3],pal); idx[ys,xs]=ix+1
    return idx,[tuple(int(round(v)) for v in c) for c in pal]

if __name__=='__main__':
    h=build_heaven(); print('unique tiles',len(h['tiles']))
    h2=reduce_tiles(h,int(sys.argv[1]) if len(sys.argv)>1 else 1000); print('after',len(h2['tiles']))
    Image.fromarray(render_heaven(h2)).resize((BW*32,BH*32),Image.NEAREST).save(W+'heaven_tiles.png')
    m=walk_mask(h['img']); img=h['img'].copy()
    ov=img.astype(float)
    for by in range(BH):
        for bx in range(BW):
            if m[by,bx]: ov[by*16:by*16+16,bx*16:bx*16+16]=ov[by*16:by*16+16,bx*16:bx*16+16]*0.6+np.array([0,255,0])*0.4
    Image.fromarray(ov.astype(np.uint8)).resize((BW*32,BH*32),Image.NEAREST).save(W+'heaven_mask.png')
