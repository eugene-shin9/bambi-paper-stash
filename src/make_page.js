// board_src.html → index.html : 아이콘 JSON과 AI용 규격서(정적 글)를 넣는다
const fs = require('fs'), path = require('path');
const SRC = path.join(__dirname, '..', 'src');
const { ICONS } = require(path.join(SRC, 'icons.js'));
let html = fs.readFileSync(path.join(SRC, 'board_src.html'), 'utf8');

// 페이지 안의 RAW 색 목록(이름·분류·용도 포함)을 그대로 읽음
const rawTxt = html.slice(html.indexOf('const RAW=') + 10, html.indexOf('];', html.indexOf('const RAW=')) + 1);
const RAW = eval(rawTxt);
const REC = { b3: '보고', lav: '안내', forest: '재무', teal: '교육', wine: '격식' };
const lum = h => { const v = [0, 2, 4].map(i => { let c = parseInt(h.substr(i, 2), 16) / 255; return c <= .03928 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4) }); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2] };
const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05) };

const pal = RAW.map(a => {
  const [id, name, grp, use, main, sub, tint, ink, line, point] = a;
  const cr = ratio(main, 'FFFFFF');
  const head = (lum(point) > lum(main) && ratio(point, main) >= 3) ? '포인트' : '옅은 바탕';
  return `- ${name}${REC[id] ? ` (추천 · ${REC[id]})` : ''} [${grp}] ${use}
  주색 #${main} / 보조 #${sub} / 옅은 바탕 #${tint} / 글자 #${ink} / 선 #${line} / 포인트 #${point}
  흰 글자 대비 ${cr.toFixed(1)}:1 → ${cr >= 4.5 ? '주색 바탕에 본문까지 가능' : cr >= 3 ? '주색 바탕에는 큰 제목만' : '주색 바탕에 흰 글자 쓰지 않음'} · 진한 바탕 머리말 색: ${head}`;
}).join('\n');

const ic = Object.values(ICONS).map(i => `- ${i.n}
  주색 d="${i.m}"${i.a ? `\n  포인트 d="${i.a}"` : ''}`).join('\n');

