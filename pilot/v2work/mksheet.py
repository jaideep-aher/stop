import json,sys,os
from PIL import Image,ImageDraw,ImageFont
ids=json.loads(open(sys.argv[1]).read()) if sys.argv[1].endswith('.json') else sys.argv[1].split(',')
pref=sys.argv[2]; CW,CH=int(sys.argv[3]) if len(sys.argv)>3 else 240, int(sys.argv[4]) if len(sys.argv)>4 else 200
cols=int(sys.argv[5]) if len(sys.argv)>5 else 6; rows=int(sys.argv[6]) if len(sys.argv)>6 else 5
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16)
n=cols*rows
for s in range(0,len(ids),n):
    im=Image.new('RGB',(CW*cols,(CH+22)*rows),'white');d=ImageDraw.Draw(im)
    for k,i in enumerate(ids[s:s+n]):
        fn=f'thumbs/{i}.jpg' if os.path.exists(f'thumbs/{i}.jpg') else i
        try: t=Image.open(fn).convert('RGB')
        except Exception: continue
        t.thumbnail((CW-4,CH));x=(k%cols)*CW;y=(k//cols)*(CH+22)
        im.paste(t,(x,y+20));d.text((x+2,y),os.path.basename(str(i)),fill='red',font=f)
    im.save(f'sheets/{pref}_{s//n:02d}.jpg',quality=85)
