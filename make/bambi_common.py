# -*- coding: utf-8 -*-
"""밤비의 서류뭉치 · 공통 모듈 (색 21조합, 글꼴 찾기, 글 처리, PIL 그리기 도우미). 고치지 않는다."""
import sys, os, re, glob, json, urllib.request, hashlib, socket
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUTDIR = "/mnt/data" if os.path.isdir("/mnt/data") else "."

PALS = [
 ["b3","청먹","1F3A5F","4A6A8C","EEF2F7","1C2430","D5DDE7","C9A227"],["slate","슬레이트","334155","64748B","F1F5F9","0F172A","E2E8F0","D97706"],
 ["ink","먹색","2B2F36","6B7280","F3F4F6","111827","E5E7EB","2563EB"],["steel","스틸블루","2F5D8A","6E8FB0","EDF3F9","1B2735","D4E0EC","E0A82E"],
 ["royal","공공 네이비","1D3C78","5873A6","EEF2FA","141E33","D3DCEE","F2B705"],["forest","차콜 그린","2F3E3A","6F807B","EFF3F1","1C2522","D9E1DE","B7791F"],
 ["teal","딥틸","1E4E5A","5F8A93","EDF3F4","1B2A2E","D6E2E4","E08E45"],["dusty","더스티 블루","4C6A8A","8AA2BB","F0F4F8","1F2B38","DCE4EC","D98C6A"],
 ["sage","세이지","5B7B6A","96AE9F","F1F5F2","1F2A24","DCE6DF","C9925A"],["olive","올리브 그레이","3F4A3C","7D8B74","F1F3EE","23281F","DDE2D8","C2853D"],
 ["lav","라벤더 그레이","5B5A7A","8F8EAD","F3F2F8","22212F","E2E1EC","D4A24C"],["mocha","모카","6B5446","A08A7C","F6F2EF","2A211C","E7DED8","4F7CAC"],
 ["cobalt","코발트","2F49A8","6E81C7","EEF1FB","1A2142","D6DCF2","F5C542"],["blue","흑백 파랑","0F62FE","6F6F6F","F4F4F4","161616","E0E0E0","161616"],
 ["emerald","에메랄드","0F766E","4FA39A","ECF7F5","10201E","CFE7E3","F59E0B"],["orange","오렌지 차콜","C2541F","8A8F98","FBF1EB","22252A","ECE1DA","22252A"],
 ["wine","와인","5A2A35","9A6B74","F6F0F1","2A1D20","E8DADD","C9A227"],["red","레드 경고","B3261E","7A7F87","FBEDEC","1F2328","EED5D3","1F2328"],
 ["terra","테라코타","C4826A","D9A994","FBF0EA","2B201B","F0DED4","5A3A2C"],["rose","로즈우드","8A4A46","B07F7B","F7EFEE","2A1C1B","EBDCDA","D9A066"],
 ["espresso","에스프레소","3B2A22","7A6458","F5EFEA","1F1712","E6DCD4","F2C9A8"],
]
PAL = {p[0]: dict(id=p[0], name=p[1], main=p[2], sub=p[3], tint=p[4], ink=p[5], line=p[6], point=p[7]) for p in PALS}
RAW = "https://raw.githubusercontent.com/eugene-shin9/bambi-paper-stash/main/fonts/"
FONTS = {"ng": ("NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf", "NanumGothic-ExtraBold.ttf"),
         "nsr": ("NanumSquareRoundR.ttf", "NanumSquareRoundB.ttf", "NanumSquareRoundEB.ttf"),
         "pg": ("NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf", "Paperlogy-8ExtraBold.ttf")}

def log(*a): print(*a, file=sys.stderr)

def lum(h):
    v = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]; v = [c/12.92 if c <= .03928 else ((c+.055)/1.055)**2.4 for c in v]
    return .2126*v[0] + .7152*v[1] + .0722*v[2]
def ratio(a, b): x, y = lum(a), lum(b); return (max(x, y)+.05)/(min(x, y)+.05)
def head_on_dark(C):
    """진한(주색) 바탕 위 머리말 색: 포인트가 충분히 밝으면 포인트, 아니면 옅은 바탕색"""
    return C["point"] if (lum(C["point"]) > lum(C["main"]) and ratio(C["point"], C["main"]) >= 3) else C["tint"]
