# 키트 pptx → 미리보기 스프라이트. LibreOffice의 한글·숫자 자동 간격을 끄고 렌더(../tools/uno_pdf.py)
import subprocess,glob,os,sys,json
from PIL import Image
pals=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify(require("./pals.js")))']))
only=sys.argv[1].split(',') if len(sys.argv)>1 else None
OUT=os.environ.get('POUT','out'); SP=os.environ.get('PSP','sprites')
os.makedirs(SP,exist_ok=True)
KINDS=[('deck','PPT_기본틀_',640),('a4','한장카드_A4_',400),('sq','카드뉴스_1대1_',360)]
if os.environ.get('PONLY'): KINDS=[k for k in KINDS if k[0]==os.environ['PONLY']]
jobs=[]
for i,p in enumerate(pals):
    if only and p['id'] not in only: continue
    d=f"{OUT}/{i+1:02d}_{p['name']}"
    for st,suf in [('base',''),('light','_가볍게')]:
        for kind,pat,w in KINDS: jobs.append((p,st,kind,w,f"{d}/{pat}{p['name']}{suf}.pptx"))
subprocess.run(['python3',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','tools','uno_pdf.py')]+[j[4] for j in jobs],check=True)
for p,st,kind,w,f in jobs:
    pdf=f[:-5]+'.pdf'; pre=f[:-5]+'_p'
    subprocess.run(['pdftoppm','-jpeg','-r','90',pdf,pre],check=True); os.remove(pdf)
    fs=sorted(glob.glob(pre+'-*.jpg'))
    imgs=[Image.open(x).convert('RGB') for x in fs]
    imgs=[im.resize((w,round(im.height*w/im.width)),Image.LANCZOS) for im in imgs]
    h=imgs[0].height; sp=Image.new('RGB',(w,h*len(imgs)),'white')
    for j,im in enumerate(imgs): sp.paste(im,(0,j*h))
    sp.save(f"{SP}/{p['id']}_{st}_{kind}.jpg",quality=70,optimize=True)
    for x in fs: os.remove(x)
print('rendered',len(jobs))
