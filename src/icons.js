// 도장(스탬프) 느낌 아이콘: 거친 가장자리 + 잉크 빠진 점. 직접 그린 원본 도형.
const ICONS = {
  house:{n:'집', m:'M16 50 L50 20 L84 50 L76 50 L76 84 L24 84 L24 50 Z M43 84 L43 66 Q50 58 57 66 L57 84 Z', a:'M63 31 L63 20 L71 20 L71 38 Z'},
  doc:{n:'서류', m:'M24 14 L62 14 L78 30 L78 86 L24 86 Z M34 42 L68 42 L68 47 L34 47 Z M34 55 L68 55 L68 60 L34 60 Z M34 68 L56 68 L56 73 L34 73 Z', a:'M62 14 L78 30 L62 30 Z'},
  pencil:{n:'연필', m:'M30 80 L22 82 L24 74 L64 30 L74 40 Z', a:'M66 28 L72 22 Q76 19 80 23 L82 25 Q85 29 82 32 L76 38 Z'},
  book:{n:'책', m:'M12 28 Q31 21 48 30 L48 80 Q31 72 12 78 Z M52 30 Q69 21 88 28 L88 78 Q69 72 52 80 Z', a:''},
  moon:{n:'달과 별', m:'M54 18 A32 32 0 1 0 82 66 A26 26 0 1 1 54 18 Z', a:'M76 20 L79 29 L88 32 L79 35 L76 44 L73 35 L64 32 L73 29 Z'},
  scale:{n:'저울', m:'M47 22 L53 22 L53 78 L66 78 L68 86 L32 86 L34 78 L47 78 Z M20 34 L80 34 L80 39 L20 39 Z M12 58 L36 58 Q34 70 24 70 Q14 70 12 58 Z M64 58 L88 58 Q86 70 76 70 Q66 70 64 58 Z', a:'M50 12 A6 6 0 1 1 49.9 12 Z'},
  calc:{n:'계산기', m:'M24 12 L76 12 Q82 12 82 18 L82 82 Q82 88 76 88 L24 88 Q18 88 18 82 L18 18 Q18 12 24 12 Z M28 22 L72 22 L72 38 L28 38 Z M28 48 L40 48 L40 58 L28 58 Z M44 48 L56 48 L56 58 L44 58 Z M28 64 L40 64 L40 74 L28 74 Z M44 64 L56 64 L56 74 L44 74 Z', a:'M60 48 L72 48 L72 74 L60 74 Z'},
  stamp:{n:'도장', m:'M42 14 L58 14 Q62 14 62 20 Q62 30 56 36 L56 50 L74 50 Q80 50 80 56 L80 66 L20 66 L20 56 Q20 50 26 50 L44 50 L44 36 Q38 30 38 20 Q38 14 42 14 Z', a:'M18 74 L82 74 L82 84 L18 84 Z'},
  bulb:{n:'전구', m:'M50 12 A26 26 0 0 1 66 58 Q62 62 62 68 L38 68 Q38 62 34 58 A26 26 0 0 1 50 12 Z', a:'M38 72 L62 72 L62 78 L38 78 Z M42 82 L58 82 Q56 88 50 88 Q44 88 42 82 Z'},
  calendar:{n:'달력', m:'M16 24 L84 24 L84 84 L16 84 Z M24 44 L36 44 L36 54 L24 54 Z M44 44 L56 44 L56 54 L44 54 Z M64 44 L76 44 L76 54 L64 54 Z M24 62 L36 62 L36 72 L24 72 Z M44 62 L56 62 L56 72 L44 72 Z', a:'M28 14 L35 14 L35 32 L28 32 Z M65 14 L72 14 L72 32 L65 32 Z M64 62 L76 62 L76 72 L64 72 Z'},
  search:{n:'돋보기', m:'M42 14 A28 28 0 1 1 41.9 14 Z M42 24 A18 18 0 1 0 42.1 24 Z', a:'M60 64 L68 56 L88 76 Q90 80 86 84 Q82 88 78 84 Z'},
  sprout:{n:'새싹', m:'M47 44 L53 44 L53 66 L47 66 Z M26 66 L74 66 L68 88 L32 88 Z', a:'M50 46 Q26 46 20 22 Q44 20 50 46 Z M50 40 Q56 16 82 16 Q80 42 50 40 Z'}
};
function svg(key, main, acc, size=512, seed=3){
  const i = ICONS[key];
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 100 100">
<defs><filter id="f" x="-10%" y="-10%" width="120%" height="120%">
<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="${seed}" result="n"/>
<feDisplacementMap in="SourceGraphic" in2="n" scale="3.4" xChannelSelector="R" yChannelSelector="G" result="r"/>
<feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="1" seed="${seed+4}" result="g"/>
<feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -10 0 0 0 7.4" result="h"/>
<feComposite in="r" in2="h" operator="in"/></filter></defs>
<g filter="url(#f)"><path fill="${main}" fill-rule="evenodd" d="${i.m}"/>${i.a?`<path fill="${acc}" fill-rule="evenodd" d="${i.a}"/>`:''}</g></svg>`;
}
module.exports = { ICONS, svg };
