#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
밤비의 서류뭉치 · 한페이지(A4 1장) 생성기  make_one.py
  python make_one.py --schema                      # content.json 예시
  python make_one.py content.json --form promo --pal b3 --font ng --style base [--illust 그림.png] -o out.pdf
  --form  promo 홍보형(모집·행사·전시, 위 색 띠) · guide 안내형(절차·공지) · schedule 일정형(타임라인) · poster 포스터형(큰 숫자)
  --pal --font --style 은 make_doc.py와 같다.  --no-emph 강조 끄기
한 장에 안 들어가면 어느 블록을 줄여야 하는지 알려 주고 만들지 않는다(글자 크기를 임의로 줄이지 않는다).
"""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd())
import bambi_common as B
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily, stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, Color

SAMPLE = {
  "form": "promo",
  "eyebrow": "2026 하반기 · 원격교육지원센터",
  "title": "K-MOOC 강좌 이수 이벤트",
  "summary": "이수율을 높이는 두 달, 참여하고 기프티콘 받으세요",
  "stamp": "참여\\n무료",
  "blocks": [
    {"type": "info2", "items": [["기간", "2026. 11. ~ 12."], ["대상", "2026학년도 2학기 K-MOOC 운영 강좌 수강생"], ["방법", "강좌 이수 후 누리집 신청서 작성"], ["혜택", "이수자 전원 기프티콘 지급"]]},
    {"type": "steps", "items": ["강좌 수강 및 이수", "누리집 신청서 작성", "확인 문자 수신 후 기프티콘 지급"]},
    {"type": "key3", "items": [["참여 강좌", "12개"], ["지급 인원", "선착순 200명"], ["마감", "12. 31.(수)"]]},
    {"type": "table", "head": ["회차", "날짜", "주제"], "rows": [["1", "11. 3.(화)", "오리엔테이션"], ["2", "11. 10.(화)", "그림책 함께 읽기"]]},
    {"type": "checklist", "items": [["신청서 제출", True], ["이수 확인", False]]},
    {"type": "timeline", "items": [["11. 3.(화)", "오리엔테이션", "과정 소개, 그림책 고르기"], ["11. 10.(화)", "함께 읽기", "소리 내어 읽기와 멈춤 질문"]], "now": 0},
    {"type": "note", "label": "유의", "text": "기프티콘은 신청서 기준으로 월말 일괄 발송"}
  ],
  "big": {"number": "12. 31.", "line": "이수 이벤트 신청\\n잊지 마세요", "grid": [["대상", "K-MOOC 수강생"], ["방법", "누리집 신청서"], ["기간", "11. 3. ~ 12. 31."], ["문의", "교육팀 000-0000"]]},
  "org": "원격교육지원센터", "contact": "교육팀 · 053-000-0000 · kmooc@example.ac.kr"
}
NOTE = """# content.json 규칙
# - form: promo(홍보형) guide(안내형) schedule(일정형) poster(포스터형). 명령줄 --form 이 우선.
# - blocks: 원문에 있는 내용으로 2~4개만. 종류: info2(라벨·값 2단) key3(핵심 3칸) steps(진행 순서) table(표, 열 4개까지)
#   checklist([항목, 체크여부]) timeline([날짜, 단계명, 설명], now=지금 단계 번호) note(라벨+한 줄)
# - 포스터형은 blocks 대신 big(number·line·grid 4칸)을 쓴다.
# - 번호("1." "①")는 쓰지 않는다. 원문에 없는 날짜·수치·연락처를 지어내지 않는다. 문의는 contact 한 줄에만.
# - 홍보형 그림(--illust)은 글자 없는 PNG. 없으면 색 띠만 쓴다.
"""

def hx(h): return HexColor("#" + h)
def alpha(h, a): r, g, b = B.rgb(h); return Color(r/255, g/255, b/255, alpha=a)

class One:
    W, H = A4; M = 15*mm; CW = A4[0] - 30*mm
    def __init__(self, d, C, style, form, paths, emph=True, illust=None):
        self.d, self.C, self.style, self.form, self.illust, self.emph = d, C, style, form, illust, emph
        pdfmetrics.registerFont(TTFont("R", paths[0])); pdfmetrics.registerFont(TTFont("B", paths[1])); pdfmetrics.registerFont(TTFont("H", paths[2]))
        registerFontFamily("R", normal="R", bold="B", italic="R", boldItalic="B")
        self.errs = []

    # ---- 글 도우미 (canvas 직접 그리기: 줄바꿈·높이 측정 가능)
    def wrap(self, text, font, size, maxw):
        out = []
        for para in str(text).replace("\\n", "↵").split("↵"):
            cur = ""
            for word in para.split(" "):
                cand = (cur + " " + word).strip() if cur else word
                if stringWidth(cand, font, size) <= maxw: cur = cand; continue
                if cur: out.append(cur); cur = ""
                if stringWidth(word, font, size) <= maxw: cur = word; continue
                for ch in word:
                    if stringWidth(cur + ch, font, size) <= maxw: cur += ch
                    else: out.append(cur); cur = ch
            out.append(cur)
        return out
    def th(self, text, font, size, maxw, lh=1.4): return len(self.wrap(text, font, size, maxw))*size*lh
    def draw(self, c, x, ytop, text, font, size, color, maxw=None, lh=1.4, align="left", emph=False):
        """ytop = 글 덩어리의 위쪽 y(아래로 자람). 반환 높이."""
        lines = self.wrap(text, font, size, maxw) if maxw else [str(text)]
        y = ytop - size
        for ln in lines:
            tw = stringWidth(ln, font, size); xx = x - tw if align == "right" else x - tw/2 if align == "center" else x
            if emph and self.emph:
                pos = 0; xx2 = xx
                for m in B.EMPH.finditer(ln):
                    pre = ln[pos:m.start()]; c.setFont(font, size); c.setFillColor(color); c.drawString(xx2, y, pre); xx2 += stringWidth(pre, font, size)
                    c.setFont("B", size); c.setFillColor(hx(self.C["main"])); c.drawString(xx2, y, m.group(0)); xx2 += stringWidth(m.group(0), "B", size); pos = m.end()
                c.setFont(font, size); c.setFillColor(color); c.drawString(xx2, y, ln[pos:])
            else:
                c.setFont(font, size); c.setFillColor(color); c.drawString(xx, y, ln)
            y -= size*lh
        return len(lines)*size*lh

    # ---- 블록: 각 블록은 (높이 측정, 그리기) 두 모드. c=None이면 높이만
    def blk_info2(self, c, b, x, y, w):
        C = self.C; items = [i for i in b.get("items", []) if len(i) == 2 and str(i[1]).strip()]
        gap = 10*mm; cw = (w - gap)/2; rows = [items[i:i+2] for i in range(0, len(items), 2)]; tot = 0
        for row in rows:
            hs = []
            for k, (lab, val) in enumerate(row):
                xx = x + k*(cw + gap); lw = stringWidth(lab, "B", 10) + 5*mm
                if c:
                    c.setFillColor(hx(C["main"])); c.roundRect(xx, y - 6*mm, lw, 6*mm, 3*mm, stroke=0, fill=1)
                    c.setFont("B", 10); c.setFillColor(white); c.drawString(xx + 2.5*mm, y - 4.3*mm, lab)
                h = self.th(val, "R", 13, cw)
                if c: self.draw(c, xx, y - 8*mm, val, "R", 13, hx(C["ink"]), cw, emph=True)
                hs.append(8*mm + h)
            tot += max(hs) + 4*mm; y -= max(hs) + 4*mm
        return tot - 4*mm

    def blk_key3(self, c, b, x, y, w):
        C = self.C; items = b.get("items", [])[:3]; n = max(1, len(items)); gap = 5*mm; cw = (w - gap*(n-1))/n
        hs = [self.th(v, "B", 13, cw - 8*mm) for _, v in items]; h = max(hs) + 16*mm
        if c:
            for k, (lab, val) in enumerate(items):
                xx = x + k*(cw + gap)
                if self.style == "light": c.setStrokeColor(hx(C["main"])); c.setLineWidth(1.2); c.line(xx, y, xx + cw, y)
                else: c.setFillColor(hx(C["tint"])); c.roundRect(xx, y - h, cw, h, 2*mm, stroke=0, fill=1)
                c.setFont("R", 11); c.setFillColor(hx(C["sub"])); c.drawString(xx + 4*mm, y - 8*mm, lab)
                self.draw(c, xx + 4*mm, y - 11*mm, val, "B", 13, hx(C["main"]), cw - 8*mm)
        return h

    def blk_steps(self, c, b, x, y, w):
        C = self.C; items = b.get("items", []); r = 3.5*mm; tot = 0
        for i, t in enumerate(items, 1):
            h = max(2*r, self.th(t, "R", 13, w - 12*mm))
            if c:
                c.setFillColor(hx(C["main"])); c.circle(x + r, y - r, r, stroke=0, fill=1)
                c.setFont("B", 10); c.setFillColor(white); c.drawCentredString(x + r, y - r - 3.5, str(i))
                self.draw(c, x + 2*r + 4*mm, y - (r - 6.5), t, "R", 13, hx(C["ink"]), w - 12*mm, emph=True)
            y -= h + 4*mm; tot += h + 4*mm
        return tot - 4*mm

    def blk_table(self, c, b, x, y, w):
        C = self.C; head = [str(h) for h in b.get("head", [])]; rows = [[str(v) for v in r] for r in b.get("rows", [])]; n = len(head) or len(rows[0])
        colw = b.get("colw"); ws = [w*cc/sum(colw) for cc in colw] if colw and len(colw) == n else [w/n]*n
        NUM = re.compile(r"^[\d,.\s~()월화수목금토일\-–]+$")
        numcol = [i > 0 and all(NUM.match(r[i].strip()) for r in rows if i < len(r) and r[i].strip()) for i in range(n)]
        rh = 8*mm; tot = 0
        def row(vals, yy, font, color, bold_line):
            xx = x
            for i, v in enumerate(vals[:n]):
                if c:
                    c.setFont(font, 12 if font == "R" else 11); c.setFillColor(color)
                    if numcol[i] and i > 0: c.drawRightString(xx + ws[i] - 1.5*mm, yy - rh + 2.7*mm, v)
                    else: c.drawString(xx + (0 if i == 0 else 1.5*mm), yy - rh + 2.7*mm, v)
                xx += ws[i]
            if c:
                c.setStrokeColor(hx(C["main"]) if bold_line else hx(C["line"])); c.setLineWidth(1.2 if bold_line else 0.5); c.line(x, yy - rh, x + w, yy - rh)
        if head: row(head, y, "B", hx(C["main"]), True); y -= rh; tot += rh
        for r in rows: row(r, y, "R", hx(C["ink"]), False); y -= rh; tot += rh
        return tot

    def blk_checklist(self, c, b, x, y, w):
        C = self.C; items = b.get("items", []); s = 7*mm; tot = 0
        for it in items:
            t, on = (it[0], bool(it[1])) if isinstance(it, list) else (str(it), False)
            if c:
                c.setStrokeColor(hx(C["main"])); c.setLineWidth(1.2)
                if on: c.setFillColor(hx(C["main"])); c.roundRect(x, y - s, s, s, 1*mm, stroke=0, fill=1); c.setStrokeColor(white); c.setLineWidth(1.6); c.line(x + 1.8*mm, y - s/2, x + 3.1*mm, y - s + 1.8*mm); c.line(x + 3.1*mm, y - s + 1.8*mm, x + 5.4*mm, y - 1.8*mm)
                else: c.roundRect(x, y - s, s, s, 1*mm, stroke=1, fill=0)
                self.draw(c, x + s + 4*mm, y - 0.6*mm, t, "R", 15, hx(C["ink"]), w - s - 4*mm, emph=True)
            y -= s + 4*mm; tot += s + 4*mm
        return tot - 4*mm

    def blk_timeline(self, c, b, x, y, w):
        C = self.C; items = b.get("items", []); now = b.get("now", 0); r = 2.5*mm; lx = x + r; tx = x + 2*r + 5*mm; tw = w - (tx - x); tot = 0; y0 = y
        hs = [6*mm + 8*mm + self.th(it[2], "R", 12, tw) if len(it) > 2 and it[2] else 6*mm + 8*mm for it in items]
        if c: c.setStrokeColor(hx(C["line"])); c.setLineWidth(0.8); c.line(lx, y - r, lx, y - sum(hs) - 6*mm*(len(items)-1) + 8*mm)
        for i, it in enumerate(items):
            date, name, desc = (it + ["", ""])[:3]
            if c:
                c.setStrokeColor(hx(C["main"])); c.setLineWidth(1.2); c.setFillColor(hx(C["main"]) if i == now else white); c.circle(lx, y - r - 1*mm, r, stroke=1, fill=1)
                c.setFont("B", 12); c.setFillColor(hx(C["sub"])); c.drawString(tx, y - 4.3*mm, date)
                c.setFont("B", 17); c.setFillColor(hx(C["ink"])); c.drawString(tx, y - 11.5*mm, name)
                if desc: self.draw(c, tx, y - 14*mm, desc, "R", 12, hx(C["sub"]), tw)
            y -= hs[i] + 6*mm; tot += hs[i] + 6*mm
        return tot - 6*mm

    def blk_note(self, c, b, x, y, w):
        C = self.C; lab = b.get("label", ""); t = b.get("text", ""); lw = (stringWidth(lab, "B", 11) + 6*mm) if lab else 0
        h = max(10*mm, self.th(t, "R", 12, w - lw - 8*mm) + 5*mm)
        if c:
            c.setFillColor(hx(C["tint"]) if self.style != "light" else white); c.setStrokeColor(hx(C["line"])); c.setLineWidth(0.5); c.roundRect(x, y - h, w, h, 2*mm, stroke=1 if self.style == "light" else 0, fill=1)
            if lab: c.setFont("B", 11); c.setFillColor(hx(C["main"])); c.drawString(x + 4*mm, y - h/2 - 3.5, lab)
            self.draw(c, x + 4*mm + lw, y - (h - self.th(t, "R", 12, w - lw - 8*mm))/2 + 1.5, t, "R", 12, hx(C["ink"]), w - lw - 8*mm, emph=True)
        return h

    def blocks(self, c, x, y, w, maxh):
        """블록을 위에서 아래로. 반환 총 높이. 넘치면 errs에 기록."""
        fn = dict(info2=self.blk_info2, key3=self.blk_key3, steps=self.blk_steps, table=self.blk_table, checklist=self.blk_checklist, timeline=self.blk_timeline, note=self.blk_note)
        tot = 0; names = []
        for b in self.d.get("blocks", []):
            f = fn.get(b.get("type"))
            if not f: self.errs.append(f"모르는 블록 종류: {b.get('type')}"); continue
            h = f(c, b, x, y - tot, w); names.append(b["type"]); tot += h + 8*mm
        tot -= 8*mm
        if tot > maxh and c is None:
            self.errs.append(f"본문 블록이 {tot/mm:.0f}mm로 지면({maxh/mm:.0f}mm)을 넘칩니다. 블록({'·'.join(names)}) 중 하나를 빼거나 글을 줄이세요.")
        return tot

    def contact(self, c):
        C = self.C; y = self.M + 4*mm
        c.setStrokeColor(hx(C["line"])); c.setLineWidth(0.5); c.line(self.M, y + 4.5*mm, self.W - self.M, y + 4.5*mm)
        c.setFont("B", 10); c.setFillColor(hx(C["ink"])); c.drawString(self.M, y, self.d.get("org", ""))
        c.setFont("R", 10); c.setFillColor(B_gray(C)); c.drawRightString(self.W - self.M, y, self.d.get("contact", ""))

    # ---- 양식
    def render(self, out):
        c = canvas.Canvas(out, pagesize=A4); c.setTitle(self.d.get("title", "")); C = self.C; M, W, H, CW = self.M, self.W, self.H, self.CW
        light = self.style == "light"; d = self.d
        if self.form == "promo":
            bh = 90*mm; top = H - M
            if not light: c.setFillColor(hx(C["main"])); c.rect(M, top - bh, CW, bh, stroke=0, fill=1)
            if self.illust and os.path.exists(self.illust):
                try: c.drawImage(self.illust, M + CW*0.55, top - bh, CW*0.45, bh, preserveAspectRatio=True, anchor="c", mask="auto")
                except Exception as e: self.errs.append(f"그림을 넣지 못함: {e}")
            fg = white if not light else hx(C["ink"]); eb = hx(B.head_on_dark(C)) if not light else hx(C["sub"])
            c.setFont("B", 16); c.setFillColor(eb); c.drawString(M + 10*mm, top - 14*mm, d.get("eyebrow", ""))
            th = self.draw(c, M + 10*mm, top - 22*mm, d.get("title", ""), "H", 34, fg, CW*0.55 - 10*mm, lh=1.25)
            if d.get("summary"): self.draw(c, M + 10*mm, top - 24*mm - th, d["summary"], "R", 13, fg if not light else hx(C["sub"]), CW*0.55 - 10*mm)
            if d.get("stamp") and not self.illust:
                stamp(c, M + CW - 28*mm, top - 26*mm, 17*mm, d["stamp"], eb if not light else hx(C["main"]))
            py = top - bh - 8*mm; pad = 10*mm; avail = py - (M + 12*mm) - pad*2
            ph = self.blocks(None, M + pad, py - pad, CW - 2*pad, avail)
            if self.errs: return
            if not light: c.setFillColor(white); c.setStrokeColor(hx(C["line"])); c.setLineWidth(0.5); c.roundRect(M, M + 12*mm, CW, py - (M + 12*mm), 3*mm, stroke=1, fill=1)
            self.blocks(c, M + pad, py - pad, CW - 2*pad, avail)
        elif self.form in ("guide", "schedule"):
            top = H - M - 4*mm
            c.setFont("B", 15); c.setFillColor(hx(C["sub"])); c.drawString(M, top - 5*mm, d.get("eyebrow", ""))
            th = self.draw(c, M, top - 9*mm, d.get("title", ""), "H", 32, hx(C["ink"]), CW, lh=1.25)
            y = top - 11*mm - th
            if d.get("summary"): y -= self.draw(c, M, y, d["summary"], "R", 13, hx(C["sub"]), CW) + 2*mm
            if d.get("stamp"): stamp(c, W - M - 17*mm, top - 15*mm, 15*mm, d["stamp"], hx(C["main"]))
            c.setStrokeColor(hx(C["main"])); c.setLineWidth(1.2); c.line(M, y - 3*mm, M + CW, y - 3*mm); y -= 12*mm
            avail = y - (M + 12*mm)
            self.blocks(None, M, y, CW, avail)
            if self.errs: return
            self.blocks(c, M, y, CW, avail)
        elif self.form == "poster":
            big = d.get("big") or {}
            if not light: c.setFillColor(hx(C["main"])); c.rect(0, 0, W, H, stroke=0, fill=1)
            eb = hx(C["tint"]) if not light else hx(C["sub"]); fg = white if not light else hx(C["ink"]); numc = hx(B.head_on_dark(C)) if not light else hx(C["main"])
            c.setFont("B", 15); c.setFillColor(eb); c.drawString(M + 5*mm, H - M - 12*mm, d.get("eyebrow", ""))
            n = str(big.get("number", "")); avail = CW - 10*mm - (42*mm if d.get("stamp") else 0); sz = 140
            while sz > 60 and stringWidth(n, "H", sz) > avail: sz -= 10
            if stringWidth(n, "H", sz) > avail: self.errs.append(f"큰 숫자 '{n}'가 너무 깁니다. 8자 이내로 줄이세요"); return
            c.setFont("H", sz); c.setFillColor(numc); c.drawString(M + 5*mm, H - M - 30*mm - sz*0.72, n)
            self.draw(c, M + 5*mm, H - M - 40*mm - sz*0.72, big.get("line", ""), "H", 38, fg, CW - 10*mm, lh=1.25)
            grid = [g for g in big.get("grid", []) if len(g) == 2][:4]; gw = (CW - 10*mm - 10*mm)/2; gy = M + 20*mm + 2*22*mm
            for i, (lab, val) in enumerate(grid):
                xx = M + 5*mm + (i % 2)*(gw + 10*mm); yy = gy - (i // 2)*22*mm
                c.setFont("R", 12); c.setFillColor(eb); c.drawString(xx, yy, lab)
                c.setFont("B", 15); c.setFillColor(fg); c.drawString(xx, yy - 7*mm, val)
                c.setStrokeColor(alpha("FFFFFF", .3) if not light else hx(C["line"])); c.setLineWidth(0.5); c.line(xx, yy - 11*mm, xx + gw, yy - 11*mm)
            if d.get("stamp"): stamp(c, W - M - 22*mm, H - M - 22*mm, 17*mm, d["stamp"], numc)
            c.showPage(); c.save(); return
        self.contact(c); c.showPage(); c.save()

def B_gray(C): return alpha(C["ink"], .7)
def stamp(c, cx, cy, r, text, color):
    c.saveState(); c.translate(cx, cy); c.rotate(-9); c.setStrokeColor(color); c.setFillColor(color)
    c.setLineWidth(r*0.07); c.circle(0, 0, r, stroke=1, fill=0); c.setLineWidth(r*0.025); c.circle(0, 0, r*0.84, stroke=1, fill=0)
    lines = str(text).replace("\\n", "↵").split("↵")[:2]; sz = r*0.42; yy = (len(lines)-1)*sz*0.6
    for ln in lines: c.setFont("B", sz); c.drawCentredString(0, yy - sz*0.35, ln); yy -= sz*1.15
    c.restoreState()

def validate(d, form):
    errs, warn = [], []
    if not str(d.get("title", "")).strip() and form != "poster": errs.append("title이 비어 있음")
    if form == "poster" and not (d.get("big") or {}).get("number"): errs.append("포스터형은 big.number(큰 숫자)가 필요")
    if form != "poster" and not d.get("blocks"): errs.append("blocks가 비어 있음(2~4개)")
    if form != "poster" and len(d.get("blocks", [])) > 4: errs.append("블록이 4개를 넘음(2~4개)")
    for b in d.get("blocks", []):
        if b.get("type") == "table" and len(b.get("head", [])) > 4: errs.append("표 열이 4개를 넘음")
        for k in ("items", "rows"):
            for it in b.get(k, []) or []:
                if isinstance(it, str): B.strip_no(it, warn)
    if re.search(r"<[a-zA-Z/]", json.dumps(d, ensure_ascii=False)): errs.append("글 안에 <태그>가 있음")
    return errs, warn

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("content", nargs="?"); ap.add_argument("--schema", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--form", default=None, choices=["promo", "guide", "schedule", "poster"]); ap.add_argument("--pal", default="b3"); ap.add_argument("--font", default="ng", choices=list(B.FONTS))
    ap.add_argument("--style", default="base", choices=["base", "light", "rich"]); ap.add_argument("--illust", default=None); ap.add_argument("--fonts-dir", default=None); ap.add_argument("--no-emph", dest="emph", action="store_false"); ap.add_argument("-o", "--out")
    a = ap.parse_args()
    if a.schema: print(NOTE + json.dumps(SAMPLE, ensure_ascii=False, indent=2)); return
    if not a.content: ap.print_help(); return
    if a.pal not in B.PAL: B.log("색 id가 없음"); sys.exit(1)
    B.log("make_one.py sha256 " + B.self_hash(os.path.abspath(__file__)) + " (고치지 않았는지 대조용)")
    d = B.load_json(a.content); form = a.form or d.get("form") or "promo"
    paths = B.font_paths(a.font, a.fonts_dir); errs, warn = validate(d, form)
    for w in warn: B.log("[경고] " + w)
    if errs: B.fail(errs)
    if a.dry_run: B.log("검사 통과"); return
    FN = dict(promo="홍보형", guide="안내형", schedule="일정형", poster="포스터형")
    out = a.out or re.sub(r"[\\/:*?\"<>|\s]+", "_", d.get("title") or (d.get("big") or {}).get("number", "한페이지"))[:30] + f"_{B.PAL[a.pal]['name']}_{FN[form]}.pdf"
    one = One(d, B.PAL[a.pal], a.style, form, paths, a.emph, a.illust); one.render(out)
    if one.errs: B.fail(one.errs)
    B.log(f"완료: {out} · 1쪽 · {FN[form]} · 블록 {len(d.get('blocks', []))}개 · 색 {B.PAL[a.pal]['name']} · 글꼴 {a.font}")
    try:
        import pymupdf; pymupdf.open(out)[0].get_pixmap(dpi=72).save(out[:-4] + "_미리보기.png"); B.log("미리보기: " + out[:-4] + "_미리보기.png")
    except Exception: pass
    print(out)

if __name__ == "__main__": main()
