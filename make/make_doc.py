#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
밤비의 서류뭉치 · 문서(A4) 생성기  make_doc.py
==============================================
AI는 배치를 그리지 않는다. 첨부 자료의 내용을 content.json에 채우고 이 스크립트를 실행만 한다.
색·글꼴·여백·정렬·쪽 넘김·강조는 전부 여기서 정해진다. 이 파일은 고치지 않는다.

  python make_doc.py --schema            # content.json 예시 출력(이걸 복사해 채운다)
  python make_doc.py content.json --dry-run                      # 검사만
  python make_doc.py content.json --pal b3 --font ng --type report -o out.pdf

  --pal   b3 청먹(기본) lav 라벤더그레이 sage 세이지 forest 차콜그린 wine 와인 … 21개(--pals 로 목록)
  --font  ng 나눔고딕(기본) · nsr 나눔스퀘어라운드 · pg 제목만 페이퍼로지EB + 본문 나눔고딕
  --style base 기본 · light 심플(색 면 없음) · rich 풍성(표지 장식)
  --type  report 보고서형(개조식 1. 가. 1) — 회의·계획·결과보고) · proposal 제안서형(로마 숫자 섹션 — 기획서·제안서)
  --no-cover --no-toc --no-overview --no-emph
글꼴: 스크립트 옆 fonts/ → 현재 폴더 fonts/ → /mnt/data(/fonts) → GitHub 내려받기 순으로 찾는다. 못 찾으면 PDF를 만들지 않고 끝낸다.
"""
import sys, os, re, json, argparse, hashlib, glob, urllib.request

try:
    import reportlab
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "reportlab"], check=False)
    try:
        import reportlab
    except ImportError:
        print("reportlab을 설치하지 못했습니다. pip install reportlab 후 다시 실행.", file=sys.stderr); sys.exit(2)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, Flowable, CondPageBreak, NextPageTemplate)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor, white

SAMPLE = {
  "doc_kind": "월간 업무자료",
  "title": "원격교육지원센터 월간회의",
  "subtitle": "2026학년도 2학기 K-MOOC 운영 및 주요 업무",
  "org": "한빛대학교", "dept": "원격교육지원센터", "author": "", "date": "2026. 10. 30.(금)",
  "overview": {
    "items": [["목적", "K-MOOC 강좌 운영 현황 점검과 하반기 사업 추진"], ["기간", "2026. 9. ~ 12."], ["대상", "원격교육지원센터 구성원"]],
    "key_points": ["정규강좌 12과목 운영, 이수율 관리 강화", "홍보단·모니터링단 활동비 11월 집행", "사업비 2026. 12. 31. 집행 마감"],
    "decisions": ["이수 이벤트 운영계획(안) 내부 승인 요청"]
  },
  "sections": [
    {"title": "2026학년도 2학기 K-MOOC 강좌 운영 및 학습지원",
     "subs": [
       {"title": "2026학년도 2학기 K-MOOC 정규강좌 운영",
        "items": ["운영기간: 2026. 9. ~ 12.",
                  {"text": "K-MOOC 및 DU-MOOC 강좌별 운영 현황 점검 및 관리", "sub": ["강좌별 학습 진도율·수강 참여율 확인", "시스템 오류 모니터링"]},
                  {"table": {"caption": "표 1. 강좌 운영 현황", "head": ["구분", "강좌 수", "수강생"], "rows": [["정규", "12", "1,240"], ["DU-MOOC", "4", "310"]], "sum": ["합계", "16", "1,550"], "colw": [2, 1, 1]}}]},
       {"title": "K-MOOC 강좌 운영 지원 및 교육지원인력 관리",
        "items": ["강좌별 교육지원인력(TA) 업무 수행 현황 점검"]}
     ]},
    {"title": "2026학년도 K-MOOC 강좌 모니터링단 운영",
     "items": ["절(가.) 없이 장 바로 아래 항목을 둘 수도 있다", {"p": "제안서형처럼 서술식 문단이 필요하면 p 로 쓴다."}]}
  ],
  "attachments": ["프로그램 세부 일정 1부."],
  "contact": "교육팀 053-000-0000"
}
SCHEMA_NOTE = """# content.json 규칙
# - 번호("1." "가." "1)")는 쓰지 않는다. 스크립트가 붙인다. 들어 있으면 떼고 경고한다.
# - 원문에 없는 날짜·수치·담당자·문의처를 지어내지 않는다. 없는 항목은 빈 배열 [] 또는 "" 로 둔다(그 부분은 빠진다).
# - items 원소: "글" | {"text": "글", "sub": ["세부 -", ...]} | {"table": {...}} | {"p": "서술식 문단"}
# - subs(절)는 없어도 된다. 표 열은 6개까지. colw는 열 폭 비율(선택).
# - 표지 제목은 2줄, 부제는 1줄 안에 들어가야 한다(넘치면 스크립트가 거부하고 글자 수를 알려 준다).
"""

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
PAL = {p[0]: dict(name=p[1], main=p[2], sub=p[3], tint=p[4], ink=p[5], line=p[6], point=p[7]) for p in PALS}
RAW = "https://raw.githubusercontent.com/eugene-shin9/bambi-paper-stash/main/fonts/"
FONTS = {"ng": ("NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf", "NanumGothic-ExtraBold.ttf"),
         "nsr": ("NanumSquareRoundR.ttf", "NanumSquareRoundB.ttf", "NanumSquareRoundEB.ttf"),
         "pg": ("NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf", "Paperlogy-8ExtraBold.ttf")}

def log(*a): print(*a, file=sys.stderr)

# ---------------------------------------------------------------- 글꼴
def find_font(name, extra_dir):
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = [extra_dir, os.path.join(here, "fonts"), here, "fonts", ".", "/mnt/data/fonts", "/mnt/data", "/mnt/user-data/uploads"]
    for d in dirs:
        if not d: continue
        p = os.path.join(d, name)
        if os.path.exists(p): return p
        for q in glob.glob(os.path.join(d, "**", name), recursive=True): return q
    try:
        os.makedirs(os.path.join(here, "fonts"), exist_ok=True); p = os.path.join(here, "fonts", name)
        urllib.request.urlretrieve(RAW + name, p); return p
    except Exception:
        return None

def load_fonts(key, extra_dir):
    names = FONTS[key]; paths = [find_font(n, extra_dir) for n in names]
    if not paths[0] or not paths[1]:
        miss = [n for n, p in zip(names, paths) if not p]
        log("글꼴을 찾지 못했습니다: " + ", ".join(miss)); log("fonts/ 폴더(또는 첨부)에 이 파일을 넣고 다시 실행하세요. PDF를 만들지 않았습니다."); sys.exit(3)
    if not paths[2]: paths[2] = paths[1]
    pdfmetrics.registerFont(TTFont("B-R", paths[0])); pdfmetrics.registerFont(TTFont("B-B", paths[1])); pdfmetrics.registerFont(TTFont("B-H", paths[2]))
    registerFontFamily("B-R", normal="B-R", bold="B-B", italic="B-R", boldItalic="B-B")
    log("글꼴: " + " / ".join(os.path.basename(p) for p in paths))
    return paths

def missing_glyphs(text, fontpath):
    try:
        f = TTFont("chk", fontpath); cmap = f.face.charToGlyph
    except Exception:
        return set()
    return {ch for ch in set(text) if ord(ch) > 127 and ord(ch) not in cmap}

# ---------------------------------------------------------------- 글 처리
def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
WD = r"(?:\s*\([월화수목금토일]\))?"
EMPH = re.compile(
    r"\d{4}\s*\.\s*\d{1,2}\s*\.(?:\s*\d{1,2}\s*\.)?" + WD + r"(?:\s*[~–-]\s*(?:\d{4}\s*\.\s*)?\d{1,2}\s*\.(?:\s*\d{1,2}\s*\.)?" + WD + r")?(?:\s*\(예정\))?"
    r"|(?<![\d.])\d{1,2}\s*\.\s*\d{1,2}\s*\." + WD + r"(?:\s*[~–-]\s*\d{1,2}\s*\.\s*\d{1,2}\s*\." + WD + r")?"
    r"|\d{4}년(?:\s*\d{1,2}월)?(?:\s*\d{1,2}일)?" + WD + r"|\d{1,2}월\s*\d{1,2}일" + WD +
    r"|\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:명|원|만\s*원|천\s*원|억\s*원|건|회|개|시간|주|%)"
    r"|\d{1,2}:\d{2}(?:\s*[~–-]\s*\d{1,2}:\d{2})?")

def emph(text, C, on=True):
    t = esc(text)
    if not on: return t
    return EMPH.sub(lambda m: f'<b><font color="#{C["main"]}">{m.group(0)}</font></b>', t)

NUM_PRE = re.compile(r"^\s*(?:\d+\s*[.)]|[가-힣]\s*[.)]|[IVX]+\s*\.|[○●◦·\-–•▪]|\(\d+\)|\([가-힣]\))\s+")
def strip_no(s, warn):
    s2 = NUM_PRE.sub("", s, count=1)
    if s2 != s: warn.append(f"번호·기호를 뗐음: {s[:24]}")
    return s2

def hx(h): return HexColor("#" + h)

class Rule(Flowable):
    def __init__(self, w, color, th=0.5, pad=0): Flowable.__init__(self); self.w, self.c, self.th, self.pad = w, color, th, pad
    def wrap(self, aw, ah): return aw, self.th + self.pad
    def draw(self): self.canv.setStrokeColor(self.c); self.canv.setLineWidth(self.th); self.canv.line(0, self.pad/2, self.w, self.pad/2)

class TocMark(Flowable):
    def __init__(self, doc, title, no): Flowable.__init__(self); self.doc, self.title, self.no = doc, title, no
    def wrap(self, aw, ah): return 0, 0
    def draw(self): self.doc.toc.append((self.title, self.no, self.canv.getPageNumber()))

# ---------------------------------------------------------------- 본체
class Doc:
    ROMAN = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV"]
    GA = list("가나다라마바사아자차카타파하")

    def __init__(self, d, C, font, style, kind, o):
        self.d, self.C, self.font, self.style, self.kind, self.o = d, C, font, style, kind, o
        self.W, self.H = A4; self.M = 20*mm; self.CW = self.W - 2*self.M
        self.toc = []; self.toc_pages = {}; self.warn = []
        self._styles()

    def _styles(self):
        C = self.C; ink, main, sub = hx(C["ink"]), hx(C["main"]), hx(C["sub"])
        HEAD = "B-H" if self.font == "pg" else "B-B"
        bs = 11 if self.kind == "report" else 10.5; ld = bs*1.6 if self.kind == "report" else bs*1.7
        P = lambda n, **k: ParagraphStyle(n, wordWrap="CJK", **k)
        self.S = dict(
            ck=P("ck", fontName="B-R", fontSize=11, leading=16, textColor=sub),
            ct=P("ct", fontName=HEAD, fontSize=26, leading=34, textColor=ink),
            cs=P("cs", fontName="B-R", fontSize=13, leading=19, textColor=sub),
            cm=P("cm", fontName="B-R", fontSize=11, leading=16, textColor=ink),
            hp=P("hp", fontName=HEAD, fontSize=18, leading=24, textColor=ink, spaceAfter=6*mm),
            h1=P("h1", fontName=HEAD, fontSize=14, leading=20, textColor=ink, spaceBefore=10*mm, spaceAfter=3*mm, keepWithNext=1),
            h2=P("h2", fontName="B-B", fontSize=12, leading=18, textColor=main, leftIndent=5*mm, spaceBefore=6*mm, spaceAfter=2*mm, keepWithNext=1),
            it=P("it", fontName="B-R", fontSize=bs, leading=ld, textColor=ink, leftIndent=10*mm+6*mm, firstLineIndent=-6*mm, spaceAfter=3*mm),
            it0=P("it0", fontName="B-R", fontSize=bs, leading=ld, textColor=ink, leftIndent=5*mm+6*mm, firstLineIndent=-6*mm, spaceAfter=3*mm),
            it2=P("it2", fontName="B-R", fontSize=bs-1, leading=(bs-1)*1.55, textColor=sub, leftIndent=15*mm+4*mm, firstLineIndent=-4*mm, spaceAfter=1.5*mm),
            pa=P("pa", fontName="B-R", fontSize=bs, leading=ld, textColor=ink, leftIndent=5*mm, spaceAfter=3*mm),
            lb=P("lb", fontName="B-R", fontSize=9, leading=13, textColor=sub),
            vl=P("vl", fontName="B-B", fontSize=11, leading=16, textColor=ink),
            sm=P("sm", fontName="B-R", fontSize=8, leading=11, textColor=sub),
            cap=P("cap", fontName="B-R", fontSize=10, leading=14, textColor=ink, spaceBefore=3*mm, spaceAfter=1.5*mm),
            th=P("th", fontName="B-B", fontSize=10, leading=14, textColor=main),
            td=P("td", fontName="B-R", fontSize=10, leading=14, textColor=ink),
            tdr=P("tdr", fontName="B-R", fontSize=10, leading=14, textColor=ink, alignment=TA_RIGHT),
            tds=P("tds", fontName="B-B", fontSize=10, leading=14, textColor=ink),
            tdsr=P("tdsr", fontName="B-B", fontSize=10, leading=14, textColor=ink, alignment=TA_RIGHT),
            t1=P("t1", fontName="B-B", fontSize=12, leading=17, textColor=ink),
            tn=P("tn", fontName="B-R", fontSize=11, leading=16, textColor=ink, alignment=TA_RIGHT),
            tno=P("tno", fontName=HEAD, fontSize=12, leading=17, textColor=main),
            bl=P("bl", fontName="B-B", fontSize=10, leading=14, textColor=main),
            bt=P("bt", fontName="B-R", fontSize=11, leading=17, textColor=ink),
            band=P("band", fontName="B-B", fontSize=13, leading=18, textColor=ink),
            rom=P("rom", fontName="B-B", fontSize=10, leading=12, textColor=white, alignment=TA_CENTER),
            end=P("end", fontName="B-R", fontSize=bs, leading=ld, textColor=ink, alignment=TA_RIGHT),
        )

    # ---------- 쪽 머리·바닥
    def _on_page(self, canv, doc):
        C = self.C; pn = canv.getPageNumber(); canv.saveState()
        canv.setFont("B-R", 8); canv.setFillColor(hx(C["sub"])); y = self.H - 12*mm
        canv.drawString(self.M, y, self.d.get("title", "")[:40]); canv.drawRightString(self.W - self.M, y, self.d.get("dept") or self.d.get("org", ""))
        canv.setStrokeColor(hx(C["line"])); canv.setLineWidth(0.5); canv.line(self.M, y - 2*mm, self.W - self.M, y - 2*mm)
        canv.setFont("B-R", 9); canv.drawCentredString(self.W/2, 10*mm, f"- {pn} -"); canv.restoreState()

    def _on_cover(self, canv, doc):
        C = self.C; canv.saveState()
        if self.kind == "report":
            if self.style == "rich":
                canv.setFillColor(hx(C["tint"])); canv.circle(self.W - 15*mm, self.H - 15*mm, 42*mm, stroke=0, fill=1)
            canv.setFillColor(hx(C["main"])); canv.rect(self.M, self.H - 125*mm, 4*mm, 62*mm, stroke=0, fill=1)
        canv.restoreState()

    def _box(self, flows, left=0, w=None):
        t = Table([[flows]], colWidths=[w or self.CW - left]); t.hAlign = "RIGHT" if left else "LEFT"
        t.setStyle(TableStyle([(k, (0, 0), (-1, -1), 0) for k in ("LEFTPADDING", "RIGHTPADDING", "TOPPADDING", "BOTTOMPADDING")])); return t

    # ---------- 표지
    def cover(self):
        C, S, d = self.C, self.S, self.d
        meta = " · ".join(x for x in [d.get("date", ""), d.get("dept", ""), d.get("author", "")] if x)
        if self.kind == "report":
            return [Spacer(1, 62*mm), self._box([Paragraph(esc(d.get("doc_kind", "")), S["ck"]), Spacer(1, 4*mm),
                    Paragraph(esc(d["title"]), S["ct"]), Spacer(1, 5*mm), Paragraph(esc(d.get("subtitle", "")), S["cs"])], left=10*mm),
                    Spacer(1, 90*mm), Rule(self.CW, hx(C["line"]), 0.5, 4*mm), Spacer(1, 3*mm), Paragraph(esc(meta), S["cm"]), NextPageTemplate("body"), PageBreak()]
        cen = lambda txt, st: Paragraph(txt, ParagraphStyle("c"+st.name, parent=st, alignment=TA_CENTER))
        rows = [[k, v] for k, v in [("제출처", d.get("org", "")), ("사업 기간", d.get("period", "")), ("작성자", d.get("author") or d.get("dept", "")), ("작성일", d.get("date", ""))] if v]
        fl = [Spacer(1, 58*mm), cen(esc(d.get("doc_kind", "")), S["ck"]), Spacer(1, 8*mm), Rule(self.CW, hx(C["main"]), 1.5), Spacer(1, 6*mm),
              cen(esc(d["title"]), S["ct"]), Spacer(1, 6*mm), Rule(self.CW, hx(C["main"]), 1.5), Spacer(1, 6*mm), cen(esc(d.get("subtitle", "")), S["cs"]), Spacer(1, 48*mm)]
        if rows:
            t = Table([[Paragraph(esc(k), S["th"]), Paragraph(esc(v), S["td"])] for k, v in rows], colWidths=[35*mm, 85*mm], rowHeights=9*mm)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), hx(C["tint"])), ("GRID", (0, 0), (-1, -1), 0.4, hx(C["line"])), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 4*mm)]))
            fl.append(t)
        return fl + [NextPageTemplate("body"), PageBreak()]

    # ---------- 목차(장만, 1쪽 고정)
    def toc_page(self):
        C, S = self.C, self.S; rows = []
        for title, no, _ in self.entries:
            pg = self.toc_pages.get((title, no), "")
            if self.kind == "proposal":
                num = Table([[Paragraph(no, ParagraphStyle("rn", parent=S["rom"], textColor=hx(C["main"])))]], colWidths=[11*mm], rowHeights=[8*mm])
                num.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), hx(C["tint"])), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            else:
                num = Paragraph(no, S["tno"])
            rows.append([num, Paragraph(esc(title), S["t1"]), Paragraph(str(pg), S["tn"])])
        pad = 3.2*mm if len(rows) <= 12 else 1.8*mm
        t = Table(rows, colWidths=[16*mm, self.CW - 30*mm, 14*mm])
        st = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
              ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, -1), 0.4, hx(C["line"]))]
        if self.kind == "proposal": st += [("LINEABOVE", (0, 0), (-1, 0), 1, hx(C["main"])), ("LINEBELOW", (0, -1), (-1, -1), 1, hx(C["main"]))]
        t.setStyle(TableStyle(st))
        head = [Paragraph("목 차", ParagraphStyle("tp", parent=S["hp"], alignment=TA_CENTER, spaceAfter=1*mm)), Paragraph("CONTENTS", ParagraphStyle("cts", parent=S["sm"], alignment=TA_CENTER, spaceAfter=8*mm))] \
               if self.kind == "proposal" else [Paragraph("목차", S["hp"])]
        return head + [t, PageBreak()]

    # ---------- 개요
    def overview(self):
        C, S = self.C, self.S; ov = self.d.get("overview") or {}
        items = [x for x in ov.get("items", []) if isinstance(x, list) and len(x) == 2 and str(x[1]).strip()]
        kp = [x for x in ov.get("key_points", []) if str(x).strip()]; dc = [x for x in ov.get("decisions", []) if str(x).strip()]
        if not (items or kp or dc): return []
        fl = [Paragraph("개요", S["hp"])]; tint = hx(C["tint"]) if self.style != "light" else white; box = 0.5 if self.style == "light" else 0
        if items:
            cells = [[Paragraph(esc(k), S["lb"]), Paragraph(emph(v, C, self.o.emph), S["vl"])] for k, v in items]
            grid = []
            for i in range(0, len(cells), 2):
                r = cells[i:i+2]; r += [["", ""]] * (2 - len(r)); grid.append([r[0][0], r[0][1], r[1][0], r[1][1]])
            half = self.CW/2
            t = Table(grid, colWidths=[24*mm, half - 24*mm, 24*mm, half - 24*mm], hAlign="LEFT")
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), tint), ("BOX", (0, 0), (-1, -1), box, hx(C["line"])), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 3*mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 3*mm), ("LEFTPADDING", (0, 0), (0, -1), 5*mm), ("LEFTPADDING", (2, 0), (2, -1), 5*mm)]))
            fl += [t, Spacer(1, 8*mm)]
        if kp:
            fl += [Paragraph("핵심 결론", S["bl"]), Rule(self.CW, hx(C["main"]), 0.8, 3*mm), Spacer(1, 1.5*mm)]
            fl += [Paragraph(f"{i}. " + emph(k, C, self.o.emph), ParagraphStyle("kp", parent=S["it0"], leftIndent=6*mm, firstLineIndent=-6*mm)) for i, k in enumerate(kp[:5], 1)]
            fl.append(Spacer(1, 6*mm))
        if dc:
            inner = [Paragraph("결정·요청 사항", S["bl"]), Spacer(1, 1.5*mm)] + [Paragraph("· " + emph(x, C, self.o.emph), S["bt"]) for x in dc[:5]]
            t = Table([[inner]], colWidths=[self.CW])
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), tint), ("BOX", (0, 0), (-1, -1), box, hx(C["line"])), ("LEFTPADDING", (0, 0), (-1, -1), 5*mm),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 5*mm), ("TOPPADDING", (0, 0), (-1, -1), 4*mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 4*mm)]))
            fl.append(t)
        return fl + [PageBreak()]

    # ---------- 표
    NUMCELL = re.compile(r"^[\d,]+(?:\.\d+)?\s*(?:원|명|%|건|회|개)?$")
    def table(self, tb):
        C, S = self.C, self.S; head = [str(x) for x in tb.get("head", [])]; rows = [[str(c) for c in r] for r in tb.get("rows", [])]
        n = len(head) or (len(rows[0]) if rows else 0)
        numcol = [i > 0 and all(self.NUMCELL.match(r[i].strip()) for r in rows if i < len(r) and r[i].strip()) for i in range(n)]
        colw = tb.get("colw"); tot = float(sum(colw)) if colw and len(colw) == n else None
        widths = [self.CW * c / tot for c in colw] if tot else [self.CW / n] * n
        data = [[Paragraph(esc(h), ParagraphStyle("thr", parent=S["th"], alignment=TA_RIGHT) if numcol[i] else S["th"]) for i, h in enumerate(head)]] if head else []
        data += [[Paragraph(esc(c), S["tdr"] if numcol[i] else S["td"]) for i, c in enumerate(r[:n])] + [""] * (n - len(r)) for r in rows]
        if tb.get("sum"): data.append([Paragraph(esc(c), S["tdsr"] if numcol[i] else S["tds"]) for i, c in enumerate([str(x) for x in tb["sum"]][:n])])
        t = Table(data, colWidths=widths, repeatRows=1 if head else 0, hAlign="LEFT", splitByRow=1)
        st = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2*mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2*mm), ("LEFTPADDING", (0, 0), (-1, -1), 2*mm),
              ("RIGHTPADDING", (0, 0), (-1, -1), 2*mm), ("LINEBELOW", (0, 0), (-1, -1), 0.4, hx(C["line"]))]
        if head: st.append(("LINEBELOW", (0, 0), (-1, 0), 1.2, hx(C["main"])))
        if head and self.kind == "proposal" and self.style != "light": st.append(("BACKGROUND", (0, 0), (-1, 0), hx(C["tint"])))
        if tb.get("sum"): st.append(("LINEABOVE", (0, -1), (-1, -1), 1.2, hx(C["main"])))
        t.setStyle(TableStyle(st))
        fl = ([Paragraph(esc(tb["caption"]), S["cap"])] if tb.get("caption") else []) + [t]
        if tb.get("source"): fl.append(Paragraph("출처: " + esc(tb["source"]), S["sm"]))
        return [self._box(fl, left=5*mm), Spacer(1, 3*mm)]

    # ---------- 본문
    def items(self, lst, indented):
        C, S, fl, n = self.C, self.S, [], 0
        for it in lst:
            if isinstance(it, dict) and "table" in it: fl += self.table(it["table"]); continue
            if isinstance(it, dict) and "p" in it: fl.append(Paragraph(emph(it["p"], C, self.o.emph), S["pa"])); continue
            text = it.get("text", "") if isinstance(it, dict) else str(it); subs = it.get("sub", []) if isinstance(it, dict) else []
            n += 1
            fl.append(Paragraph(f"{n}) " + emph(text, C, self.o.emph), S["it"] if indented else S["it0"]))
            for s in subs: fl.append(Paragraph("- " + emph(s, C, self.o.emph), S["it2"]))
        return fl

    def body(self):
        C, S = self.C, self.S; fl = []; self.entries = []
        for si, sec in enumerate(self.d["sections"], 1):
            no = f"{si}." if self.kind == "report" else (self.ROMAN[si-1] if si <= 15 else str(si)); title = sec["title"]
            self.entries.append((title, no.rstrip("."), si))
            if self.kind == "report":
                h = [Paragraph(f"{no} " + esc(title), S["h1"])]
            else:
                sq = Table([[Paragraph(no, S["rom"])]], colWidths=[6*mm], rowHeights=[6*mm]); sq.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), hx(C["main"])), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
                band = Table([[sq, Paragraph(esc(title), S["band"])]], colWidths=[9*mm, self.CW - 9*mm], rowHeights=[7*mm])
                band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), hx(C["tint"]) if self.style != "light" else white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                          ("LEFTPADDING", (0, 0), (0, 0), 0.5*mm), ("LEFTPADDING", (1, 0), (1, 0), 2*mm), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                h = [Spacer(1, 8*mm), band, Spacer(1, 3*mm)]
            top = sec.get("items", [])
            subs = list(sec.get("subs", []))
            first_block = self.items(top, False) if top else []
            # 장 제목 + 첫 덩어리의 앞 2개는 같이 움직인다(제목만 쪽 끝에 남지 않게)
            fl.append(CondPageBreak(45*mm)); fl += [KeepTogether(h + [TocMark(self, title, no.rstrip("."))] + first_block[:2])] + first_block[2:]
            for ki, sub in enumerate(subs):
                g = self.GA[ki % 14]
                blk = self.items(sub.get("items", []), True)
                fl += [KeepTogether([Paragraph(f"{g}. " + esc(sub["title"]), S["h2"])] + blk[:2])] + blk[2:]
        att = [a for a in self.d.get("attachments", []) if str(a).strip()]
        tail = [Spacer(1, 6*mm)]
        for i, a in enumerate(att, 1):
            tail.append(Paragraph(("붙임 " if i == 1 else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;") + f"{i}. " + esc(a), ParagraphStyle("at", parent=S["it0"], leftIndent=0, firstLineIndent=0, spaceAfter=1*mm)))
        tail += [Spacer(1, 2*mm), Paragraph("끝.", S["end"])]
        if self.d.get("contact"): tail += [Spacer(1, 8*mm), Rule(self.CW, hx(C["line"]), 0.5, 2*mm), Paragraph(esc(self.d["contact"]), S["sm"])]
        fl.append(KeepTogether(tail))
        return fl

    # ---------- 빌드(2차: 1차에서 쪽번호를 모아 2차 목차에 넣는다. 목차는 1쪽 고정이라 2차에서 쪽이 밀리지 않는다)
    def build(self, out):
        frame = Frame(self.M, 18*mm, self.CW, self.H - 18*mm - 22*mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="f")
        def story():
            s = []
            if self.o.cover: s += self.cover()
            body = self.body()
            if self.o.toc: s += self.toc_page()
            if self.o.overview: s += self.overview()
            return s + body
        for _ in range(2):
            doc = BaseDocTemplate(out, pagesize=A4, leftMargin=self.M, rightMargin=self.M, topMargin=22*mm, bottomMargin=18*mm, title=self.d["title"], author=self.d.get("dept", ""))
            doc.addPageTemplates([PageTemplate(id="cover" if self.o.cover else "body", frames=[frame], onPage=self._on_cover if self.o.cover else self._on_page),
                                  PageTemplate(id="body", frames=[frame], onPage=self._on_page)])
            self.toc = []; doc.build(story())
            self.toc_pages = {(t, n): p for t, n, p in self.toc}
        return doc.page

# ---------------------------------------------------------------- 검사
def validate(d, font_paths, kind):
    errs, warn = [], []
    if not isinstance(d, dict): print("content.json이 객체({})가 아닙니다.", file=sys.stderr); sys.exit(4)
    known = {"doc_kind", "title", "subtitle", "org", "dept", "author", "date", "period", "overview", "sections", "attachments", "contact"}
    for k in d:
        if k not in known: warn.append(f"모르는 키 무시: {k}")
    if not str(d.get("title", "")).strip(): errs.append("title이 비어 있음")
    if not d.get("sections"): errs.append("sections가 비어 있음")
    if re.search(r"<[a-zA-Z/]", json.dumps(d, ensure_ascii=False)): errs.append("글 안에 <태그>가 있음. 꾸밈 태그는 쓰지 않는다")
    # 표지 폭
    W = (210 - 40 - 10) * mm
    if d.get("title"):
        lines = sum(1 for _ in wrap_count(d["title"], "B-B", 26, W));
        if lines > 2: errs.append(f"표지 제목이 {lines}줄. 2줄 안으로 줄일 것(지금 {len(d['title'])}자)")
    if d.get("subtitle") and sum(1 for _ in wrap_count(d["subtitle"], "B-R", 13, W)) > 1: errs.append(f"부제가 2줄. 1줄로 줄일 것(지금 {len(d['subtitle'])}자)")
    for i, s in enumerate(d.get("sections") or [], 1):
        if not isinstance(s, dict) or not str(s.get("title", "")).strip(): errs.append(f"sections[{i}].title 없음"); continue
        for k in s:
            if k not in {"title", "subs", "items"}: warn.append(f"sections[{i}]: 모르는 키 {k}" + (" (subs 아닌가요?)" if k in ("sub", "subsections") else ""))
        s["title"] = strip_no(str(s["title"]), warn)
        for j, sub in enumerate(s.get("subs") or [], 1):
            if not isinstance(sub, dict) or not str(sub.get("title", "")).strip(): errs.append(f"sections[{i}].subs[{j}].title 없음"); continue
            sub["title"] = strip_no(str(sub["title"]), warn); check_items(sub.get("items", []), errs, warn, f"sections[{i}].subs[{j}]")
        check_items(s.get("items", []), errs, warn, f"sections[{i}]")
    if len(d.get("sections") or []) > 15: errs.append("장이 15개를 넘음. 묶거나 나눌 것")
    # 글리프
    text = json.dumps(d, ensure_ascii=False)
    miss = missing_glyphs(text, font_paths[0])
    if miss: warn.append("글꼴에 없는 글자(□로 찍힘): " + "".join(sorted(miss))[:40])
    return errs, warn

def check_items(lst, errs, warn, where):
    if not isinstance(lst, list): errs.append(f"{where}.items가 배열이 아님"); return
    for k, it in enumerate(lst):
        if isinstance(it, str): lst[k] = strip_no(it, warn)
        elif isinstance(it, dict):
            if "table" in it:
                tb = it["table"]; n = len(tb.get("head") or (tb.get("rows") or [[]])[0])
                if n > 6: errs.append(f"{where} 표 열이 {n}개. 6개 이하로")
                if not tb.get("rows"): errs.append(f"{where} 표에 rows가 없음")
            elif "p" in it: it["p"] = str(it["p"])
            elif "text" in it:
                it["text"] = strip_no(str(it["text"]), warn); it["sub"] = [strip_no(str(x), warn) for x in it.get("sub", [])]
            else: errs.append(f"{where}.items[{k}]: text/table/p 중 하나가 있어야 함")
        else: errs.append(f"{where}.items[{k}] 형식 오류")

def wrap_count(text, font, size, width):
    line, cur = [], 0.0
    for ch in text:
        w = stringWidth(ch, font, size)
        if cur + w > width: yield line; line, cur = [], 0.0
        line.append(ch); cur += w
    yield line

def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("content", nargs="?"); ap.add_argument("--schema", action="store_true"); ap.add_argument("--pals", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pal", default="b3"); ap.add_argument("--font", default="ng", choices=list(FONTS)); ap.add_argument("--fonts-dir", default=None)
    ap.add_argument("--style", default="base", choices=["base", "light", "rich"]); ap.add_argument("--type", default="report", choices=["report", "proposal"]); ap.add_argument("-o", "--out")
    ap.add_argument("--no-cover", dest="cover", action="store_false"); ap.add_argument("--no-toc", dest="toc", action="store_false")
    ap.add_argument("--no-overview", dest="overview", action="store_false"); ap.add_argument("--no-emph", dest="emph", action="store_false")
    a = ap.parse_args()
    if a.schema: print(SCHEMA_NOTE + json.dumps(SAMPLE, ensure_ascii=False, indent=2)); return
    if a.pals: print("\n".join(f"{k}  {v['name']}" for k, v in PAL.items())); return
    if not a.content: ap.print_help(); return
    if a.pal not in PAL: log("색 id가 없음. --pals 로 목록 확인"); sys.exit(1)
    me = open(os.path.abspath(__file__), "rb").read(); log("make_doc.py sha256 " + hashlib.sha256(me).hexdigest()[:12] + " (고치지 않았는지 대조용)")
    try: d = json.load(open(a.content, encoding="utf-8"))
    except Exception as e: log(f"content.json을 읽지 못함: {e}"); sys.exit(4)
    paths = load_fonts(a.font, a.fonts_dir)
    errs, warn = validate(d, paths, a.type)
    for w in warn: log("[경고] " + w)
    if errs: log("content.json 오류 — PDF를 만들지 않았습니다:\n- " + "\n- ".join(errs)); sys.exit(4)
    if a.dry_run: log("검사 통과"); return
    out = a.out or re.sub(r"[\\/:*?\"<>|\s]+", "_", d["title"])[:40] + f"_{PAL[a.pal]['name']}_{'보고서형' if a.type=='report' else '제안서형'}.pdf"
    pages = Doc(d, PAL[a.pal], a.font, a.style, a.type, a).build(out)
    n_sec = len(d["sections"]); n_items = sum(len(s.get("items", [])) + sum(len(x.get("items", [])) for x in s.get("subs", [])) for s in d["sections"])
    log(f"완료: {out} · {pages}쪽 · 장 {n_sec}개 · 항목 {n_items}개 · 색 {PAL[a.pal]['name']} · 글꼴 {a.font}")
    try:
        import pymupdf
        pm = pymupdf.open(out); pm[min(2, len(pm)-1)].get_pixmap(dpi=60).save(out[:-4] + "_미리보기.png"); log("미리보기: " + out[:-4] + "_미리보기.png")
    except Exception: pass
    print(out)

if __name__ == "__main__":
    main()