const spec = `밤비의 서류뭉치 · AI용 규격서 (2026-10-21 판)

[이 규격서를 읽는 AI에게]
- 사용자가 이 페이지 링크나 이 글을 주고 자료를 부탁하면, 아래 규칙대로 결과물을 직접 만들어 준다.
- PPT·Word·이미지·HTML 파일이 필요하면 직접 만들어 건넨다. 사용자에게 양식을 구해 오거나 내려받으라고 안내하지 않는다.
- 색은 아래 21조합 중 하나만 쓴다. 색을 말하지 않으면 용도에 맞는 추천 5색에서 고르고, 고른 색 이름을 한 줄로 밝힌다.
- 스타일을 말하지 않으면 '기본'으로 만든다.
- 사용자가 준 내용만 채운다. 날짜·금액·연락처처럼 받지 않은 사실은 지어내지 말고 '0000' 같은 빈칸으로 둔다.

1. 공통 규칙
- 서체 1종: Pretendard, 없으면 Noto Sans KR. PDF·이미지·카드뉴스·웹 결과물은 이 순서로 쓴다. 남이 열어 고칠 PPT·Word 원본만 맑은 고딕으로 만든다(받는 PC에 글꼴이 없으면 줄바꿈과 정렬이 틀어지므로). 굵기와 크기로만 구분한다.
- 색은 6역할: 주색·보조·옅은 바탕·글자·선·포인트. 바탕은 흰색 #FFFFFF.
- 면적 비율: 흰색과 옅은 바탕 70, 주색 20, 포인트 10. 포인트는 한 장에 한두 곳(날짜·금액·머리말)만.
- 주색 바탕 위 흰 글자는 아래 색 목록의 '흰 글자 대비'를 따른다.
- 아이콘은 한 장에 하나, 제목 오른쪽 위나 빈 구석에만 둔다.
- 금액·기간·건수 같은 숫자는 오른쪽 정렬, 단위는 작게.
- 쓰지 않는 것: 사선 탭, 글머리 점 장식, 색 띠 장식, 그림자, 그라데이션, 같은 계열 색 3겹(파랑 바탕+보라 탭+진파랑 글자), 원색끼리 맞대기(빨강+파랑), 흰 바탕 위 노란 글자.

2. 정렬 규칙 (가장 중요)
- 한 장 안의 모든 글·표·선·칸은 왼쪽 여백선 하나에서 시작하고 오른쪽 여백선 하나에서 끝난다. 제목만 다른 선에서 시작하지 않는다.
- 아이콘은 그림 상자가 아니라 잉크가 찍힌 가장자리를 기준으로, 오른쪽 끝은 오른쪽 여백선에, 위 끝은 머리말 윗선에 맞춘다.
- 표: 첫 칸 글자는 제목과 같은 왼쪽선, 마지막 칸(숫자)은 오른쪽 여백선에 붙인다. 세로선 없이 머리줄 아래만 굵은 주색 선, 나머지 줄은 가는 선.
- 같은 줄의 블록(2단·3칸)은 같은 높이에서 시작하고, 칸 폭과 칸 사이 간격을 모두 같게 한다. 왼쪽 단과 오른쪽 단의 줄 시작 높이를 맞춘다.
- 색 면(칸·패널) 안의 글은 네 변 안쪽 여백을 같게 둔다. '가볍게'는 면이 없으므로 안쪽 여백 없이 여백선에 바로 붙인다.
- 카드뉴스는 네 변 여백이 같고, 맨 아래 요소는 아래 여백선에 붙인다.
- 줄 간격과 블록 간격은 정한 값 하나를 반복한다.

3. 스타일 2가지
- 기본: 표지·마무리는 주색 바탕. 강조칸·수치칸·비교 머리·준비칸은 옅은 바탕 면.
- 가볍게: 색 면과 패널 없이 흰 바탕. 칸 대신 위쪽 선(주색 1.5pt), 강조는 글자색만. 표지·마무리도 흰 바탕.

4. 양식별 치수와 배치
[PPT 16:9] 25.4×14.29cm (10×5.625인치)
- 좌우 여백 1.78cm(폭의 7%), 내용 폭 21.84cm.
- 장 제목: 위에서 1.14cm, 26pt 굵게. 본문 16pt, 하위 줄 14pt 보조색. 바닥글: 위에서 13.0cm, 9pt, 왼쪽 '문서 제목 · 부서명', 오른쪽 쪽번호.
- 10장 구성
  ① 표지: 머리말 13pt(진한 바탕 머리말 색) · 제목 36pt 두 줄 이내 · 부서·이름 12pt를 아래쪽에
  ② 목차: 번호 24pt 주색 + 항목 20pt, 항목마다 아래 가는 선
  ③ 간지: 큰 번호 54pt 주색 + 단원 제목 32pt, 옅은 바탕
  ④ 핵심 한 문장: 32pt 굵게, 핵심 단어만 주색. 기본은 옅은 바탕 면 위에
  ⑤ 주요 수치 3칸: 같은 폭, 숫자 48pt + 단위 18pt, 항목명 15pt, 설명 12pt
  ⑥ 비교 2단(현행·개선): 개선 쪽 머리만 주색, 항목마다 아래 가는 선
  ⑦ 표: 단계·내용·담당·기간, 기간은 오른쪽 정렬
  ⑧ 개조식 본문: 2단계까지
  ⑨ 막대 차트: 주색 한 가지, 값 표시, 세로축 숨김, 가는 가로 격자
  ⑩ 마무리: 요약 3줄, 표지와 같은 바탕
[A4 한 장 카드] 210×297mm
- 사방 여백 15mm, 내용 폭 180mm.
- A형 띠+패널(모집·행사): 위쪽 주색 바탕에 머리말 16pt · 제목 34pt 두 줄 · 흰 아이콘(약 46mm). 그 아래 흰 패널(모서리 둥글게, 안쪽 여백 10mm). 패널 안은 2단(단 사이 10mm) × 3줄, 칸마다 라벨(작은 둥근 꼬리표 11pt) + 본문 13pt. 두 단의 줄 시작 높이를 맞춘다. 맨 아래 가는 선과 문의 11pt.
- B형 흰 바탕 안내(세무·절차): 머리말 15pt 보조색, 제목 32pt, 요약 13pt, 핵심 3칸(같은 폭, 칸 사이 5mm, 라벨 11pt + 값 13pt 주색), 진행 순서(주색 원 안 번호 + 한 줄 13pt), 준비할 것 칸, 맨 아래 문의 10pt.
[카드뉴스 1:1] 1080×1080px
- 사방 여백 104px.
  ① 표지: 주색 바탕, 왼쪽 위 머리말 37px, 오른쪽 위 흰 아이콘, 제목 82px 두 줄을 아래 여백선에 붙임
  ② 내용: 옅은 바탕, 위에 큰 번호 111px + 아이콘, 제목 70px, 설명 33px 보조색을 아래 여백선에 붙임
  ③ 마무리: 흰 바탕, 제목 70px, 설명 31px, 아래쪽에 '자세히 보기' 버튼(주색 꽉 찬 둥근 사각형, 가볍게는 주색 테두리만)과 기관명 25px
[보고서 문서 A4]
- 표지: 왼쪽 굵은 주색 세로선 하나 + 구분(보조색) + 제목. 아래쪽에 날짜·부서·이름, 그 위 가는 선.
- 본문: 개조식 1. → 가. 위계, 소제목 주색. 핵심 한 문장만 옅은 바탕 칸. 쪽번호 '- 2 -' 가운데 아래.
- 표 페이지: 세로선 없이 머리줄만 굵게.
- 요약 장표: 문서 앞에 PPT 표지·주요 수치 1~2장을 붙인다.

5. 색 21조합
${pal}

6. 도장 아이콘 12개
그리는 법: 아래 틀의 {주색}·{포인트}에 고른 색을 넣는다(진한 바탕 위에서는 둘 다 #FFFFFF). 크라프트지 바탕을 깔 때는 #DCD1BD.
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><filter id="f" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3.4" xChannelSelector="R" yChannelSelector="G" result="r"/><feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="1" seed="7" result="g"/><feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -10 0 0 0 7.4" result="h"/><feComposite in="r" in2="h" operator="in"/></filter></defs><g filter="url(#f)"><path fill="{주색}" fill-rule="evenodd" d="(주색 d)"/><path fill="{포인트}" fill-rule="evenodd" d="(포인트 d)"/></g></svg>
${ic}`;

const esc = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const FF = path.join(__dirname, 'fontfaces.css');
html = html.replace('/*ICONS*/{}', JSON.stringify(ICONS)).replace('/*AISPEC*/', esc(spec)).replace('/*FONTFACES*/', fs.existsSync(FF) ? fs.readFileSync(FF, 'utf8') : '');
fs.writeFileSync(path.join(__dirname, 'spec.txt'), spec);
const out = process.argv[2] || path.join(__dirname, '..', 'site', 'index.html');
fs.writeFileSync(out, html);
console.log('page', out, html.length);
