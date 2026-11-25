import numpy as np, math, sys
from PIL import Image
from scipy import ndimage
src=Image.open('matt_parts.png').convert('RGBA'); lab=np.load('lab.npy')
def piece(k):
    sl=ndimage.find_objects((lab==k).astype(int))[0]
    a=np.asarray(src).copy(); m=ndimage.binary_erosion(lab==k,iterations=1)
    a[...,3]=np.where(m,255,0)
    a[...,3]=(ndimage.gaussian_filter(a[...,3].astype(float),0.8)).astype(np.uint8)
    return Image.fromarray(a).crop((sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)), (sl[1].start,sl[0].start)
torso,to=piece(1); head,ho=piece(8); upper,uo=piece(3); fore,fo=piece(5)
def endpoints(k):
    ys,xs=np.nonzero(lab==k); pts=np.stack([xs,ys],1).astype(float)
    c=pts.mean(0); u,s,vt=np.linalg.svd(pts-c,full_matrices=False); d=vt[0]
    t=(pts-c)@d; a=c+d*np.percentile(t,4); b=c+d*np.percentile(t,96)
    return (a,b) if a[1]<b[1] else (b,a)   # top end first
ua,ub=endpoints(3); fa,fb=endpoints(5)
def paste_rot(canvas,img,origin,pivot_src,pivot_dst,angle):
    # rotate img about pivot (in source-sheet coords) by angle deg (ccw), place pivot at pivot_dst
    px,py=pivot_src[0]-origin[0],pivot_src[1]-origin[1]
    pad=max(img.size)*2; big=Image.new('RGBA',(pad*2,pad*2)); big.paste(img,(int(pad-px),int(pad-py)))
    r=big.rotate(angle,resample=Image.BICUBIC,center=(pad,pad))
    canvas.alpha_composite(r,(int(pivot_dst[0]-pad),int(pivot_dst[1]-pad)))
def base_angle(a,b):  # angle needed to make a->b point straight down
    v=b-a; return -math.degrees(math.atan2(v[0],v[1]))
ub_ang=base_angle(ua,ub); fb_ang=base_angle(fa,fb)
shoulder=np.array([815.,240.]); W,H=700,1300
frames=[]
for i in range(24):
    t=i/24*2*math.pi
    sw=28*math.sin(t); el=-(18+14*math.sin(t+0.6))   # shoulder swing, elbow bend
    c=Image.new('RGBA',(W,H),(128,128,128,255)); off=np.array([-560.,40.])
    sh=shoulder+off
    ang_u=-ub_ang+sw
    L=np.linalg.norm(ub-ua); r=math.radians(ang_u)
    elbow=sh+np.array([math.sin(r)*L, math.cos(r)*L])
    # back arm hidden behind torso in side view; front arm drawn over torso
    paste_rot(c,torso,to,np.array(to,float),np.array(to,float)+off,0)
    paste_rot(c,head,ho,np.array([ho[0]+200,ho[1]+330.]),np.array([ho[0]+200+560-560+ (815-ho[0]-200)+0,0])*0+np.array([sh[0]-30,sh[1]-150]),0)
    paste_rot(c,fore,fo,fa,elbow,-fb_ang+sw+el)
    paste_rot(c,upper,uo,ua,sh,ang_u)
    frames.append(c.convert('RGB').resize((W//2,H//2)))
frames[0].save('arm_test.gif',save_all=True,append_images=frames[1:],duration=60,loop=0)
frames[0].save('arm_frame0.png'); frames[6].save('arm_frame6.png'); frames[18].save('arm_frame18.png')
s=Image.new('RGB',(W//2*3,H//2)); [s.paste(f,(j*W//2,0)) for j,f in enumerate([frames[0],frames[6],frames[18]])]; s.save('arm_strip.png')
print('ok', ua,ub,fa,fb)