def rgb(h): return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def mix(h1, h2, t):  # h1 쪽 비율 t
    a, b = rgb(h1), rgb(h2); return tuple(round(a[i]*t + b[i]*(1-t)) for i in range(3))

# ---------------- 글꼴
def find_font(name, extra_dir=None):
    here = HERE
    for d in [extra_dir, os.path.join(here, "fonts"), here, "fonts", ".", "/mnt/data/fonts", "/mnt/data", "/mnt/user-data/uploads"]:
        if not d: continue
        p = os.path.join(d, name)
        if os.path.exists(p): return p
        for q in glob.glob(os.path.join(d, "**", name), recursive=True): return q
    try:
        os.makedirs(os.path.join(here, "fonts"), exist_ok=True); p = os.path.join(here, "fonts", name)
        socket.setdefaulttimeout(6); urllib.request.urlretrieve(RAW + name, p); return p
    except Exception:
        return None

def font_paths(key, extra_dir=None):
    """(Regular, Bold, 제목용) 경로. 못 찾으면 안내 후 종료(파일을 만들지 않는다)."""
    names = FONTS[key]; paths = [find_font(n, extra_dir) for n in names]
    if not paths[0] or not paths[1]:
        miss = [n for n, p in zip(names, paths) if not p]
        log("글꼴을 찾지 못했습니다: " + ", ".join(miss)); log("fonts/ 폴더(또는 첨부)에 넣고 다시 실행하세요. 파일을 만들지 않았습니다."); sys.exit(3)
    if not paths[2]: paths[2] = paths[1]
    log("글꼴: " + " / ".join(os.path.basename(p) for p in paths)); return paths

def self_hash(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]

# ---------------- 글
WD = r"(?:\s*\([월화수목금토일]\))?"
EMPH = re.compile(
    r"\d{4}\s*\.\s*\d{1,2}\s*\.(?:\s*\d{1,2}\s*\.)?" + WD + r"(?:\s*[~–-]\s*(?:\d{4}\s*\.\s*)?\d{1,2}\s*\.(?:\s*\d{1,2}\s*\.)?" + WD + r")?(?:\s*\(예정\))?"
    r"|(?<![\d.])\d{1,2}\s*\.\s*\d{1,2}\s*\." + WD + r"(?:\s*[~–-]\s*\d{1,2}\s*\.\s*\d{1,2}\s*\." + WD + r")?"
    r"|\d{4}년(?:\s*\d{1,2}월)?(?:\s*\d{1,2}일)?" + WD + r"|\d{1,2}월\s*\d{1,2}일" + WD +
    r"|\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:명|원|만\s*원|천\s*원|억\s*원|건|회|개|시간|주|%)"
    r"|\d{1,2}:\d{2}(?:\s*[~–-]\s*\d{1,2}:\d{2})?")
NUM_PRE = re.compile(r"^\s*(?:\d+\s*[.)]|[가-힣]\s*[.)]|[IVX]+\s*\.|[○●◦·\-–•▪]|\(\d+\)|\([가-힣]\))\s+")
def strip_no(s, warn):
    s2 = NUM_PRE.sub("", str(s), count=1)
    if s2 != s: warn.append(f"번호·기호를 뗐음: {str(s)[:24]}")
    return s2
def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def missing_glyphs(text, fontpath):
    try:
        from reportlab.pdfbase.ttfonts import TTFont
        cmap = TTFont("chk", fontpath).face.charToGlyph; return {ch for ch in set(text) if ord(ch) > 127 and ord(ch) not in cmap}
    except Exception:
        return {ch for ch in set(text) if ord(ch) > 0xFFFF}

