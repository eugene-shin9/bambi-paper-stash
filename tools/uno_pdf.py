# 미리보기 전용: 한글-영문/숫자 사이 자동 간격(LibreOffice 기본) 끄고 PDF로 내보냄
import sys, os, time, subprocess, uno
from com.sun.star.beans import PropertyValue
def P(n,v):
    p=PropertyValue(); p.Name=n; p.Value=v; return p
port=2002
prof='file:///tmp/claude-0/lo_prof'
proc=subprocess.Popen(['soffice','--headless','--invisible','--nologo','--norestore',f'-env:UserInstallation={prof}',f'--accept=socket,host=127.0.0.1,port={port};urp;'],env=dict(os.environ,SAL_USE_VCLPLUGIN='svp'))
ctx=None
for _ in range(60):
    try:
        lc=uno.getComponentContext(); r=lc.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',lc)
        ctx=r.resolve(f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext'); break
    except Exception: time.sleep(1)
desk=ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
def fix_text(t):
    try:
        e=t.getText().createEnumeration()
        while e.hasMoreElements():
            par=e.nextElement()
            try: par.ParaIsCharacterDistance=False
            except Exception: pass
    except Exception: pass
def walk(sh):
    if sh.supportsService('com.sun.star.drawing.GroupShape'):
        for i in range(sh.getCount()): walk(sh.getByIndex(i))
        return
    if sh.ShapeType=='com.sun.star.drawing.TableShape':
        m=sh.Model
        for r in range(m.Rows.Count):
            for c in range(m.Columns.Count):
                fix_text(m.getCellByPosition(c,r))
        return
    if hasattr(sh,'getText'): fix_text(sh)
for f in sys.argv[1:]:
    url=uno.systemPathToFileUrl(os.path.abspath(f))
    d=desk.loadComponentFromURL(url,'_blank',0,(P('Hidden',True),))
    pages=[d.DrawPages, d.MasterPages]
    for pg in pages:
        for i in range(pg.Count):
            p=pg.getByIndex(i)
            for j in range(p.Count): walk(p.getByIndex(j))
    out=uno.systemPathToFileUrl(os.path.abspath(f[:-5]+'.pdf'))
    d.storeToURL(out,(P('FilterName','impress_pdf_Export'),)); d.close(True)
    print('pdf',f,flush=True)
try: desk.terminate()
except Exception: pass
proc.wait(timeout=30)
