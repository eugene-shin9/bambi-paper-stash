const pptxgen=require('pptxgenjs'),sharp=require('sharp'),fs=require('fs');
const {applyTheme}=require('/mnt/skills/public/pptx/scripts/apply_theme.js');
const {ICONS,svg}=require('./icons.js'); const PALS=require('./pals.js');
const lum=h=>{const v=[0,2,4].map(i=>{let c=parseInt(h.substr(i,2),16)/255;return c<=.03928?c/12.92:Math.pow((c+.055)/1.055,2.4)});return .2126*v[0]+.7152*v[1]+.0722*v[2]};
const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
const only=process.argv[2]?process.argv[2].split(','):null;
// 키트 파일은 맑은 고딕. 미리보기용으로만 PFONT(글꼴 이름)·POUT(출력 폴더)를 바꿔 다른 글꼴 판을 만든다
const FONT=process.env.PFONT||'맑은 고딕', OUT=process.env.POUT||'out';

async function icons(p,dir){
  fs.mkdirSync(`${dir}/아이콘`,{recursive:true}); const out={};
  for(const [k,i] of Object.entries(ICONS)){
    const c=await sharp(Buffer.from(svg(k,'#'+p.main,'#'+p.point,512))).png().toBuffer();
    const w=await sharp(Buffer.from(svg(k,'#FFFFFF','#FFFFFF',512))).png().toBuffer();
    fs.writeFileSync(`${dir}/아이콘/${i.n}_컬러.png`,c); fs.writeFileSync(`${dir}/아이콘/${i.n}_흰색.png`,w);
    // 잉크가 실제로 찍힌 범위(0~1) — 아이콘 눈에 보이는 가장자리를 글 여백선에 맞추는 데 씀
    const {data,info}=await sharp(c).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    let x1=info.width,y1=info.height,x2=0,y2=0;
    for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){if(data[(y*info.width+x)*4+3]>40){if(x<x1)x1=x;if(x>x2)x2=x;if(y<y1)y1=y;if(y>y2)y2=y;}}
    out[k]={c:'image/png;base64,'+c.toString('base64'),w:'image/png;base64,'+w.toString('base64'),b:[x1/info.width,y1/info.height,(x2+1)/info.width,(y2+1)/info.height]};
  } return out;
}
// 아이콘을 눈에 보이는 오른쪽 끝·위 끝 기준으로 놓기
function place(s,icon,white,size,re,top,name){const b=icon.b;s.addImage({data:white?icon.w:icon.c,x:re-size*b[2],y:top-size*b[1],w:size,h:size,objectName:name||'아이콘'});}
let RICH=false; const SUF=()=>RICH?'_풍성하게':'';
function deco(s,pres,C,dark,W,H){if(!RICH||!dark)return;
  s.addShape(pres.shapes.OVAL,{x:W-3.2,y:-1.9,w:4.6,h:4.6,fill:{color:C.accent2,transparency:60},line:{type:'none'},objectName:'장식원'});}
function theme(p){
  const eb = (lum(p.point)>lum(p.main)&&ratio(p.point,p.main)>=3)?p.point:p.tint;
  return {name:p.name,headFontFace:FONT,bodyFontFace:FONT,colors:{dk1:p.ink,lt1:'FFFFFF',dk2:p.main,lt2:p.tint,accent1:p.main,accent2:p.sub,accent3:p.line,accent4:eb,accent5:p.point,accent6:'5E6876',hlink:p.main,folHlink:p.sub}};
}