def save_png(img, out, scale=2):
    """2배로 그린 그림을 LANCZOS로 줄여 저장(도형 가장자리 매끈하게)."""
    from PIL import Image
    if scale != 1: img = img.resize((img.width//scale, img.height//scale), Image.LANCZOS)
    img.convert("RGB").save(out, "PNG"); return img

def pptx_font(run, name, size=None, bold=None, color=None):
    """python-pptx run에 한글(ea)·라틴 글꼴을 함께 지정"""
    from pptx.util import Pt
    from pptx.dml.color import RGBColor
    from pptx.oxml.ns import qn
    from lxml import etree
    run.font.name = name
    if size: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if color: run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None: el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", name)

def load_json(path):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception as e: log(f"JSON을 읽지 못함: {e}"); sys.exit(4)

def fail(errs):
    log("입력 오류 — 파일을 만들지 않았습니다:\n- " + "\n- ".join(errs)); sys.exit(4)

# ---------------- PIL 그리기 도우미
class Pen:
    """PIL ImageDraw 위에 글을 놓는 도우미. 단위는 px. 글꼴 캐시, CJK 줄바꿈, 정렬."""
    def __init__(self, img, paths):
        from PIL import ImageDraw, ImageFont
        self.img, self.d, self.paths, self._f, self.IF = img, ImageDraw.Draw(img), paths, {}, ImageFont
    def font(self, size, w="r"):
        k = (size, w)
        if k not in self._f: self._f[k] = self.IF.truetype(self.paths[{"r": 0, "b": 1, "h": 2}[w]], int(round(size)))
        return self._f[k]
    def width(self, text, size, w="r"): return self.d.textlength(text, font=self.font(size, w))
    def wrap(self, text, size, maxw, w="r"):
        """어절 단위로 줄을 나누고, 한 어절이 너무 길면 글자 단위로 자른다. '↵'는 강제 줄바꿈."""
        lines = []
        for para in str(text).replace("\\n", "↵").split("↵"):
            cur = ""
            for word in para.split(" "):
                cand = (cur + " " + word).strip() if cur else word
                if self.width(cand, size, w) <= maxw: cur = cand; continue
                if cur: lines.append(cur); cur = ""
                if self.width(word, size, w) <= maxw: cur = word; continue
                for ch in word:
                    if self.width(cur + ch, size, w) <= maxw or ch in ".,)·%」": cur += ch
                    else: lines.append(cur); cur = ch
            lines.append(cur)
        return lines
    def text(self, x, y, text, size, color, w="r", maxw=None, lh=1.35, align="left", spacing=0, maxlines=None):
        """왼쪽 위(x,y)에서 시작. 반환: 그린 높이(px). align: left/center/right (x는 기준점)."""
        lines = self.wrap(text, size, maxw, w) if maxw else [str(text)]
        if maxlines and len(lines) > maxlines: lines = lines[:maxlines]; lines[-1] = lines[-1][:-1] + "…"
        f = self.font(size, w); step = size*lh; asc = f.getmetrics()[0]; yy = y + (step - size)/2 + asc  # 밑선(baseline) 기준으로 찍어 줄 높이 고정
        for ln in lines:
            tw = self.width(ln, size, w) + spacing*max(0, len(ln)-1)
            xx = x - tw if align == "right" else x - tw/2 if align == "center" else x
            if spacing:
                for i, ch in enumerate(ln): self.d.text((xx + self.width(ln[:i], size, w) + spacing*i, yy), ch, font=f, fill=color, anchor="ls")
            else: self.d.text((xx, yy), ln, font=f, fill=color, anchor="ls")
            yy += step
        return len(lines)*step
    def height(self, text, size, maxw, w="r", lh=1.35): return len(self.wrap(text, size, maxw, w))*size*lh
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1, r=0):
        if r: self.d.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=fill, outline=outline, width=width)
        else: self.d.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=width)
    def line(self, x0, y0, x1, y1, color, width=1): self.d.line((x0, y0, x1, y1), fill=color, width=width)
    def circle(self, cx, cy, r, fill=None, outline=None, width=1): self.d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=fill, outline=outline, width=width)
    def stamp(self, cx, cy, r, text, color, size=None):
        """도장: 원 테두리 + 안쪽 가는 원 + 가운데 글(최대 2줄), -9° 회전, 불투명도 88%"""
        from PIL import Image, ImageDraw
        s = int(r*2.6); lay = Image.new("RGBA", (s, s), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay); c = s/2
        col = color + (224,)
        dd.ellipse((c-r, c-r, c+r, c+r), outline=col, width=max(2, int(r*0.07)))
        ir = r*0.84; dd.ellipse((c-ir, c-ir, c+ir, c+ir), outline=col, width=max(1, int(r*0.025)))
        sz = size or r*0.42; f = self.font(sz, "b"); lines = str(text).replace("\\n", "↵").split("↵")[:2]
        tot = len(lines)*sz*1.15; yy = c - tot/2
        for ln in lines:
            tw = dd.textlength(ln, font=f); dd.text((c-tw/2, yy), ln, font=f, fill=col); yy += sz*1.15
        lay = lay.rotate(9, resample=Image.BICUBIC)
        self.img.paste(lay, (int(cx-c), int(cy-c)), lay)
