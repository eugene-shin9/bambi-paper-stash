#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
밤비의 서류뭉치 · 카드뉴스(1:1 1080px) 생성기  make_cards.py
  python make_cards.py --schema
  python make_cards.py content.json --pal b3 --font ng --style base [-o 폴더]
장: 표지 → 왜 → 무엇 → 언제·어떻게 → 마무리 (+ quote가 있으면 인용 장). 내용이 없는 장은 뺀다(최소 3장).
출력: 01_표지.png … 와 전체를 묶은 PDF.
"""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd())
import bambi_common as B
from PIL import Image

SAMPLE = {
  "eyebrow": "원격교육지원센터",
  "title": "K-MOOC 이수 이벤트\\n11월부터 시작",
  "stamp": "참여\\n무료",
  "why": {"title": "왜 하나요", "text": "이수율을 높이고 학습 참여 동기를 주려고 11월부터 두 달 동안 이수 이벤트를 엽니다."},
  "what": {"title": "이렇게 참여해요", "items": ["강좌 수강 후 이수", "누리집 신청서 작성", "확인 문자 받고 기프티콘 수령"]},
  "when": {"title": "언제, 어디서", "grid": [["기간", "11. 3. ~ 12. 31."], ["대상", "K-MOOC 수강생"], ["인원", "선착순 200명"], ["비용", "무료"]]},
  "closing": {"title": "기한 안에\\n꼭 신청하세요", "text": "자세한 내용은 센터 누리집에서 볼 수 있습니다.", "button": "자세히 보기", "org": "원격교육지원센터"},
  "quote": {"text": "그림을 다 그린 아이에게 먼저 물어보세요. “이건 무슨 이야기야?”", "by": "어린이 미술교육 노트", "account": "@hanbit_art_edu"}
}
NOTE = """# content.json 규칙
# - 줄바꿈이 꼭 필요한 곳만 \\n. 번호·기호는 쓰지 않는다(스크립트가 붙인다). 원문에 없는 날짜·수치·연락처를 지어내지 않는다.
# - what.items 2~4개, when.grid 2~4칸. why·what·when 중 내용 없는 것은 빼면 그 장이 빠진다(최소 3장).
# - quote는 인용 장이 필요할 때만.
"""
S = 1080; K = 2  # 2배로 그려 줄임
def px(v): return int(v*K)

class Cards:
    def __init__(self, d, C, paths, style):
        self.d, self.C, self.paths, self.style = d, C, paths, style; self.errs = []
    def new(self, bg):
        img = Image.new("RGB", (S*K, S*K), B.rgb(bg)); return img, B.Pen(img, self.paths)
    def col(self, k): return B.rgb(self.C[k])

    def cover(self):
        C, d = self.C, self.d; img, p = self.new(C["main"]); M = px(104)
        eb = B.rgb(B.head_on_dark(C)) if self.style != "light" else self.col("sub")
        if self.style == "light": img, p = self.new("FFFFFF"); fg = self.col("ink")
        else: fg = (255, 255, 255)
        p.text(M, M, d.get("eyebrow", ""), px(37), eb, "b")
        if d.get("stamp"): p.stamp(S*K - M - px(95), M + px(95), px(95), d["stamp"], eb if self.style != "light" else self.col("main"))
        lines = p.wrap(d["title"], px(82), S*K - 2*M, "h")
        if len(lines) > 3: self.errs.append(f"표지 제목이 {len(lines)}줄. 3줄 안으로"); return img
        h = len(lines)*px(82)*1.25; p.text(M, S*K - M - h, d["title"], px(82), fg, "h", S*K - 2*M, lh=1.25)
        return img

    def numbered(self, no, title, bg):
        C = self.C; img, p = self.new(bg); M = px(104)
        p.text(M, M - px(10), no, px(111), self.col("main"), "h")
        p.text(M, M + px(150), title, px(70), self.col("ink"), "h", S*K - 2*M, lh=1.2)
        return img, p, M

    def why(self):
        w = self.d["why"]; img, p, M = self.numbered("01", w.get("title", ""), self.C["tint"] if self.style != "light" else "FFFFFF")
        t = w.get("text", ""); y = M + px(330); h = p.height(t, px(46), S*K - 2*M, lh=1.55)
        if y + h > S*K - M: self.errs.append("why.text가 길어 한 장에 안 들어감. 두세 문장으로 줄이기"); return img
        p.text(M, y, t, px(46), self.col("ink"), "r", S*K - 2*M, lh=1.55)
        return img

    def what(self):
        w = self.d["what"]; img, p, M = self.numbered("02", w.get("title", ""), "FFFFFF"); items = w.get("items", [])[:4]
        y = M + px(330); gap = (S*K - M - y) / max(1, len(items)); r = px(26)
        for i, t in enumerate(items, 1):
            cy = y + gap*i - gap/2
            p.circle(M + r, cy, r, fill=self.col("main")); p.text(M + r, cy - px(13), str(i), px(24), (255, 255, 255), "b", align="center")
            hh = p.height(t, px(40), S*K - 2*M - 3*r, lh=1.3); p.text(M + 3*r, cy - hh/2, t, px(40), self.col("ink"), "r", S*K - 2*M - 3*r, lh=1.3)
        return img

    def when(self):
        w = self.d["when"]; img, p, M = self.numbered("03", w.get("title", ""), self.C["tint"] if self.style != "light" else "FFFFFF"); grid = [g for g in w.get("grid", []) if len(g) == 2][:4]
        cw = (S*K - 2*M - px(40))/2; y0 = M + px(330); rh = px(150)
        for i, (lab, val) in enumerate(grid):
            x = M + (i % 2)*(cw + px(40)); y = y0 + (i // 2)*rh
            p.text(x, y, lab, px(30), self.col("sub")); p.text(x, y + px(44), val, px(44), self.col("ink"), "b", cw, maxlines=1)
            p.line(x, y + rh - px(30), x + cw, y + rh - px(30), self.col("line"), px(2))
        return img

    def closing(self):
        w = self.d["closing"]; C = self.C; img, p = self.new("FFFFFF"); M = px(104)
        p.text(M, M, w.get("title", ""), px(70), self.col("ink"), "h", S*K - 2*M, lh=1.2)
        th = p.height(w.get("title", ""), px(70), S*K - 2*M, "h", 1.2)
        if w.get("text"): p.text(M, M + th + px(30), w["text"], px(31), self.col("sub"), "r", S*K - 2*M, lh=1.5)
        bh = px(110); by = S*K - M - px(60) - bh
        if self.style == "light": p.rect(M, by, S*K - M, by + bh, outline=self.col("main"), width=px(3), r=px(16)); tc = self.col("main")
        else: p.rect(M, by, S*K - M, by + bh, fill=self.col("main"), r=px(16)); tc = (255, 255, 255)
        p.text(S*K/2, by + (bh - px(32)*1.35)/2, w.get("button", "자세히 보기"), px(32), tc, "b", align="center")
        p.text(S*K/2, S*K - M - px(28), w.get("org", ""), px(25), self.col("sub"), align="center")
        return img

    def quote(self):
        q = self.d["quote"]; C = self.C; img, p = self.new(C["tint"]); M = px(86)
        p.text(M, px(30), "“", px(320), self.col("point"), "h")
        p.text(M, px(290), q.get("text", ""), px(76), self.col("main"), "b", S*K - M - px(108), lh=1.38, maxlines=5)
        if q.get("by"): p.line(M, S*K - px(150), M + px(75), S*K - px(150), self.col("sub"), px(4)); p.text(M + px(100), S*K - px(172), q["by"], px(36), self.col("sub"))
        if q.get("account"): p.text(M, S*K - px(100), q["account"], px(30), self.col("sub"))
        return img

    def build(self, outdir):
        d = self.d; pages = [("01_표지", self.cover)]
        if (d.get("why") or {}).get("text"): pages.append(("02_왜", self.why))
        if (d.get("what") or {}).get("items"): pages.append(("03_무엇", self.what))
        if (d.get("when") or {}).get("grid"): pages.append(("04_언제어떻게", self.when))
        pages.append(("05_마무리", self.closing))
        if (d.get("quote") or {}).get("text"): pages.append(("06_인용", self.quote))
        if len(pages) < 3: self.errs.append("장이 3장 미만. why·what·when 중 하나 이상 필요")
        imgs = []
        for name, fn in pages:
            im = fn()
            if self.errs: return []
            imgs.append((name, B.save_png(im, os.path.join(outdir, name + ".png"), K)))
        pdf = os.path.join(outdir, "카드뉴스_전체.pdf")
        imgs[0][1].save(pdf, save_all=True, append_images=[i for _, i in imgs[1:]], resolution=254)
        return [n for n, _ in imgs]

def validate(d):
    errs, warn = [], []
    if not str(d.get("title", "")).strip(): errs.append("title이 비어 있음")
    for k in ("what",):
        for it in (d.get(k) or {}).get("items", []): B.strip_no(it, warn)
    if len((d.get("what") or {}).get("items", [])) > 4: errs.append("what.items가 4개를 넘음")
    if re.search(r"<[a-zA-Z/]", json.dumps(d, ensure_ascii=False)): errs.append("글 안에 <태그>가 있음")
    return errs, warn

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("content", nargs="?"); ap.add_argument("--schema", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pal", default="b3"); ap.add_argument("--font", default="ng", choices=list(B.FONTS)); ap.add_argument("--style", default="base", choices=["base", "light", "rich"])
    ap.add_argument("--fonts-dir"); ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    if a.schema: print(NOTE + json.dumps(SAMPLE, ensure_ascii=False, indent=2)); return
    if not a.content: ap.print_help(); return
    if a.pal not in B.PAL: B.log("색 id가 없음"); sys.exit(1)
    B.log("make_cards.py sha256 " + B.self_hash(os.path.abspath(__file__)) + " (고치지 않았는지 대조용)")
    d = B.load_json(a.content); paths = B.font_paths(a.font, a.fonts_dir); errs, warn = validate(d)
    miss = B.missing_glyphs(json.dumps(d, ensure_ascii=False), paths[0])
    if miss: warn.append("글꼴에 없는 글자(□로 찍힘): " + "".join(sorted(miss))[:30])
    for w in warn: B.log("[경고] " + w)
    if errs: B.fail(errs)
    if a.dry_run: B.log("검사 통과"); return
    outdir = a.out or os.path.join(B.OUTDIR, re.sub(r"[\\/:*?\"<>|\s]+", "_", d["title"].split("\\n")[0])[:24] + f"_카드뉴스_{B.PAL[a.pal]['name']}")
    os.makedirs(outdir, exist_ok=True)
    cs = Cards(d, B.PAL[a.pal], paths, a.style); names = cs.build(outdir)
    if cs.errs: B.fail(cs.errs)
    B.log(f"완료: {outdir}/ · {len(names)}장({', '.join(names)}) + 카드뉴스_전체.pdf · 색 {B.PAL[a.pal]['name']} · 글꼴 {a.font}")
    print(outdir)

if __name__ == "__main__": main()