async function deck(p,dir,L){
  const TH=theme(p), pres=new pptxgen(); pres.layout='LAYOUT_16x9'; pres.title='PPT 기본틀 '+p.name;
  pres.theme={headFontFace:TH.headFontFace,bodyFontFace:TH.bodyFontFace}; const C=pres.SchemeColor;
  const foot=()=>({text:{text:'문서 제목 · 부서명',options:{x:0.7,y:5.12,w:6,h:0.3,fontSize:9,color:C.accent6,margin:0}}});
  const num=()=>({x:8.8,y:5.12,w:0.5,h:0.3,fontSize:9,color:C.accent6,align:'right'});
  const TITLE=()=>({name:'title',type:'title',align:'left',x:0.7,y:0.45,w:8.6,h:0.75,fontSize:26,bold:true,color:C.text1,margin:0,valign:'top'});
  pres.defineSlideMaster({title:'표지',background:{color:L?C.background1:C.text2},objects:[
    {placeholder:{options:{name:'eyebrow',type:'body',x:0.7,y:1.25,w:8,h:0.4,fontSize:13,color:L?C.accent1:C.accent4,bold:true,margin:0},text:'보고 구분 · 날짜'}},
    {placeholder:{options:{name:'title',type:'title',align:'left',x:0.7,y:1.7,w:8.4,h:1.6,fontSize:36,bold:true,color:L?C.text1:C.background1,margin:0,valign:'top'},text:'제목을 입력하세요'}},
    {placeholder:{options:{name:'meta',type:'body',x:0.7,y:4.55,w:8,h:0.4,fontSize:12,color:L?C.accent6:C.background2,margin:0},text:'부서 · 이름'}}]});
  pres.defineSlideMaster({title:'간지',background:{color:L?C.background1:C.background2},objects:[
    {placeholder:{options:{name:'num',type:'body',x:0.7,y:1.55,w:3,h:0.9,fontSize:54,bold:true,color:C.accent1,margin:0},text:'01'}},
    {placeholder:{options:{name:'title',type:'title',align:'left',x:0.7,y:2.55,w:8.4,h:0.9,fontSize:32,bold:true,color:C.text1,margin:0,valign:'top'},text:'단원 제목'}}]});
  const band=()=>RICH?[{rect:{x:0.7,y:1.22,w:0.5,h:0.05,fill:{color:C.accent5}}}]:[];
  const TITLE2=()=>TITLE();
  pres.defineSlideMaster({title:'제목만',background:{color:C.background1},slideNumber:num(),objects:[...band(),foot(),{placeholder:{options:TITLE2(),text:'장표 제목'}}]});
  pres.defineSlideMaster({title:'제목+본문',background:{color:C.background1},slideNumber:num(),objects:[...band(),foot(),{placeholder:{options:TITLE2(),text:'장표 제목'}},
    {placeholder:{options:{name:'body',type:'body',x:0.7,y:1.45,w:8.6,h:3.4,fontSize:16,color:C.text1,margin:0,valign:'top',paraSpaceAfter:8},text:'본문을 입력하세요'}}]});
  pres.defineSlideMaster({title:'마무리',background:{color:L?C.background1:C.text2},objects:[
    {placeholder:{options:{name:'title',type:'title',align:'left',x:0.7,y:0.6,w:8.6,h:0.75,fontSize:28,bold:true,color:L?C.text1:C.background1,margin:0},text:'요약'}},
    {placeholder:{options:{name:'body',type:'body',x:0.7,y:1.6,w:8.6,h:3.2,fontSize:16,color:L?C.text1:C.background1,margin:0,valign:'top',paraSpaceAfter:10},text:'핵심 내용'}}]});
  const T=(s,t,o)=>s.addText(t,Object.assign({margin:0,isTextBox:true},o));
  pres.addSection({title:'표지'});
  let s=pres.addSlide({masterName:'표지',sectionTitle:'표지'}); deco(s,pres,C,true,10,5.625);
  s.addText('업무 보고 · 0000. 00.',{placeholder:'eyebrow'}); s.addText('보고서 제목을\n두 줄 이내로 적습니다',{placeholder:'title'}); s.addText('부서명 · 이름',{placeholder:'meta'});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'표지'}); s.addText('목차',{placeholder:'title'});
  [['현황','지금 어디까지 와 있는지'],['검토 내용','무엇이 문제이고 왜 그런지'],['향후 계획','무엇을 언제 누가 할지'],['행정 사항','협조와 결정이 필요한 것']].forEach(([t,d],i)=>{const y=1.5+i*0.85;
    T(s,String(i+1).padStart(2,'0'),{x:0.7,y,w:0.9,h:0.5,fontSize:22,bold:true,color:C.accent1,objectName:'목차번호'+(i+1)});
    T(s,t,{x:1.7,y,w:6,h:0.45,fontSize:18,bold:true,color:C.text1,valign:'middle',objectName:'목차'+(i+1)});
    T(s,d,{x:1.7,y:y+0.4,w:6,h:0.3,fontSize:12,color:C.accent6,objectName:'목차설명'+(i+1)});
    s.addShape(pres.shapes.LINE,{x:0.7,y:y+0.78,w:8.6,h:0,line:{color:C.accent3,width:0.75},objectName:'목차선'+(i+1)});});
  pres.addSection({title:'본문'});
  s=pres.addSlide({masterName:'간지',sectionTitle:'본문'}); deco(s,pres,C,false,10,5.625); s.addText('01',{placeholder:'num'}); s.addText('현황',{placeholder:'title'});
  T(s,'이 장에서 다루는 것  ·  추진 경과  ·  현재 수치  ·  남은 과제',{x:0.7,y:3.6,w:8.4,h:0.4,fontSize:14,color:C.accent2,objectName:'간지설명'});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('핵심 메시지',{placeholder:'title'});
  if(!L)s.addShape(pres.shapes.RECTANGLE,{x:0.7,y:1.5,w:8.6,h:1.9,fill:{color:C.background2},line:{type:'none'},objectName:'강조배경'});
  T(s,[{text:'가장 중요한 결론을 '},{text:'한 문장',options:{color:C.accent1}},{text:'으로 적습니다'}],{x:L?0.7:1.1,y:1.6,w:7.8,h:1.7,fontSize:28,bold:true,color:C.text1,valign:'middle',objectName:'핵심문장'});
  ['근거 1 · 수치나 사실 한 줄','근거 2 · 수치나 사실 한 줄','근거 3 · 수치나 사실 한 줄'].forEach((t,i)=>{const y=3.65+i*0.42;
    s.addShape(pres.shapes.OVAL,{x:0.7,y:y+0.1,w:0.16,h:0.16,fill:{color:C.accent1},line:{type:'none'},objectName:'근거점'+(i+1)});
    T(s,t,{x:1.0,y,w:8.3,h:0.36,fontSize:14,color:C.text1,valign:'middle',objectName:'근거'+(i+1)});});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('주요 수치',{placeholder:'title'});
  [['00','건','처리 건수','비교 기준을 적습니다'],['00','%','개선 비율','전년 같은 기간 대비'],['00','일','소요 기간','평균값 기준']].forEach((d,i)=>{const x=0.7+i*2.95;
    if(L)s.addShape(pres.shapes.LINE,{x,y:1.6,w:2.7,h:0,line:{color:C.accent1,width:1.5},objectName:'수치선'+(i+1)});else s.addShape(pres.shapes.RECTANGLE,{x,y:1.6,w:2.7,h:2.9,fill:{color:C.background2},line:{type:'none'},objectName:'수치칸'+(i+1)});
    const px=L?x:x+0.3;
    T(s,[{text:d[0],options:{fontSize:48,bold:true}},{text:' '+d[1],options:{fontSize:18,bold:true}}],{x:px,y:1.85,w:2.2,h:1.0,color:C.accent1,valign:'bottom',objectName:'수치'+(i+1)});
    T(s,d[2],{x:px,y:3.0,w:2.2,h:0.4,fontSize:15,bold:true,color:C.text1,objectName:'수치제목'+(i+1)});
    T(s,d[3],{x:px,y:3.45,w:2.2,h:0.8,fontSize:12,color:C.accent6,valign:'top',objectName:'수치설명'+(i+1)});});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('현행과 개선',{placeholder:'title'});
  [['현행',['절차가 여러 단계로 나뉨','서식이 부서마다 다름','진행 상황 공유가 늦음']],['개선',['한 번에 처리하도록 통합','공통 서식으로 정리','공유 일정표로 관리']]].forEach(([h,items],i)=>{const x=0.7+i*4.45,on=i===1;
    const IN=L?0:0.16;
    if(L)s.addShape(pres.shapes.LINE,{x,y:2.08,w:4.15,h:0,line:{color:on?C.accent1:C.accent3,width:1.5},objectName:'비교머리선'+(i+1)});else s.addShape(pres.shapes.RECTANGLE,{x,y:1.55,w:4.15,h:0.5,fill:{color:on?C.accent1:C.background2},line:{type:'none'},objectName:'비교머리칸'+(i+1)});
    T(s,h,{x:x+IN,y:1.55,w:4.15-2*IN,h:0.5,fontSize:15,bold:true,color:L?(on?C.accent1:C.accent6):(on?C.background1:C.accent1),valign:'middle',objectName:'비교머리'+(i+1)});
    items.forEach((t,j)=>{const y=2.25+j*0.75; T(s,t,{x:x+IN,y,w:4.15-2*IN,h:0.55,fontSize:15,color:C.text1,valign:'middle',objectName:`비교${i+1}-${j+1}`});
      s.addShape(pres.shapes.LINE,{x,y:y+0.62,w:4.15,h:0,line:{color:C.accent3,width:0.75},objectName:`비교선${i+1}-${j+1}`});});});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('추진 일정',{placeholder:'title'});
  const nb={type:'none'}, hb=[nb,nb,{type:'solid',pt:1.5,color:p.main},nb], rb=[nb,nb,{type:'solid',pt:0.75,color:p.line},nb];
  const MG=[[0,0.12,0,0],[0,0.12,0,0.12],[0,0.12,0,0.12],[0,0,0,0.12]];
  const H=(t,a,c)=>({text:t,options:{bold:true,color:C.accent1,border:hb,align:a||'left',margin:MG[c]}}), R=(t,a,c)=>({text:t,options:{color:C.text1,border:rb,align:a||'left',margin:MG[c]}});
  const rows=[['준비','계획 수립, 자료 정리','담당 부서','0주'],['시행','일부 적용, 의견 수렴','담당 부서','0주'],['확대','전체 적용, 보완','전 부서','0주']];
  s.addTable([['단계','내용','담당','기간'].map((t,c)=>H(t,c==3?'right':'left',c)),...rows.map(r=>r.map((t,c)=>R(t,c==3?'right':'left',c)))],
    {x:0.7,y:1.55,w:8.6,colW:[1.4,4.2,1.8,1.2],rowH:0.55,fontSize:14,valign:'middle',objectName:'일정표'});
  s=pres.addSlide({masterName:'제목+본문',sectionTitle:'본문'}); s.addText('검토 내용',{placeholder:'title'});
  s.addText([{text:'첫 번째 검토 사항을 한 줄로 적습니다',options:{bullet:true,breakLine:true}},{text:'세부 근거나 예시는 한 단계 들여 씁니다',options:{bullet:true,indentLevel:1,fontSize:14,color:C.accent6,breakLine:true}},
    {text:'두 번째 검토 사항',options:{bullet:true,breakLine:true}},{text:'세부 내용',options:{bullet:true,indentLevel:1,fontSize:14,color:C.accent6,breakLine:true}},{text:'세 번째 검토 사항',options:{bullet:true}}],{placeholder:'body'});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('월별 추이',{placeholder:'title'});
  s.addChart(pres.charts.BAR,[{name:'건수',labels:['1월','2월','3월','4월'],values:[42,47,51,58]}],{x:0.7,y:1.45,w:8.6,h:3.5,barDir:'col',chartColors:[p.main],showValue:true,dataLabelPosition:'outEnd',dataLabelColor:p.ink,dataLabelFontSize:12,
    dataLabelFontFace:'+mn-lt',catAxisLabelFontFace:'+mn-lt',valAxisLabelFontFace:'+mn-lt',catAxisLabelColor:'5E6876',valAxisLabelColor:'5E6876',catAxisLabelFontSize:12,valAxisLabelFontSize:10,valGridLine:{color:p.line,size:0.5},catGridLine:{style:'none'},showLegend:false,valAxisHidden:true,barGapWidthPct:80,objectName:'추이차트'});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('진행 단계',{placeholder:'title'});
  ['신청','검토','선정','안내'].forEach((t,i)=>{const x=0.7+i*2.15,cx=x+1.075;
    if(i<3)s.addShape(pres.shapes.LINE,{x:cx+0.35,y:2.3,w:1.45,h:0,line:{color:C.accent3,width:1.5},objectName:'단계연결'+(i+1)});
    s.addShape(pres.shapes.OVAL,{x:cx-0.3,y:2.0,w:0.6,h:0.6,fill:{color:i===0?C.accent1:C.background1},line:{color:C.accent1,width:1.5},objectName:'단계원'+(i+1)});
    T(s,String(i+1),{x:cx-0.3,y:2.0,w:0.6,h:0.6,fontSize:14,bold:true,color:i===0?C.background1:C.accent1,align:'center',valign:'middle',objectName:'단계번호'+(i+1)});
    T(s,t,{x,y:2.85,w:2.15,h:0.4,fontSize:16,bold:true,color:C.text1,align:'center',objectName:'단계명'+(i+1)});
    T(s,'설명을 한 줄로',{x,y:3.25,w:2.15,h:0.6,fontSize:12,color:C.accent6,align:'center',valign:'top',objectName:'단계설명'+(i+1)});});
  s=pres.addSlide({masterName:'제목만',sectionTitle:'본문'}); s.addText('현장 사진',{placeholder:'title'});
  s.addShape(pres.shapes.RECTANGLE,L?{x:0.7,y:1.45,w:4.1,h:3.4,fill:{color:C.background1},line:{color:C.accent3,width:1},objectName:'사진자리'}:{x:0.7,y:1.45,w:4.1,h:3.4,fill:{color:C.background2},line:{type:'none'},objectName:'사진자리'});
  T(s,'사진 자리\n이 칸을 사진으로 채웁니다',{x:0.7,y:1.45,w:4.1,h:3.4,fontSize:12,color:C.accent6,align:'center',valign:'middle',objectName:'사진안내'});
  T(s,'사진 설명 제목',{x:5.2,y:1.5,w:4.1,h:0.5,fontSize:20,bold:true,color:C.text1,objectName:'사진제목'});
  s.addText([{text:'무엇을 찍었는지 한 줄',options:{bullet:true,breakLine:true}},{text:'언제·어디서',options:{bullet:true,breakLine:true}},{text:'눈여겨볼 점',options:{bullet:true}}],{x:5.2,y:2.1,w:4.1,h:2.5,fontSize:15,color:C.text1,valign:'top',paraSpaceAfter:8,margin:0,objectName:'사진설명'});
  pres.addSection({title:'마무리'});
  s=pres.addSlide({masterName:'마무리',sectionTitle:'마무리'}); deco(s,pres,C,true,10,5.625); s.addText('요약과 다음 단계',{placeholder:'title'});
  s.addText([{text:'첫 번째 결론',options:{bullet:true,breakLine:true}},{text:'두 번째 결론',options:{bullet:true,breakLine:true}},{text:'세 번째 결론',options:{bullet:true}}],{placeholder:'body'});
  const fc=L?C.text1:C.background1, fs=L?C.accent6:C.background2;
  s.addShape(pres.shapes.LINE,{x:0.7,y:3.35,w:8.6,h:0,line:{color:L?C.accent3:C.accent2,width:0.75},objectName:'마무리선'});
  T(s,'다음 단계',{x:0.7,y:3.5,w:2,h:0.35,fontSize:13,bold:true,color:L?C.accent1:C.accent4,objectName:'다음단계라벨'});
  T(s,'0000. 00.까지 ○○ 완료  →  0000. 00. 결과 보고',{x:2.5,y:3.5,w:6.8,h:0.35,fontSize:14,color:fc,objectName:'다음단계'});
  T(s,'결정 요청',{x:0.7,y:3.95,w:2,h:0.35,fontSize:13,bold:true,color:L?C.accent1:C.accent4,objectName:'결정라벨'});
  T(s,'승인이 필요한 사항 한 줄',{x:2.5,y:3.95,w:6.8,h:0.35,fontSize:14,color:fc,objectName:'결정요청'});
  T(s,'문의 · 담당 부서 000-0000',{x:0.7,y:4.75,w:8.6,h:0.3,fontSize:11,color:fs,objectName:'문의'});
  const f=`${dir}/PPT_기본틀_${p.name}${L?'_가볍게':SUF()}.pptx`; await pres.writeFile({fileName:f}); await applyTheme(f,TH); require('child_process').execFileSync('python3',[__dirname+'/fixfont.py',FONT,f]); return f;
}

