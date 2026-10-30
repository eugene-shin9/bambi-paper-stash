#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
밤비의 서류뭉치 · 홍보물·서식 9종 생성기  make_promo.py
  python make_promo.py --schema poster          # 종류별 content.json 예시
  python make_promo.py content.json --kind poster --pal b3 --font pg [--logo 로고.png] -o 폴더
종류(--kind): poster 공연·전시 포스터(A4) · story 행사 스토리(9:16) · sale 할인 게시물(1:1) · deck 발표 표지(16:9) · flyer 개업 전단(A4)
             invite 초대장(5:7) · thumb 썸네일(16:9) · resume 이력서(A4) · card 명함 앞·뒤
출력: PNG(+ 인쇄 크기는 PDF). 배치·색·글꼴은 고정. 글은 content.json의 값만 쓴다.
"""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd())
import bambi_common as B
from PIL import Image

K = 2
SIZES = dict(poster=(2480, 3508), story=(1080, 1920), sale=(1080, 1080), deck=(1920, 1080), flyer=(2480, 3508), invite=(1500, 2100), thumb=(1280, 720), resume=(2480, 3508), card=(1063, 591), quote=(1080, 1080))
PDF_MM = dict(poster=(210, 297), flyer=(210, 297), invite=(127, 178), resume=(210, 297), card=(90, 50))
SAMPLES = {
 "poster": {"eyebrow": "2026 가을 어린이 기획전", "title": "그림책\\n속\\n옷장", "sub": "그림책 주인공들이 입은 옷을 직접 만져 보고, 내 옷을 그려 보는 체험 전시입니다.", "stamp": "무료\\n관람",
            "info": [["기간", "11.01 토 – 11.30 일"], ["시간", "10:00 – 18:00 (월 휴관)"], ["장소", "한빛어린이미술관 2층 기획전시실"], ["대상", "5세 – 초등 3학년과 보호자"]], "org": "한빛어린이미술관", "contact": "교육팀 053-000-0000"},
 "story": {"top": "가을 그림책 축제", "date": "11.08", "day": "토요일 오전 10시", "title": "읽고, 그리고,\\n입어 보는 하루", "items": [["10:00", "그림책 함께 읽기"], ["11:30", "주인공 옷 그리기"], ["14:00", "종이 옷 패션쇼"]], "cta": "신청은 프로필 링크에서", "org": "한빛어린이도서관 · 선착순 40명"},
 "sale": {"tag": "가을 신상 입고", "big": "30", "unit": "%", "title": "니트·가디건 전 품목", "when": "10.25 토 – 11.03 월", "stamp": "매장\\n한정", "shop": "한빛옷방 동성로점", "account": "@hanbit_closet"},
 "deck": {"eyebrow": "교육팀 사업 보고", "title": "2027 어린이 미술교육\\n운영 계획", "sub": "학기별 프로그램 4종, 학교 연계 12회, 가족 체험 6회 운영안", "who": "교육기획 담당 · 2026.11.12", "stamp": "교육팀\\n보고", "no": "01 / 18"},
 "flyer": {"k": "새로 문을 엽니다", "name": "한빛옷방", "open_label": "오픈 날짜", "open": "11.15 토", "stamp": "오픈\\n기념", "perks": [["20%", "첫 구매 할인"], ["1+1", "양말 선착순 50명"], ["무료", "바지 기장 수선"]],
           "where": [["오는 길", ["대구 중구 동성로 00길 12, 1층", "중앙로역 2번 출구 도보 4분"]], ["영업 시간", ["매일 11:00 – 21:00", "매주 화요일 휴무"]]], "org": "한빛옷방", "contact": "053-000-0000 · @hanbit_closet"},
 "invite": {"k": "INVITATION", "title": "개관 10주년\\n기념식", "msg": "지난 10년을 함께해 주신 분들을\\n작은 자리에 모시고자 합니다.", "info": [["일시", "2026.12.05 토 오후 3시"], ["장소", "한빛어린이미술관 1층 로비"], ["회신", "11.28까지 053-000-0000"]], "host": "한빛어린이미술관장"},
 "thumb": {"title": "아이 그림,\\n**이렇게** 물어보면\\n이야기가 나와요", "num": "5", "num_label": "가지 질문", "sub": "미술교육 연구자의 집에서 하는 대화법"},
 "resume": {"name": "정다온", "role": "교육기획 · 미술교육 연구", "contacts": ["010-0000-0000", "daon@example.com", "대구 수성구"],
            "left": [["학력", [["교육학 박사 수료", "한빛대학교 대학원 · 2024"], ["미술교육 석사", "한빛대학교 대학원 · 2019"]]], ["자격", [["정교사 2급(미술)", "2015"], ["평생교육사 2급", "2020"]]], ["할 줄 아는 것", [["교육과정 설계 · 교재 개발 · 전시 연계 프로그램 · 한글/PPT", ""]]]],
            "right": [["경력", [["2022 – 현재", "한빛어린이미술관 교육팀", "전시 연계 어린이 프로그램 기획·운영, 연 48회"], ["2019 – 2022", "한빛대학교 미술교육연구소", "연구원 · 유아 미술 활동 평가 도구 개발"]]], ["대표 성과", [["2025", "", "가족 체험 프로그램 참여 만족도 4.7점(5점 만점)"]]]]},
 "quote": {"text": "그림을 다 그린 아이에게 먼저 물어보세요.\n“이건 무슨 이야기야?”", "by": "어린이 미술교육 노트", "account": "@hanbit_art_edu"},
 "card": {"name": "정다온", "title": "교육팀 · 교육기획", "info": ["053-000-0000 · 010-0000-0000", "daon@example.com", "대구 중구 동성로 00길 12"], "stamp": "한빛", "back_stamp": "한빛\\n미술관", "en": "HANBIT CHILDREN'S ART MUSEUM", "org": "한빛어린이미술관"}
}
NOTE = "# 줄바꿈은 \\n. 썸네일 제목의 **강조**만 형광 표시. 원문에 없는 값은 지어내지 않고 \"\"로 둔다. --logo 를 주면 명함 도장 자리에 로고가 들어간다(원본 그대로).\n"

class Promo:
    def __init__(self, kind, d, C, paths, logo=None):
        self.kind, self.d, self.C, self.paths, self.logo = kind, d, C, paths, logo; self.errs = []
        self.W, self.H = SIZES[kind]
    def new(self, bg, size=None):
        W, H = size or (self.W, self.H); img = Image.new("RGB", (W*K, H*K), B.rgb(bg) if isinstance(bg, str) else bg); return img, B.Pen(img, self.paths)
    def c(self, k): return B.rgb(self.C[k])
    def wh(self, a): return (255, 255, 255)
    def mixw(self, t): return B.mix("FFFFFF", self.C["main"], t)
    def u(self, pct, axis="w"): return (self.W if axis == "w" else self.H)*pct/100*K   # 폭(%) 단위 → px

    def poster(self):
        d, C = self.d, self.C; img, p = self.new(C["tint"]); u = self.u; W, H = self.W*K, self.H*K
        p.text(u(8), u(8), d.get("eyebrow", ""), u(2.8), self.c("sub"), "b", spacing=u(.1))
        p.text(u(8), u(15), d.get("title", ""), u(17), self.c("main"), "h", u(80), lh=1.02)
        p.text(u(8), u(74), d.get("sub", ""), u(3.3), self.c("ink"), "r", u(60), lh=1.4)
        if d.get("stamp"): p.stamp(W - u(8) - u(11), u(9) + u(11), u(11), d["stamp"], self.c("point"))
        p.rect(0, u(92), W, H, fill=self.c("main"))
        y = u(99)
        for lab, val in d.get("info", [])[:5]:
            p.text(u(8), y, lab, u(3.4), self.mixw(.65), "b"); p.text(u(30), y, val, u(3.4), (255, 255, 255), "b"); y += u(3.4)*1.35 + u(3.2)
        p.line(u(8), H - u(6) - u(3.6), W - u(8), H - u(6) - u(3.6), self.mixw(.3), max(2, int(u(.25))))
        p.text(u(8), H - u(6) - u(3), d.get("org", ""), u(2.3), self.mixw(.75)); p.text(W - u(8), H - u(6) - u(3), d.get("contact", ""), u(2.3), self.mixw(.75), align="right")
        return [("포스터", img)]

    def story(self):
        d, C = self.d, self.C; img, p = self.new(C["main"]); u = self.u; W, H = self.W*K, self.H*K
        p.text(u(9), u(12), d.get("top", ""), u(4), self.mixw(.7), "b")
        p.text(u(9), u(22), d.get("date", ""), u(30), (255, 255, 255), "h", lh=.95, spacing=-u(1.5))
        p.text(u(9), u(52), d.get("day", ""), u(6), self.c("point"), "b")
        p.text(u(9), u(70), d.get("title", ""), u(10), (255, 255, 255), "h", W - 2*u(9), lh=1.12)
        y = u(104)
        for t, v in d.get("items", [])[:5]:
            p.text(u(9), y, t, u(4.4), self.c("point"), "b"); p.text(u(26), y, v, u(4.4), (255, 255, 255))
            p.line(u(9), y + u(4.4)*1.35 + u(3.4), W - u(9), y + u(4.4)*1.35 + u(3.4), self.mixw(.22), max(2, int(u(.3)))); y += u(4.4)*1.35 + u(3.4)*2
        bh = u(4.6)*1.35 + 2*u(4); by = H - u(14) - bh
        p.rect(u(9), by, W - u(9), by + bh, fill=(255, 255, 255), r=int(bh/2)); p.text(W/2, by + u(4), d.get("cta", ""), u(4.6), self.c("main"), "b", align="center")
        p.text(W/2, H - u(6) - u(3.4)*1.35, d.get("org", ""), u(3.4), self.mixw(.65), align="center")
        return [("스토리", img)]

    def sale(self):
        d, C = self.d, self.C; img, p = self.new("FFFFFF"); u = self.u; W, H = self.W*K, self.H*K
        p.rect(0, 0, W, u(4), fill=self.c("point"))
        tag = d.get("tag", ""); tw = p.width(tag, u(4), "b"); p.rect(u(8), u(12), u(8) + tw + 2*u(3), u(12) + u(4)*1.35 + 2*u(1.2), outline=self.c("main"), width=max(2, int(u(.5))), r=int(u(4))); p.text(u(8) + u(3), u(12) + u(1.2), tag, u(4), self.c("main"), "b")
        big = d.get("big", ""); p.text(u(6.5), u(22), big, u(36), self.c("main"), "h", lh=1, spacing=-u(2)); bw = p.width(big, u(36), "h") - u(2)*(len(big)-1)
        p.text(u(6.5) + bw + u(1), u(22) + u(36)*0.62 - u(13.7), d.get("unit", ""), u(13.7), self.c("main"), "h", lh=1)
        p.text(u(8), u(63), d.get("title", ""), u(7.4), self.c("ink"), "h", u(60), maxlines=2, lh=1.15)
        p.text(u(8), u(74), d.get("when", ""), u(4), self.c("sub"))
        if d.get("stamp"): p.stamp(W - u(8) - u(12), u(58) + u(12), u(12), d["stamp"], self.c("point"))
        p.line(u(8), H - u(7) - u(3.2)*1.35 - u(2.6), W - u(8), H - u(7) - u(3.2)*1.35 - u(2.6), self.c("line"), max(2, int(u(.3))))
        p.text(u(8), H - u(7) - u(3.2)*1.35, d.get("shop", ""), u(3.2), self.c("sub")); p.text(W - u(8), H - u(7) - u(3.2)*1.35, d.get("account", ""), u(3.2), self.c("sub"), align="right")
        return [("할인게시물", img)]

    def deck(self):
        d, C = self.d, self.C; img, p = self.new("FFFFFF"); u = self.u; W, H = self.W*K, self.H*K
        p.rect(W - u(34), 0, W, H, fill=self.c("main"))
        p.text(u(6), u(7), d.get("eyebrow", ""), u(1.9), self.c("sub"), "b")
        p.text(u(6), u(16), d.get("title", ""), u(5.4), self.c("main"), "h", u(52), lh=1.2)
        p.text(u(6), u(36), d.get("sub", ""), u(2.1), self.c("ink"), "r", u(50))
        p.rect(u(6), H - u(6) - u(1.8)*1.5, u(6) + u(.5), H - u(6), fill=self.c("point")); p.text(u(6) + u(.5) + u(1.6), H - u(6) - u(1.8)*1.5, d.get("who", ""), u(1.8), self.c("sub"), lh=1.5)
        if d.get("stamp"): p.stamp(W - u(34) + u(7) + u(10), u(7) + u(10), u(10), d["stamp"], self.mixw(.8))
        p.text(W - u(34) + u(7), H - u(6) - u(1.9)*1.35, d.get("no", ""), u(1.9), self.mixw(.7))
        return [("발표표지", img)]

    def flyer(self):
        d, C = self.d, self.C; img, p = self.new("FFFFFF"); u = self.u; W, H = self.W*K, self.H*K
        p.rect(0, 0, W, u(30), fill=self.c("main")); p.text(u(8), u(8), d.get("k", ""), u(3.4), self.c("point"), "b"); p.text(u(8), u(8) + u(3.4)*1.35 + u(1), d.get("name", ""), u(11), (255, 255, 255), "h", lh=1.05, spacing=-u(.4))
        p.text(u(8), u(38), d.get("open_label", ""), u(4), self.c("sub")); p.text(u(8), u(38) + u(4)*1.35, d.get("open", ""), u(9), self.c("main"), "h", lh=1.1, spacing=-u(.25))
        if d.get("stamp"): p.stamp(W - u(8) - u(11.5), u(36) + u(11.5), u(11.5), d["stamp"], self.c("point"))
        perks = d.get("perks", [])[:3]; n = max(1, len(perks)); pw = (W - 2*u(8) - u(3)*(n-1))/n
        for i, (b, t) in enumerate(perks):
            x = u(8) + i*(pw + u(3)); p.rect(x, u(68), x + pw, u(68) + u(18), fill=self.c("tint"))
            p.text(x + u(3), u(68) + u(4), b, u(6), self.c("main"), "h"); p.text(x + u(3), u(68) + u(4) + u(6)*1.35 + u(1.2), t, u(3), self.c("ink"), "r", pw - 2*u(3))
        wh = d.get("where", [])[:2]; cw = (W - 2*u(8) - u(4))/2
        for i, (lab, lines) in enumerate(wh):
            x = u(8) + i*(cw + u(4)); p.line(x, u(104), x + cw, u(104), self.c("main"), max(2, int(u(.6)))); p.text(x, u(104) + u(2.5), lab, u(2.6), self.c("sub"), "b", spacing=u(.1))
            y = u(104) + u(2.5) + u(2.6)*1.35 + u(1)
            for ln in lines[:3]: y += p.text(x, y, ln, u(3.1), self.c("ink"), "r", cw)
        p.line(u(8), H - u(6) - u(2.3)*1.35 - u(2.4), W - u(8), H - u(6) - u(2.3)*1.35 - u(2.4), self.c("line"), max(2, int(u(.25))))
        p.text(u(8), H - u(6) - u(2.3)*1.35, d.get("org", ""), u(2.3), self.c("sub")); p.text(W - u(8), H - u(6) - u(2.3)*1.35, d.get("contact", ""), u(2.3), self.c("sub"), align="right")
        return [("전단", img)]

    def invite(self):
        d, C = self.d, self.C; img, p = self.new(C["tint"]); u = self.u; W, H = self.W*K, self.H*K
        p.rect(u(5), u(5), W - u(5), H - u(5), outline=self.c("main"), width=max(2, int(u(.4)))); p.rect(u(6.6), u(6.6), W - u(6.6), H - u(6.6), outline=self.c("main"), width=max(1, int(u(.2))))
        y = u(14); y += p.text(W/2, y, d.get("k", ""), u(3.2), self.c("sub"), "b", align="center", spacing=u(.96)) + u(6)
        y += p.text(W/2, y, d.get("title", ""), u(8.4), self.c("main"), "h", W - 2*u(13), lh=1.25, align="center") + u(6)
        y += p.text(W/2, y, d.get("msg", ""), u(3.5), self.c("ink"), "r", W - 2*u(13), lh=1.7, align="center") + u(7)
        p.circle(W/2, y + u(1), u(1), fill=self.c("point")); y += u(2) + u(7)
        info = d.get("info", [])[:4]; lw = max([p.width(k, u(3.4), "b") for k, _ in info] + [0]) + u(4); tw = lw + max([p.width(v, u(3.4)) for _, v in info] + [0]); x0 = W/2 - tw/2
        for k, v in info:
            p.text(x0, y, k, u(3.4), self.c("sub"), "b"); p.text(x0 + lw, y, v, u(3.4), self.c("ink")); y += u(3.4)*1.35 + u(2.4)
        p.text(W/2, H - u(13) - u(3.4)*1.35, d.get("host", ""), u(3.4), self.c("main"), "b", align="center")
        return [("초대장", img)]

    def thumb(self):
        d, C = self.d, self.C; img, p = self.new(C["ink"]); u = self.u; W, H = self.W*K, self.H*K
        sz = u(8.6); y = u(12); lh = 1.18
        for ln in str(d.get("title", "")).replace("\\n", "↵").split("↵")[:3]:
            x = u(6); parts = re.split(r"(\*\*[^*]+\*\*)", ln)
            for part in parts:
                if not part: continue
                m = part.startswith("**"); t = part.strip("*"); w = p.width(t, sz, "h") - u(.35)*(len(t)-1)
                if m: p.rect(x - u(.6), y + sz*(lh-1)/2, x + w + u(.6), y + sz*(lh-1)/2 + sz*1.05, fill=self.c("point"))
                p.text(x, y, t, sz, self.c("ink") if m else (255, 255, 255), "h", spacing=-u(.35)); x += w
            y += sz*lh
        r = u(14); cx, cy = W - u(6) - r, H/2; p.circle(cx, cy, r, fill=self.c("main"))
        p.text(cx, cy - u(12)*0.75, d.get("num", ""), u(12), (255, 255, 255), "h", align="center", lh=1); p.text(cx, cy + u(12)*0.4, d.get("num_label", ""), u(3), self.mixw(.75), align="center")
        p.text(u(6), H - u(8) - u(2.6)*1.35, d.get("sub", ""), u(2.6), B.mix("FFFFFF", self.C["ink"], .7))
        return [("썸네일", img)]

    def resume(self):
        d, C = self.d, self.C; img, p = self.new("FFFFFF"); u = self.u; W, H = self.W*K, self.H*K
        y = u(8); y += p.text(u(8), y, d.get("name", ""), u(7.4), self.c("main"), "h", lh=1.2) + u(.5)
        y += p.text(u(8), y, d.get("role", ""), u(3.2), self.c("sub")) + u(2.6)
        x = u(8)
        for ct in d.get("contacts", [])[:4]: p.text(x, y, ct, u(2.5), self.c("ink")); x += p.width(ct, u(2.5)) + u(4)
        y += u(2.5)*1.35 + u(4); p.line(u(8), y, W - u(8), y, self.c("main"), max(2, int(u(.6)))); y0 = u(40)
        def section(x, y, title, w):
            p.text(x, y, title, u(2.6), self.c("main"), "b", spacing=u(.2)); return y + u(2.6)*1.35 + u(2)
        yl = y0; xl = u(8); wl = u(30)
        for title, items in d.get("left", []):
            yl = section(xl, yl, title, wl)
            for it in items:
                yl += p.text(xl, yl, it[0], u(2.5), self.c("ink"), "r", wl, lh=1.5)
                if len(it) > 1 and it[1]: yl += p.text(xl, yl, it[1], u(2.2), self.c("sub"), "r", wl, lh=1.5)
                yl += u(2.2)
            yl += u(4)
        yr = y0; xr = u(8) + wl + u(6); wr = W - u(8) - xr
        for si, (title, items) in enumerate(d.get("right", [])):
            if si: p.line(xr, yr + u(1), W - u(8), yr + u(1), self.c("line"), max(1, int(u(.25)))); yr += u(4)
            yr = section(xr, yr, title, wr)
            for it in items:
                when, org, desc = (list(it) + ["", "", ""])[:3]; p.text(xr, yr, when, u(2.2), self.c("sub"), lh=1.5); yy = yr
                if org: yy += p.text(xr + u(15), yy, org, u(2.7), self.c("ink"), "b", wr - u(15), lh=1.5)
                if desc: yy += p.text(xr + u(15), yy, desc, u(2.5), self.c("ink"), "r", wr - u(15), lh=1.5)
                yr = max(yy, yr + u(2.2)*1.5) + u(3.6)
            yr += u(2.4)
        if max(yl, yr) > H - u(8): self.errs.append("이력서 내용이 한 장을 넘칩니다. 항목을 줄이세요")
        return [("이력서", img)]

    def quote(self):
        d, C = self.d, self.C; img, p = self.new(C["tint"]); u = self.u; W, H = self.W*K, self.H*K
        p.text(u(8), u(3), "“", u(30), self.c("point"), "h", lh=1)
        p.text(u(8), u(27), d.get("text", ""), u(7.2), self.c("main"), "b", W - u(8) - u(10), lh=1.38, maxlines=5)
        if d.get("by"): p.line(u(8), H - u(15) - u(1.5), u(15), H - u(15) - u(1.5), self.c("sub"), max(2, int(u(.4)))); p.text(u(8) + u(9.4), H - u(15) - u(3.4), d["by"], u(3.4), self.c("sub"))
        if d.get("account"): p.text(u(8), H - u(7) - u(2.8)*1.35, d["account"], u(2.8), self.c("sub"))
        return [("인용장", img)]

    def card(self):
        d, C = self.d, self.C; u = self.u; W, H = self.W*K, self.H*K; out = []
        img, p = self.new("FFFFFF")
        p.text(u(8), u(8), d.get("name", ""), u(8), self.c("main"), "h", spacing=u(.16)); p.text(u(8), u(19), d.get("title", ""), u(3.6), self.c("sub"))
        p.rect(u(8), u(26.5), u(18), u(27.1), fill=self.c("point"))
        y = H - u(6) - u(3.3)*1.6*len(d.get("info", [])[:3])
        for ln in d.get("info", [])[:3]: y += p.text(u(8), y, ln, u(3.3), self.c("ink"), lh=1.6)
        self._logo_or_stamp(img, p, W - u(8) - u(8), u(9) + u(8), u(8), d.get("stamp", ""), self.c("main"), False); out.append(("명함_앞", img))
        img, p = self.new(C["main"])
        self._logo_or_stamp(img, p, W - u(8) - u(9.5), u(7) + u(9.5), u(9.5), d.get("back_stamp", ""), self.c("point"), True)
        p.text(u(8), H - u(19) - u(2.8)*1.35, d.get("en", ""), u(2.8), self.mixw(.65), spacing=u(.4)); p.text(u(8), H - u(9) - u(6.4)*1.35, d.get("org", ""), u(6.4), (255, 255, 255), "h", spacing=-u(.13)); out.append(("명함_뒤", img))
        return out
    def _logo_or_stamp(self, img, p, cx, cy, r, text, color, dark):
        if self.logo and os.path.exists(self.logo):
            try:
                lg = Image.open(self.logo).convert("RGBA"); box = int(r*2)
                if dark: p.rect(cx - r, cy - r, cx + r, cy + r, fill=(255, 255, 255), r=int(r*0.16)); box = int(r*2*0.84)
                lg.thumbnail((box, box), Image.LANCZOS); img.paste(lg, (int(cx - lg.width/2), int(cy - lg.height/2)), lg); return
            except Exception as e: self.errs.append(f"로고를 넣지 못함: {e}")
        if text: p.stamp(cx, cy, r, text, color)

    def build(self, outdir):
        fn = getattr(self, self.kind); pages = fn()
        if self.errs: return []
        names = []
        for name, im in pages:
            B.save_png(im, os.path.join(outdir, name + ".png"), K); names.append(name)
        if self.kind in PDF_MM:
            mmw, mmh = PDF_MM[self.kind]; dpi = self.W/(mmw/25.4)
            ims = [Image.open(os.path.join(outdir, n + ".png")).convert("RGB") for n in names]
            ims[0].save(os.path.join(outdir, names[0].split("_")[0] + ".pdf"), save_all=True, append_images=ims[1:], resolution=dpi); names.append(names[0].split("_")[0] + ".pdf")
        return names

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("content", nargs="?"); ap.add_argument("--schema", nargs="?", const="poster"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--kind", choices=list(SIZES)); ap.add_argument("--pal", default="b3"); ap.add_argument("--font", default="ng", choices=list(B.FONTS)); ap.add_argument("--logo"); ap.add_argument("--fonts-dir"); ap.add_argument("-o", "--out")
    a = ap.parse_args()
    if a.schema: print(NOTE + json.dumps(dict(kind=a.schema, **SAMPLES[a.schema]), ensure_ascii=False, indent=2)); return
    if not a.content: ap.print_help(); return
    if a.pal not in B.PAL: B.log("색 id가 없음"); sys.exit(1)
    B.log("make_promo.py sha256 " + B.self_hash(os.path.abspath(__file__)) + " (고치지 않았는지 대조용)")
    d = B.load_json(a.content); kind = a.kind or d.get("kind")
    if kind not in SIZES: B.fail([f"kind가 없거나 틀림: {kind}. 가능한 값: " + " ".join(SIZES)])
    if re.search(r"<[a-zA-Z/]", json.dumps(d, ensure_ascii=False)): B.fail(["글 안에 <태그>가 있음"])
    paths = B.font_paths(a.font, a.fonts_dir)
    miss = B.missing_glyphs(json.dumps(d, ensure_ascii=False), paths[0])
    if miss: B.log("[경고] 글꼴에 없는 글자(□로 찍힘): " + "".join(sorted(miss))[:30])
    if a.dry_run: B.log("검사 통과"); return
    KN = dict(poster="포스터", story="스토리", sale="할인게시물", deck="발표표지", flyer="전단", invite="초대장", thumb="썸네일", resume="이력서", card="명함", quote="인용장")
    outdir = a.out or os.path.join(B.OUTDIR, f"{KN[kind]}_{B.PAL[a.pal]['name']}"); os.makedirs(outdir, exist_ok=True)
    pr = Promo(kind, d, B.PAL[a.pal], paths, a.logo); names = pr.build(outdir)
    if pr.errs: B.fail(pr.errs)
    B.log(f"완료: {outdir}/ · {', '.join(names)} · 색 {B.PAL[a.pal]['name']} · 글꼴 {a.font}")
    print(outdir)

if __name__ == "__main__": main()
