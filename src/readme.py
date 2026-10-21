# 규격서 글(spec.txt) → GitHub README.md
import re,sys
t=open('/home/claude/kit/tools/spec.txt',encoding='utf8').read().rstrip('\n').split('\n')
out=[]
for i,l in enumerate(t):
    if i==0: out+=['# 밤비의 서류뭉치 · AI용 규격서','',l.split('(')[-1].rstrip(')')+' · 문서·PPT·A4 카드·카드뉴스를 같은 색과 배치로 만들기 위한 기준입니다.','','사람이 보는 견본 페이지(색·글꼴을 바꿔 가며 보기): https://claude.ai/artifact/2yiYVG8FiANfpGyY1Y8L6W']; continue
    if l=='[이 규격서를 읽는 AI에게]': out.append('## 이 규격서를 읽는 AI에게'); continue
    if re.match(r'^\d\. ',l): out.append('## '+l); continue
    m=re.match(r'^\[(.+?)\](.*)$',l)
    if m: out.append('### '+m.group(1)+m.group(2)); continue
    if l.startswith('<svg'): out+=['```svg',l,'```']; continue
    if l.startswith('  '):
        s=re.sub(r'd="([^"]+)"',r'`d="\1"`',l.strip()); out.append('  - '+s); continue
    out.append(l.replace('이 페이지 링크나 이 글','이 리포지토리 링크나 이 글'))
open(sys.argv[1],'w',encoding='utf8').write('\n'.join(out)+'\n')