async function a4(p,dir,ic,L){
  const TH=theme(p), pres=new pptxgen(); pres.defineLayout({name:'A4P',width:8.27,height:11.69}); pres.layout='A4P'; pres.title='한장 카드형 '+p.name;
  pres.theme={headFontFace:TH.headFontFace,bodyFontFace:TH.bodyFontFace}; const C=pres.SchemeColor;
  const T=(s,t,o)=>s.addText(t,Object.assign({margin:0,isTextBox:true,color:C.text1,valign:'top'},o));
  // 정렬 기준: 바깥 여백 M, 내용 폭 CW, 오른쪽 끝 RE
  const M=0.6, CW=8.27-2*M, RE=M+CW;
  const label=(s,t,x,y,name)=>L?T(s,t,{x,y,w:2.5,h:0.32,fontSize:12,bold:true,color:C.accent1,valign:'middle',objectName:name}):T(s,t,{x,y,w:1.5,h:0.32,fontSize:11,bold:true,color:RICH?C.background1:C.accent1,fill:{color:RICH?C.accent1:C.background2},shape:pres.shapes.ROUNDED_RECTANGLE,rectRadius:0.16,align:'center',valign:'middle',objectName:name});
  // A: 띠 + 패널 (교육 모집)
  let s=pres.addSlide(); s.background={color:L?C.background1:C.text2}; if(RICH){s.addShape(pres.shapes.OVAL,{x:4.9,y:-2.0,w:4.8,h:4.8,fill:{color:C.accent2,transparency:60},line:{type:'none'},objectName:'장식원'});}
  const IC=1.8;
  T(s,'2027 상반기',{x:M,y:0.75,w:4.8,h:0.4,fontSize:16,bold:true,color:L?C.accent2:C.accent4,objectName:'머리말'});
  T(s,'교육 프로그램\n참가자 모집',{x:M,y:1.2,w:RE-IC-0.3-M,h:1.6,fontSize:34,bold:true,color:L?C.text1:C.background1,objectName:'제목'});
  place(s,ic.book,!L,IC,RE,0.8);
  const PAD=L?0:0.4, LX=M+PAD, IW=CW-2*PAD, G=0.4, W=(IW-G)/2, R=LX+W+G, Y=[3.75,5.95,8.15];
  if(L)s.addShape(pres.shapes.LINE,{x:M,y:3.25,w:CW,h:0,line:{color:C.accent1,width:1.5},objectName:'구분선'});else s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:M,y:3.15,w:CW,h:11.69-M-3.15,rectRadius:0.25,fill:{color:C.background1},line:{type:'none'},objectName:'정보패널'});
  const block=(x,y,t,body,n)=>{label(s,t,x,y,n+'라벨');T(s,body,{x,y:y+0.48,w:W,h:1.5,fontSize:13,paraSpaceAfter:4,objectName:n});};
  block(LX,Y[0],'대상',[{text:'관심 있는 누구나',options:{breakLine:true}},{text:'선착순 00명',options:{color:C.accent6}}],'대상');
  block(LX,Y[1],'기간',[{text:'3. 2. ~ 3. 13.',options:{bold:true,color:C.accent1,breakLine:true}},{text:'신청 기간 기준',options:{color:C.accent6}}],'기간');
  block(LX,Y[2],'신청 방법',[{text:'1  신청서 작성',options:{breakLine:true}},{text:'2  이메일 제출',options:{breakLine:true}},{text:'3  확인 문자 수신'}],'신청');
  block(R,Y[0],'내용',[{text:'주제별 강의와 실습',options:{breakLine:true}},{text:'사례 중심 토론',options:{breakLine:true}},{text:'수료 후 자료 제공'}],'내용');
  label(s,'일정',R,Y[1],'일정라벨');
  [['1주','오리엔테이션'],['2~3주','강의·실습'],['4주','결과 공유']].forEach((r,i)=>{const y=Y[1]+0.48+i*0.5;
    T(s,r[0],{x:R,y,w:0.9,h:0.36,fontSize:13,bold:true,color:C.accent1,valign:'middle',objectName:'주차'+i});
    T(s,r[1],{x:R+0.95,y,w:W-0.95,h:0.36,fontSize:13,valign:'middle',objectName:'일정'+i});
    s.addShape(pres.shapes.LINE,{x:R,y:y+0.43,w:W,h:0,line:{color:C.accent3,width:0.5},objectName:'일정선'+i});});
  block(R,Y[2],'혜택',[{text:'수료증 발급',options:{breakLine:true}},{text:'교재·자료 무료'}],'혜택');
  s.addShape(pres.shapes.LINE,{x:LX,y:10.45,w:IW,h:0,line:{color:C.accent3,width:0.75},objectName:'하단선'});
  T(s,'문의  담당 부서 · 000-0000-0000',{x:LX,y:10.6,w:IW,h:0.35,fontSize:11,color:C.accent6,objectName:'문의'});
  // B: 흰 바탕 세무 안내
  s=pres.addSlide(); s.background={color:C.background1};
  const IB=1.3;
  place(s,ic.doc,false,IB,RE,0.85);
  T(s,'세무 안내',{x:M,y:0.8,w:5,h:0.4,fontSize:15,bold:true,color:C.accent2,objectName:'머리말'});
  T(s,'신고 기간과 방법을\n확인하세요',{x:M,y:1.25,w:RE-IB-0.3-M,h:1.7,fontSize:32,bold:true,objectName:'제목'});
  T(s,'신고 대상, 기간, 준비할 것을 한 장에 정리합니다.',{x:M,y:3.0,w:CW,h:0.4,fontSize:13,color:C.accent6,objectName:'요약'});
  const G3=0.2, cw=(CW-2*G3)/3, CP=L?0:0.2;
  [['기간','0월 0일 ~ 0월 0일'],['대상','해당 소득이 있는 분'],['방법','홈택스·손택스\n또는 세무서']].forEach((d,i)=>{const x=M+i*(cw+G3);
    if(L)s.addShape(pres.shapes.LINE,{x,y:3.85,w:cw,h:0,line:{color:C.accent1,width:1.5},objectName:'핵심선'+i});else s.addShape(pres.shapes.RECTANGLE,{x,y:3.85,w:cw,h:1.7,fill:{color:C.background2},line:{type:'none'},objectName:'핵심칸'+i});
    T(s,d[0],{x:x+CP,y:4.08,w:cw-2*CP,h:0.3,fontSize:11,bold:true,color:C.accent2,objectName:'핵심라벨'+i});
    T(s,d[1],{x:x+CP,y:4.45,w:cw-2*CP,h:0.9,fontSize:14,bold:true,color:C.accent1,objectName:'핵심값'+i});});
  T(s,'진행 순서',{x:M,y:6.1,w:4,h:0.35,fontSize:15,bold:true,objectName:'순서제목'});
  ['홈택스 로그인(공동·간편 인증)','신고서 작성 · 소득 자료 불러오기','내용 확인 후 제출 · 접수증 저장','기한 안에 납부 또는 환급 계좌 확인'].forEach((t,i)=>{const y=6.6+i*0.68;
    s.addShape(pres.shapes.OVAL,{x:M,y,w:0.38,h:0.38,fill:{color:C.accent1},line:{type:'none'},objectName:'순번원'+i});
    T(s,String(i+1),{x:M,y,w:0.38,h:0.38,fontSize:12,bold:true,color:C.background1,align:'center',valign:'middle',objectName:'순번'+i});
    T(s,t,{x:M+0.6,y,w:CW-0.6,h:0.38,fontSize:13,valign:'middle',objectName:'순서'+i});});
  if(L)s.addShape(pres.shapes.LINE,{x:M,y:9.55,w:CW,h:0,line:{color:C.accent3,width:0.75},objectName:'준비선'});else s.addShape(pres.shapes.RECTANGLE,{x:M,y:9.55,w:CW,h:1.25,fill:{color:C.background2},line:{type:'none'},objectName:'준비칸'});
  const QP=L?0:0.25;
  T(s,'준비할 것',{x:M+QP,y:9.72,w:3,h:0.3,fontSize:12,bold:true,color:C.accent1,objectName:'준비제목'});
  T(s,'본인 인증 수단  ·  관련 증빙자료  ·  환급받을 계좌',{x:M+QP,y:10.08,w:CW-2*QP,h:0.5,fontSize:12,objectName:'준비목록'});
  T(s,'문의  국번 없이 126 · 가까운 세무서',{x:M,y:11.0,w:CW,h:0.3,fontSize:10,color:C.accent6,objectName:'문의'});
  const f=`${dir}/한장카드_A4_${p.name}${L?'_가볍게':SUF()}.pptx`; await pres.writeFile({fileName:f}); await applyTheme(f,TH); require('child_process').execFileSync('python3',[__dirname+'/fixfont.py',FONT,f]); return f;
}

