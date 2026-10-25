# 테마의 한글(ea·Hang) 글꼴 자리를 라틴 글꼴과 같게 맞춘다: python3 fixfont.py 글꼴이름 파일...
import sys,zipfile,re,os,shutil
font=sys.argv[1]
for f in sys.argv[2:]:
    tmp=f+'.tmp'
    with zipfile.ZipFile(f) as zi, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            d=zi.read(it.filename)
            if it.filename=='ppt/theme/theme1.xml':
                x=d.decode('utf8')
                def fix(blk,fn):
                    blk=re.sub(r'<a:ea typeface="[^"]*"',f'<a:ea typeface="{fn}"',blk)
                    return re.sub(r'(<a:font script="Hang" typeface=")[^"]*"',rf'\g<1>{fn}"',blk)
                head=os.environ.get('PHEAD') or font  # 미리보기 전용: 제목 글꼴(major)만 따로
                x=re.sub(r'<a:majorFont>.*?</a:majorFont>',lambda m:fix(m.group(0),head),x,flags=re.S)
                x=re.sub(r'<a:minorFont>.*?</a:minorFont>',lambda m:fix(m.group(0),font),x,flags=re.S)
                d=x.encode('utf8')
            zo.writestr(it,d)
    os.replace(tmp,f)
