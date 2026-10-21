# 견본에 쓰인 글자만 남긴 Pretendard·SUIT 글꼴을 페이지 안에 넣을 @font-face로 만든다
import base64,subprocess,os,sys
src=open('/home/claude/kit/src/board_src.html',encoding='utf8').read()
chars=''.join(sorted(set(c for c in src if ord(c)>=32)))+''.join(chr(i) for i in range(32,127))+'·~→①②③④⑤⑥⑦⑧⑨⑩×'
open('/tmp/claude-0/chars.txt','w',encoding='utf8').write(chars)
F={'Pretendard':'/home/claude/fonts/pkg/pretendard-1.3.9/package/dist/public/static/Pretendard-{}.otf',
   'SUIT':'/home/claude/fonts/pkg/sun-typeface-suit-2.0.5/package/fonts/static/otf/SUIT-{}.otf'}
css=[]
for fam,pat in F.items():
  for w,name in [(400,'Regular'),(600,'SemiBold'),(700,'Bold')]:
    out=f'/tmp/claude-0/{fam}-{w}.woff2'
    subprocess.run(['pyftsubset',pat.format(name),'--text-file=/tmp/claude-0/chars.txt','--flavor=woff2','--layout-features=*',f'--output-file={out}'],check=True)
    b=base64.b64encode(open(out,'rb').read()).decode()
    css.append(f'@font-face{{font-family:"{fam}";font-weight:{w};font-style:normal;font-display:swap;src:url(data:font/woff2;base64,{b}) format("woff2")}}')
open('/home/claude/kit/tools/fontfaces.css','w').write('\n'.join(css))
print(len(chars), sum(len(x) for x in css)//1024,'KB')