async function sq(p,dir,ic,L){
  const TH=theme(p), pres=new pptxgen(); pres.defineLayout({name:'SQ',width:7.29,height:7.29}); pres.layout='SQ'; pres.title='카드뉴스 '+p.name;
  pres.theme={headFontFace:TH.headFontFace,bodyFontFace:TH.bodyFontFace}; const C=pres.SchemeColor;
  const T=(s,t,o)=>s.addText(t,Object.assign({margin:0,isTextBox:true,color:C.text1,valign:'top'},o));
  // 네 변 여백 0.7 동일
  const M=0.7, CW=7.29-2*M, RE=M+CW, BE=7.29-M;
  let s=pres.addSlide(); s.background={color:L?C.background1:C.text2}; deco(s,pres,C,true,7.29,7.29);
  T(s,'카드뉴스',{x:M,y:M,w:3.5,h:0.45,fontSize:18,bold:true,color:L?C.accent2:C.accent4,objectName:'머리말'});
  place(s,ic.calendar,!L,1.9,RE,M+0.05);
  T(s,'한눈에 보는\n주요 일정',{x:M,y:BE-2.2,w:CW,h:2.2,fontSize:40,bold:true,color:L?C.text1:C.background1,valign:'bottom',objectName:'제목'});
  s=pres.addSlide(); s.background={color:L?C.background1:C.background2};
  T(s,'01',{x:M,y:M,w:2,h:1.0,fontSize:54,bold:true,color:C.accent1,objectName:'번호'});
  place(s,ic.search,false,1.4,RE,M+0.12);
  T(s,'무엇을\n확인하나요',{x:M,y:2.3,w:CW,h:1.8,fontSize:34,bold:true,objectName:'제목'});
  T(s,'핵심 내용을 두세 줄로 짧게 적습니다.\n한 장에 메시지 하나만 담습니다.',{x:M,y:BE-1.2,w:CW,h:1.2,fontSize:16,color:C.accent2,valign:'bottom',objectName:'본문'});
  s=pres.addSlide(); s.background={color:C.background1};
  T(s,'02',{x:M,y:M,w:2,h:1.0,fontSize:54,bold:true,color:C.accent1,objectName:'번호'});
  place(s,ic.pencil,false,1.4,RE,M+0.12);
  T(s,'이렇게\n진행합니다',{x:M,y:2.3,w:CW,h:1.6,fontSize:32,bold:true,objectName:'제목'});
  ['신청서 작성','이메일 제출','확인 문자 수신'].forEach((t,i)=>{const y=4.15+i*0.78;
    s.addShape(pres.shapes.OVAL,{x:M,y,w:0.46,h:0.46,fill:{color:C.accent1},line:{type:'none'},objectName:'항목원'+(i+1)});
    T(s,String(i+1),{x:M,y,w:0.46,h:0.46,fontSize:15,bold:true,color:C.background1,align:'center',valign:'middle',objectName:'항목번호'+(i+1)});
    T(s,t,{x:M+0.65,y,w:CW-0.65,h:0.46,fontSize:20,valign:'middle',objectName:'항목'+(i+1)});});
  s=pres.addSlide(); s.background={color:L?C.background1:C.background2};
  T(s,'03',{x:M,y:M,w:2,h:1.0,fontSize:54,bold:true,color:C.accent1,objectName:'번호'});
  place(s,ic.calendar,false,1.4,RE,M+0.12);
  T(s,'언제, 어디서',{x:M,y:2.3,w:CW,h:0.9,fontSize:32,bold:true,objectName:'제목'});
  [['기간','0. 0. ~ 0. 0.'],['장소','0층 강의실'],['대상','누구나'],['비용','무료']].forEach(([k,v],i)=>{const col=i%2,row=Math.floor(i/2),w=(CW-0.3)/2,x=M+col*(w+0.3),y=3.6+row*1.25;
    T(s,k,{x,y,w,h:0.35,fontSize:15,color:C.accent6,objectName:'정보라벨'+(i+1)});
    T(s,v,{x,y:y+0.38,w,h:0.5,fontSize:22,bold:true,objectName:'정보값'+(i+1)});
    s.addShape(pres.shapes.LINE,{x,y:y+1.0,w,h:0,line:{color:C.accent3,width:0.75},objectName:'정보선'+(i+1)});});
  s=pres.addSlide(); s.background={color:C.background1};
  T(s,'기한 안에\n꼭 확인하세요',{x:M,y:M,w:CW,h:1.9,fontSize:34,bold:true,objectName:'제목'});
  T(s,'자세한 내용은 기관 누리집에서 볼 수 있습니다.',{x:M,y:2.8,w:CW,h:0.5,fontSize:15,color:C.accent6,objectName:'설명'});
  const btn={x:M,y:BE-1.35,w:CW,h:0.8,fontSize:20,bold:true,shape:pres.shapes.ROUNDED_RECTANGLE,rectRadius:0.12,align:'center',valign:'middle',objectName:'버튼'};
  T(s,'자세히 보기',L?Object.assign(btn,{color:C.accent1,line:{color:C.accent1,width:1.5}}):Object.assign(btn,{color:C.background1,fill:{color:C.accent1}}));
  T(s,'기관명',{x:M,y:BE-0.35,w:CW,h:0.35,fontSize:12,color:C.accent6,align:'center',valign:'bottom',objectName:'기관명'});
  const f=`${dir}/카드뉴스_1대1_${p.name}${L?'_가볍게':SUF()}.pptx`; await pres.writeFile({fileName:f}); await applyTheme(f,TH); require('child_process').execFileSync('python3',[__dirname+'/fixfont.py',FONT,f]); return f;
}

(async()=>{for(const p of PALS){ if(only&&!only.includes(p.id))continue;
  const dir=`${OUT}/${String(PALS.indexOf(p)+1).padStart(2,'0')}_${p.name}`; fs.mkdirSync(dir,{recursive:true});
  const ic=await icons(p,dir); const ONLY=(process.env.PONLY||'deck,a4,sq').split(','); const STS=(process.env.PSTY||'base,light,rich').split(','); for(const ST of STS){const L=ST==='light'; RICH=ST==='rich';if(ONLY.includes('deck'))await deck(p,dir,L); if(ONLY.includes('a4'))await a4(p,dir,ic,L); if(ONLY.includes('sq'))await sq(p,dir,ic,L);} console.log('built',p.name);}})().catch(e=>{console.error(e);process.exit(1)});
