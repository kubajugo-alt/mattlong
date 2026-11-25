import sys
from PIL import Image
import os
S=os.environ.get('WORK', '.')
out=sys.argv[1]; ks=[3,5,7,10]
H=640; pairs=[]
for k in ks:
    t=Image.open(f'{S}/reference/muybridge-plate1/f{k}.png').convert('RGB'); t=t.crop((0,20,t.width,t.height-60)); t=t.resize((int(t.width*H/t.height),H))
    m=Image.open(f'{S}/shots/cmp_m{k}.png').convert('RGB'); w,h=m.size; m=m.crop((int(w*0.22),int(h*0.06),int(w*0.78),int(h*0.95))); m=m.resize((int(m.width*H/m.height),H))
    pair=Image.new('RGB',(t.width+m.width,H),'white'); pair.paste(t,(0,0)); pair.paste(m,(t.width,0)); pairs.append(pair)
W=sum(p.width for p in pairs)+30; s=Image.new('RGB',(W,H),'white'); x=0
for p in pairs: s.paste(p,(x,0)); x+=p.width+10
s.thumbnail((2600,2600)); s.save(out)
