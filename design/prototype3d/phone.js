// The in-game phone: a complete device, always upright (the owner's word of 11 Nov 2026). It opens small at the side
// of the screen, the game going on beside it: a look at the balance and at the red dots, nothing more (a tap on it
// does nothing; a drag over it turns the view as anywhere else). A long press on it enlarges it, whole, in the middle
// of the screen, the scene dimmed behind: the same phone drawn larger, as large as the screen's height allows (the
// owner, 13 Nov); a tap outside it makes it small again. It shows the player's own game only, from the rules engine
// (setGame), and sends the player's orders to it (setEngine): the home screen (the date and its season, the balance,
// the herd), الوايت and العلف (approved 12 Nov: design/ui/phone_supplies.html), الحليب and العزبة (13 Nov:
// design/ui/phone_start_*.jpg), الحراج (13 Nov: design/ui/phone_haraj.jpg), البنك (13 Nov: design/ui/phone_bank.jpg),
// المزاين and «المحادثات», the treatment man's secret chat (13 Nov: design/ui/phone_mazayen.jpg).
// The design's other screens (design/ui/phone.html: auction, a talk with a buyer, weather) and the other apps come in as each works on the
// engine; until then they are not shown (the owner, 13 Nov: no example content in a new game).
// Light: plain DOM in a shadow root (its styles and the page's cannot touch each other), no canvas, no blur; while it
// is enlarged the page stops drawing the 3D scene (farm.html).
const SMALL = 0.4, SMALL_ROOM = 105;      // the small phone's scale at most, and the height left clear above it (the top row of buttons), px
const LONG_PRESS = 450, SLOP = 10;        // ms held, and px moved at most, for a long press
const DOUBLE_TAP = 400;                   // ms after a screen changes, or a sale is readied, in which a tap is the second of a double tap
const SURE_FOR = 5000;                    // ms a sale readied by its first tap waits for the second
const W = 334, H = 712, EDGE = 10;        // the device at true size, and its margin from the screen's top and bottom when enlarged, px

const CSS = `
  :host { position: absolute; inset: 0; z-index: 40; pointer-events: none; }
  *, *::before, *::after { -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; -webkit-tap-highlight-color: transparent; }      /* (a long press selects nothing and calls nothing out: farm.html's top) */
  img, svg { -webkit-user-drag: none; }
  input, textarea, [contenteditable]:not([contenteditable="false"]) { -webkit-user-select: text; user-select: text; -webkit-touch-callout: default; }      /* (a text field, if one is ever added, is typed in and selected as anywhere) */
  .phone { position: absolute; inset: 0; overflow: hidden; color-scheme: light; }
  .dim { position: absolute; inset: 0; background: rgba(12, 8, 4, 0.55); display: none; pointer-events: auto; touch-action: none; }
  .dev { position: absolute; width: ${W}px; height: ${H}px; border-radius: 50px; padding: 9px; background: linear-gradient(145deg, #4a4036, #1d1813 40%, #2b241d);
    box-shadow: inset 0 0 0 1.5px rgba(255, 255, 255, .12), 0 30px 60px rgba(0, 0, 0, .55); touch-action: none; user-select: none; -webkit-user-select: none; -webkit-tap-highlight-color: transparent; }
  .phone[data-state="closed"] .dev { display: none; }
  .dev:focus { outline: none; }
  .phone[data-state="small"] .dev { right: var(--r); bottom: var(--b); transform-origin: 100% 100%; transform: scale(var(--s)); pointer-events: none; }
  .phone[data-state="big"] .dim { display: block; }
  .phone[data-state="big"] .dev { left: 50%; top: 0; margin-left: ${-W / 2}px; transform-origin: 50% 0; transform: translateY(var(--y)) scale(var(--sb, 1)); pointer-events: auto; will-change: transform; }
  [data-go], .back, button { cursor: pointer; }
  /* enlarged: the small phone's own screens, the whole device drawn as large as the screen's height allows (0.59 of true
     size at 956 x 440), nothing re-arranged (the owner, 13 Nov: the content magnified to true size and re-flowed for its
     narrow width was "not a phone's proportions", the dock over the widgets). An app longer than the screen scrolls; its
     top bar stays. */
  .phone[data-state="big"] .body { overflow-y: auto; overscroll-behavior: contain; touch-action: pan-y; }
  .phone[data-state="big"] .nav { position: sticky; top: -1px; margin-top: -1px; padding-top: 1px; z-index: 3; background: var(--bg); box-shadow: 0 -3px 0 var(--bg); }      /* (held a pixel past the scroll's top edge, where it already rests, and painted a little above itself: that edge falls between two of the screen's pixels, and a row of the scrolled content showed there; resting a pixel lower, it stepped up as a scroll began) */
  * { box-sizing: border-box; margin: 0; }
  .phone { font-family: "IBM Plex Sans Arabic", system-ui, sans-serif; font-size: 13px; line-height: 1.35; -webkit-font-smoothing: antialiased; font-variant-numeric: tabular-nums; direction: rtl; text-align: start; text-wrap: pretty; --bg: #f2f2f7; --card: #ffffff; --ink: #111114; --ink2: #6e6e73; --line: #e5e5ea; --acc: #087a51; --acc-soft: #e3f4ec; --red: #d42f25; --amber: #a3660e; }      /* (each a little darker than approved, to 4.5:1 or better where it writes text, WCAG AA: green 4.37 → 5.37 under white and 3.83 → 4.71 on its pale chip, red 4.27 → 4.96, amber 3.45 → 4.70 on white, the proxy's T-B) */
  b.fit { font: inherit; }
  .num { font-family: "Marah Figures", "Alexandria", "IBM Plex Sans Arabic", sans-serif; }
  svg.i { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; flex: none; }
  button { font: inherit; color: inherit; border: 0; background: none; cursor: pointer; }
  .scr { position: relative; width: 100%; height: 100%; border-radius: 42px; overflow: hidden; background: var(--bg); color: var(--ink); display: flex; flex-direction: column; }
  .scr .pill { position: absolute; top: 9px; left: 50%; translate: -50% 0; width: 92px; height: 27px; border-radius: 14px; background: #000; z-index: 5; }
  .sbar { height: 46px; flex: none; display: flex; align-items: center; justify-content: space-between; padding: 6px 26px 0; font: 600 14px/1 "Marah Figures", "Alexandria", sans-serif; }
  .sbar .r { display: flex; gap: 5px; align-items: center; direction: ltr; }
  .sbar .bat { width: 22px; height: 11px; border-radius: 3.5px; border: 1.3px solid currentColor; position: relative; opacity: .85; }
  .sbar .bat::after { content: ""; position: absolute; inset: 1.3px; width: 60%; border-radius: 1.5px; background: currentColor; }
  .body { flex: 1; min-height: 0; overflow: hidden; padding: 2px 14px 0; display: flex; flex-direction: column; gap: 12px; }
  .hb { height: 4px; width: 110px; border-radius: 2px; background: rgba(0,0,0,.75); margin: 8px auto 8px; flex: none; }
  .ink2 { color: var(--ink2); }
  /* ---------- shared app pieces ---------- */
  .nav { display: flex; align-items: center; gap: 8px; height: 30px; }
  .nav .back { display: flex; align-items: center; gap: 2px; color: var(--acc); font-size: 14px; font-weight: 500; }
  .nav .back svg { width: 18px; height: 18px; stroke-width: 2.2; }
  .nav .end { margin-inline-start: auto; color: var(--acc); }
  .title { font: 700 27px/1.1 "Marah Figures", "Alexandria", sans-serif; }      /* (no tracking: letter-spacing pulls Arabic's joined letters apart, the audit) */
  .group { background: var(--card); border-radius: 16px; overflow: hidden; }
  .row { display: grid; grid-template-columns: 36px 1fr auto; column-gap: 11px; align-items: center; padding: 9px 12px; min-height: 52px; position: relative; }
  .row + .row::before { content: ""; position: absolute; top: 0; inset-inline: 59px 0; height: .5px; background: var(--line); }
  .row .lead { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; background: var(--acc-soft); color: var(--acc); grid-row: span 2; }
  .row .lead svg { width: 18px; height: 18px; }
  .row b { font-size: 13.5px; font-weight: 600; }
  .row small { font-size: 11.5px; color: var(--ink2); }
  .row .qty { grid-row: span 2; font: 600 14px/1 "Marah Figures", "Alexandria", "IBM Plex Sans Arabic", sans-serif; font-variant-numeric: tabular-nums; white-space: nowrap; }      /* (tabular after the font shorthand, which resets the phone's tabular-nums: the column's figures line up, the audit) */
  .pos { color: var(--acc); }
  .ltr { direction: ltr; unicode-bidi: isolate; display: inline-block; }
  .sec { font-size: 12px; font-weight: 600; color: var(--ink2); padding-inline: 4px; margin-bottom: -6px; }
  .btn { height: 44px; border-radius: 14px; font-weight: 700; font-size: 14px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding-inline: 16px; }
  .btn.pri { background: var(--acc); color: #fff; }
  .btn.ghost { background: var(--acc-soft); color: var(--acc); }
  /* ---------- home ---------- */
  .home { background: url(phone/wall_camel.png) 0% 104% / 124% auto no-repeat, linear-gradient(180deg, #cfe3f2 0%, #efe3cf 55%, #e2c9a2 100%); }
  .home .body { padding: 6px 18px 0; gap: 14px; }
  .widgets { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .wg { border-radius: 22px; padding: 12px 13px; background: rgba(255,255,255,.78); -webkit-backdrop-filter: none; height: 136px; display: flex; flex-direction: column; box-shadow: 0 4px 14px rgba(70,50,20,.10); }
  .wg small { font-size: 11.5px; font-weight: 600; color: var(--ink2); }
  .wg .big2 { font: 700 21px/1.1 "Marah Figures", "Alexandria", sans-serif; margin-top: 8px; }
  .wg .big2.bad { color: var(--red); }      /* (a balance under zero: «عليك», what the player owes) */
  .wg .ln { font-size: 11.5px; font-weight: 500; margin-top: auto; }
  .apps { display: grid; grid-template-columns: repeat(4, 1fr); row-gap: 14px; }
  .app { display: flex; flex-direction: column; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; color: #2b2116; position: relative; }
  .app .ic { width: 56px; height: 56px; border-radius: 15px; display: grid; place-items: center; background: #fff; color: var(--acc); box-shadow: 0 3px 8px rgba(70,50,20,.14); }
  .app .ic svg { width: 27px; height: 27px; stroke-width: 1.8; }
  .app .bd { position: absolute; top: -5px; left: 2px; min-width: 20px; height: 20px; border-radius: 10px; background: var(--red); color: #fff; font: 700 11px/20px "Marah Figures", "Alexandria", sans-serif; text-align: center; padding: 0 5px; }
  /* ---------- the segmented control (العلف's ration) ---------- */
  .seg { display: grid; grid-template-columns: 1fr 1fr 1fr; padding: 2px; border-radius: 10px; background: #e3e3e8; }
  .seg span { text-align: center; padding: 6px 0; border-radius: 8px; font-weight: 600; font-size: 12.5px; color: #3a3a3f; }
  .seg span.on { background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.12); color: var(--ink); }
  .hs { display: contents; }      /* (the home's widgets and apps laid out in the screen's own column) */
  .phone[data-state="big"] .fit { display: inline-block; white-space: nowrap; }      /* (a big number: shrunk to its card when it is wider, see fitNumbers) */
  .phone.turned[data-state="big"] .body { touch-action: none; }      /* (the game turned: the phone scrolls it itself, see drag) */
  /* ---------- الوايت and العلف (approved 12 Nov 2026: design/ui/phone_supplies.html) ---------- */
  .body > * { flex-shrink: 0; }
  .tank { background: var(--card); border-radius: 20px; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px; }
  .tank small { font-size: 12px; color: var(--ink2); font-weight: 500; }
  .tank .v { font: 700 30px/1.1 "Marah Figures", "Alexandria", sans-serif; letter-spacing: -.01em; display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 4px; }
  .tank .v span { font-size: 14px; font-weight: 600; color: var(--ink2); letter-spacing: normal; }      /* (the figure's tracking kept off its Arabic unit) */
  .tank .ln { font-size: 12px; font-weight: 500; }
  .bar { height: 8px; border-radius: 4px; background: #e8eef3; overflow: hidden; margin-block: 4px 2px; white-space: nowrap; }
  .bar i { display: inline-block; vertical-align: top; height: 100%; background: linear-gradient(90deg, #2f7fcf, #5aa8ea); }
  .bar.feed i { background: linear-gradient(90deg, #c58a2b, #e2b25c); }
  .bar.low i { background: var(--red); }
  .bar .in, .bar.feed .in { background: #ecd9b4; }
  .kind { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0 6px; font-size: 12.5px; font-weight: 600; margin-top: 6px; }
  .kind .d { color: var(--ink2); font-weight: 500; }
  .kind .d.bad { color: var(--red); font-weight: 700; }
  .warn { display: grid; grid-template-columns: 36px 1fr; column-gap: 11px; align-items: center; padding: 10px 12px; border-radius: 16px; background: #fff; box-shadow: inset 0 0 0 1.5px #f3c2bd; }
  .warn .lead { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; background: #fde6e4; color: var(--red); grid-row: span 2; align-self: start; }
  .warn b { font-size: 13.5px; } .warn small { font-size: 11.5px; color: var(--ink2); }
  .row .act { grid-row: span 2; }
  .row .act .btn { height: 36px; border-radius: 11px; font-size: 13px; padding-inline: 14px; }
  .btn[disabled] { background: #eeeef1; color: #a5a5ab; cursor: default; }
  .btn.two { height: auto; min-height: 44px; flex-direction: column; gap: 0; padding-block: 6px; line-height: 1.25; }
  .stp { display: flex; align-items: center; gap: 4px; }
  .stp button { width: 32px; height: 32px; border-radius: 10px; background: var(--acc-soft); color: var(--acc); display: grid; place-items: center; }
  .stp button[disabled] { background: #eeeef1; color: #b8b8bd; cursor: default; }
  .stp button svg { width: 16px; height: 16px; stroke-width: 2.6; }
  .stp .n { min-width: 54px; text-align: center; font-weight: 700; font-size: 13px; }
  .stp .n b { font: 700 15px/1 "Marah Figures", "Alexandria", sans-serif; font-variant-numeric: tabular-nums; }
  .row.ord .lead { grid-column: 1; grid-row: 1 / span 2; }
  .row.ord b { grid-column: 2; grid-row: 1; }
  .row.ord small { grid-column: 2; grid-row: 2; }
  .row.ord .stp { grid-column: 3; grid-row: 1 / span 2; }
  .order { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 6px 10px; background: var(--card); border-radius: 16px; padding: 10px 12px; }
  .order > span > small { font-size: 11.5px; color: var(--ink2); display: block; }
  .order .t { font: 700 18px/1.1 "Marah Figures", "Alexandria", sans-serif; }
  .order .t small { font-size: 11.5px; color: var(--ink2); }
  .order .btn { padding-inline: 26px; }
  .note { font-size: 11.5px; color: var(--ink2); padding-inline: 4px; margin-top: -6px; }
  .way .row { grid-template-columns: 36px 1fr; }
  .way .lead { background: #e6eef8; color: #2f7fcf; }
  .cmp { display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: center; font-size: 11px; color: var(--ink2); margin-top: -4px; }
  .cmp b { display: block; font: 700 12px/1.3 "Marah Figures", "Alexandria", sans-serif; color: var(--ink); }
  .seg span { cursor: pointer; }
  .hs .datebar { align-self: center; font-size: 12px; font-weight: 700; color: #2b2116; background: rgba(255,255,255,.7); border-radius: 12px; padding: 4px 12px; text-align: center; }
  .datebar span { white-space: nowrap; }
  /* ---------- البنك (approved 13 Nov 2026: design/ui/phone_bank.jpg, its styles from design/ui/phone.html) ---------- */
  .balance { background: var(--card); border-radius: 20px; padding: 14px 16px; display: flex; flex-direction: column; gap: 3px; }
  .balance small { font-size: 12px; color: var(--ink2); font-weight: 500; }
  .balance .v { font: 700 30px/1.1 "Marah Figures", "Alexandria", sans-serif; margin-top: 2px; letter-spacing: -.01em; white-space: nowrap; }
  .balance .v span { font-size: 15px; font-weight: 600; color: var(--ink2); margin-inline-start: 4px; letter-spacing: normal; }
  .balance .ln { font-size: 12px; font-weight: 500; }
  .balance .v.bad { color: var(--red); }      /* (a balance under zero: what the player owes, «عليك») */
  .row .amt { grid-row: span 2; font: 600 14px/1 "Marah Figures", "Alexandria", sans-serif; font-variant-numeric: tabular-nums; direction: ltr; unicode-bidi: isolate; white-space: nowrap; }
  .row .amt.pos { color: var(--acc); }
  .row .lead.out { background: #f1f1f4; color: #55555b; }
  /* ---------- الحراج (approved 13 Nov 2026: design/ui/phone_haraj.jpg, its list styles from design/ui/phone.html) ---------- */
  .seg.two { grid-template-columns: 1fr 1fr; }
  .seg .dot { display: inline-block; min-width: 17px; height: 17px; border-radius: 9px; background: var(--red); color: #fff; font: 700 10.5px/17px "Marah Figures", "Alexandria", sans-serif; text-align: center; padding: 0 4px; margin-inline-start: 3px; font-style: normal; vertical-align: 1px; }
  .lst { display: flex; flex-direction: column; gap: 8px; padding-bottom: 56px; }
  .lst.flat { padding-bottom: 0; }
  .it { display: grid; grid-template-columns: 70px 1fr; column-gap: 11px; padding: 8px; border-radius: 16px; background: var(--card); align-items: center; }
  .it .ph { width: 70px; height: 70px; border-radius: 12px; background: linear-gradient(180deg, #f3eadc, #e2cfae); overflow: hidden; grid-row: span 4; }
  .it .ph img { width: 100%; height: 100%; object-fit: contain; }
  .it .ph img.homr { filter: sepia(.6) saturate(1.8) hue-rotate(-12deg) brightness(.82); }      /* (no red camel's photo yet: the sorrel's, tinted, as the approved design has it) */
  .it b { font-size: 13.5px; font-weight: 700; }
  .it small { font-size: 11.5px; color: var(--ink2); }
  .it .pr { display: flex; align-items: center; }
  .it .pr .price { font: 700 15px/1 "Marah Figures", "Alexandria", sans-serif; font-variant-numeric: tabular-nums; margin-inline-end: auto; }
  .it.big { grid-template-columns: 96px 1fr; }
  .it.big .ph { width: 96px; height: 96px; grid-row: span 5; }
  .it.off { opacity: .55; }
  .sell { position: absolute; bottom: 26px; inset-inline: 14px; height: 46px; border-radius: 15px; background: var(--acc); color: #fff; font-weight: 700; font-size: 14.5px; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 6px 16px rgba(11,138,92,.35); z-index: 4; }
  .sell svg { width: 18px; height: 18px; stroke-width: 2.4; }
  .btn.wide { width: 100%; }
  .btn.sure { background: var(--red); color: #fff; }
  .row .act.two { display: flex; gap: 6px; }
  .row .act.two .btn { padding-inline: 11px; }
  .msgc { display: grid; grid-template-columns: 36px 1fr; column-gap: 11px; align-items: center; padding: 10px 12px; border-radius: 16px; background: #fff; }
  .msgc.good { box-shadow: inset 0 0 0 1.5px #bfe3d2; }
  .msgc .lead { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; background: var(--acc-soft); color: var(--acc); grid-row: span 2; align-self: start; }
  .msgc b { font-size: 13.5px; } .msgc small { font-size: 11.5px; color: var(--ink2); }
  .row.ord.full .stp { grid-row: 1; }      /* (a price's stepper: its line under it as well, not squeezed beside it) */
  .row.ord.full small { grid-column: 2 / 4; }
  .nw { white-space: nowrap; }
  /* ---------- المزاين and «المحادثات» (approved 13 Nov 2026: design/ui/phone_mazayen.jpg, its styles from design/ui/phone_mazayen.cjs) ---------- */
  .row .qty.ok { color: var(--acc); font: 600 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.now { color: var(--amber); font: 700 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.bad { color: var(--red); font: 700 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.wait { color: var(--ink2); font: 500 12px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row.now .lead { background: #fdf1dc; color: var(--amber); }
  .row.next .lead { background: #eeeef1; color: #a5a5ab; }
  .row.next b { color: var(--ink2); font-weight: 500; }
  .row.bad .lead { background: #fde6e4; color: var(--red); }
  .row .lead.rk { font: 700 15px/1 "Marah Figures", "Alexandria", sans-serif; }
  .row .lead.rk.g1 { background: #fbefd2; color: #8f620a; }
  .row.later .lead { background: #eeeef1; color: #8e8e93; }
  .row.two { grid-template-columns: 36px 1fr; }
  .row .qty .dot { display: inline-block; min-width: 20px; height: 20px; border-radius: 10px; background: var(--red); color: #fff; font: 700 11px/20px "Marah Figures", "Alexandria", sans-serif; text-align: center; padding: 0 5px; font-style: normal; }
  .row .lead.av2 { border-radius: 50%; background: #d9cbb4; color: #4a3720; font: 700 15px/1 "Marah Figures", "Alexandria", sans-serif; }
  .it small.bad, .row small.bad { color: var(--red); font-weight: 600; }
  .it.no .ph, .it.no b { opacity: .55; }
  .it.sel { box-shadow: inset 0 0 0 2px var(--acc); }
  .open { background: var(--card); border-radius: 18px; padding: 12px 14px; display: flex; flex-direction: column; gap: 3px; box-shadow: inset 0 0 0 1.5px #bfe3d2; }
  .open .tag { align-self: flex-start; font-size: 11px; font-weight: 700; color: var(--acc); background: var(--acc-soft); border-radius: 8px; padding: 2px 8px; }
  .open b { font: 700 17px/1.3 "Marah Figures", "Alexandria", sans-serif; }
  .open small { font-size: 12px; color: var(--ink2); }
  .chathd { display: flex; align-items: center; gap: 9px; }
  .chathd .av { width: 34px; height: 34px; border-radius: 50%; background: #d9cbb4; display: grid; place-items: center; font: 700 15px/1 "Marah Figures", "Alexandria", sans-serif; color: #4a3720; }
  .chathd b { font-size: 14.5px; display: block; line-height: 1.2; }
  .chathd small { font-size: 11px; color: var(--ink2); }
  .strip { display: flex; align-items: center; gap: 10px; padding: 7px; border-radius: 14px; background: var(--card); }
  .strip .ph { width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(180deg, #f3eadc, #e2cfae); overflow: hidden; flex: none; }
  .strip .ph img { width: 100%; height: 100%; object-fit: contain; }
  .strip b { font-size: 13px; display: block; }
  .strip small { font-size: 11px; color: var(--ink2); }
  .strip .lim { margin-inline-start: auto; text-align: end; font-size: 11px; color: var(--ink2); }
  .strip .lim span { display: block; font: 700 14px/1.1 "Marah Figures", "Alexandria", sans-serif; color: var(--ink); }
  .chat { display: flex; flex-direction: column; gap: 6px; }
  .msg { max-width: 82%; padding: 7px 11px; border-radius: 17px; font-size: 13px; line-height: 1.4; }
  .msg.them { align-self: flex-start; background: #e9e9eb; border-end-start-radius: 5px; }
  .msg.me { align-self: flex-end; background: var(--acc); color: #fff; border-end-end-radius: 5px; }
  .row .act .btn.pr { padding-inline: 10px; font-size: 12.5px; }
  /* ---------- the rush and التقويم (task T15: design/ui/phone_rush.jpg, phone_calendar.jpg, awaiting the owner's approval) ---------- */
  .row.r3 { grid-template-columns: 36px 1fr auto; }
  .row.r2 { grid-template-columns: 36px 1fr; }
  .row small.rush { grid-column: 2; }
  .row small.now, .note.now { color: var(--acc); font-weight: 700; }
  .lnk { grid-column: 2; justify-self: start; color: var(--acc); font: 700 11.5px/1.35 "IBM Plex Sans Arabic", sans-serif; padding: 2px 0; text-align: start; }
  .lnk.sure { color: var(--red); }
  .lnk[disabled] { color: #a5a5ab; cursor: default; }
  .row .act .btn.sm { height: 34px; padding-inline: 12px; font-size: 12.5px; }
  .row .lead.bad { background: #fde6e4; color: var(--red); }
  .row .lead.fest { background: #fbefd2; color: #a8730c; }
  .row .lead.milk { background: #e6eef8; color: #2f7fcf; }
  .row .lead.sea { background: #f1f1f4; color: #55555b; }
  .row .chev { grid-row: span 2; color: #c4c4c9; } .row .chev svg { width: 16px; height: 16px; }
  .sw { display: block; width: 46px; height: 28px; border-radius: 14px; background: #e3e3e8; position: relative; flex: none; cursor: pointer; }
  .sw i { position: absolute; top: 2px; right: 2px; width: 24px; height: 24px; border-radius: 12px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.25); }
  .sw.on { background: var(--acc); } .sw.on i { right: auto; left: 2px; }
  .yr { background: var(--card); border-radius: 16px; padding: 10px 12px 8px; display: flex; flex-direction: column; gap: 5px; }
  .yr .m { display: grid; grid-template-columns: 50px 1fr; align-items: center; column-gap: 8px; height: 17px; }
  .yr .m > span { font-size: 11px; font-weight: 600; color: var(--ink2); }
  .yr .m > span.now { color: var(--ink); font-weight: 700; }
  .yr .t { position: relative; height: 12px; border-radius: 3px; background: #ececf0; overflow: hidden; }
  .yr .t i { position: absolute; top: 0; bottom: 0; }
  .yr .t i.past { background: #f7f7f9; }
  .yr .t i.brd { top: auto; height: 3px; background: #57b88a; }
  .yr .t i.reg { background: #f6e3b8; }
  .yr .t i.fest { background: #d9a033; top: 2px; bottom: 2px; border-radius: 2px; }
  .yr .t i.me { width: 6px; height: 6px; top: 3px; border-radius: 3px; background: var(--red); margin-right: -3px; }
  .yr .t i.milk { background: #2f7fcf; }
  .yr .t i.today { width: 2px; background: var(--ink); margin-right: -1px; top: -1px; bottom: -1px; }
  .key { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 11px; color: var(--ink2); padding-inline: 4px; margin-top: -4px; }
  .key span { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
  .key i { display: inline-block; width: 12px; height: 8px; border-radius: 2px; }
  .cal { background: var(--card); border-radius: 16px; padding: 10px 10px 8px; display: grid; grid-template-columns: repeat(7, 1fr); row-gap: 4px; text-align: center; }
  .cal .wd { font-size: 10.5px; font-weight: 600; color: var(--ink2); }
  .cal .d { height: 30px; display: grid; place-items: center; font: 600 13px/1 "Alexandria", sans-serif; border-radius: 9px; position: relative; color: var(--ink); }
  .cal .d.past { color: #c4c4c9; cursor: default; }
  .cal .d.fest { background: #fbefd2; color: #7a530a; }
  .cal .d.sel { background: var(--acc); color: #fff; }
  .cal .d.brd::after { content: ""; position: absolute; bottom: 3px; left: 50%; width: 4px; height: 4px; margin-left: -2px; border-radius: 2px; background: #57b88a; }
  .cal .d.sel::after { background: #fff; }
  .span { background: var(--card); border-radius: 16px; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; }
  .span b { font: 700 15px/1.3 "Alexandria", sans-serif; }
  .span small { font-size: 12px; color: var(--ink2); }
  .stops { font-size: 12px; line-height: 1.55; background: var(--card); border-radius: 16px; padding: 10px 12px; color: var(--ink); }
  .calnav { display: flex; justify-content: space-between; align-items: center; }
  .calnav button { color: var(--acc); font-weight: 700; font-size: 13px; padding: 4px 6px; }
  .calnav button[disabled] { color: #c4c4c9; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }      /* (what is said after an order, for a screen reader: outside the screen the redraws replace) */
`;

const I = {
    truck: '<path d="M2.5 6.5h11v9.5h-11z"/><path d="M13.5 9.5h4.2l3.3 3.6V16h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    water: '<path d="M12 3.5s6 6.4 6 10.6a6 6 0 0 1-12 0C6 9.9 12 3.5 12 3.5z"/>',
    feed: '<rect x="4" y="7" width="16" height="11" rx="2"/><path d="M9.5 7v11M14.5 7v11"/>',
    back: '<path d="M9 6l6 6-6 6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    leaf: '<path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z"/><path d="M5 19 13 11"/>',
    minus: '<path d="M5 12h14"/>',
    alert: '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>',
    milk: '<path d="M8.5 3.5h7M9 3.5v3l-2.2 3.3a3 3 0 0 0-.5 1.7v7.5a1.5 1.5 0 0 0 1.5 1.5h8.4a1.5 1.5 0 0 0 1.5-1.5V11.5a3 3 0 0 0-.5-1.7L15 6.5v-3"/><path d="M6.4 13h11.2"/>',
    build: '<path d="M3.5 20.5h17"/><path d="M5.5 20.5V10l6.5-5 6.5 5v10.5"/><path d="M10 20.5v-5h4v5"/>',
    camel: '<path d="M3 8.5c0-1 .8-1.6 1.7-1.6h.9c.9 0 1.5.7 1.4 1.6l-.2 1.2c-.1.8.2 1.5.8 2 .5.4 1.1.4 1.6 0 .5-.5.9-1 1.1-1.6.9-1.7 2.5-2.8 4.4-2.7 1.1.1 2.1.8 2.7 1.8.5.8 1.1 1.3 2 1.6 1.1.4 1.9 1.5 1.9 2.8V15c0 .6-.4 1.2-.9 1.5V20"/><path d="M6.4 12.2V20M9.5 15.5V20M15 15.5V20"/>',
    pen: '<path d="M4 20V7l2-2 2 2v13M16 20V7l2-2 2 2v13M8 10h8M8 15h8"/>',
    tank: '<rect x="6" y="4" width="12" height="11" rx="3"/><path d="M8 15v5M16 15v5M6 9h12"/>',
    store: '<path d="M3 11 12 5l9 6"/><path d="M5 10v10h14V10"/><path d="M9 20v-5h6v5"/>',
    caravan: '<rect x="3" y="7" width="15" height="9" rx="2"/><path d="M18 13h3M6 16v2M7 10h3v3H7zM12 10h3"/>',
    tent: '<path d="M2.5 18 8 8h8l5.5 10z"/><path d="M8 8l-2 10M16 8l2 10M12 8v10"/>',
    room: '<path d="M4 20V9l8-5 8 5v11z"/><path d="M9 20v-6h6v6M8 11h2M14 11h2"/>',
    haraj: '<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>',
    user: '<circle cx="12" cy="8" r="3.2"/><path d="M5.5 19.5c.6-3.3 3-5 6.5-5s5.9 1.7 6.5 5"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    talk: '<path d="M4 5.5h16v10H9l-5 4z"/>',
    // المزاين (design/ui/phone_mazayen.cjs)
    cup: '<path d="M7.5 4h9v5.5a4.5 4.5 0 0 1-9 0z"/><path d="M7.5 6H4.8c0 2.4 1.2 3.8 3.2 4.2M16.5 6h2.7c0 2.4-1.2 3.8-3.2 4.2"/><path d="M12 14v3.5M9.5 17.5h5v3h-5z"/>',
    x: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    dot: '<circle cx="12" cy="12" r="4.2" fill="currentColor"/>',
    herd: '<path d="M2.5 10.5c0-.8.6-1.3 1.3-1.3h.7c.7 0 1.2.6 1.1 1.3l-.2 1c0 .6.2 1.2.6 1.6.4.3.9.3 1.3 0 .4-.4.7-.8.9-1.3.7-1.4 2-2.3 3.5-2.2.9.1 1.7.7 2.2 1.5.4.6.9 1 1.6 1.3.9.3 1.5 1.2 1.5 2.2v1.2"/><path d="M5.6 13.4v5M8 15.9v2.5M12.5 15.9v2.5"/><path d="M14 6.5c.5-1.2 1.6-1.9 2.9-1.8.9.1 1.6.6 2.1 1.4.3.5.7.8 1.2 1 .7.3 1.2 1 1.2 1.8"/>',
    rule: '<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/>',
    chip: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M9.5 3v3.5M14.5 3v3.5M9.5 17.5V21M14.5 17.5V21M3 9.5h3.5M3 14.5h3.5M17.5 9.5H21M17.5 14.5H21"/>',
    eye: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.6"/>',
    scope: '<path d="M6 3.5v6a4 4 0 0 0 8 0v-6"/><path d="M10 13.5v2a4.5 4.5 0 0 0 9 0v-2"/><circle cx="19" cy="11.5" r="2"/>',
    star: '<path d="M12 3.8l2.5 5.2 5.7.8-4.1 4 1 5.6-5.1-2.7-5.1 2.7 1-5.6-4.1-4 5.7-.8z"/>',
    chev: '<path d="M15 6l-6 6 6 6"/>',
    bank: '<path d="M3.5 9.5 12 4l8.5 5.5"/><path d="M5.5 10v7.5M10 10v7.5M14 10v7.5M18.5 10v7.5"/><path d="M3.5 20h17"/>',
    // the rush and التقويم (T15)
    cal: '<rect x="4" y="5.5" width="16" height="14.5" rx="2.5"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/><path d="M8 14h2M14 14h2M8 17h2"/>',
    fast: '<path d="M12 3.5v4M12 16.5v4M3.5 12h4M16.5 12h4"/><circle cx="12" cy="12" r="4.5"/>',
    heart: '<path d="M12 19.5s-7-4.3-7-9.5a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.2-7 9.5-7 9.5z"/>',
    sun: '<circle cx="12" cy="12" r="3.8"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/>',
    flag: '<path d="M5.5 21V4M5.5 4.5h11l-2 3.5 2 3.5h-11"/>',
    stop: '<rect x="7" y="7" width="10" height="10" rx="2"/>',
    repeat: '<path d="M4 9.5a6 6 0 0 1 10.5-4l2 2M20 14.5a6 6 0 0 1-10.5 4l-2-2"/><path d="M16.5 3.5v4h-4M7.5 20.5v-4h4"/>',
  };
const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
// the status bar: the time is the player's own clock (kept to the minute while the phone is out)
const clockText = () => { const d = new Date(); return `${d.getHours() % 12 || 12}:${String(d.getMinutes()).padStart(2, '0')}`; };
const sbar = () => `<div class="sbar"><span class="clk">${clockText()}</span><span class="r"><svg width="16" height="11" viewBox="0 0 18 12" fill="currentColor"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1" opacity=".35"/></svg><span class="bat"></span></span></div>`;
// the top bar: رجوع goes home, or to the screen [to] (الحراج's pages, one inside another)
const nav = (end = '', to = '') => `<div class="nav"><button class="back"${to ? ` data-go="${to}"` : ''}>${svg('back')}رجوع</button>${end ? `<span class="end">${end}</span>` : ''}</div>`;
const APP_GO = { water: 'water', feed: 'feed', milk: 'milk', build: 'build', haraj: 'haraj', bank: 'bank', cup: 'mazayen', talk: 'chats', cal: 'cal' };      // the apps that open a screen
const badgeSaid = (extra, k) => { const m = extra.match(/class="bd">(\d+)</); return !m ? '' : k === 'haraj' ? `، ${count(Number(m[1]), 'bid')}` : k === 'cup' ? `، ${count(Number(m[1]), 'news')}` : k === 'talk' ? `، ${count(Number(m[1]), 'message')}` : k === 'water' ? '، الماء يخلص' : m[1] === '1' ? '، صنف يخلص' : '، الشعير والبرسيم يخلصون'; };
const app = (k, n, extra = '') => `<div class="app"${APP_GO[k] ? ` data-go="${APP_GO[k]}" role="button" tabindex="0" aria-label="${n}${badgeSaid(extra, k)}"` : ''}>${extra}<span class="ic">${svg(k)}</span><span>${n}</span></div>`;      // (named by the app and its badge)


// ---------------------------------------------------------------- the game's own numbers (the rules engine, engine.js)
// G: the engine's latest view of the game (marah_runtime's SnapshotJson); null until it has started. ORD: the feed order
// being made up (bags and bales), set when العلف opens. ERR: the engine's refusal of the last order, said on the screen
// until the next tap.
let G = null, ERR = null;
const ORD = { barley: null, alfalfa: null };
const n0 = (v) => Math.round(v).toLocaleString('en-US');
// the GDD's counting rule (9, «الكتابة»): one and two by the word, 3 to 10 the plural, 11 and up the singular
const NOUN = {
  day: ['يوم واحد', 'يومين', 'أيام', 'يوم'],
  bag: ['كيس واحد', 'كيسين', 'أكياس', 'كيس'],
  bale: ['بالة وحدة', 'بالتين', 'بالات', 'بالة'],
  tanker: ['وايت واحد', 'وايتين', 'وايتات', 'وايت'],
  head: ['راس واحد', 'راسين', 'روس', 'راس'],
  month: ['شهر واحد', 'شهرين', 'شهور', 'شهر'],
  shepherd: ['راعي واحد', 'راعيين', 'رعاة', 'راعي'],
  camel: ['ناقة وحدة', 'ناقتين', 'نياق', 'ناقة'],
  year: ['سنة وحدة', 'سنتين', 'سنين', 'سنة'],
  bid: ['سومة وحدة', 'سومتين', 'سومات', 'سومة'],
  order: ['طلب واحد', 'طلبين', 'طلبات', 'طلب'],          // (البنك: a feed or water order)
  trip: ['نقلة وحدة', 'نقلتين', 'نقلات', 'نقلة'],         // (a truck's trip: a camel home, to a stud, to a festival)
  treat: ['علاج واحد', 'علاجين', 'علاجات', 'علاج'],       // (the vet's treatment)
  prize: ['جائزة وحدة', 'جائزتين', 'جوائز', 'جائزة'],
  mating: ['تلقيح واحد', 'تلقيحين', 'تلقيحات', 'تلقيح'],   // (a stud's fee, one a mating)
  build: ['منشأة وحدة', 'منشأتين', 'منشآت', 'منشأة'],
  time: ['مرة وحدة', 'مرتين', 'مرات', 'مرة'],
  entry: ['تسجيل واحد', 'تسجيلين', 'تسجيلات', 'تسجيل'],  // (البنك: a late festival entry's fee)
  fine: ['غرامة وحدة', 'غرامتين', 'غرامات', 'غرامة'],
  news: ['خبر واحد', 'خبرين', 'أخبار', 'خبر'],           // (المزاين's badge: a registration open, a stage told, a result)
  message: ['رسالة وحدة', 'رسالتين', 'رسايل', 'رسالة'],   // («المحادثات»'s badge)
  fest: ['مهرجان واحد', 'مهرجانين', 'مهرجانات', 'مهرجان'],
  edition: ['دورة وحدة', 'دورتين', 'دورات', 'دورة'],
  bull: ['فحل واحد', 'فحلين', 'فحول', 'فحل'],
  rush: ['استعجال واحد', 'استعجالين', 'استعجالات', 'استعجال'],   // (البنك: what was hurried, T15)
};
const count = (n, k) => { const [one, two, few, many] = NOUN[k]; return n === 1 ? one : n === 2 ? two : n >= 3 && n <= 10 ? `${n} ${few}` : `${n} ${many}`; };
const days = (n) => count(n, 'day');
// a stepper's word under its number: the number is shown, so one takes the bare singular and two the dual
const unitWord = (n, k) => { const [one, two, few, many] = NOUN[k]; return n === 2 ? two : n >= 3 && n <= 10 ? few : n === 1 ? one.split(' ')[0] : many; };
const WEEKDAY = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
const MONTH = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
// the seasons of the Najdi calendar, by their start (month, day; research section 7): الوسم from about 16 October for 52
// days, المربعانية 40 days from 7 December, الشبط from 15 January, العقارب from 10 February for 39 days, and سهيل from
// its rising about 24 August. Between them the plain seasons, a game choice: الربيع from 21 March, القيظ from 1 June
// (the folk names there vary by source and year)
const SEASONS = [[1, 15, 'الشبط'], [2, 10, 'العقارب'], [3, 21, 'الربيع'], [6, 1, 'القيظ'], [8, 24, 'سهيل'], [10, 16, 'الوسم'], [12, 7, 'المربعانية']];
function season(d) {
  const m = d.getUTCMonth() + 1, day = d.getUTCDate();
  let name = 'المربعانية';
  for (const [sm, sd, n] of SEASONS) if (m > sm || (m === sm && day >= sd)) name = n;
  return name;
}
function dateLine() {
  if (!G) return '';
  const d = new Date(G.date + 'T00:00:00Z');
  const first = `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`;
  const second = [season(d), G.breedingSeason ? 'وقت الضراب' : null].filter(Boolean).join(' · ');
  return `<div class="datebar"><span>${first}</span><span class="sep"> · </span><span>${second}</span></div>`;
}
const sup = (k) => G.farm.supplies.find((x) => x.supply === k);
// the red badges: the supplies that will not last three days (or did not cover the day)
const lowCount = (keys) => !G ? 0 : keys.filter((k) => { const x = sup(k); return x.short || (x.daysLeft != null && x.daysLeft <= 3); }).length;
const badge = (n) => n ? `<span class="bd">${n}</span>` : '';
const waiting = () => `<div class="note" style="margin-top:6px">يجهّز…</div>`;
const alertCard = (title, line) => `<div class="warn"><span class="lead">${svg('alert')}</span><b>${title}</b><small>${line}</small></div>`;
const errCard = () => ERR ? alertCard('ما تم الطلب', ERR) : '';
// cash below zero (wages or a fine can take it there: the owner's decision 8): no camel bought and nothing built till
// it is paid
const debtLine = () => `عليك دين ${n0(-G.cash)} ريال: ما تقدر تشتري حلال ولا تبني لين تسدد.`;
// the merchant's account (the owner's decisions 9 and 10): feed, water and the vet go on it when the money does not
// cover them, up to its limit. [cost]: what the money does not cover goes on it; null when it is past the limit
// (the engine's account.spend: the most an order of necessities may cost now, the money above zero and the room left on
// the account; what the money does not cover goes on it. Each tanker comes quoted: t.goes, t.onAccount)
function onAccount(cost) {
  const A = G.farm.account, short = Math.max(0, cost - Math.max(0, G.cash));
  if (cost > A.spend) return null;
  return { short, owed: A.owed + short };
}
const accountLine = (owed) => `على الحساب: عليك للتاجر ${n0(owed)} ريال من حده ${n0(G.farm.account.limit)} ريال`;
const accountFullLine = () => `حساب التاجر وصل حده ${n0(G.farm.account.limit)} ريال: بيع من حلالك أو سدد.`;
// a treatment's kind in the phone's words
const TAMPER = { botox: 'بوتوكس', filler: 'فيلر', hormones: 'هرمونات', lipStretch: 'شد الشفة', teethFiling: 'برد الأسنان', tailCut: 'قص الذيل', dye: 'صبغ' };
const tamperNames = (ks) => ks.map((k) => TAMPER[k] || 'تجميل').join(' و');
// a treatment found in one of his camels (GDD 7.1), said on الحراج's answer card: by a buyer's or the broker's look
// before paying (the sale off), or outside a sale (the vet, the daily look). With the fine when there is one; with no
// fine (he bought her treated without knowing: the owner's decision 15) that he was not fined and knows now, and that
// it goes in time. [who]: the one who looked, or null.
function foundWords(name, kinds, fine, who, male) {
  const what = tamperNames(kinds), hf = (f, m) => (male ? m : f);
  const title = who ? `${esc(who)} فحص ${esc(name)} ولقى ${hf('فيها', 'فيه')} ${what}` : `انكشف إن ${esc(name)} ${hf('فيها', 'فيه')} ${what}`;
  const off = who ? 'البيعة انلغت' : '';
  const rest = fine > 0
    ? `وانكتبت عليك غرامة ${n0(fine)} ريال.`
    : `ما تتغرم لأنك ما دريت، والحين صرت تدري. التجميل يروح مع الوقت، ولو ${hf('بعتها', 'بعته')} ساكت قبل وانكشف تتغرم.`;
  return { title, line: off ? `${off}، ${rest}` : rest };
}
// treatments found outside a festival and a sale (the daily look, the vet) are told once on الحراج's answer card, the
// oldest first, from the engine's untold list (G.findings), and marked told there (markFindingsTold): none missed, none
// told twice, whether the phone was shut or the game restarted
const FEED = { barley: 'شعير', alfalfa: 'برسيم' };
const stepper = (k, n, unit, canUp) => `<span class="stp"><button data-act="step" data-s="${k}" data-d="-1" aria-label="${FEED[k]} أقل" ${n ? '' : 'disabled'}>${svg('minus')}</button><span class="n"><b>${n}</b> <span>${unit}</span></span><button data-act="step" data-s="${k}" data-d="1" aria-label="${FEED[k]} أكثر" ${canUp ? '' : 'disabled'}>${svg('plus')}</button></span>`;
// where the feed is kept: the start's shade until the store is built (the review: العلف spoke of a store the farm has not)
const built = (f) => (G ? G.farm.facilities.find((x) => x.facility === f) : null);
const hasStore = () => (built('store')?.has ?? 0) > 0;
const STORE = () => (hasStore()
  ? { name: 'مستودع العلف', the: 'المستودع', to: 'للمستودع', holds: 'يشيل', lasts: 'يكفي', none: 'ما فيه' }
  : { name: 'مظلة العلف', the: 'المظلة', to: 'للمظلة', holds: 'تشيل', lasts: 'تكفي', none: 'ما فيها' });
// the engine's refusal of [command] in words
function refusal(r, command) {
  const code = r.error?.code, p = r.error?.params || {};
  // الحراج's refusals by the camel's sex (the one on the page: a listing's or one's own)
  const subj = command.listing ? listingOf(command.listing)?.camel : command.camel ? myCamel(command.camel) : null;
  const hf = (f, m) => (subj && subj.sex === 'male' ? m : f);
  const water = command.supply === 'water', st = STORE();
  const where = water ? 'الخزان' : st.the, holds = water ? 'يشيل' : st.holds, none = water ? 'ما فيه' : st.none;
  const unit = water ? 'tanker' : command.supply === 'barley' ? 'bag' : 'bale';
  if (code === 'inDebt') return debtLine();
  if (code === 'accountFull') return accountFullLine();
  // the rush (T15): cash only; a stale hour; a day the herd was not short
  if (code === 'priceChanged') return 'السعر تغيّر مع الوقت: شوفه مرة ثانية.';
  if (code === 'notShortToday') return p.supply === 'water' ? 'حلالك شرب كفايته اليوم: الطلبة العادية توصل قبل شربه بكرة.' : 'حلالك شبع اليوم: الطلبة العادية توصل قبل علفته بكرة.';
  if (code === 'nothingToRush') return 'ما فيه شي بالطريق تستعجله.';
  if (code === 'contractState') return 'العقد تغيّر: شوفه مرة ثانية.';
  if (/^rush|^setStanding|Vet/.test(command.type || '') || command.now) {
    if (code === 'insufficientFunds') return `رصيدك ما يكفي: تبي ${n0(p.needed ?? 0)} ريال من رصيدك.`;
    return 'جرّب مرة ثانية.';
  }
  if (command.type === 'treat') {
    if (code === 'notSick') return 'ما عادت مريضة.';
    return 'جرّب مرة ثانية.';
  }
  if (command.type === 'buyListing' || command.type === 'bargain') {
    if (code === 'insufficientFunds') return `رصيدك ما يكفي: تبي ${n0(p.needed ?? 0)} ريال مع النقل.`;
    if (code === 'farmFull') return 'عزبتك مليانة: ابنِ شبك من العزبة.';
    if (code === 'notFound') return hf('انباعت قبل لا توصلها.', 'انباع قبل لا توصله.');
    if (code === 'sellerRefusesBargaining') return 'البايع ما عاد يقبل منك سوم.';
    if (code === 'invalidAmount') return 'السوم لازم يكون فوق الصفر.';
    return 'جرّب مرة ثانية.';
  }
  if (command.type === 'listForSale' || command.type === 'quickSale') {
    if (code === 'alreadyListed') return hf('معروضة بالحراج من قبل، شوفها بإعلاناتي.', 'معروض بالحراج من قبل، شوفه بإعلاناتي.');
    if (code === 'enteredInContest') return hf('مشاركة بمزاين، اسحبها منه أول.', 'مشارك بمزاين، اسحبه منه أول.');
    if (code === 'onTheWay') return hf('ما وصلت عزبتك للحين، توصل بكرة.', 'ما وصل عزبتك للحين، يوصل بكرة.');
    if (code === 'invalidAmount') return `أقل سعر ${n0(G.haraj.minAsk)} ريال.`;
    if (code === 'notYourCamel' || code === 'notFound') return hf('ما عادت عندك.', 'ما عاد عندك.');
    return 'جرّب مرة ثانية.';
  }
  if (command.type === 'acceptOffer' || command.type === 'declineOffer' || command.type === 'cancelListing') {
    if (code === 'notFound') return 'السوم انتهى أو الإعلان انشال.';
    return 'جرّب مرة ثانية.';
  }
  if (command.type === 'buildFacility') {
    if (code === 'insufficientFunds') return `رصيدك ما يكفي: البناء بـ ${n0(p.needed ?? 0)} ريال.`;
    if (code === 'alreadyBuilt') return 'هذا مبني أو ينبني.';
    return 'جرّب مرة ثانية.';
  }
  if (code === 'insufficientFunds') return `رصيدك ما يكفي: الطلب بـ ${n0(p.needed ?? 0)} ريال.`;
  if (code === 'storeFull') return p.room ? `${where} ما ${holds} إلا ${count(p.room, unit)} بعد.` : `${where} ${none} مكان الحين.`;
  return 'جرّب مرة ثانية.';
}

function waterScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">الوايت</div>${waiting()}</div>`;
  const f = G.farm, w = sup('water'), need = w.need, have = w.amount, coming = w.onTheWayAmount;
  const lasts = need > 0 ? Math.floor(have / need) : null;
  const pct = (v) => Math.max(0, Math.min(100, v / f.tankL * 100));
  let warn = '';
  if (f.dryDays > 0) {
    // deaths begin the day after the herd's limit (the limit's day itself it still lasts)
    const left = f.thirstDays - f.dryDays;
    warn = alertCard(`الحلال عطشان من ${days(f.dryDays)}`, `${left > 0 ? `باقي ${days(left)} ويبدأ يموت` : left === 0 ? 'يبدأ يموت بكرة' : 'بدأ يموت من العطش'}، وحالته تنزل كل يوم. اطلب اليوم يوصل بكرة.`);
  } else if (w.short || have <= 0) {
    warn = alertCard('الماء خلص', 'الحلال ما شرب كفايته اليوم. اطلب اليوم يوصل بكرة.');
  } else if (lasts != null && lasts <= 3) {
    warn = alertCard(lasts <= 1 ? 'الماء يخلص بكرة' : `الماء يخلص بعد ${days(lasts)}`, 'اطلب اليوم يوصل بكرة.');
  }
  const row = (t) => {
    const tonnes = Math.round(t.litres / 1000), name = `وايت ${tonnes} طن`;
    // the engine's rule: a tanker fills the tank to the top and takes the rest back, so it is taken once there is room
    // for half its load; a tank smaller than that never takes it (a bigger one is built from العزبة)
    let line;
    const fill = Math.min(t.litres, Math.max(0, f.tankL - have - coming));
    if (t.room > 0) line = `${n0(t.price)} ريال · ${fill < t.litres ? `يعبّي الخزان ${n0(fill)} لتر والباقي يرجع` : need > 0 ? `يكفي ${days(Math.floor(t.litres / need))}` : 'يوصل بكرة'}`;
    else if (f.tankL < t.litres / 2) {
      const big = built('tank'), soon = big && big.building ? daysTo(big.doneOn) : null;
      line = soon != null ? `الخزان الكبير ينبني، يخلص ${soon <= 1 ? 'بكرة' : `بعد ${days(soon)}`}` : 'خزانك ما يشيله، ابنِ خزان أكبر من العزبة';
    }
    else {
      const under = f.tankL - t.litres / 2, wait = need > 0 ? Math.ceil((have + coming - under) / need) : null;
      line = `الخزان ما يشيله لين ينزل تحت ${n0(under)} لتر${wait ? `، بعد ${days(wait)} تقريبًا` : ''}`;
    }
    const acc = t.goes ? { short: t.onAccount, owed: f.account.owed + t.onAccount } : null;
    if (t.room > 0 && acc && acc.short > 0) line = `${n0(t.price)} ريال · ${accountLine(acc.owed)}`;
    else if (t.room > 0 && !acc) line = `${n0(t.price)} ريال · ${accountFullLine()}`;
    const can = t.room > 0 && acc != null;
    // a short day: the tanker can come now and the herd drinks today (the rush at ordering, cash only)
    const nowFee = (RU().tankerNow || {})[t.tanker];
    const now = can && nowFee != null && G.cash >= t.price + nowFee ? nowLink(`tankerNow:${t.tanker}`, `data-act="tankerNow" data-t="${t.tanker}" aria-label="اطلب ${name} يوصل الحين بـ ${n0(t.price + nowFee)} ريال"`, `أو يوصل الحين ويشربون اليوم بـ ${n0(t.price + nowFee)} ريال`, `اضغط مرة ثانية ويوصل الحين بـ ${n0(t.price + nowFee)} ريال`) : '';
    return `<div class="row"><span class="lead">${svg('water')}</span><b>${name}</b><span class="act"><button class="btn ${can ? 'pri' : ''}" data-act="tanker" data-t="${t.tanker}" aria-label="اطلب ${name}" ${can ? '' : 'disabled'}>اطلب</button></span><small>${line}</small>${now}</div>`;
  };
  // on its way: rushed only on a day the herd went short (it then drinks today); else the ordinary one is in time
  const rw = RU().rushWater;
  const wayRow = !coming ? '' : rw != null
    ? `<div class="sec">بالطريق</div><div class="group way"><div class="row r3"><span class="lead">${svg('truck')}</span><b>${n0(coming)} لتر</b>${rushBtn('rushWater', 'data-act="rushWater"', `استعجل الوايت بـ ${n0(rw)} ريال`, G.cash >= rw)}<small>${G.cash >= rw ? (HJ.sure === 'rushWater' ? `يوصل الحين ويشربون، وتدفع ${n0(rw)} ريال زيادة` : `يوصل بكرة · الحين بـ ${n0(rw)} ريال زيادة`) : `الاستعجال ${n0(rw)} ريال، ورصيدك ${n0(G.cash)}`}</small></div></div>
      <div class="note">حلالك ما شرب كفايته اليوم. لو استعجلته يوصل الحين ويشربون، وما ينحسب اليوم عطش.${coming > f.tankL - have ? ' ويعبّي الخزان والباقي يرجع.' : ''}</div>`
    : `<div class="sec">بالطريق</div><div class="group way"><div class="row"><span class="lead">${svg('truck')}</span><b>${n0(coming)} لتر</b><small>الطلبة العادية توصل قبل شرب حلالك بكرة</small></div></div>
      ${coming > f.tankL - have ? '<div class="note">يعبّي الخزان، والباقي يرجع.</div>' : ''}`;
  const bar = `<div class="bar${f.dryDays > 0 ? ' low' : ''}"><i style="width:${pct(have).toFixed(1)}%"></i>${coming ? `<i class="in" style="width:${(pct(have + coming) - pct(have)).toFixed(1)}%"></i>` : ''}</div>`;
  return `<div class="body">${nav()}<div class="title">الوايت</div>${errCard()}${warn}
    <div class="tank"><small>خزان العزبة · ${n0(f.tankL)} لتر</small><div class="v"><b class="fit">${n0(have)}</b><span>لتر</span></div>
      ${bar}
      <div class="ln">${lasts ? `يكفي ${days(lasts)} · ` : ''}يشربون ${n0(need)} لتر باليوم</div></div>
    <div class="sec">اطلب وايت</div>
    <div class="group">${f.tankers.map(row).join('')}</div>
    ${coming ? wayRow : '<div class="note">بالطريق: ما فيه وايت.</div>'}
    ${standingRow('water', 'يجيك وايت بنفسه', 'لما يبقى بالخزان 3 أيام، الوايت اللي يدخله، وتدفعه مثل أي طلب (على الحساب لو رصيدك ما كفى)')}</div>`;
}

// a feed's need over [weeks], less what is in store and on its way, in whole units
const suggest = (x, weeks = 3) => Math.max(0, Math.ceil((x.need * 7 * weeks - x.amount - x.onTheWayAmount) / x.unitSize));
// the store's room left (kg), orders on the way counted
const storeRoom = (f, b, a) => f.storeKg - (b.amount + a.amount + b.onTheWayAmount + a.onTheWayAmount);
// [nb] bags and [na] bales cut down, in proportion, to what the store still holds
function fitRoom(nb, na, b, a, room) {
  const kg = nb * b.unitSize + na * a.unitSize;
  if (kg <= room || kg <= 0) return [nb, na];
  const k = Math.max(0, room) / kg;
  return [Math.floor(nb * k), Math.floor(na * k)];
}
function feedScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">العلف</div>${waiting()}</div>`;
  const f = G.farm, b = sup('barley'), a = sup('alfalfa'), room = storeRoom(f, b, a);
  if (ORD.barley == null) [ORD.barley, ORD.alfalfa] = fitRoom(suggest(b), suggest(a), b, a, room);
  const lastsOf = (x) => x.need > 0 ? Math.floor(x.amount / x.need) : null;
  const lb = lastsOf(b), la = lastsOf(a);
  const out = (x, l) => x.short || x.amount <= 0 || l === 0;
  const line = (name, x, l) => {
    const withOrder = x.need > 0 && x.onTheWayAmount ? Math.floor((x.amount + x.onTheWayAmount) / x.need) : null;
    const full = 21, now = Math.min(100, (l ?? full) / full * 100), all = Math.min(100, (withOrder ?? 0) / full * 100);
    const bad = !withOrder && (out(x, l) || (l != null && l <= 3));
    const today = out(x, l) ? 'خلص' : l == null ? '' : days(l);
    const tail = withOrder != null ? `${today}، و${days(withOrder)} لما يوصل` : today;
    return `<div class="kind"><span>${name} ${n0(x.amount)} كجم</span><span class="d${bad ? ' bad' : ''}">${tail}</span></div><div class="bar feed${bad ? ' low' : ''}"><i style="width:${now.toFixed(1)}%"></i>${withOrder != null ? `<i class="in" style="width:${Math.max(0, all - now).toFixed(1)}%"></i>` : ''}</div>`;
  };
  const ST = STORE();
  const store = `<div class="tank"><small>${ST.name} · ${n0(f.storeKg)} كجم</small>${line('شعير', b, lb)}${line('برسيم', a, la)}
      <div class="ln">ياكلون باليوم ${n0(b.need)} كجم شعير و${n0(a.need)} كجم برسيم</div></div>`;
  const usedKg = ORD.barley * b.unitSize + ORD.alfalfa * a.unitSize;
  const total = ORD.barley * b.unitPrice + ORD.alfalfa * a.unitPrice;
  const rows = (canUp) => `<div class="group">
      <div class="row ord"><span class="lead">${svg('feed')}</span><b>شعير</b>${stepper('barley', ORD.barley, unitWord(ORD.barley, 'bag'), canUp(b))}<small>الكيس ${b.unitSize} كجم بـ ${n0(b.unitPrice)} ريال</small></div>
      <div class="row ord"><span class="lead">${svg('leaf')}</span><b>برسيم</b>${stepper('alfalfa', ORD.alfalfa, unitWord(ORD.alfalfa, 'bale'), canUp(a))}<small>البالة ${a.unitSize} كجم بـ ${n0(a.unitPrice)} ريال</small></div></div>`;
  const canUp = (x) => usedKg + x.unitSize <= room;
  // three weeks that do not fit in the store: the order is cut to what does, and the heading says so
  const cut = suggest(b) * b.unitSize + suggest(a) * a.unitSize > room;
  const heading = (ordered) => `<div class="sec">${ordered ? 'اطلب زيادة' : cut ? `اطلب على قد ${ST.the}` : suggest(b) + suggest(a) > 0 ? 'اطلب لـ 3 أسابيع' : 'اطلب'}</div>`;
  const ordered = b.onTheWayAmount || a.onTheWayAmount;
  // past the merchant's account: as the approved short-of-money screen has it, the warning and a week's order first
  // (an order the money does not cover goes on the account, up to its limit: the owner's decisions 9 and 10)
  const acc = onAccount(total);
  if (!acc) {
    const [wb, wa] = fitRoom(suggest(b, 1), suggest(a, 1), b, a, room), wt = wb * b.unitPrice + wa * a.unitPrice;
    const week = wt > 0 && onAccount(wt) != null;
    return `<div class="body">${nav()}<div class="title">العلف</div>${errCard()}
      ${alertCard('حساب التاجر وصل حده', `حده ${n0(G.farm.account.limit)} ريال: بيع من حلالك أو سدد.${week ? ` يكفي لأسبوع: ${[wb ? count(wb, 'bag') : '', wa ? count(wa, 'bale') : ''].filter(Boolean).join(' و')}.` : ''}`)}
      ${week ? `<button class="btn ghost two" data-act="week"><span>اطلب لأسبوع</span><span>${n0(wt)} ريال</span></button>` : ''}
      ${store}${heading(ordered)}${rows(canUp)}
      <div class="order"><span><small>المجموع</small><span class="t num">${n0(total)} <small>ريال</small></span></span><button class="btn" disabled>اطلب</button></div></div>`;
  }
  let warn = '';
  const lowB = out(b, lb) || (lb != null && lb <= 3), lowA = out(a, la) || (la != null && la <= 3);
  if ((lowB || lowA) && !ordered) {
    // each feed as it is (one out and the other low are said apart); the two together when they are the same
    const state = (x, l, two) => out(x, l) ? (two ? 'خلصوا' : 'خلص') : `${two ? 'يخلصون' : 'يخلص'} ${l <= 1 ? 'بكرة' : `بعد ${days(l)}`}`;
    const gone = (lowB && out(b, lb)) || (lowA && out(a, la));
    const title = lowB && lowA && state(b, lb) === state(a, la) ? `الشعير والبرسيم ${state(b, lb, true)}`
      : [lowB ? `الشعير ${state(b, lb)}` : '', lowA ? `البرسيم ${state(a, la)}` : ''].filter(Boolean).join(' و');
    warn = alertCard(title, gone ? 'الحلال ما شبع اليوم وحالته تنزل. اطلب اليوم يوصل بكرة.' : 'اطلب اليوم يوصل بكرة قبل العلفة.');
  }
  const plans = { economy: 'خفيفة', standard: 'عادية', premium: 'قوية' };
  const R = f.rations, cur = R.find((r) => r.plan === f.feedPlan);
  const ration = `<div class="sec">العليقة</div>
    <div class="seg" role="group" aria-label="العليقة">${R.map((r) => `<span data-act="plan" data-p="${r.plan}" role="button" tabindex="0" aria-pressed="${r.plan === f.feedPlan}" ${r.plan === f.feedPlan ? 'class="on"' : ''}>${plans[r.plan]}</span>`).join('')}</div>
    <div class="cmp">${R.map((r) => `<span><b>${n0(r.costPerDay)} ريال</b>باليوم<br>حالة لين ${r.conditionTarget}</span>`).join('')}</div>
    <div class="note">${plans[cur.plan]} ${cur.asFedKg.toFixed(1)} كجم علف للراس الكبير باليوم (${cur.dryMatterKg} كجم مادة جافة)، <span class="ltr">${Math.round(cur.barleyShare * 100)}%</span> منها شعير. الحالة توصل لين حدها مع رعاية زينة.</div>`;
  // on its way: rushed (one trip for all of it) only on a day the herd went short of feed; else the ordinary delivery
  // comes before the herd eats tomorrow
  const rf = RU().rushFeed;
  const wayRows = [[b, 'شعير', 'bag'], [a, 'برسيم', 'bale']].filter(([x]) => x.onTheWayAmount).map(([x, nm, k]) => `<div class="row"><span class="lead">${svg('truck')}</span><b>${nm} · ${count(x.onTheWay, k)}</b><small>${n0(x.onTheWayAmount)} كجم · ${n0(x.onTheWay * x.unitPrice)} ريال · ${rf != null ? 'يوصل بكرة' : 'يوصل قبل علفة حلالك بكرة'}</small></div>`).join('');
  const rushRow = rf == null ? '' : `<div class="row r3"><span class="lead">${svg('fast')}</span><b>استعجل العلف</b>${rushBtn('rushFeed', 'data-act="rushFeed"', `استعجل العلف بـ ${n0(rf)} ريال`, G.cash >= rf)}<small>${G.cash >= rf ? (HJ.sure === 'rushFeed' ? `يوصل الحين ويشبعون، وتدفع ${n0(rf)} ريال زيادة` : `يوصل الحين كله بـ ${n0(rf)} ريال زيادة`) : `الاستعجال ${n0(rf)} ريال، ورصيدك ${n0(G.cash)}`}</small></div>`;
  const way = ordered ? `<div class="sec">بالطريق</div><div class="group way">${wayRows}${rushRow}</div>${rf != null ? '<div class="note">حلالك ما شبع اليوم. لو استعجلته يوصل الحين ويشبعون، وما تنزل حالتهم اليوم.</div>' : ''}` : '';
  let order;
  if (usedKg > room) order = `<div class="order"><span><small>${ST.the} ${ST.holds} ${n0(Math.max(0, room))} كجم بعد</small><span class="t num">${n0(total)} <small>ريال</small></span></span><button class="btn" disabled>اطلب</button></div>`;
  else if (total > 0) {
    // a short day: ordered and brought now (one trip; half the order again, at most the cap), the herd fed today
    const R = RU(), fee = R.feedShort ? Math.min(R.feedCap ?? 300, Math.round(total * (R.feedShare ?? 0.5))) : null;
    const now = fee != null && G.cash >= fee ? nowLink('feedNow', `data-act="feedNow" aria-label="اطلبها توصل الحين بـ ${n0(fee)} ريال زيادة"`, `أو اطلبها توصل الحين بـ ${n0(fee)} ريال زيادة: يشبعون اليوم`, `اضغط مرة ثانية وتوصل الحين بـ ${n0(fee)} ريال زيادة`) : '';
    order = `<div class="order"><span><small>المجموع · يوصل بكرة ${ST.to}</small><span class="t num">${n0(total)} <small>ريال</small></span></span><button class="btn pri" data-act="feed">اطلب</button></div>${now}${acc.short > 0 ? `<div class="note">${accountLine(acc.owed)}.</div>` : ''}`;
  }
  else order = `<div class="note">${suggest(b) + suggest(a) > 0 || ordered ? 'زد الكمية ويطلع لك المجموع وزر الطلب.' : `${ST.the} ${ST.lasts} أكثر من 3 أسابيع.`}</div>`;
  return `<div class="body">${nav()}<div class="title">العلف</div>${errCard()}${warn}
    ${store}${ration}${way}${heading(ordered)}${rows(canUp)}${order}
    ${standingRow('feed', 'يجيك العلف بنفسه', 'لما يبقى بالمخزن 3 أيام، شعير وبرسيم على قد العليقة لين يمتلي، وتدفعه مثل أي طلب (على الحساب لو رصيدك ما كفى)')}</div>`;
}

// days from today to an engine date ('YYYY-MM-DD')
const daysTo = (d) => Math.round((Date.parse(d + 'T00:00:00Z') - Date.parse(G.date + 'T00:00:00Z')) / 86400000);
const litres = (v) => `${(Math.round(v * 10) / 10).toLocaleString('en-US')} لتر`;
// a nursing camel's time since calving: days under a month, then months by the counting rule
const sinceCalving = (d) => d < 30 ? (d <= 1 ? 'من يوم' : `من ${days(d)}`) : `من ${count(Math.floor(d / 30), 'month')}`;
// الحليب (approved 13 Nov 2026: design/ui/phone_start_milk.jpg): today's milk, what was sold, each nursing camel, and how
// much the calves keep, each choice with what it brings a day and what it does to the calves
function milkScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">الحليب</div>${waiting()}</div>`;
  const M = G.farm.milk, cs = M.camels;
  // the day's milking as it was sold (the share changed since, the list's litres follow the new share: the review)
  const total = M.litres, sold = M.incomeToday / M.price, kept = Math.max(0, total - sold);
  const calves = cs.filter((c) => c.calfName).length;
  // a calf by its own sex: حوارها, or حوارتها for a she-calf (the re-review: the alert said حوارتها, this screen حوارها)
  const calfWord = (m) => (m.calfSex === 'female' ? 'حوارتها' : 'حوارها');
  const one = cs.find((c) => c.calfName);
  const keptTo = calves > 1 ? 'للحيران' : `ل${one ? calfWord(one) : 'حوارها'}`;
  if (!cs.length) {
    return `<div class="body">${nav()}<div class="title">الحليب</div>${errCard()}
      <div class="tank"><small>حليب اليوم</small><div class="v"><b class="fit">0</b><span>لتر</span></div>
        <div class="ln ink2">ما عندك ناقة مرضع. الناقة تدر سنة من ولادتها.</div>
        ${M.thisMonth ? `<div class="ln ink2">دخل الحليب هالشهر ${n0(M.thisMonth)} ريال</div>` : ''}</div></div>`;
  }
  let line;
  if (M.incomeToday) line = `بعت ${litres(sold)} بـ ${n0(M.incomeToday)} ريال${kept > 0.05 ? `، وخليت ${keptTo} ${litres(kept)}` : ''}`;
  else if (M.sold > 0) line = `يمر المشتري بكرة وياخذ ${litres(M.sold)}`;      // (a new game's first day, or the share just changed from all: nothing sold today)
  else line = `خليته كله ${keptTo}`;
  const rows = cs.map((c) => `<div class="row"><span class="lead">${svg('camel')}</span><b>${c.name}</b><span class="qty">${litres(c.litres)}</span><small>مرضع ${sinceCalving(c.days)} · ${c.calfName ? `${calfWord(c)} ${c.calfName}` : 'حليبها كله ينباع'}</small></div>`).join('');
  // each choice: the riyals a day (a camel without her calf sells all hers whatever the choice), and the calves'
  // growth by the engine's rule (Balance.calfMilkTarget): in their first three months a half share already slows them
  const share = { all: 1, half: 0.5, quarter: 0.25 }, names = { all: 'كله', half: 'النص', quarter: 'الربع' };
  const young = cs.some((c) => c.calfName && c.days < 90);
  const grows = young ? { all: 'يكبر أحسن', half: 'يكبر أبطأ', quarter: 'يضعف' } : { all: 'يكبر أحسن', half: 'يكبر عادي', quarter: 'يكبر أبطأ' };
  const perDay = (k) => Math.round(cs.reduce((n, c) => n + c.litres * (c.calfName ? 1 - share[k] : 1), 0) * M.price);
  const keys = ['all', 'half', 'quarter'];
  const seg = calves ? `<div class="sec">كم تخلي للحوار</div>
    <div class="seg" role="group" aria-label="كم تخلي للحوار">${keys.map((k) => `<span data-act="share" data-p="${k}" role="button" tabindex="0" aria-pressed="${M.calfShare === k}" ${M.calfShare === k ? 'class="on"' : ''}>${names[k]}</span>`).join('')}</div>
    <div class="cmp">${keys.map((k) => `<span><b>${n0(perDay(k))} ريال</b>باليوم<br>${grows[k]}</span>`).join('')}</div>` : '';
  return `<div class="body">${nav()}<div class="title">الحليب</div>${errCard()}
    <div class="tank"><small>حليب اليوم</small><div class="v"><b class="fit">${(Math.round(total * 10) / 10).toLocaleString('en-US')}</b><span>لتر</span></div>
      <div class="ln">${line}</div>
      <div class="ln ink2">دخل الحليب هالشهر ${n0(M.thisMonth)} ريال</div></div>
    <div class="sec">الحلايب${M.nursing > cs.length ? ` · ${n0(M.nursing)}` : ''}</div>
    <div class="group">${rows}</div>${M.nursing > cs.length ? `<div class="note">وغيرها ${M.nursing - cs.length === 1 ? 'ناقة مرضع وحدة' : `${count(M.nursing - cs.length, 'camel')} مرضع`}.</div>` : ''}
    ${seg}
    <div class="note">المشتري يمر كل يوم وياخذ الحليب، اللتر بـ ${n0(M.price)} ريال. الحوار يرضع لين يكمل سنة، وأول 3 شهور يبي حليب أمه كله.</div></div>`;
}

// العزبة (approved 13 Nov 2026: design/ui/phone_start_build.jpg): what the farm has, and the facilities it can build
// ---------------------------------------------------------------- the rush (T15: design/ui/phone_rush.jpg, awaiting
// the owner's approval). What money can hurry finishes now for more, from cash only, asked twice (it cannot be
// undone): a facility being built, a camel on the truck, and water or feed only on a day the herd went short (the
// rushed delivery makes good today's loss; on other days the ordinary delivery is in time and the row says so). The
// engine prices it (the snapshot's rush), except the truck's, which falls with the game's hour (its shares given).
const RU = () => (G && G.rush) || {};
// the game's hour by the engine's clock (sent with each snapshot) carried on by the wall clock: 7 game minutes a real
// minute. The engine checks it again (this hour or the one before; a stale one is refused and the row drawn again)
const gameHour = () => { if (!G || G.minute == null) return 0; const m = G.minute + (Date.now() - (G.minuteAt || Date.now())) * 7 / 60000; return Math.max(0, Math.min(23, Math.floor(m / 60))); };
const truckFee = (trucking, hour = gameHour()) => { const R = RU(); return Math.round(trucking * (R.truckShare ?? 0.5) * Math.max(R.truckFloor ?? 0.2, (24 - hour) / 24) / 5) * 5; };
// a rush's button on a row: «استعجل», then red «أكّد» for its second tap
const rushBtn = (key, attrs, label, can) => { const sure = HJ.sure === key; return `<span class="act"><button class="btn sm ${!can ? '' : sure ? 'sure' : 'ghost'}" ${attrs} aria-label="${sure ? 'أكّد ' : ''}${label}" ${can ? '' : 'disabled'}>${sure ? 'أكّد' : 'استعجل'}</button></span>`; };
// the rush at ordering: a line under the row's own («أو ابنه الحين بـ …»), asked twice too (where it sits is the
// owner's eye: drawn here as the design has it)
const nowLink = (key, attrs, text, sureText) => { const sure = HJ.sure === key; return `<button class="lnk${sure ? ' sure' : ''}" ${attrs}>${sure ? sureText : text}</button>`; };
// a camel on the truck by the day's purchase (the yard leaves camels on the truck out)
const onTruck = () => (RU().trucks || []).map((t) => ({ ...t, male: t.sex === 'male' }));
// the vet's quote for a sick camel, and the contract (T15: design/ui/phone_calendar.jpg's العزبة)
const sinceSick = (x) => { const d = G.today - (x.sickSince ?? G.today); const f = x.sex !== 'male'; return d <= 0 ? (f ? 'مريضة من اليوم' : 'مريض من اليوم') : `${f ? 'مريضة' : 'مريض'} من ${days(d)}`; };
const sickRow = (x) => {
  const f = x.sex !== 'male', acc = onAccount(x.quote);
  const line = [sinceSick(x), `البيطري\u00a0${n0(x.quote)} ريال`, `${f ? 'تطيب' : 'يطيب'} بـ ${x.recoverMin} إلى\u00a0${days(x.recoverMax)}`].join(' · ');
  return `<div class="row r3"><span class="lead bad">${svg('heart')}</span><b>${esc(x.name)} · ${esc(x.illnessName)}</b><span class="act"><button class="btn sm ${acc ? 'pri' : ''}" data-act="treat" data-id="${esc(x.camel)}" aria-label="${f ? 'عالج' : 'عالج'} ${esc(x.name)} بـ ${n0(x.quote)} ريال" ${acc ? '' : 'disabled'}>${f ? 'عالجها' : 'عالجه'}</button></span><small>${line}</small>${acc && acc.short > 0 ? `<small class="rush">${accountLine(acc.owed)}</small>` : !acc ? `<small class="rush">${accountFullLine()}</small>` : ''}</div>`;
};
function vetRows() {
  const v = RU().vet;
  if (!v) return '';
  if (v.on) {
    const ends = v.endsOn != null;
    return `<div class="row r3"><span class="lead">${svg('heart')}</span><b>عقد البيطري</b>${ends ? '' : rushLike('vetCancel', 'data-act="vetCancel"', 'ألغه', 'ألغ عقد البيطري', true)}<small>${ends ? `ينتهي ${dShortAt(v.endsOn)}، وما يرجع شي من رسومه` : `عندك عقد: ${n0(v.monthly)} ريال بالشهر، ويعالج اللي يمرض بيومه`}</small></div>`;
  }
  const can = G.cash >= v.part;
  return `<div class="row r3"><span class="lead">${svg('heart')}</span><b>عقد البيطري</b>${rushLike('vetSign', 'data-act="vetSign"', 'اتعاقد', 'اتعاقد مع البيطري', can)}<small>${n0(v.monthly)} ريال بالشهر (1,000 و20 للراس)، ويعالج اللي يمرض بيومه بسعر العلاج</small><small class="rush">${can ? `هالشهر ${n0(v.part)} ريال من رصيدك` : `يبي ${n0(v.part)} ريال من رصيدك، ورصيدك ما يكفي`}</small></div>`;
}
// a two-tap button with its own word (the contract)
const rushLike = (key, attrs, word, label, can) => { const sure = HJ.sure === key; return `<span class="act"><button class="btn sm ${!can ? '' : sure ? 'sure' : 'ghost'}" ${attrs} aria-label="${sure ? 'أكّد ' : ''}${label}" ${can ? '' : 'disabled'}>${sure ? 'أكّد' : word}</button></span>`; };
const dShortAt = (day) => { const d = new Date(Date.parse(G.date + 'T00:00:00Z') + (day - G.today) * 864e5); return `${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
// a standing order's switch (الوايت, العلف): one tap, it can be turned off again
const standingRow = (kind, title, line) => {
  const on = (RU().standing || []).includes(kind);
  return `<div class="sec">طلب ثابت</div><div class="group"><div class="row r3"><span class="lead">${svg('repeat')}</span><b>${title}</b><span class="act"><span class="sw${on ? ' on' : ''}" data-act="standing" data-k="${kind}" role="switch" tabindex="0" aria-checked="${on}" aria-label="${title}"><i></i></span></span><small>${line}</small></div></div>`;
};

const FAC = {
  pen: { icon: 'pen', what: 'يشيل 10 روس زيادة' },
  tank: { name: 'خزان 30 طن', icon: 'tank', what: 'يشيل وايت 19 طن' },
  store: { name: 'مستودع علف', icon: 'store', what: 'يشيل 10 طن علف' },
  caravan: { name: 'كرفان الراعي', icon: 'caravan', what: 'لازم قبل الراعي' },
  tent: { name: 'بيت الشعر', icon: 'tent', what: 'للضيوف والقهوة' },
  room: { name: 'غرفة العزبة', icon: 'room', what: 'جلسة ومكيفات' },
};
const PEN_NTH = ['ثاني', 'ثالث', 'رابع', 'خامس', 'سادس'];
function buildScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">العزبة</div>${waiting()}</div>`;
  const f = G.farm, F = Object.fromEntries(f.facilities.map((x) => [x.facility, x]));
  const kind = (label, value) => `<div class="kind"><span>${label}</span><span class="d">${value}</span></div>`;
  const pens = F.pen.has, store = F.store.has;
  const care = f.shepherdsNeeded === 0 ? `أنت ترعاها لين ${count(f.ownerTendsUpTo, 'head')}` : f.shepherds >= f.shepherdsNeeded ? count(f.shepherds, 'shepherd') : 'تحتاج راعي';
  const have = `<div class="tank"><small>عزبتك</small>
      ${kind(pens ? 'الشبوك' : 'الحوش', `يشيل ${count(f.capacity, 'head')} · عندك ${n0(G.herd.total)}`)}
      ${kind('الخزان', `${n0(f.tankL)} لتر`)}
      ${kind(store ? 'العلف' : 'مظلة العلف', `${n0(f.storeKg)} كجم`)}
      ${kind('الرعاية', care)}</div>`;
  const row = (x) => {
    const d = FAC[x.facility], made = x.has + x.building;
    const nameOf = (n) => (x.facility === 'pen' ? `شبك ${PEN_NTH[Math.min(n, PEN_NTH.length - 1)]}` : d.name);
    const out = [];
    for (let k = 0; k < x.building; k++) {      // (each one being built, by its own name: «شبك ثالث … ينبني» named the next pen, the review)
      const soon = daysTo(x.doneOns?.[k] ?? x.doneOn);      // (each its own day: three days from its own order)
      const approved = `ينبني، يخلص ${soon <= 1 ? 'بكرة' : `بعد ${days(soon)}`}`;
      // the earliest of its kind can be hurried (the engine's price), its approved line kept and the rush after it
      const rb = k === 0 ? (RU().builds || []).find((y) => y.facility === x.facility) : null;
      if (!rb) { out.push(`<div class="row"><span class="lead">${svg(d.icon)}</span><b>${nameOf(x.has + k)}</b><small>${approved}</small></div>`); continue; }
      const key = `rushBuild:${x.facility}`, can = G.cash >= rb.fee, name = nameOf(x.has + k);
      const extra = !can ? `الاستعجال ${n0(rb.fee)} ريال، ورصيدك ${n0(G.cash)}` : HJ.sure === key ? `يخلص الحين، وتدفع ${n0(rb.fee)} ريال زيادة` : `الحين بـ ${n0(rb.fee)} ريال زيادة`;
      out.push(`<div class="row r3"><span class="lead">${svg(d.icon)}</span><b>${name}</b>${rushBtn(key, `data-act="rushBuild" data-f="${x.facility}"`, `استعجل ${name} بـ ${n0(rb.fee)} ريال`, can)}<small>${approved}</small><small class="rush${HJ.sure === key ? ' now' : ''}">${extra}</small></div>`);
    }
    if (made < x.most) {
      const debt = x.cannot === 'inDebt', poor = debt || x.cannot === 'insufficientFunds', name = nameOf(made);
      const line = [d.what, `${n0(x.price)} ريال`, debt ? `عليك دين ${n0(-G.cash)} ريال` : poor ? 'رصيدك ما يكفي' : ''].filter(Boolean).join(' · ');
      // at ordering: built now for more, where the money covers it
      const fee = (RU().buildNow || {})[x.facility], all = x.price + (fee ?? 0);
      const now = !poor && fee != null && G.cash >= all ? nowLink(`buildNow:${x.facility}`, `data-act="buildNow" data-f="${x.facility}" aria-label="ابنِ ${name} الحين بـ ${n0(all)} ريال"`, `أو ابنه الحين بـ ${n0(all)} ريال`, `اضغط مرة ثانية ويخلص الحين بـ ${n0(all)} ريال`) : '';
      out.push(`<div class="row"><span class="lead">${svg(d.icon)}</span><b>${name}</b><span class="act"><button class="btn ${poor ? '' : 'pri'}" data-act="build" data-f="${x.facility}" aria-label="ابنِ ${name}" ${poor ? 'disabled' : ''}>ابنه</button></span><small>${line}</small>${now}</div>`);
    } else if (!x.building) {
      out.push(`<div class="row"><span class="lead">${svg(d.icon)}</span><b>${x.facility === 'pen' ? 'الشبوك' : d.name}</b><small>${x.facility === 'pen' ? 'بنيت الشبوك كلها' : 'مبني'}</small></div>`);
    }
    return out.join('');
  };
  // the sick, with the vet's price (the phone's first treatment: T15), and the vet's contract
  const sick = RU().sick || [], all = RU().sickCount ?? sick.length;
  // a large herd: the first ones by name, how many more, and one «عالجهم كلهم» (its total first; two taps)
  const more = all - sick.length, accAll = all > 1 ? onAccount(RU().treatAll) : null;
  const treatAll = all > 1 ? `<div class="row r3"><span class="lead bad">${svg('heart')}</span><b>${more > 0 ? `وغيرها ${count(more, 'head')}` : `${count(all, 'head')} مريضة`}</b>${rushLike('treatAll', 'data-act="treatAll"', 'عالجهم', `عالج ${count(all, 'head')} بـ ${n0(RU().treatAll)} ريال`, accAll != null)}<small>${HJ.sure === 'treatAll' ? `يعالج ${count(all, 'head')} بـ ${n0(RU().treatAll)} ريال` : `علاجهم كلهم بـ ${n0(RU().treatAll)} ريال`}</small>${accAll && accAll.short > 0 ? `<small class="rush">${accountLine(accAll.owed)}</small>` : !accAll ? `<small class="rush">${accountFullLine()}</small>` : ''}</div>` : '';
  const vet = sick.length ? `<div class="sec">يبي علاج</div><div class="group">${sick.map(sickRow).join('')}${treatAll}</div>
    <div class="note">${sick.length === 1 ? `لو ${sick[0].sex !== 'male' ? 'تركتها' : 'تركته'} بعد ${days(sick[0].graceDays)} ممكن ${sick[0].sex !== 'male' ? 'تموت' : 'يموت'}.` : `لو تركتهم بعد ${days(sick[0].graceDays)} ممكن يموتون.`}</div>` : '';
  const building = (RU().builds || []).length > 0;
  return `<div class="body">${nav()}<div class="title">العزبة</div>${errCard()}
    ${vet}${have}
    <div class="sec">ابنِ ووسّع</div>
    <div class="group">${f.facilities.map(row).join('')}</div>
    ${G.cash < 0 ? `<div class="note">${debtLine()}</div>` : ''}
    <div class="note">اللي تبنيه يخلص بعد 3 أيام ويطلع مكانه في العزبة.${building ? ' ولو استعجلته يخلص الحين: تدفع نص سعره لو باقي له 3 أيام، وأقل كل ما قرب يخلص.' : ' ولو تبيه الحين تدفع نص سعره زيادة.'}</div>
    <div class="sec">البيطري</div><div class="group">${vetRows()}</div>
    <div class="note">الاستعجال من رصيدك بس، ما ينكتب على حساب التاجر: الحساب للعلف والماء والبيطري.</div></div>`;
}

// ---------------------------------------------------------------- الحراج (approved 13 Nov 2026: design/ui/phone_haraj.jpg)
// The market on the engine: what is for sale (the cheapest first: a new player's 20,000 riyals), a camel's page (buy
// at the asking price, or haggle: three tries a seller, each answered at once), selling one's own (listed at one's
// price for the offers to come, or to the broker now, for less), and one's listings with their offers. A sale (to the
// broker, or an offer taken) and taking a listing down are asked twice: they cannot be undone. A camel bought comes
// on the truck the next day (Balance.camelTruckDays). HJ: the page's own state (the tab, the camel looked at, the
// figures being set, the word to say after an order, the button waiting for its second tap).
const HJ = { tab: 'market', listing: null, camel: null, bid: null, ask: null, msg: null, sure: null };
const REGION = { riyadh: 'الرياض', qassim: 'القصيم', hail: 'حائل', jouf: 'الجوف', northern: 'الحدود الشمالية', sharqiya: 'الشرقية', tabuk: 'تبوك', najran: 'نجران' };
// a coat's name: a she-camel's own (وضحاء), a male by his colour's group (وضح), as the farm's cards have it
const COAT = { wodh: ['وضحاء', 'وضح'], shoqh: ['شقحاء', 'شقح'], shoal: ['شعلاء', 'شعل'], sofr: ['صفراء', 'صفر'], homr: ['حمراء', 'حمر'], majaheem: ['مجهمية', 'مجاهيم'] };
const PHOTO = { wodh: 'camel_side_wodh.png', shoqh: 'thumb_shaqh.png', shoal: 'thumb_shaal.png', sofr: 'thumb_safra.png', majaheem: 'thumb_majaheem.png', homr: 'thumb_shaal.png' };
const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch]);
const fem = (c) => c.sex === 'female';
const her = (c, f, m) => (fem(c) ? f : m);      // a word by the camel's sex: her (f) or his (m)
const titleOf = (c) => `${c.ageName} ${COAT[c.category][fem(c) ? 0 : 1]}`;
const photo = (c) => `<img src="phone/${PHOTO[c.category]}" alt="" draggable="false"${c.category === 'homr' ? ' class="homr"' : ''}>`;
const est = (c) => `<bdi dir="ltr">${n0(c.estimateLow)}–${n0(c.estimateHigh)}</bdi>`;
const ageText = (d) => (d < 30 ? days(Math.max(1, d)) : d < 365 ? count(Math.floor(d / 30), 'month') : count(Math.floor(d / 365), 'year'));
const dueText = (c) => { const d = c.dueOn - G.today; return d <= 1 ? 'تولد بكرة' : d < 60 ? `تولد بعد ${days(d)}` : `تولد بعد ${count(Math.round(d / 30), 'month')}`; };
const healthText = (c) => (c.health === 'sick' ? her(c, 'مريضة', 'مريض') : c.health === 'treated' ? 'تحت العلاج' : her(c, 'صحتها زينة', 'صحته زينة'));
// a step for a price set by + and − (a game choice: 500 riyals under 50,000, 1,000 under 200,000, then 5,000)
const stepOf = (v) => (v < 50000 ? 500 : v < 200000 ? 1000 : 5000);
const roundTo = (v, k) => Math.round(v / k) * k;
const listingOf = (id) => (G ? G.market.find((l) => l.id === id) || null : null);
const myCamel = (id) => (G ? G.yard.find((c) => c.id === id) || null : null);
// what one's own camel is doing, in a word or two: «مرضع وعشار», a calf at its mother's, sick
function doing(c) {
  const milk = G.farm.milk.camels, dam = milk.find((m) => m.calfId === c.id);
  const parts = [];
  if (milk.some((m) => m.id === c.id)) parts.push('مرضع');
  if (c.pregnant) parts.push('عشار');
  if (dam) parts.push(her(c, `ترضع من أمها ${esc(dam.name)}`, `يرضع من أمه ${esc(dam.name)}`));
  if (c.health === 'sick') parts.push(her(c, 'مريضة', 'مريض'));
  return parts.join(' و');
}
const msgCard = () => (HJ.msg ? `<div class="msgc${HJ.msg.good ? ' good' : ''}"><span class="lead">${svg(HJ.msg.good ? 'check' : 'talk')}</span><b>${HJ.msg.title}</b><small>${HJ.msg.line}</small></div>` : '');
const tabs = () => {
  const mine = HJ.tab === 'mine', n = G.openOffers;
  const tab = (k, name, on) => `<span data-act="tab" data-p="${k}" role="tab" tabindex="0" aria-selected="${on}"${on ? ' class="on"' : ''}>${name}</span>`;
  return `<div class="seg two" role="tablist" aria-label="الحراج">${tab('market', 'المعروض', !mine)}${tab('mine', `إعلاناتي${n ? `<i class="dot" aria-label="${count(n, 'bid')}">${n}</i>` : ''}`, mine)}</div>`;
};
function harajScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">الحراج</div>${waiting()}</div>`;
  const mine = HJ.tab === 'mine';
  // a camel bought today, on the truck: brought now by a second driver, for less as the day goes
  const trucks = onTruck().map((t) => {
    const fee = truckFee(t.trucking), key = `rushTruck:${t.camel}`, can = G.cash >= fee, f = !t.male;
    return `<div class="row r3"><span class="lead">${svg('truck')}</span><b>${esc(t.name)} على اللوري</b>${rushBtn(key, `data-act="rushTruck" data-id="${esc(t.camel)}"`, `استعجل ${esc(t.name)} بـ ${n0(fee)} ريال`, can)}<small>${can ? (HJ.sure === key ? `${f ? 'توصل' : 'يوصل'} الحين، وتدفع ${n0(fee)} ريال زيادة` : `${f ? 'توصل' : 'يوصل'} الحين بسواق ثاني، بـ ${n0(fee)} ريال زيادة`) : `الاستعجال ${n0(fee)} ريال، ورصيدك ${n0(G.cash)}`}</small></div>`;
  }).join('');
  const truck = trucks ? `<div class="group way">${trucks}</div><div class="note">كل ما مضى من اليوم يرخص الاستعجال، لأن الباقي على وصولها أقل.</div>` : '';
  return `<div class="body">${nav()}<div class="title">الحراج</div>${tabs()}${msgCard()}${errCard()}${mine ? '' : truck}${mine ? myListings() : marketList()}</div>${mine ? '' : `<button class="sell" data-go="pick">${svg('plus')}اعرض حلالك للبيع</button>`}`;
}
function marketList() {
  const list = G.market.slice().sort((a, b) => a.askPrice - b.askPrice || (a.id < b.id ? -1 : 1));
  if (!list.length) return '<div class="note">ما فيه شي معروض اليوم. يجي حلال جديد كل يوم.</div>';
  const item = (l) => {
    const c = l.camel;
    return `<div class="it" data-go="listing" data-id="${esc(l.id)}" role="button" tabindex="0" aria-label="${titleOf(c)} بـ ${n0(l.askPrice)} ريال، النقل ${n0(l.transport)}، ${her(c, 'يقدّرونها', 'يقدّرونه')} من ${n0(c.estimateLow)} إلى ${n0(c.estimateHigh)}"><span class="ph">${photo(c)}</span><b>${titleOf(c)}</b><small>${REGION[l.region]} · ${esc(l.sellerName)} · <span class="nw">النقل ${n0(l.transport)} ريال</span></small><span class="pr"><span class="price num">${n0(l.askPrice)}</span></span><small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${est(c)}</small></div>`;
  };
  return `<div class="note" style="margin-top:-4px">${count(list.length, 'head')} معروض · رصيدك ${n0(G.cash)} ريال</div>
    <div class="lst">${list.map(item).join('')}</div>`;
}
function listingScreen() {
  const back = nav('', 'haraj');
  if (!G) return `<div class="body">${back}<div class="title">الحراج</div>${waiting()}</div>`;
  const l = listingOf(HJ.listing);
  if (!l) return `<div class="body">${back}<div class="title">الحراج</div>${msgCard()}<div class="note" style="margin-top:6px">هالإعلان انباع أو انشال.</div></div>`;
  const c = l.camel, total = l.askPrice + l.transport, k = stepOf(l.askPrice);
  const full = G.herd.total >= G.farm.capacity, poor = G.cash < total;
  // the haggle starts at the low end of their appraisal (at 90% of the asking price the first bid was over the seller's
  // floor 96% of the time, a purchase in one tap: the review); it goes no higher than a step under the price (at the
  // price it is a purchase)
  const top = Math.max(k, l.askPrice - k);
  if (HJ.bid == null) HJ.bid = Math.min(top, Math.max(k, roundTo(c.estimateLow, k)));
  HJ.bid = Math.min(top, Math.max(k, HJ.bid));
  const left = l.bargainsLeft, canPayBid = G.cash >= HJ.bid + l.transport;
  const canBid = left > 0 && !full && canPayBid && G.cash >= 0;
  const facts = [
    `<b>${esc(c.name)}</b>`,
    `<small>${REGION[l.region]} · عند ${esc(l.sellerName)}</small>`,
    `<small>العمر ${ageText(c.ageDays)} · الحالة ${Math.round(c.condition)} · ${healthText(c)}</small>`,
    c.pregnant && c.dueOn != null ? `<small>عشار، ${dueText(c)}</small>` : '',
    `<small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${est(c)} ريال</small>`,
  ].join('');
  const why = full ? 'عزبتك مليانة: ابنِ شبك من العزبة.' : G.cash < 0 ? debtLine() : poor ? `رصيدك ${n0(G.cash)} ريال ما يكفي.` : '';
  const canBuy = !full && !poor;
  const bidRow = `<div class="group"><div class="row ord full"><span class="lead">${svg('haraj')}</span><b>سومك</b><span class="stp"><button data-act="bidStep" data-d="-1" aria-label="سوم أقل" ${HJ.bid > k ? '' : 'disabled'}>${svg('minus')}</button><span class="n"><b>${n0(HJ.bid)}</b> <span>ريال</span></span><button data-act="bidStep" data-d="1" aria-label="سوم أكثر" ${HJ.bid < top ? '' : 'disabled'}>${svg('plus')}</button></span><small>${left > 0 ? `باقي لك ${count(left, 'bid')} ${her(c, 'عليها', 'عليه')}` : `${esc(l.sellerName)} ما عاد يقبل منك سوم`}</small></div></div>`;
  return `<div class="body">${back}<div class="title" style="font-size:22px">${titleOf(c)}</div>${msgCard()}${errCard()}
    <div class="it big"><span class="ph">${photo(c)}</span>${facts}</div>
    <div class="tank"><small>اللي تدفعه</small>
      <div class="kind"><span>${her(c, 'سعرها', 'سعره')}</span><span class="d">${n0(l.askPrice)} ريال</span></div>
      <div class="kind"><span>${her(c, 'نقلها', 'نقله')} لعزبتك</span><span class="d">${n0(l.transport)} ريال</span></div>
      <div class="kind"><span><b>المجموع</b></span><span class="d"><b>${n0(total)} ريال</b></span></div></div>
    <button class="btn ${canBuy ? 'pri' : ''} wide" data-act="buy" ${canBuy ? '' : 'disabled'}>${her(c, 'اشترها', 'اشتره')} بـ ${n0(l.askPrice)}</button>
    ${canBuy && G.cash >= total + truckFee(l.transport) ? nowLink(`buyNow:${l.id}`, `data-act="buyNow" style="align-self:center" aria-label="${her(c, 'اشترها وتوصل', 'اشتره ويوصل')} الحين بـ ${n0(total + truckFee(l.transport))} ريال مع النقل"`, `أو ${her(c, 'اشترها وتوصل', 'اشتره ويوصل')} الحين بـ ${n0(total + truckFee(l.transport))} ريال مع النقل`, `اضغط مرة ثانية ${her(c, 'وتوصل', 'ويوصل')} الحين بـ ${n0(total + truckFee(l.transport))} ريال`) : ''}
    ${why ? `<div class="note">${why}</div>` : ''}
    <div class="sec">${her(c, 'سوم عليها', 'سوم عليه')}</div>
    ${bidRow}
    <button class="btn ${canBid ? 'ghost' : ''} wide" data-act="bid" ${canBid ? '' : 'disabled'}>سوم بـ ${n0(HJ.bid)}</button>
    ${left > 0 && !full && !canPayBid && G.cash >= 0 ? `<div class="note">لو قبل سومك تدفع ${n0(HJ.bid + l.transport)} ريال مع النقل، ورصيدك ما يكفي.</div>` : ''}
    <div class="note">يرد عليك على طول: يقبل، أو ينزل لك، أو يرفض. والنقل ${her(c, 'يوصلها', 'يوصله')} بكرة لعزبتك.</div></div>`;
}
// one's own camels to sell: those on the farm (the 3D yard's, the first 40 to come), each with what stops a sale
function pickScreen() {
  const back = nav('', 'haraj');
  if (!G) return `<div class="body">${back}<div class="title">اعرض للبيع</div>${waiting()}</div>`;
  const item = (c) => {
    const why = c.listed ? her(c, 'معروضة بالحراج', 'معروض بالحراج') : c.entered ? her(c, 'مشاركة بمزاين', 'مشارك بمزاين') : '';
    const can = !why && c.quickSale != null, what = doing(c);
    return `<div class="it${can ? '' : ' off'}"${can ? ` data-go="sell" data-id="${esc(c.id)}" role="button" tabindex="0" aria-label="بيع ${esc(c.name)}"` : ''}><span class="ph">${photo(c)}</span><b>${esc(c.name)} · ${titleOf(c)}</b><small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${est(c)} ريال</small>${why || what ? `<small>${why || what}</small>` : ''}</div>`;
  };
  // the camels bought today are on the truck (not on the farm, not yet for sale); beyond the yard's 40 the rest of a big
  // herd is for the herd's own page, still to come
  const onWay = G.recentEvents.filter((e) => e.type === 'camelBought' && e.day === G.today).length;
  const more = Math.max(0, G.herd.total - G.yard.length - onWay);
  return `<div class="body">${back}<div class="title">اعرض للبيع</div>${errCard()}
    ${G.yard.length ? `<div class="lst flat">${G.yard.map(item).join('')}</div>` : '<div class="note" style="margin-top:6px">ما عندك حلال بالعزبة.</div>'}
    ${onWay ? `<div class="note">${onWay > 1 ? `اللي اشتريتها اليوم (${count(onWay, 'head')}) توصل` : 'اللي اشتريته اليوم يوصل'} بكرة، وتقدر تبيع بعدها.</div>` : ''}
    ${more ? `<div class="note">وعندك ${count(more, 'head')} غيرها ما تطلع هنا للحين.</div>` : ''}</div>`;
}
function sellScreen() {
  const back = nav('', 'pick');
  if (!G) return `<div class="body">${back}<div class="title">بيع</div>${waiting()}</div>`;
  const c = myCamel(HJ.camel);
  if (!c || c.listed || c.quickSale == null) return `<div class="body">${back}<div class="title">بيع</div>${msgCard()}${errCard()}<div class="note" style="margin-top:6px">${!c ? 'ما عاد عندك هالحلال.' : c.listed ? her(c, 'معروضة بالحراج، شوفها بإعلاناتي.', 'معروض بالحراج، شوفه بإعلاناتي.') : her(c, 'ما تنباع الحين.', 'ما ينباع الحين.')}</div></div>`;
  const k = stepOf(c.estimateHigh), min = G.haraj.minAsk;
  if (HJ.ask == null) HJ.ask = Math.max(min, roundTo(c.estimateHigh, k));
  HJ.ask = Math.max(min, HJ.ask);
  const fee = Math.round(HJ.ask * G.haraj.commission), what = doing(c);
  const dam = G.farm.milk.camels.find((m) => m.id === c.id && m.calfName);
  const cf = (f, m) => (dam && dam.calfSex === 'female' ? f : m);      // (the calf's own sex, from the engine: not only the yard's 40)
  // the asking price against the appraisals: above them, fewer buyers come (Balance.buyerInterest); below, money left
  const hint = HJ.ask > c.estimateHigh * 1.15 ? 'سعرك فوق تقديرهم بواجد: السومات تقل.' : HJ.ask < c.estimateLow ? 'سعرك تحت تقديرهم.' : '';
  const sure = HJ.sure === `quick:${c.id}`;
  return `<div class="body">${back}<div class="title" style="font-size:22px">بيع ${esc(c.name)}</div>${errCard()}
    <div class="it"><span class="ph">${photo(c)}</span><b>${titleOf(c)}</b><small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${est(c)} ريال</small>${what ? `<small>${what}</small>` : ''}</div>
    ${dam ? alertCard(`${cf('حوارتها', 'حوارها')} ${esc(dam.calfName)} ${cf('ترضع', 'يرضع')} منها`, `لو بعتها ${cf('تضعف بدون حليب أمها', 'يضعف بدون حليب أمه')}، خصوصًا قبل 3 شهور.`) : ''}
    <div class="sec">${her(c, 'اعرضها', 'اعرضه')} بالحراج</div>
    <div class="group"><div class="row ord full"><span class="lead">${svg('haraj')}</span><b>سعرك</b><span class="stp"><button data-act="askStep" data-d="-1" aria-label="سعر أقل" ${HJ.ask - k >= min ? '' : 'disabled'}>${svg('minus')}</button><span class="n"><b>${n0(HJ.ask)}</b> <span>ريال</span></span><button data-act="askStep" data-d="1" aria-label="سعر أكثر">${svg('plus')}</button></span><small>السعي ${n0(fee)} ريال · يوصلك ${n0(HJ.ask - fee)}</small></div></div>
    ${hint ? `<div class="note">${hint}</div>` : ''}
    <button class="btn pri wide" data-act="list">${her(c, 'اعرضها', 'اعرضه')} بـ ${n0(HJ.ask)}</button>
    <div class="note">تجيك السومات بإعلاناتي، وتقبل أو ترفض. الإعلان يبقى ${days(G.haraj.listingDays)}.</div>
    <div class="sec">أو ${her(c, 'بيعها', 'بيعه')} للدلال الحين</div>
    <button class="btn ${sure ? 'sure' : 'ghost'} two wide" data-act="quick"><span>${sure ? her(c, 'اضغط مرة ثانية وتنباع', 'اضغط مرة ثانية وينباع') : her(c, 'بيعها الحين', 'بيعه الحين')}</span><span>${n0(c.quickSale)} ريال</span></button>
    <div class="note">الدلال يشتري${her(c, 'ها', 'ه')} بنفسه ويدفع على طول بدون سعي، بس أقل من الحراج.</div></div>`;
}
function myListings() {
  const L = G.myListings;
  if (!L.length) return '<div class="note" style="margin-top:6px">ما عندك شي معروض. اعرض حلالك من «المعروض».</div>';
  const when = (d) => (d <= 0 ? 'ينتهي اليوم' : d === 1 ? 'ينتهي بكرة' : `ينتهي بعد ${days(d)}`);
  return L.map((l) => {
    const c = l.camel, left = l.expiresOn - G.today;
    const offer = (o) => {
      const sure = HJ.sure === `accept:${o.id}`, fee = Math.round(o.amount * G.haraj.commission);
      return `<div class="row"><span class="lead">${svg('user')}</span><b>${esc(o.buyerName)} سام ${n0(o.amount)}</b><span class="act two"><button class="btn ${sure ? 'sure' : 'pri'}" data-act="accept" data-o="${esc(o.id)}" aria-label="اقبل سوم ${esc(o.buyerName)}">${sure ? 'أكّد' : 'اقبل'}</button><button class="btn ghost" data-act="decline" data-o="${esc(o.id)}" aria-label="ارفض سوم ${esc(o.buyerName)}">لا</button></span><small>يوصلك ${n0(o.amount - fee)} بعد السعي · ${when(o.expiresOn - G.today)}</small></div>`;
    };
    const sure = HJ.sure === `unlist:${l.id}`;
    return `<div class="it"><span class="ph">${photo(c)}</span><b>${esc(c.name)} · ${titleOf(c)}</b><small>${her(c, 'معروضة', 'معروض')} بـ ${n0(l.askPrice)} · الإعلان ${when(left)}</small><span class="pr"><span class="price num">${n0(l.askPrice)}</span></span><small>${l.offers.length ? count(l.offers.length, 'bid') : `ما ${her(c, 'جاها', 'جاه')} سوم للحين`}</small></div>
      ${l.offers.length ? `<div class="sec">السومات</div><div class="group">${l.offers.map(offer).join('')}</div>` : ''}
      <button class="btn ${sure ? 'sure' : 'ghost'} wide" data-act="unlist" data-id="${esc(l.id)}">${sure ? 'اضغط مرة ثانية وينشال' : 'شيل الإعلان'}</button>`;
  }).join('') + `<div class="note">السوم يبقى ${days(G.haraj.offerDays)}، وإذا ما قبلته يروح.</div>`;
}

// ---------------------------------------------------------------- البنك (approved 13 Nov 2026: design/ui/phone_bank.jpg)
// The player's money from the engine's ledger: the balance, today's money (its net in the home widget's words, and what
// came in and went out when it moved both ways), every month with its net and the kind that moved the most money (the
// owner's option B), the opening balance in a line; and a month opened, its kinds, money in and out apart. A sale is
// what reached the player, its price and السعي in its line (the owner: السعي goes with its sale). The month's kinds come
// from the engine when it is opened (engine.bankMonth: the snapshot carries each month's net and biggest kind only).
// BK: the month opened ('YYYY-MM'), its kinds as the engine gave them, and the bank revision they were read at.
const BK = { month: null, data: null, rev: null, asked: 0 };
const dayName = (iso) => `${Number(iso.slice(8, 10))} ${MONTH[Number(iso.slice(5, 7)) - 1]}`;
const monName = (ym) => MONTH[Number(ym.slice(5, 7)) - 1];
const monthName = (ym) => `${monName(ym)} ${ym.slice(0, 4)}`;
const signed = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + n0(Math.abs(v));
const inOut = (inn, out) => [inn ? `دخل ${n0(inn)} ريال` : '', out ? `طلع ${n0(out)} ريال` : ''].filter(Boolean).join(' · ');
const FAC_NAME = (f) => (f === 'pen' ? 'شبك' : FAC[f]?.name ?? '');
// each kind: its name, its icon, and the line under it (the line's fields as the engine gives them)
const one = (l) => l.count === 1;
const KIND = {
  milk: { name: 'الحليب', icon: 'milk', line: (l, cur) => (cur ? 'ينباع كل يوم، لين اليوم' : 'ينباع كل يوم') },
  sale: { name: 'بيع حلال', icon: 'camel', line: (l) => {
    const what = one(l) && l.name ? `${esc(l.name)} بـ ${n0(l.price)}` : `${count(l.count, 'head')} بـ ${n0(l.price)}`;
    return l.fee ? `${what} · السعي ${n0(l.fee)}` : one(l) && l.day ? `${what} · ${dayName(l.day)}` : what;
  } },
  prize: { name: 'جوائز المزاين', icon: 'camel', line: (l) => (one(l) && l.name ? esc(l.name) : count(l.count, 'prize')) },
  purchase: { name: 'شراء حلال', icon: 'camel', line: (l) => (one(l) && l.name ? `${esc(l.name)} · ${dayName(l.day)}` : count(l.count, 'head')) },
  transport: { name: 'النقل', icon: 'truck', line: (l) => {
    if (!one(l) || !l.trip) return count(l.count, 'trip');
    if (l.trip === 'festival') return `${l.name ? esc(l.name) : 'المزاين'}، رايح جاي`;
    return l.name ? (l.trip === 'purchase' ? `نقل ${esc(l.name)} لعزبتك` : `نقل ${esc(l.name)} للفحل`) : count(1, 'trip');
  } },
  feed: { name: 'العلف', icon: 'feed', line: (l) => count(l.count, 'order') },
  water: { name: 'الوايت', icon: 'water', line: (l) => count(l.count, 'order') },
  wages: { name: 'رواتب الرعاة', icon: 'user', line: () => 'تنخصم أول الشهر' },
  construction: { name: 'البناء', icon: 'build', line: (l) => (l.facilities?.length === l.count ? l.facilities.map(FAC_NAME).join('، ') : count(l.count, 'build')) },
  vet: { name: 'البيطري', icon: 'user', line: (l) => count(l.count, 'treat') },
  // the rush (T15): what was hurried, by the facility's name, the supply or the camel
  rush: { name: 'الاستعجال', icon: 'build', line: (l) => (l.facilities?.length === l.count ? l.facilities.map((f) => `${FAC_NAME(f)}، خلص بيومه`).join('، ') : one(l) && l.name ? `${esc(l.name)}، وصل بيومه` : count(l.count, 'rush')) },
  studFee: { name: 'أجرة الفحل', icon: 'camel', line: (l) => count(l.count, 'mating') },
  // the festivals (GDD 7): a late entry's fee by its festival
  entryFee: { name: 'رسوم التسجيل المتأخر', icon: 'camel', line: (l) => (one(l) && l.name ? esc(l.name) : count(l.count, 'entry')) },
  // the player's own spending on a camel treated, said plainly by her name (never as something the bank offers)
  tampering: { name: 'تجميل', icon: 'camel', line: (l) => (one(l) && l.name ? `تجميل ${esc(l.name)}` : count(l.count, 'time')) },
  // a fine names what it was for: found at a festival, outside one (the vet, the daily look), or at a sale
  fine: { name: 'غرامات', icon: 'bank', line: (l) => {
    if (!one(l) || !l.fineFor) return count(l.count, 'fine');
    if (l.fineFor === 'festival') return l.name ? `غرامة تجميل في ${esc(l.name)}` : 'غرامة تجميل في المزاين';
    if (l.fineFor === 'sale') return l.name ? `غرامة بيع ${esc(l.name)}` : 'غرامة بيع';
    return l.name ? `غرامة تجميل ${esc(l.name)}` : 'غرامة تجميل';
  } },
  testMoney: { name: 'فلوس تجربة', icon: 'bank', line: () => 'فلوس بلا حد للتجربة' },      // (the owner's testing only: the meter's switch, farm.html; GDD 13)
};
// a kind this phone has no words for yet (the engine may add one before the phone knows it): said plainly, never broken
const OTHER = { name: 'حركة ثانية', icon: 'bank', line: (l) => (one(l) && l.day ? dayName(l.day) : count(l.count, 'time')) };
const kindOf = (k) => KIND[k] || OTHER;
// a month's biggest kind on the main screen («أكبرها: …»): a camel bought or sold by its name, a sale by what reached
// the player
function biggest(l) {
  const a = n0(Math.abs(l.amount));
  if (l.kind === 'purchase' && one(l) && l.name) return `شراء ${esc(l.name)} ${a} ريال`;
  if (l.kind === 'sale' && one(l) && l.name) return `بيع ${esc(l.name)}، وصلك ${a} ريال`;
  if (l.kind === 'tampering' && one(l) && l.name) return `تجميل ${esc(l.name)} ${a} ريال`;
  if (l.kind === 'fine' && one(l)) return `${KIND.fine.line(l)} ${a} ريال`;
  return `${kindOf(l.kind).name} ${a} ريال`;
}
// today: the net as the home widget says it; the split on a grey line under it when money moved both ways; green only
// when money only came in
function todayLines() {
  const B = G.bank, inn = B.todayIn, out = B.todayOut, net = inn - out;
  const head = net > 0 ? `دخل اليوم ${n0(net)} ريال` : net < 0 ? `صرفت اليوم ${n0(-net)} ريال` : inn ? 'اليوم ما زاد ولا نقص' : 'ما فيه حركة اليوم';
  return `<div class="ln${inn && !out ? ' pos' : !inn && !out ? ' ink2' : ''}">${head}</div>${inn && out ? `<div class="ln ink2">${inOut(inn, out)}</div>` : ''}`;
}
function bankScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">البنك</div>${waiting()}</div>`;
  const B = G.bank, now = G.date.slice(0, 7);
  const row = (m) => {
    const t = m.top, k = kindOf(t.kind), cur = m.month === now, name = cur ? `${monName(m.month)} · هالشهر` : monthName(m.month);
    return `<div class="row" data-go="bankMonth" data-month="${m.month}" role="button" tabindex="0" aria-label="${name}، ${m.net < 0 ? 'صرفت' : 'دخلك'} ${n0(Math.abs(m.net))} ريال"><span class="lead${t.amount < 0 ? ' out' : ''}">${svg(k.icon)}</span><b>${name}</b><span class="amt${m.net > 0 ? ' pos' : ''}">${signed(m.net)}</span><small>أكبرها: ${biggest(t)}</small></div>`;
  };
  const first = B.startedOn === G.date
    ? `بديت اليوم برصيد ${n0(B.opening)} ريال.${G.farm.milk.sold > 0.05 ? ' حليب ناقتك أول دخل لك: يمر المشتري بكرة وياخذه.' : ''}`
    : `بديت اللعبة ${dayName(B.startedOn)} ${B.startedOn.slice(0, 4)} برصيد ${n0(B.opening)} ريال.`;
  return `<div class="body">${nav()}<div class="title">البنك</div>
    <div class="balance">${G.cash < 0 ? `<small>عليك</small><div class="v bad"><b class="fit">${n0(-G.cash)}</b><span>ريال</span></div>` : `<small>رصيدك</small><div class="v"><b class="fit">${n0(G.cash)}</b><span>ريال</span></div>`}${todayLines()}</div>
    ${B.months.length ? `<div class="sec">الشهور</div><div class="group">${B.months.map(row).join('')}</div>` : ''}
    <div class="note">${first}</div></div>`;
}
function bankMonthScreen() {
  const ym = BK.month, m = BK.data;
  if (!G || !ym || !m) return `<div class="body">${nav('', 'bank')}<div class="title">${ym ? monthName(ym) : 'البنك'}</div>${waiting()}</div>`;
  const cur = ym === G.date.slice(0, 7), net = m.in - m.out;
  const line = (l) => { const k = kindOf(l.kind); return `<div class="row"><span class="lead${l.amount < 0 ? ' out' : ''}">${svg(k.icon)}</span><b>${k.name}</b><span class="amt${l.amount > 0 ? ' pos' : ''}">${signed(l.amount)}</span><small>${k.line(l, cur)}</small></div>`; };
  const ins = m.lines.filter((l) => l.amount > 0 && l.kind !== 'testMoney'), outs = m.lines.filter((l) => l.amount <= 0 && l.kind !== 'testMoney'), test = m.lines.filter((l) => l.kind === 'testMoney');      // (money for testing apart: the net is the farm's, the engine's)
  // a month without milk says so
  const noMilk = m.lines.some((l) => l.kind === 'milk') ? '' : `<div class="row"><span class="lead out">${svg('milk')}</span><b>الحليب</b><span class="amt"></span><small>ما فيه حليب ${cur ? 'هالشهر' : `في ${monName(ym)}`}</small></div>`;
  return `<div class="body">${nav('', 'bank')}<div class="title">${monthName(ym)}</div>
    <div class="balance"><small>${cur ? 'الصافي لين اليوم' : 'الصافي'}</small><div class="v${net > 0 ? ' pos' : ''}"><bdi dir="ltr">${signed(net)}</bdi><span>ريال</span></div>
      <div class="ln ink2">${inOut(m.in, m.out)}</div></div>
    <div class="sec">الدخل</div><div class="group">${ins.map(line).join('')}${noMilk}</div>
    ${outs.length ? `<div class="sec">المصروف</div><div class="group">${outs.map(line).join('')}</div>` : ''}
    ${test.length ? `<div class="sec">فلوس تجربة</div><div class="group">${test.map(line).join('')}</div>` : ''}</div>`;
}

// ---------------------------------------------------------------- المزاين (approved 13 Nov 2026: design/ui/phone_mazayen.jpg)
// The festivals on the engine (GDD 7 and 7.1): the one open for registration, the player's entries (withdrawn by two
// taps), the coming ones by their days and the highest first prize a player can enter for; a festival's page (its
// individual rounds, each colour's day, the group rounds as coming later, the rules); registering (each camel with its
// own round or the engine's refusal, the cost, two taps: it costs the trucking); the round's day told stage by stage as
// the engine tells it (each stage at its hour; nothing of a stage not told is in the snapshot); the results; and the day
// a treatment is found. The festival's page comes from the engine when it is opened (engine.festival), again when the
// festivals change. Cheating is never offered here: it lives in «المحادثات» (the owner, 13 Nov).
// MZ: the festival opened, its page as the engine gave it and the revision it was read at, the camel picked to
// register, the entry looked at ({round, camel}).
const MZ_SCREENS = new Set(['mazayen', 'fest', 'enter', 'day', 'result', 'chats', 'chat', 'strength']);
const MZ = { fest: null, page: null, text: null, rev: null, asked: 0, sel: null, entry: null };
// the phone's own words for the engine's names (one table each, as its other apps keep theirs; the engine's catalog
// labels are not sent: these words change with the sentence, by sex and with the article)
const RK = { fardiJil: 'الفردي جل', fardiDiq: 'الفردي دق', mafareed: 'مفاريد القعدان والبكار', diq: 'دق القعدان والبكار', fahal: 'الفحل وإنتاجه', jamal: 'الجمل', manqiya: 'المنقية', jazeera: 'منقية الجزيرة', hajij: 'الهجيج', tabaa: 'الطبع', badawa: 'البداوة' };
const RK_SHORT = { fardiJil: 'الجل', fardiDiq: 'الدق', mafareed: 'المفاريد', diq: 'الدق', fahal: 'الفحل وإنتاجه' };
const FAMILY = { wodh: 'الوضح', shoqh: 'الشقح', shoal: 'الشعل', sofr: 'الصفر', homr: 'الحمر', majaheem: 'المجاهيم' };
const STAGE = ['الشريحة والشاهد', 'فحص الهجين واللون والعمر', 'التحكيم الأولي', 'خبراء التلاعب', 'اللجنة الطبية', 'التحكيم النهائي'];
const STAGE_KEY = ['chipWitness', 'breedColourAge', 'preliminary', 'tamperingExperts', 'medical', 'finalJudging'];
const STAGE_NEXT = ['يطابقون الشريحة باسمك', 'اللون صافي والعمر بالأسنان', 'اللجنة تختار النص للتحكيم النهائي', 'فحص الشفايف والخشم والوبر', 'سونار وأشعة وتحاليل', 'المراكز والجوايز'];
const STAGE_ICON = ['chip', 'eye', 'dot', 'eye', 'scope', 'star'];
// a stage's hour in words (the engine's festivalRules.stageMinutes, a game choice): the morning, noon, the afternoon, sunset
const WHEN = (min) => (min < 720 ? 'الصبح' : min < 900 ? 'الظهر' : min < 1050 ? 'العصر' : 'المغرب');
const FEATURE = { head: 'الرأس', nose: 'الخشم', lips: 'الشفايف', ears: 'الأذن', neck: 'الرقبة', hump: 'السنام', back: 'الغارب والظهر', fore: 'المقدمة', hind: 'المؤخرة', stance: 'الوقفة', coat: 'اللون والوبر' };
// where each kind is done, said of her, of him, or of one of a group
const WHERE = { botox: 'بشفايف', filler: 'بخشم', hormones: 'بسنام', lipStretch: 'بشفايف', teethFiling: 'بأسنان', tailCut: 'بذيل', dye: 'بوبر' };
// an entry's words: of a she-camel (f), a male (m), or a group (pl: الفحل وإنتاجه)
const ew = (e, f, m, pl = m) => ((e.head || 1) > 1 ? pl : e.sex === 'male' ? m : f);
const where = (e, k) => ew(e, `${WHERE[k]}ها`, `${WHERE[k]}ه`, `${WHERE[k]} واحد منهم`);
// the counting noun of a round's entries: نياق in a she-camels' round, روس in a males' or a group's
const fieldNoun = (e) => ((e.head || 1) > 1 ? 'bull' : e.sex === 'male' ? 'head' : 'camel');      // (الفحل وإنتاجه: its entries are the bulls)
const STRENGTH = ['خفيف', 'وسط', 'قوي'];
const theTamper = (k) => (/ /.test(TAMPER[k]) ? TAMPER[k] : `ال${TAMPER[k]}`);
const list = (xs) => (xs.length < 2 ? xs.join('') : `${xs.slice(0, -1).join('، ')} و${xs[xs.length - 1]}`);
// dates: the engine's game days as the phone says them
const dateOf = (day) => new Date(Date.parse(G.date + 'T00:00:00Z') + (day - G.today) * 864e5);
const dd = (day) => { const d = dateOf(day); return `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
const dShort = (day) => { const d = dateOf(day); return `${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
const span = (f) => { const a = dateOf(f.startsOn), z = dateOf(f.endsOn); if (f.startsOn === f.endsOn) return dShort(f.startsOn); return a.getUTCMonth() === z.getUTCMonth() ? `من ${a.getUTCDate()} لين ${dShort(f.endsOn)}` : `من ${dShort(f.startsOn)} لين ${dShort(f.endsOn)}`; };
const inDays = (day) => { const n = day - G.today; return n <= 0 ? 'اليوم' : n === 1 ? 'بكرة' : `بعد ${days(n)}`; };
// a festival still taking entries: from its opening, free till its closing, then late (till 72 hours before each round)
const openFests = () => (G ? G.festivals.filter((f) => !f.done && G.today >= f.opensOn && G.today <= f.endsOn - 3).sort((a, b) => a.startsOn - b.startsOn) : []);
const myEntries = () => (G ? G.festivals.flatMap((f) => (f.entries || []).map((e) => ({ ...e, festival: f.id, fest: f }))) : []);
const entryKey = (e) => `${e.round}:${e.camel}`;
// what the badge has shown the player (a convenience of this phone, kept in its storage: a registration open, the
// stages of an entry's day told, its result); lost, it only shows the badge again
const SEEN_KEY = 'marah.phone.mazayen';
let SEEN = { open: [], told: {} };
try { SEEN = { open: [], told: {}, ...JSON.parse(localStorage.getItem(SEEN_KEY) || '{}') }; } catch { /* no storage: the badge shows again */ }
function saveSeen() {
  const keep = new Set(myEntries().map(entryKey)), open = new Set(openFests().map((f) => f.id));
  SEEN = { open: SEEN.open.filter((id) => open.has(id)), told: Object.fromEntries(Object.entries(SEEN.told).filter(([k]) => keep.has(k))) };
  try { localStorage.setItem(SEEN_KEY, JSON.stringify(SEEN)); } catch { /* no storage */ }
}
const mzBadge = () => (G ? openFests().filter((f) => !SEEN.open.includes(f.id)).length + myEntries().filter((e) => e.told > (SEEN.told[entryKey(e)] || 0)).length : 0);
// the camel of an entry as the festival's page has it (on the farm or not)
const entryCamel = (e) => (MZ.page && MZ.page.rounds.find((r) => r.id === e.round)?.myEntries.flat().find((c) => c.id === e.camel)) || myCamel(e.camel) || null;
const strip = (c, line, end = '') => `<div class="strip"><span class="ph">${c ? photo(c) : ''}</span><span><b>${esc(c ? `${c.name} · ${titleOf(c)}` : '')}</b><small>${line}</small></span>${end}</div>`;
const pageRound = (id) => (MZ.page ? MZ.page.rounds.find((r) => r.id === id) || null : null);
const roundTitle = (kind, cat) => `${RK[kind]}${cat ? ` · ${FAMILY[cat]}` : ''}`;
// the engine's refusals of an entry, in the phone's words, by the camel's sex
const REASON = {
  ownershipTooRecent: (c, p) => `${her(c, 'اشتريتها', 'اشتريته')}${c.onTheWay ? ' اليوم' : ' قريب'}، ولازم ${her(c, 'تكون', 'يكون')} باسمك ${days(p.days)} قبل الشوط`,
  wrongAgeClass: (c) => (c.ageDays < 365 ? `${her(c, 'صغيرة', 'صغير')}، وأصغر شوط للمفاريد من سنة` : `${her(c, 'كبيرة', 'كبير')} على شوطها بهالمهرجان`),
  wrongCategory: (c) => `ما فيه شوط ل${FAMILY[c.category]} بهالمهرجان`,
  sick: (c) => her(c, 'مريضة، ما تدخل لين تطيب', 'مريض، ما يدخل لين يطيب'),
  tooFewCalvings: (c, p) => `شوط الجل لمن ولدت ${p.calvings === 2 ? 'مرتين' : `${p.calvings} مرات`} وفوق`,
  listedForSale: (c) => her(c, 'معروضة بالحراج، شيل الإعلان أول', 'معروض بالحراج، شيل الإعلان أول'),
  alreadyEnteredInFestival: (c) => her(c, 'مسجلة بهالمهرجان', 'مسجل بهالمهرجان'),
  oneFardiRound: () => 'سجلت ناقة بشوط فردي، وما يدخل إلا ناقة وحدة بكل مهرجان',
  roundOwnerLimit: (c, p) => `ما تسجّل أكثر من ${count(p.max, fem(c) ? 'camel' : 'head')} بهالشوط`,
  wrongGroupSize: (c, p) => (p.have == 1 ? `ما عنده إنتاج بالعزبة، والشوط يبي ${p.size - 1} من إنتاجه` : p.have != null ? `ما عنده إلا ${count(p.have - 1, 'head')} من إنتاجه يدخلون، والشوط يبي ${p.size - 1}` : `الشوط يبي الفحل ومعه ${p.size - 1} من إنتاجه`),
  tooYoungToBreed: () => 'صغير على الفحل وإنتاجه',
  notOffspring: () => 'واحد منهم ما هو من إنتاجه',
  registrationClosed: (c) => `التسجيل ${her(c, 'لشوطها', 'لشوطه')} قفل`,
  scratched: (c) => `${her(c, 'سحبتها', 'سحبته')} بعد الإغلاق، وما ${her(c, 'ترجع', 'يرجع')} بهالمهرجان`,
  camelBanned: (c) => her(c, 'محرومة من المهرجانات', 'محروم من المهرجانات'),
  crossbred: (c) => her(c, 'هجين، ما تدخل المزاين', 'هجين، ما يدخل المزاين'),
  insufficientFunds: (c, p) => `رصيدك ما يكفي: النقل والرسوم ${n0(p.needed ?? 0)} ريال`,
  inDebt: () => debtLine(),
};
const why = (c, err) => (REASON[err.code] ? REASON[err.code](c, err.params || {}) : 'ما تدخل الحين');
// a removal by its stage, said of her
const outWords = (e) => ({
  chip: ew(e, 'شريحتها ما طابقت', 'شريحته ما طابقت', 'شريحة واحد منهم ما طابقت'), short: ew(e, 'ناقصة', 'ناقص', 'ناقصين'),
  colour: ew(e, 'لونها ما هو صافي', 'لونه ما هو صافي', 'لون واحد منهم ما هو صافي'), teeth: ew(e, 'أسنانها انقرت سن ثاني', 'أسنانه انقرت سن ثاني', 'أسنان واحد منهم انقرت سن ثاني'),
  cut: ew(e, 'ما تأهلت للتحكيم النهائي', 'ما تأهل للتحكيم النهائي', 'ما تأهلوا للتحكيم النهائي'), sick: ew(e, 'مريضة يوم الشوط', 'مريض يوم الشوط', 'واحد منهم مريض يوم الشوط'),
  banned: ew(e, 'طلعت لأنك انحرمت', 'طلع لأنك انحرمت', 'طلعوا لأنك انحرمت'),
})[e.reason] || '';
const caughtCard = (e, c) => {
  const out = e.removedAt === e.foundAt ? `${ew(e, 'طلعت', 'طلع', 'طلعوا')} ${esc(e.name)}${(e.head || 1) > 1 ? ' وإنتاجه' : ''} من الشوط، و` : '';
  return alertCard(`انكشف ${theTamper(e.foundKind)}`, `${out}انكتبت عليك غرامة ${n0(e.fine)} ريال. وانحرمت أنت وحلالك من كل المهرجانات، هالدورة و${count(G.festivalRules.banEditionsAfter, 'edition')} جاية، والخبر طلع للملاك. وصيتك ب${FAMILY[c ? c.category : e.cat]} نزل.`);
};
const debtCard = () => (G.cash < 0 ? alertCard(`رصيدك صار <bdi dir="ltr">−${n0(-G.cash)}</bdi> ريال`, `ما تقدر تشتري حلال ولا تبني لين تسدد. والعلف والماء والبيطري ينطلبون على الحساب لين ${n0(G.farm.account.limit)} ريال${G.farm.account.owed ? ` (عليك ${n0(G.farm.account.owed)})` : ''}، وبعده لازم تبيع من حلالك.`) : '');

function mazayenScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">المزاين</div>${waiting()}</div>`;
  const FR = G.festivalRules, open = openFests();
  const top = (f) => (f.topEnterable ? `جايزة الأول لين ${n0(f.topEnterable)} ريال (${RK[f.topEnterableKind]})` : '');
  const openCard = (f) => {
    const late = G.today > f.closesOn;
    const when = late ? `التسجيل المتأخر بـ ${n0(FR.lateEntryFee)} ريال لين قبل كل شوط بـ ${FR.lateEntryHoursBefore} ساعة` : `التسجيل ببلاش لين ${dd(f.closesOn)}، وبعده بـ ${n0(FR.lateEntryFee)} ريال لين قبل كل شوط بـ ${FR.lateEntryHoursBefore} ساعة`;
    return `<div class="open" data-go="fest" data-id="${esc(f.id)}" role="button" tabindex="0" aria-label="${esc(f.name)}، ${late ? 'تسجيل متأخر' : 'التسجيل مفتوح'}"><span class="tag">${late ? 'تسجيل متأخر' : 'التسجيل مفتوح'}</span><b>${esc(f.name)}</b><small>${REGION[f.region]} · ${span(f)}</small><small>${when}</small>${top(f) ? `<small>${top(f)}</small>` : ''}</div>`;
  };
  // the player's entries: the coming ones (withdrawn by two taps till the day before), the day under way, the results
  const mine = myEntries().filter((e) => !e.fest.done || G.today - e.day <= 30).sort((a, b) => a.day - b.day);
  const entryRow = (e) => {
    const c = myCamel(e.camel) || e, title = `${esc(e.name)} · ${roundTitle(e.kind, e.cat)}`;
    if (G.today < e.day) {
      const sure = HJ.sure === `withdraw:${e.camel}`;
      return `<div class="row"><span class="lead">${svg('camel')}</span><b>${title}</b><span class="act"><button class="btn ${sure ? 'sure' : 'ghost'}" data-act="withdraw" data-f="${esc(e.festival)}" data-o="${esc(e.round)}" data-id="${esc(e.camel)}" aria-label="${sure ? 'أكّد سحب' : 'اسحب'} ${esc(e.name)} من الشوط">${sure ? 'أكّد' : her(c, 'اسحبها', 'اسحبه')}</button></span><small>${her(c, 'شوطها', 'شوطه')} ${dd(e.day)} (${inDays(e.day)})</small></div>`;
    }
    const go = `data-go="${e.told >= 6 && e.foundAt == null && (e.rank || e.removedAt != null) ? 'result' : 'day'}" data-f="${esc(e.festival)}" data-o="${esc(e.round)}" data-id="${esc(e.camel)}" role="button" tabindex="0"`;
    let line;
    if (e.foundAt != null) line = `انكشف ${ew(e, 'فيها', 'فيه', 'فيهم')} ${TAMPER[e.foundKind]}`;
    else if (e.told >= 6 && !e.rank && e.removedAt == null && e.announceOn > G.today) line = `النتيجة بعد فحص الحمض النووي، ${dd(e.announceOn)}`;
    else if (e.told >= 6) line = e.rank ? `المركز ${e.rank}${e.prize ? ` · ${n0(e.prize)} ريال` : ''}` : outWords(e);
    else if (e.removedAt != null) line = `${outWords(e)} · ${STAGE[STAGE_KEY.indexOf(e.removedAt)]}`;
    else line = e.told ? `يوم الشوط: الحين ${STAGE[e.told]}` : `يوم الشوط: يبدأ ${WHEN(FR.stageMinutes[0])}`;
    return `<div class="row" ${go} aria-label="${title}، ${line}"><span class="lead">${svg(e.told >= 6 && e.rank ? 'cup' : 'camel')}</span><b>${title}</b><span class="qty" aria-hidden="true">${svg('chev')}</span><small>${line}</small></div>`;
  };
  const coming = G.festivals.filter((f) => !f.done && !open.includes(f) && f.startsOn > G.today).sort((a, b) => a.startsOn - b.startsOn);
  const comingRow = (f) => `<div class="row" data-go="fest" data-id="${esc(f.id)}" role="button" tabindex="0"><span class="lead">${svg('cup')}</span><b>${esc(f.name)}</b><span class="qty">${f.topEnterable ? n0(f.topEnterable) : ''}</span><small>${span(f)}${f.topEnterable ? ` · ${RK[f.topEnterableKind]}` : ''} · التسجيل ${f.opensOn > G.today ? `من ${dShort(f.opensOn)}` : `لين ${dShort(f.closesOn)}`}</small></div>`;
  const rest = coming.length - 3;
  const banned = G.bannedThrough != null ? alertCard('محروم من المهرجانات', `أنت وحلالك، كل المهرجانات لين موسم ${G.bannedThrough}.`) : '';
  return `<div class="body">${nav()}<div class="title">المزاين</div>${msgCard()}${errCard()}${banned}
    ${G.bannedThrough == null ? open.map(openCard).join('') : ''}
    ${mine.length ? `<div class="sec">مشاركاتك</div><div class="group">${mine.map(entryRow).join('')}</div>` : ''}
    ${coming.length ? `<div class="sec">الجاية · أعلى جايزة أول تدخلها، بالريال</div><div class="group">${coming.slice(0, 3).map(comingRow).join('')}</div>` : ''}
    ${rest > 0 ? `<div class="note">وبعدها ${count(rest, 'fest')} لين ${MONTH[dateOf(coming[coming.length - 1].endsOn).getUTCMonth()]}.</div>` : ''}
    ${!open.length && !mine.length && !coming.length ? '<div class="note" style="margin-top:6px">ما فيه مهرجان جاي للحين.</div>' : ''}</div>`;
}

function festScreen() {
  const back = nav('', 'mazayen');
  const D = MZ.page, F = D ? D.festival : G && G.festivals.find((f) => f.id === MZ.fest);
  if (!G || !D) return `<div class="body">${back}<div class="title">${F ? esc(F.name) : 'المزاين'}</div>${waiting()}</div>`;
  const FR = G.festivalRules, rounds = D.rounds;
  const kindRound = (k) => rounds.find((r) => r.kind === k && r.enterable);
  const cats = [...new Set(rounds.filter((r) => r.cat && r.enterable).map((r) => r.cat))];
  const missing = Object.keys(FAMILY).filter((k) => !cats.includes(k));
  const dayOf = (k) => Math.min(...rounds.filter((r) => r.cat === k && r.enterable && r.kind !== 'mafareed' && r.kind !== 'diq').map((r) => r.day).concat(rounds.filter((r) => r.cat === k && r.enterable).map((r) => r.day)));
  const rnd = (icon, k, line) => { const r = kindRound(k); return r ? `<div class="row"><span class="lead">${svg(icon)}</span><b>${RK[k]}</b><span class="qty">${n0(r.prizes[0])}</span><small>${line}</small></div>` : ''; };
  const fahal = kindRound('fahal');
  const later = ['الجمل', 'المنقية', 'البداوة', 'الهجيج', 'الطبع'];      // (the approved line: the group rounds the game will have)
  const late = G.today > F.closesOn;
  const canRegister = D.register.length > 0 && F.bannedThrough == null;
  return `<div class="body">${back}<div class="title">${esc(F.name)}</div>
    <div class="tank"><small>${REGION[F.region]} · ${span(F)}</small>
      <div class="kind"><span>التسجيل ببلاش</span><span class="d">لين ${dd(F.closesOn)}</span></div>
      <div class="kind"><span>وبعده بـ ${n0(FR.lateEntryFee)} ريال تأخير</span><span class="d">لين قبل الشوط بـ ${FR.lateEntryHoursBefore} ساعة</span></div></div>
    <div class="sec">الأشواط · جايزة الأول بالريال</div>
    <div class="group">
      ${rnd('camel', 'fardiJil', 'النياق من ثاني ولادة وفوق')}
      ${rnd('camel', 'fardiDiq', 'النياق من بعد المفرودة لين الجذعة')}
      ${rnd('camel', 'mafareed', 'من سنة لين سنتين')}
      ${rnd('camel', 'diq', 'من بعد المفرود لين الجذع')}
      ${fahal ? `<div class="row"><span class="lead">${svg('star')}</span><b>${RK.fahal}</b><span class="qty">${n0(fahal.prizes[0])}</span><small>الفحل ومعه ${fahal.size - 1} من إنتاجه · النتيجة بعد فحص الحمض النووي</small></div>` : ''}</div>
    <div class="sec">كل لون بيومه</div>
    <div class="group">${[...new Set(cats.map(dayOf))].sort((a, b) => a - b).map((d) => `<div class="row two"><span class="lead">${svg('camel')}</span><b>${dd(d)}</b><small>${cats.filter((k) => dayOf(k) === d).map((k) => FAMILY[k]).join('، ')}</small></div>`).join('')}</div>
    ${missing.length ? `<div class="note">وما فيه ${missing.map((k) => FAMILY[k]).join(' ولا ')} بهالمهرجان.</div>` : ''}
    ${later.length ? `<div class="group"><div class="row two later"><span class="lead">${svg('herd')}</span><b>الأشواط الجماعية تجي بعدين</b><small>${later.join('، ')}</small></div></div>` : ''}
    <div class="sec">الشروط</div>
    <div class="group">
      <div class="row two"><span class="lead">${svg('rule')}</span><b>ناقة وحدة بشوط فردي واحد</b><small>بكل مهرجان. والمفاريد والدق والفحل وإنتاجه غيره</small></div>
      <div class="row two"><span class="lead">${svg('chip')}</span><b>الشريحة باسمك</b><small>هي وثيقة الملكية الوحيدة، والتسجيل من هنا</small></div>
      <div class="row two"><span class="lead">${svg('eye')}</span><b>العمر يُفحص بالأسنان يوم الشوط</b><small>واللون والشوط ما يتغيرون بعد الإغلاق</small></div></div>
    ${canRegister ? `<button class="sell" style="position:static;box-shadow:none;margin-bottom:6px" data-go="enter">${svg('plus')}${late ? 'سجّل ناقة متأخر' : 'سجّل ناقة'}</button>` : `<div class="note">${F.bannedThrough != null ? 'أنت محروم من المهرجانات.' : 'التسجيل بهالمهرجان قفل أو ما فتح للحين.'}</div>`}</div>`;
}

function enterScreen() {
  const back = nav('', 'fest');
  const D = MZ.page;
  if (!G || !D) return `<div class="body">${back}<div class="title">سجّل ناقة</div>${waiting()}</div>`;
  const F = D.festival, FR = G.festivalRules, rows = D.register;
  const ok = rows.filter((x) => !x.error && x.round);
  if (!ok.some((x) => x.camel.id === MZ.sel)) MZ.sel = ok.length ? ok[0].camel.id : null;
  const item = (x) => {
    const c = x.camel, r = x.round ? pageRound(x.round) : null, sel = c.id === MZ.sel;
    const young = x.error && x.error.code === 'wrongAgeClass' && c.ageDays < 365;
    const fahal = r && r.kind === 'fahal';
    const roundLine = fahal ? `شوطه الفحل وإنتاجه · ${dShort(r.day)}` : r && !young ? `${her(c, 'شوطها', 'شوطه')} ${roundTitle(r.kind, r.cat)} · ${dShort(r.day)}` : doing(c) || titleOf(c);
    // (the offspring the engine shows with him: his best by look)
    const line = fahal && x.group && x.group.length ? `ومعه ${list(x.group.map((k) => esc(k.name)))}` : [doing(c), healthText(c)].filter(Boolean).join(' · ');
    const reason = x.error ? why(c, x.error) : '';
    const attrs = !x.error ? ` data-act="mzsel" data-id="${esc(c.id)}" role="button" tabindex="0" aria-pressed="${sel}" aria-label="${esc(c.name)}، ${roundLine}"` : '';
    return `<div class="it${sel ? ' sel' : ''}${reason ? ' no' : ''}"${attrs}><span class="ph">${photo(c)}</span><b>${esc(c.name)} · ${titleOf(c)}</b><small>${roundLine}</small><small${reason ? ' class="bad"' : ''}>${reason || line}</small></div>`;
  };
  const x = ok.find((y) => y.camel.id === MZ.sel), c = x && x.camel, r = x && pageRound(x.round);
  const late = G.today > F.closesOn, sure = c && HJ.sure === `enter:${c.id}`, head = x ? 1 + (x.group || []).length : 1;
  const more = D.registerTotal - rows.length;
  return `<div class="body">${back}<div class="title">سجّل ناقة</div>${errCard()}
    <div class="note" style="margin-top:-4px">${esc(F.name)} · كل ناقة وشوطها من لونها وعمرها</div>
    <div class="lst flat">${rows.map(item).join('')}</div>
    ${more > 0 && rows.length ? `<div class="note">وعندك ${count(more, 'head')} غيرها، والقائمة تبدأ بالأزين.</div>` : ''}
    ${c ? `<div class="tank"><small>اللي تدفعه عن ${esc(c.name)}</small>
      <div class="kind"><span>التسجيل</span><span class="d">${late ? `${n0(x.fee)} ريال تأخير` : `ببلاش لين ${dShort(F.closesOn)}، وبعده ${n0(x.lateFee)} ريال لين ${dShort(r.lastEntryDay)}`}</span></div>
      <div class="kind"><span>${head > 1 ? 'نقلهم' : her(c, 'نقلها', 'نقله')} لـ${REGION[F.region]} و${head > 1 ? 'رجعتهم' : her(c, 'رجعتها', 'رجعته')}</span><span class="d">${x.trip ? `${n0(x.trip)} ريال يوم الشوط` : 'مع حلالك الرايح'}</span></div></div>
    <button class="btn ${sure ? 'sure' : 'pri'} wide" data-act="enter" data-id="${esc(c.id)}">${sure ? (head > 1 ? 'اضغط مرة ثانية ويتسجلون' : her(c, 'اضغط مرة ثانية وتتسجل', 'اضغط مرة ثانية ويتسجل')) : `سجّل ${esc(c.name)} بشوط ${RK_SHORT[r.kind]}`}</button>
    <div class="note">تقدر ${her(c, 'تسحبها', 'تسحبه')} لين يوم ${her(c, 'شوطها', 'شوطه')}، وبعد ما يقفل التسجيل ما ${her(c, 'ترجع تسجّلها', 'ترجع تسجّله')} بهالمهرجان. وما تقدر ${her(c, 'تبيعها وهي مسجلة', 'تبيعه وهو مسجل')}.</div>`
    : '<div class="note">ما عندك حلال يدخل شوط بهالمهرجان الحين.</div>'}</div>`;
}

// the round's day: the six stages as the engine has told them, each at its hour (festivalRules.stageMinutes); a found
// treatment is told at its stage for an entry the preliminary kept or cut alike (the preliminary's list says nothing of
// the examination)
function dayScreen() {
  const back = nav('', 'mazayen');
  const e = MZ.entry && myEntries().find((x) => x.round === MZ.entry.round && x.camel === MZ.entry.camel);
  const R = e && pageRound(e.round);
  if (!G || !e || !R) return `<div class="body">${back}<div class="title">يوم الشوط</div>${G && !e ? '<div class="note" style="margin-top:6px">ما عاد لها شوط هنا.</div>' : waiting()}</div>`;
  const FR = G.festivalRules, c = entryCamel(e), told = e.told, fld = R.field || [], entered = R.entrants;
  const lost = (i) => (i === 0 ? entered : fld[i - 1]) - fld[i];
  // (she-camels: «طلعت» whatever the count, as approved; males and bulls: «طلع / طلعوا»)
  const outLine = (i) => (lost(i) > 0 ? ` · ${fieldNoun(e) === 'camel' ? 'طلعت' : lost(i) === 1 ? 'طلع' : 'طلعوا'} ${count(lost(i), fieldNoun(e))}` : '');
  const removed = e.removedAt != null ? STAGE_KEY.indexOf(e.removedAt) : 99, found = e.foundAt != null ? STAGE_KEY.indexOf(e.foundAt) : 99;
  const row = (cls, icon, i, line, right) => `<div class="row ${cls}"><span class="lead">${svg(icon)}</span><b>${STAGE[i]}</b><span class="qty ${right[0]}">${right[1]}</span><small>${line}</small></div>`;
  const pending = e.announceOn != null && !e.rank && e.removedAt == null;
  const okLine = (i) => [
    ew(e, 'شريحتها باسمك', 'شريحته باسمك', 'شرايحهم باسمك'),
    (e.head || 1) > 1 ? 'ألوانهم صافية وأعمارهم بأسنانهم' : c ? ew(e, `${COAT[c.category][0]} صافية، و${esc(c.ageName)} بأسنانها`, `${COAT[c.category][1]} صافي، و${esc(c.ageName)} بأسنانه`) : ew(e, 'لونها وعمرها مثل التسجيل', 'لونه وعمره مثل التسجيل'),
    `اللجنة اختارت ${fld[2]} من ${fld[1]}`,
    'ما لقوا شي', 'ما لقوا شي',
    e.rank ? `المركز ${e.rank} من ${count(entered, fieldNoun(e))}` : pending ? `النتيجة بعد فحص الحمض النووي، ${dd(e.announceOn)}` : '',
  ][i];
  const rows = [];
  for (let i = 0; i < 6; i++) {
    if (i < told) {
      if (i === found) rows.push(row('bad', 'x', i, `لقوا ${TAMPER[e.foundKind]} ${where(e, e.foundKind)}`, ['bad', ew(e, 'انكشفت', 'انكشف', 'انكشفوا')]));
      else if (i === removed) rows.push(row('bad', 'x', i, `${outWords(e)}${outLine(i)}`, ['bad', ew(e, 'طلعت', 'طلع', 'طلعوا')]));
      else if (i > removed) rows.push(row('next', STAGE_ICON[i], i, `${ew(e, 'طلعت', 'طلع', 'طلعوا')} قبلها${outLine(i)}`, ['wait', '']));
      else rows.push(row('', 'check', i, `${okLine(i)}${outLine(i)}`, ['ok', ew(e, 'عدّت', 'عدّى', 'عدّوا')]));
    } else if (i === told && told > 0 && G.today === e.day) rows.push(row('now', 'dot', i, STAGE_NEXT[i], ['now', 'الحين']));
    else rows.push(row('next', STAGE_ICON[i], i, STAGE_NEXT[i], ['wait', WHEN(FR.stageMinutes[i])]));
  }
  if (!SEEN.told[entryKey(e)] || SEEN.told[entryKey(e)] < told) { SEEN.told[entryKey(e)] = told; saveSeen(); }
  return `<div class="body">${back}<div class="title">يوم الشوط</div>
    <div class="note" style="margin-top:-4px">${esc(e.fest.name)} · ${roundTitle(e.kind, e.cat)} · ${dd(e.day)}</div>
    ${found >= 6 ? strip(c, `بالشوط ${count(entered, fieldNoun(e))}${told ? ` · باقي ${count(fld[told - 1], fieldNoun(e))}` : ''}`) : ''}
    <div class="group">${rows.join('')}</div>
    ${found < 6 ? caughtCard(e, c) + debtCard() : ''}
    ${told < 6 ? '<div class="note">يجيك خبر مع كل مرحلة، ولو قفلت الجوال يكمل الشوط بدونك.</div>' : found >= 6 && !pending ? `<button class="btn ghost wide" data-go="result" data-f="${esc(e.festival)}" data-o="${esc(e.round)}" data-id="${esc(e.camel)}">النتيجة</button>` : ''}</div>`;
}

function resultScreen() {
  const back = nav('', 'mazayen');
  const e = MZ.entry && myEntries().find((x) => x.round === MZ.entry.round && x.camel === MZ.entry.camel);
  const R = e && pageRound(e.round);
  if (!G || !e || !R || !R.results) return `<div class="body">${back}<div class="title">النتيجة</div>${waiting()}</div>`;
  const c = entryCamel(e) || myCamel(e.camel), fld = R.field || [], entered = R.entrants;
  const out = ew(e, 'طلعت', 'طلع', 'طلعوا'), found = ew(e, 'انكشفت', 'انكشف', 'انكشفوا');
  const STAGE_OUT = { preliminary: outWords({ ...e, reason: 'cut' }), chipWitness: `${out} عند الشريحة والشاهد`, breedColourAge: `${out} بفحص الهجين واللون والعمر`, tamperingExperts: `${found} عند خبراء التلاعب`, medical: `${found} عند اللجنة الطبية` };
  const outcome = e.rank ? `المركز ${e.rank} من ${count(entered, fieldNoun(e))}` : e.reason === 'sick' || e.reason === 'banned' ? outWords(e) : STAGE_OUT[e.removedAt] || '';
  const place = (r) => `<div class="row"><span class="lead rk${r.rank === 1 ? ' g1' : ''}">${r.rank}</span><b>${esc(r.name)}</b><span class="qty">${n0(r.prize)}</span><small>${esc(r.ownerName || '')}</small></div>`;
  const places = R.results.filter((r) => r.rank != null).sort((a, b) => a.rank - b.rank);
  const repWord = { rose: 'كبر', fell: 'نزل', same: 'ما تغير' }[e.reputation] || 'ما تغير';
  const second = e.removedAt === 'preliminary' ? `اللجنة اختارت ${fld[2]} من ${fld[1]}` : e.prize ? `${ew(e, 'جايزتها', 'جايزته', 'جايزتهم')} ${n0(e.prize)} ريال نزلت برصيدك` : '';
  const worth = e.rank && e.rank <= 10 ? ew(e, 'المركز زاد قيمتها', 'المركز زاد قيمته', 'المركز زاد قيمتهم') : ew(e, 'الشوط ما زاد قيمتها شي', 'الشوط ما زاد قيمته شي', 'الشوط ما زاد قيمتهم شي');
  if (!SEEN.told[entryKey(e)] || SEEN.told[entryKey(e)] < e.told) { SEEN.told[entryKey(e)] = e.told; saveSeen(); }
  return `<div class="body">${back}<div class="title">النتيجة</div>
    <div class="note" style="margin-top:-4px">${esc(e.fest.name)} · ${roundTitle(e.kind, e.cat)} · ${count(entered, fieldNoun(e))}</div>
    <div class="it big"><span class="ph">${c ? photo(c) : ''}</span><b>${esc(e.name)}</b><small class="${e.rank && e.rank <= 10 ? '' : 'bad'}">${outcome}</small>${second ? `<small>${second}</small>` : ''}<small>${worth}</small>${c && c.estimateLow ? `<small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${est(c)}</small>` : ''}</div>
    <div class="sec">المراكز · الجايزة بالريال</div>
    <div class="group">${places.slice(0, 5).map(place).join('')}</div>
    <div class="note">والجوايز لين العاشر (${n0(R.prizes[9])} ريال). اللي يجي بالعشرة الأوائل تزيد قيمته ويكبر صيته بلونه، وصيتك ب${FAMILY[c ? c.category : e.cat]} ${repWord}. والدرجات ما تنعلن. ${MZ.page.tripPaid ? `ونقل حلالك لهالمهرجان ${n0(MZ.page.tripPaid)} ريال انخصم.` : ''}</div></div>`;
}

// ---------------------------------------------------------------- «المحادثات»: the treatment man's secret chat (the owner, 13 Nov)
// He messages after each registration (the engine's G.dealer, kept until read: opening his chat reads them); his offer
// is for the latest camel registered whose round is still to come: the seven kinds (GDD 7.1), then light, middle or
// strong, each with its price, its fine and how often it is found in words (never a chance), kinds stacking, the full
// warning, and two taps to buy (it is illegal and costs money). CH: the kind looked at.
const CH = { kind: null };
const dealerOffer = () => {
  if (!G) return null;
  const ms = G.dealer.messages;
  for (let i = ms.length - 1; i >= 0; i--) {
    const m = ms[i], c = myCamel(m.camel);
    // (her round still to come, and she still in it: withdrawn, he offers nothing for her)
    if (c && m.roundDay != null && m.roundDay > G.today && myEntries().some((e) => e.camel === m.camel && e.round === m.round)) return { m, c };
  }
  return null;
};
const chatTop = (to = 'chats') => `<div class="nav"><button class="back" data-go="${to}" aria-label="رجوع">${svg('back')}</button><div class="chathd"><span class="av">${esc(G.dealer.name.slice(-3, -2) || 'س')}</span><span><b>${esc(G.dealer.name)}</b><small>يجمّل الحلال بالسر</small></span></div></div>`;
function chatsScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">المحادثات</div>${waiting()}</div>`;
  const ms = G.dealer.messages, last = ms[ms.length - 1], n = G.dealer.unread;
  return `<div class="body">${nav()}<div class="title">المحادثات</div>
    ${last ? `<div class="group"><div class="row" data-go="chat" role="button" tabindex="0" aria-label="${esc(G.dealer.name)}${n ? `، ${count(n, 'message')}` : ''}"><span class="lead av2">${esc(G.dealer.name.slice(-3, -2) || 'س')}</span><b>${esc(G.dealer.name)}</b><span class="qty">${n ? `<i class="dot">${n}</i>` : svg('chev')}</span><small>أقدر أزيّن ${esc(last.name)} قبل الشوط…</small></div></div>`
    : '<div class="note" style="margin-top:6px">ما عندك محادثات.</div>'}</div>`;
}
// his messages and what was bought from him (the treatments the player knows are in his camels)
// what he bought from him is drawn once, after the last message about that camel (never one his vet found)
function chatLines() {
  const ms = G.dealer.messages.slice(-3), out = [];
  ms.forEach((m, i) => {
    out.push(`<div class="msg them">أقدر أزيّن ${esc(m.name)} قبل الشوط. بيني وبينك. وش تبي؟</div>`);
    if (ms.slice(i + 1).some((x) => x.camel === m.camel)) return;
    for (const t of G.tamperings.filter((x) => x.camel === m.camel && x.bought)) out.push(`<div class="msg me">${TAMPER[t.kind]} ${STRENGTH[t.strength - 1]}.</div><div class="msg them">تم.</div>`);
  });
  return out.join('');
}
function chatScreen() {
  if (!G) return `<div class="body">${nav('', 'chats')}${waiting()}</div>`;
  const FR = G.festivalRules, o = dealerOffer();
  const kindRow = (k) => `<div class="row" data-go="strength" data-k="${k.kind}" role="button" tabindex="0" aria-label="${TAMPER[k.kind]}، من ${n0(k.price[0])} ريال، الغرامة لين ${n0(k.fineCap)} ريال"><span class="lead">${svg('scope')}</span><b>${TAMPER[k.kind]}</b><span class="qty" aria-hidden="true">${svg('chev')}</span><small>من ${n0(k.price[0])} ريال · الغرامة لين ${n0(k.fineCap)} ريال</small></div>`;
  return `<div class="body">${chatTop()}${errCard()}
    <div class="chat">${chatLines()}</div>
    ${o ? `<div class="group">${FR.tamperKinds.map(kindRow).join('')}</div>` : '<div class="note">ما عندك شوط جاي يعرض عليه.</div>'}</div>`;
}
function strengthScreen() {
  const o = dealerOffer(), FR = G && G.festivalRules, K = FR && FR.tamperKinds.find((k) => k.kind === CH.kind);
  if (!G || !o || !K) return chatScreen();
  const c = o.c, m = o.m;
  const often = (band) => ({ low: 'قليل ما ينكشف', medium: 'ينكشف أحيان', high: 'ينكشف أغلب المرات' })[band];
  const BY = { tamperingExperts: 'أكثر ما يلقونه خبراء التلاعب', medical: 'أكثر ما تلقاه اللجنة الطبية' };
  const onHer = G.tamperings.filter((t) => t.camel === c.id).map((t) => `${TAMPER[t.kind]} ${STRENGTH[t.strength - 1]}`);
  const raises = `يزيّن ${list(K.traits.map((t) => FEATURE[t]))}`;
  const strRow = (i) => {
    const sure = HJ.sure === `tamper:${K.kind}:${i + 1}`;
    return `<div class="row"><span class="lead">${svg('scope')}</span><b>${STRENGTH[i]}</b><span class="act"><button class="btn ${sure ? 'sure' : 'ghost'} pr" data-act="tamper" data-k="${K.kind}" data-p="${i + 1}" aria-label="${sure ? 'أكّد ' : ''}${TAMPER[K.kind]} ${STRENGTH[i]} بـ ${n0(K.price[i])} ريال">${sure ? 'أكّد' : `${n0(K.price[i])} ريال`}</button></span><small>${often(K.festivalRisk[i])} · الغرامة ${n0(K.fine[i])} ريال</small></div>`;
  };
  return `<div class="body">${chatTop('chat')}${errCard()}
    ${strip(c, onHer.length ? `فيها: ${onHer.join('، ')}` : `${roundTitle(m.kind, m.cat)} · ${esc(m.festivalName)}`, `<span class="lim">الشوط<span>${dShort(m.roundDay)}</span></span>`)}
    <div class="chat"><div class="msg me">${TAMPER[K.kind]}.</div>
      <div class="msg them">${raises} يوم التحكيم، ويبقى ${her(c, 'فيها', 'فيه')} ${days(K.lastsDays)}. خفيف ولا وسط ولا قوي؟</div></div>
    <div class="group">${[0, 1, 2].map(strRow).join('')}</div>
    <div class="note">كل ما قوي يبيّن أكثر، وينكشف أكثر، وغرامته أكبر. و${BY[K.foundMostlyBy]}. وتقدر تجمع أكثر من نوع، وكل نوع له فحصه وغرامته، فالخطر يتجمع.</div>
    ${alertCard('لو انكشف', `بالمهرجان ${her(c, 'تطلع', 'يطلع')} ${esc(c.name)} من الشوط على طول وتنكتب عليك الغرامة، وتنحرم أنت وحلالك من كل المهرجانات، هالدورة و${count(FR.banEditionsAfter, 'edition')} جاية، والخبر يطلع. ولو ${her(c, 'بعتها يفحصونها', 'بعته يفحصونه')} قبل ما يدفعون: لو لقوه تنلغي البيعة وتنغرم، ولو ما لقوه يزيد ${her(c, 'سعرها', 'سعره')} شوي. وممكن يلقاه البيطري بعد، وصيتك ينزل.`)}</div>`;
}

const herdWord = () => {
  if (!G) return '';
  const m = G.farm.milk.camels;
  return G.herd.total === 2 && m.length === 1 && m[0].calfName ? (m[0].calfSex === 'female' ? 'ناقة وحوارتها' : 'ناقة وحوارها') : unitWord(G.herd.total, 'head');
};

// ---------------------------------------------------------------- التقويم (T15: design/ui/phone_calendar.jpg, awaiting the
// owner's approval). Optional: the year at a glance from the engine's own calendar, and the game moved forward to a
// day the player picks (EngineCore.away): the card first (will the stores last, what falls due, what stops it), the
// jump under way with «وقّف هنا», the early stop with what to do, and what happened. Forward only. CAL: the screen's own
// state (the day picked, the month shown, the jump's progress and its result).
const CAL = { day: null, month: null, progress: null, result: null, running: false, from: null };
const BREED = [11, 12, 1, 2, 3, 4];
const dateAt = (day) => new Date(Date.parse(G.date + 'T00:00:00Z') + (day - G.today) * 864e5);
const dayAt = (iso) => G.today + Math.round((Date.parse(iso + 'T00:00:00Z') - Date.parse(G.date + 'T00:00:00Z')) / 864e5);
const ddAt = (day) => { const d = dateAt(day); return `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
const spanAt = (a, z) => { const x = dateAt(a), y = dateAt(z); if (a === z) return dShortAt(a); return x.getUTCMonth() === y.getUTCMonth() ? `من ${x.getUTCDate()} لين ${dShortAt(z)}` : `من ${dShortAt(a)} لين ${dShortAt(z)}`; };
const inDaysAt = (day) => { const n = day - G.today; return n <= 0 ? 'اليوم' : n === 1 ? 'بكرة' : `بعد ${days(n)}`; };
const shortFest = (name) => (/الكبير/.test(name) ? 'الكبير' : name.replace(/^(مهرجان )?مزاين /, ''));
// the year's dated things: the engine's festivals, the breeding season, the seasons, the herd's own
function calItems() {
  const items = [], end = G.today + 365, y = dateAt(G.today).getUTCFullYear();
  for (const f of G.festivals.filter((x) => !x.done && x.startsOn <= end)) {
    if (f.closesOn > G.today) items.push({ day: f.closesOn, icon: 'flag', cls: 'fest', b: `تسجيل ${esc(f.name)} يقفل`, s: `${ddAt(f.closesOn)} · وبعده متأخر لين 72 ساعة قبل الشوط` });
    if (f.startsOn > G.today) items.push({ day: f.startsOn, icon: 'cup', cls: 'fest', b: esc(f.name), s: `${spanAt(f.startsOn, f.endsOn)} · ${inDaysAt(f.startsOn)}` });
  }
  for (let k = 0; k < 2; k++) {
    const bs = dayAt(`${y + k}-11-01`);
    if (bs > G.today && bs <= end) items.push({ day: bs, icon: 'heart', cls: '', b: 'يبدأ وقت الضراب', s: `${ddAt(bs)} لين آخر أبريل` });
    for (const [m, d, nm] of SEASONS) {
      const day = dayAt(`${y + k}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`);
      if (day > G.today && day <= end) items.push({ day, icon: 'sun', cls: 'sea', b: nm, s: `يبدأ ${ddAt(day)}` });
    }
  }
  for (const c of G.yard) if (c.pregnant && c.dueOn != null && c.dueOn > G.today) items.push({ day: c.dueOn, icon: 'heart', cls: 'bad', b: `${esc(c.name)} تولد`, s: `متوقع ${ddAt(c.dueOn)} · ${inDaysAt(c.dueOn)}` });
  for (const m of G.farm.milk.camels) { const e = G.today + (365 - m.days); if (e > G.today) items.push({ day: e, icon: 'milk', cls: 'milk', b: `حليب ${esc(m.name)} يخلص`, s: `${ddAt(e)} · ${m.calfName ? `يكمل ${esc(m.calfName)} سنة` : 'تكمل سنة من ولادتها'}` }); }
  for (const l of G.myListings) if (l.expiresOn > G.today) items.push({ day: l.expiresOn, icon: 'haraj', cls: '', b: `إعلان ${esc(l.camel.name)} ينتهي`, s: ddAt(l.expiresOn) });
  return items.sort((a, b) => a.day - b.day);
}
const calRow = (x) => `<div class="row r3" data-go="calDay" data-day="${x.day}" role="button" tabindex="0" aria-label="${x.b.replace(/<[^>]+>/g, '')}، ${x.s.replace(/<[^>]+>/g, '')}"><span class="lead ${x.cls}">${svg(x.icon)}</span><b>${x.b}</b><span class="chev">${svg('chev')}</span><small>${x.s}</small></div>`;
function calScreen() {
  if (!G) return `<div class="body">${nav()}<div class="title">التقويم</div>${waiting()}</div>`;
  const items = calItems(), d0 = dateAt(G.today), months = [];
  for (let k = 0; k < 12; k++) {
    const ym = new Date(Date.UTC(d0.getUTCFullYear(), d0.getUTCMonth() + k, 1));
    const first = dayAt(ym.toISOString().slice(0, 10)), len = new Date(Date.UTC(ym.getUTCFullYear(), ym.getUTCMonth() + 1, 0)).getUTCDate(), last = first + len - 1;
    const pos = (day) => ((day - first) / len) * 100, w = (a, z) => ((z - a + 1) / len) * 100, clip = (a, z) => [Math.max(a, first), Math.min(z, last)];
    const segs = [];
    if (G.today > first) { const [a, z] = clip(first, G.today - 1); segs.push(`<i class="past" style="right:${pos(a)}%;width:${w(a, z)}%"></i>`); }
    if (BREED.includes(ym.getUTCMonth() + 1)) segs.push('<i class="brd" style="right:0;width:100%"></i>');
    for (const f of G.festivals.filter((x) => !x.done)) { const [a, z] = clip(f.opensOn, f.closesOn); if (a <= z) segs.push(`<i class="reg" style="right:${pos(a)}%;width:${w(a, z)}%"></i>`); }
    for (const f of G.festivals.filter((x) => !x.done)) { const [a, z] = clip(f.startsOn, f.endsOn); if (a <= z) segs.push(`<i class="fest" style="right:${pos(a)}%;width:${w(a, z)}%"></i>`); }
    for (const x of items) if ((x.cls === 'bad' || x.cls === 'milk') && x.day >= first && x.day <= last) segs.push(`<i class="me${x.cls === 'milk' ? ' milk' : ''}" style="right:${pos(x.day) + 50 / len}%"></i>`);
    if (G.today >= first && G.today <= last) segs.push(`<i class="today" style="right:${pos(G.today) + 50 / len}%"></i>`);
    months.push(`<div class="m"><span${G.today >= first && G.today <= last ? ' class="now"' : ''}>${MONTH[ym.getUTCMonth()]}${ym.getUTCMonth() === 0 || k === 0 ? ` ${ym.getUTCFullYear()}` : ''}</span><div class="t">${segs.join('')}</div></div>`);
  }
  const key = `<div class="key"><span><i style="background:#57b88a;height:3px"></i>الضراب</span><span><i style="background:#f6e3b8"></i>التسجيل</span><span><i style="background:#d9a033"></i>المزاين</span><span><i style="background:var(--red);width:8px;border-radius:4px"></i>ولادة</span><span><i style="background:#2f7fcf;width:8px;border-radius:4px"></i>يخلص الحليب</span></div>`;
  const pickToday = `<button class="btn ghost wide" data-go="calDay" data-day="${G.today + 1}">اختار يوم</button>`;
  return `<div class="body">${nav()}<div class="title">التقويم</div>
    <div class="note" style="margin-top:-4px">اليوم ${ddAt(G.today)} · ${season(d0)}${G.breedingSeason ? ' · وقت الضراب' : ''}</div>
    <div class="yr" aria-hidden="true">${months.join('')}</div>${key}
    ${pickToday}
    <div class="sec">اللي جاي</div>
    <div class="group">${items.slice(0, 24).map(calRow).join('')}</div>
    <div class="note">اختار أي يوم أو أي شي جاي، وتمشي له. التقويم يمشي لقدام بس، واللي يمضي ما يرجع.</div></div>`;
}
function calDayScreen() {
  const back = nav('', 'cal');
  if (!G) return `<div class="body">${back}<div class="title">التقويم</div>${waiting()}</div>`;
  const d0 = dateAt(G.today);
  if (CAL.month == null) { const pd = CAL.day != null ? dateAt(CAL.day) : d0; CAL.month = (pd.getUTCFullYear() - d0.getUTCFullYear()) * 12 + pd.getUTCMonth() - d0.getUTCMonth(); }
  const ym = new Date(Date.UTC(d0.getUTCFullYear(), d0.getUTCMonth() + CAL.month, 1));
  const first = dayAt(ym.toISOString().slice(0, 10)), len = new Date(Date.UTC(ym.getUTCFullYear(), ym.getUTCMonth() + 1, 0)).getUTCDate();
  const cells = ['ح', 'ن', 'ث', 'ر', 'خ', 'ج', 'س'].map((x) => `<span class="wd" aria-hidden="true">${x}</span>`);
  for (let k = 0; k < ym.getUTCDay(); k++) cells.push('<span></span>');
  const fests = G.festivals.filter((x) => !x.done);
  for (let k = 0; k < len; k++) {
    const day = first + k, ok = day > G.today && day <= G.today + 365;
    const fest = fests.some((f) => day >= f.startsOn && day <= f.endsOn), brd = BREED.includes(ym.getUTCMonth() + 1);
    const cls = `d${day === CAL.day ? ' sel' : !ok ? ' past' : fest ? ' fest' : ''}${brd ? ' brd' : ''}`;
    cells.push(ok ? `<button class="${cls}" data-act="calPick" data-day="${day}" aria-label="${ddAt(day)}" aria-pressed="${day === CAL.day}">${k + 1}</button>` : `<span class="${cls}" aria-hidden="true">${k + 1}</span>`);
  }
  const t = CAL.day;
  const on = t == null ? [] : calItems().filter((x) => x.day === t);
  const inFest = t == null ? [] : fests.filter((f) => t >= f.startsOn && t <= f.endsOn);
  const details = t == null ? '<div class="note">اختار اليوم اللي تبي تمشي له.</div>' : `<div class="span"><b>${ddAt(t)}</b><small>${season(dateAt(t))} · ${inDaysAt(t)}</small></div>
    ${on.length || inFest.length ? `<div class="group">${[...on.map((x) => `<div class="row r2"><span class="lead ${x.cls}">${svg(x.icon)}</span><b>${x.b}</b><small>${x.s}</small></div>`), ...inFest.filter((f) => !on.some((x) => x.day === f.startsOn && x.icon === 'cup')).map((f) => `<div class="row r2"><span class="lead fest">${svg('cup')}</span><b>${esc(f.name)}</b><small>${spanAt(f.startsOn, f.endsOn)}</small></div>`)].join('')}</div>` : ''}
    <button class="btn pri wide" data-go="calCard">امشِ لين ${ddAt(t)}</button>
    <div class="note">قبلها يوريك وش تحتاج للأيام هذي.</div>`;
  return `<div class="body">${back}<div class="title">${MONTH[ym.getUTCMonth()]} ${ym.getUTCFullYear()}</div>
    <div class="calnav"><button data-act="calMonth" data-d="-1" aria-label="الشهر اللي قبل" ${CAL.month > 0 ? '' : 'disabled'}>${svg('back')}</button><button data-act="calMonth" data-d="1" aria-label="الشهر اللي بعد" ${CAL.month < 12 ? '' : 'disabled'}>${svg('chev')}</button></div>
    <div class="cal">${cells.join('')}</div>${details}</div>`;
}
// the orders that fill the tank and the feed store before leaving (the card's «عبّه»)
function calFill() {
  const f = G.farm, b = sup('barley'), a = sup('alfalfa'), w = sup('water');
  const tanker = f.tankers.filter((t) => t.room > 0).sort((x, y) => y.litres - x.litres)[0] || null;
  const room = storeRoom(f, b, a), share = b.need + a.need > 0 ? b.need / (b.need + a.need) : 0.3;
  let bags = Math.max(0, Math.floor((f.storeKg * share - b.amount - b.onTheWayAmount) / b.unitSize));
  let bales = Math.max(0, Math.floor((f.storeKg * (1 - share) - a.amount - a.onTheWayAmount) / a.unitSize));
  while (bags * b.unitSize + bales * a.unitSize > room && (bags > 0 || bales > 0)) { if (bales > 0) bales--; else bags--; }
  const litresIn = tanker ? Math.min(f.tankL, w.amount + w.onTheWayAmount + tanker.litres) : w.amount + w.onTheWayAmount;
  return {
    tanker, bags, bales, feedCost: bags * b.unitPrice + bales * a.unitPrice,
    water: w.need > 0 ? Math.floor(litresIn / w.need) : 999,
    feed: Math.min(b.need > 0 ? Math.floor((b.amount + b.onTheWayAmount + bags * b.unitSize) / b.need) : 999, a.need > 0 ? Math.floor((a.amount + a.onTheWayAmount + bales * a.unitSize) / a.need) : 999),
    tankRoom: Math.max(0, f.tankL - w.amount - w.onTheWayAmount),
  };
}
const STOPS_TEXT = 'مرض شي من حلالك، أو مات من مرض أو عطش · قرب العلف أو الماء يخلص (باقي 3 أيام) · نزل رصيدك تحت الصفر، أو وصل حساب التاجر حده · انكتبت عليك غرامة · جاك سوم على إعلان · جا يوم شوطك · باقي 3 أيام على قفل تسجيل مهرجان تقدر تدخله · بدا وقت الضراب وعندك ناقة تنلقح · ضاقت الشبوك على حلالك';
function calCardScreen() {
  const back = nav('', 'calDay');
  if (!G || CAL.day == null) return `<div class="body">${back}<div class="title">قبل ما تمشي</div>${waiting()}</div>`;
  const t = CAL.day, N = t - G.today, R = RU(), F = calFill();
  const w = sup('water'), b = sup('barley'), a = sup('alfalfa');
  const lasts = (x) => (x.need > 0 ? Math.floor((x.amount + x.onTheWayAmount) / x.need) : 999);
  const lw = lasts(w), lf = Math.min(lasts(b), lasts(a));
  const word = (n) => (n >= N ? '<span class="pos">يكفي</span>' : '<span style="color:var(--red);font-weight:700">ما يكفي</span>');
  const standW = (R.standing || []).includes('water'), standF = (R.standing || []).includes('feed');
  const supRow = (icon, name, last, fill, after, key, can) => `<div class="row r3"><span class="lead${last < N ? ' bad' : ''}">${svg(icon)}</span><b>${name} · ${last <= 0 ? (key === 'water' ? 'خلص' : 'خلص') : `يكفي ${days(Math.min(last, 999))}`}</b>${can ? `<span class="act"><button class="btn sm ghost" data-act="calFill" data-s="${key}" aria-label="عبّ ${name}">عبّه</button></span>` : ''}<small>${fill}${word(after)}</small></div>`;
  const wFill = standW ? 'الطلب الثابت شغّال: يجيك الوايت بنفسه. ' : F.tanker ? `وايت ${Math.round(F.tanker.litres / 1000)} طن يعبّي الخزان ${n0(Math.min(F.tankRoom, F.tanker.litres))} لتر والباقي يرجع، بـ ${n0(F.tanker.price)} ريال، يصير يكفي ${days(F.water)} تقريبًا: ` : 'الخزان ما يشيل وايت الحين: ';
  const fFill = standF ? 'الطلب الثابت شغّال: يجيك العلف بنفسه. ' : F.bags + F.bales > 0 ? `${[F.bags ? count(F.bags, 'bag') : '', F.bales ? count(F.bales, 'bale') : ''].filter(Boolean).join(' و')} بـ ${n0(F.feedCost)} ريال، يصير يكفي ${days(F.feed)} تقريبًا: ` : `${STORE().the} ${STORE().none} مكان الحين: `;
  const wAfter = standW ? N : F.tanker ? F.water : lw, fAfter = standF ? N : F.bags + F.bales > 0 ? F.feed : lf;
  const stopAt = Math.min(wAfter, fAfter) - 3;
  // what falls due on the way (the engine's dates)
  const due = [];
  const bs = calItems().find((x) => x.b === 'يبدأ وقت الضراب' && x.day <= t);
  if (bs) { const females = G.yard.filter((c) => c.sex === 'female' && !c.pregnant && c.ageDays >= 1209 && c.health === 'healthy').length; due.push(`<div class="row r2"><span class="lead">${svg('heart')}</span><b>وقت الضراب يبدأ ${dShortAt(bs.day)}</b><small>${females ? `عندك ${count(females, 'camel')} تقدر تنلقح` : 'ما عندك ناقة تنلقح للحين'}</small></div>`); }
  const between = G.festivals.filter((f) => !f.done && f.startsOn > G.today && f.startsOn <= t);
  const mine = between.filter((f) => (f.myEntries || []).length);
  if (between.length) due.push(`<div class="row r2"><span class="lead fest">${svg('cup')}</span><b>${count(between.length, 'fest')}</b><small>${between.map((f) => shortFest(f.name)).join('، ')} · ${mine.length ? `مسجّل بـ ${mine.map((f) => shortFest(f.name)).join('، ')}، ويوقف يوم شوطك` : 'ما سجلت بشي'}</small></div>`);
  const calvings = G.yard.filter((c) => c.pregnant && c.dueOn != null && c.dueOn > G.today && c.dueOn <= t);
  if (calvings.length) due.push(`<div class="row r2"><span class="lead bad">${svg('heart')}</span><b>${calvings.map((c) => esc(c.name)).join('، ')} ${calvings.length > 1 ? 'يولدن' : 'تولد'}</b><small>${calvings.map((c) => ddAt(c.dueOn)).join('، ')}${R.crowdedSoon ? ' · الشبوك ما تشيل زيادة: ابنِ شبك قبل' : ''}</small></div>`);
  const milkDay = G.farm.milk.sold * G.farm.milk.price, wages = G.farm.monthlyWages;
  due.push(`<div class="row r2"><span class="lead milk">${svg('milk')}</span><b>${milkDay > 0 ? `الحليب يدخلك ${n0(milkDay)} ريال باليوم` : 'ما فيه حليب ينباع'}</b><small>${wages ? `والرواتب ${n0(wages)} ريال أول كل شهر` : 'وما عليك رواتب: ما عندك رعاة'}</small></div>`);
  // the guard: a sick camel waits for her treatment (unless a contract); his round being told today
  const block = R.awayBlock, sick = R.sick || [];
  const guard = block === 'sick' ? `${alertCard(sick.length === 1 ? `${esc(sick[0].name)} ${sick[0].sex !== 'male' ? 'مريضة' : 'مريض'}` : `${count(sick.length, 'head')} مريضة`, `${sick.length === 1 && sick[0].sex === 'male' ? 'عالجه' : 'عالجها'} أول، وبعدها تمشي. أو اتعاقد مع البيطري ويعالج اللي يمرض وأنت بعيد.`)}<div class="group">${sick.map(sickRow).join('')}</div>`
    : block === 'round' ? alertCard('شوطك اليوم ما خلص', 'تمشي بعد ما تخلص مراحله.') : '';
  const goKey = 'calGo', sure = HJ.sure === goKey, can = !block;
  return `<div class="body">${back}<div class="title">قبل ما تمشي</div>${errCard()}
    <div class="span"><b>لين ${ddAt(t)}</b><small>${days(N)} · من ${ddAt(G.today)}</small></div>
    ${guard}
    <div class="sec">يكفي ${days(N)}؟</div>
    <div class="group">
      ${supRow('water', 'الماء', lw, wFill, wAfter, 'water', !standW && !!F.tanker)}
      ${supRow('feed', 'العلف', lf, fFill, fAfter, 'feed', !standF && F.bags + F.bales > 0)}</div>
    ${stopAt < N ? `<div class="note">حتى لو عبّيت، ما يكفي الأيام كلها: يوقف التقويم حوالي ${dShortAt(G.today + Math.max(1, stopAt))} عشان تطلب، وبعدها تكمل.</div>` : ''}
    <div class="sec">اللي يجي بالطريق</div>
    <div class="group">${due.join('')}</div>
    <div class="sec">تقدر تجهّز قبل</div>
    <div class="group">
      <div class="row r3"><span class="lead">${svg('repeat')}</span><b>طلب ثابت للماء والعلف</b><span class="act"><span class="sw${standW && standF ? ' on' : ''}" data-act="standingBoth" role="switch" tabindex="0" aria-checked="${standW && standF}" aria-label="طلب ثابت للماء والعلف"><i></i></span></span><small>لما يبقى 3 أيام يجيك الطلب بنفسه، وتدفعه مثل أي طلب</small></div>
      ${vetRows()}</div>
    <div class="sec">يوقف ويرجع لك لو</div>
    <div class="stops">${STOPS_TEXT}</div>
    <div class="note">وكل شي ثاني يمشي بنفسه: الحليب ينباع، والرواتب تنخصم، والولادات تصير، وتلقاها كلها بالآخر.</div>
    <button class="btn ${!can ? '' : sure ? 'sure' : 'pri'} wide" data-act="calGo" ${can ? '' : 'disabled'}>${sure ? 'اضغط مرة ثانية ويمشي' : `امشِ لين ${ddAt(t)}`}</button>
    <div class="note">التقويم يمشي لقدام بس: الأيام اللي تمضي ما ترجع. وتقدر توقفه بنص الطريق.</div></div>`;
}
function calGoingScreen() {
  const P = CAL.progress, t = CAL.day, from = CAL.from ?? (G ? G.today : 0);
  const day = P ? P.day : from, done = P ? P.done : 0, total = P ? P.total : Math.max(1, (t ?? from) - from);
  const pct = Math.round(done / Math.max(1, total) * 100);
  if (P && P.saving) return `<div class="body"><div class="nav"></div><div class="title">يمشي الوقت</div>
    <div class="tank"><small>وصل</small><div class="v"><b class="fit">${G ? ddAt(day) : ''}</b></div>
      <div class="bar"><i style="width:100%;background:linear-gradient(90deg,#0b8a5c,#3fb487)"></i></div>
      <div class="ln">يحفظ اللعبة…</div></div>
    <div class="note">خلصت الأيام، ويحفظ قبل ما يرجع لك.</div></div>`;
  return `<div class="body"><div class="nav"></div><div class="title">يمشي الوقت</div>
    <div class="tank"><small>وصل</small><div class="v"><b class="fit">${G ? ddAt(day) : ''}</b></div>
      <div class="bar"><i style="width:${pct}%;background:linear-gradient(90deg,#0b8a5c,#3fb487)"></i></div>
      <div class="ln">${days(done)} من ${days(total)}${t != null && G ? ` · لين ${dShortAt(t)}` : ''}</div></div>
    <button class="btn ghost wide" data-act="calStop">${svg('stop')}وقّف هنا</button>
    <div class="note">الأيام تنحسب يوم يوم، ويوقف بنفسه لو صار شي يبيك. ولو حلالك كبير ممكن ياخذ ثواني.</div></div>`;
}
const SUP_AR = { barley: 'الشعير', alfalfa: 'البرسيم', water: 'الماء' };
function stopWords(stop) {
  const c = stop.subject ? (G.yard.find((x) => x.id === stop.subject) || null) : null;
  const f = !c || c.sex !== 'male', nm = esc(stop.name || (c && c.name) || '');
  switch (stop.kind) {
    case 'illness': return { title: `${nm} ${f ? 'مرضت' : 'مرض'}`, line: `${f ? 'عالجها' : 'عالجه'} اليوم: لو ${f ? 'تركتها' : 'تركته'} بعد 10 أيام ممكن ${f ? 'تموت' : 'يموت'}.`, act: f ? 'عالجها' : 'عالجه', go: 'build' };
    case 'death': return { title: `${f ? 'ماتت' : 'مات'} ${nm}`, line: 'شوف وش يحتاج حلالك قبل ما تكمل.', act: 'العزبة', go: 'build' };
    case 'supply': { const x = sup(stop.subject); const l = x && x.need > 0 ? Math.floor(x.amount / x.need) : 0; const nmS = SUP_AR[stop.subject] || 'العلف';
      return { title: x && (x.short || l <= 0) ? `${nmS} خلص` : `${nmS} يخلص ${l <= 1 ? 'بكرة' : `بعد ${days(l)}`}`, line: 'اطلب اليوم يوصل بكرة، وبعدها كمّل.', act: stop.subject === 'water' ? 'اطلب وايت' : 'اطلب علف', go: stop.subject === 'water' ? 'water' : 'feed' }; }
    case 'money': return { title: `رصيدك صار تحت الصفر`, line: debtLine(), act: 'البنك', go: 'bank' };
    case 'account': return { title: 'حساب التاجر وصل حده', line: accountFullLine(), act: 'البنك', go: 'bank' };
    case 'fine': return { title: `انكشف تجميل ${nm ? `بـ${nm}` : 'بحلالك'}`, line: 'وانكتبت عليك الغرامة. التفاصيل بالحراج.', act: 'الحراج', go: 'haraj' };
    case 'offer': return { title: `جاك سوم على ${nm}`, line: `السوم ينتهي بعد ${days(G.haraj.offerDays ?? 3)}: اقبله أو ارفضه من إعلاناتي.`, act: 'إعلاناتي', go: 'haraj', tab: 'mine' };
    case 'round': return { title: `اليوم شوطك بـ${shortFest(stop.name || '')}`, line: `وقف الساعة 6 الصبح قبل أول مرحلة الساعة 7، وتجيك المراحل وحدة وحدة مثل أي يوم.${/money/.test(stop.extra || '') ? ' ونقل حلالك للمهرجان نزّل رصيدك تحت الصفر: ما تقدر تشتري حلال ولا تبني لين تسدد.' : ''}`, act: 'شوف يوم الشوط', go: 'mazayen' };
    case 'registration': return { title: `باقي 3 أيام ويقفل تسجيل ${esc(stop.name || '')}`, line: 'وعندك حلال يقدر يدخله. وبعد القفل تسجيل متأخر برسوم لين 72 ساعة قبل الشوط.', act: 'شوف المزاين', go: 'mazayen' };
    case 'breeding': return { title: 'بدا وقت الضراب', line: 'وعندك ناقة تنلقح.', act: null, go: null };
    case 'crowded': return { title: 'ضاقت الشبوك على حلالك', line: 'ابنِ شبك من العزبة.', act: 'العزبة', go: 'build' };
    case 'cancelled': return { title: 'وقّفته', line: '', act: null, go: null };
    default: return { title: 'وقف التقويم', line: '', act: null, go: null };
  }
}
function calStopScreen() {
  const back = nav();
  const R = CAL.result;
  if (!G || !R) return `<div class="body">${back}<div class="title">التقويم</div>${waiting()}</div>`;
  const s = R.stop, w = stopWords(s), left = R.target - R.to, sure = HJ.sure === 'calGo';
  const blocked = RU().awayBlock;
  return `<div class="body">${back}<div class="title">وقف التقويم</div>
    <div class="${s.kind === 'round' || s.kind === 'breeding' || s.kind === 'cancelled' ? 'msgc good' : 'warn'}"><span class="lead">${svg(s.kind === 'round' ? 'cup' : 'alert')}</span><b>${w.title}</b><small>وقف ${ddAt(R.to)}${left > 0 ? `، وباقي ${days(left)} لين ${dShortAt(R.target)}` : ''}. ${w.line}</small></div>
    ${w.act ? `<button class="btn pri wide" data-go="${w.go}"${w.tab ? ` data-tab="${w.tab}"` : ''}>${w.act}</button>` : ''}
    ${left > 0 ? `<button class="btn ${blocked ? '' : sure ? 'sure' : 'ghost'} wide" data-act="calGo" data-again="1" ${blocked ? 'disabled' : ''}>${sure ? 'اضغط مرة ثانية ويكمل' : `كمّل لين ${ddAt(R.target)}`}</button>` : ''}
    ${blocked === 'round' && s.kind === 'round' ? '<div class="note">ما يكمّل إلا بعد ما يخلص الشوط، عشان ما يفوتك شي منه.</div>' : blocked === 'sick' ? '<div class="note">يكمّل بعد ما تعالج اللي مرض.</div>' : ''}
    <div class="group"><div class="row r3" data-go="calSum" role="button" tabindex="0"><span class="lead sea">${svg('flag')}</span><b>اللي صار لين هنا</b><span class="chev">${svg('chev')}</span><small>${days(R.to - R.from)}، من ${dShortAt(R.from)}</small></div></div></div>`;
}
const SPENT = { feed: 'العلف', water: 'الوايت', wages: 'الرواتب', vet: 'البيطري', vetContract: 'عقد البيطري', transport: 'النقل' };
function calSumScreen() {
  const back = nav('', CAL.result && CAL.result.stop.kind !== 'target' ? 'calStop' : '');
  const R = CAL.result;
  if (!G || !R) return `<div class="body">${back}<div class="title">اللي صار</div>${waiting()}</div>`;
  const m = R.summary, rows = [];
  rows.push(`<div class="row r2"><span class="lead milk">${svg('milk')}</span><b>${m.milk ? `الحليب دخلك ${n0(m.milk)} ريال` : 'ما دخل حليب'}</b><small>${m.milk ? 'ينباع كل يوم' : 'ما فيه ناقة مرضع'}</small></div>`);
  const spent = Object.entries(m.spent || {}).filter(([k]) => SPENT[k]).sort((x, y) => y[1] - x[1]);
  if (spent.length) rows.push(`<div class="row r2"><span class="lead">${svg('bank')}</span><b>صرفت ${n0(spent.reduce((n, [, v]) => n + v, 0))} ريال</b><small>${spent.slice(0, 3).map(([k, v]) => `${SPENT[k]} ${n0(v)}`).join('، ')}</small></div>`);
  if (m.delivered) rows.push(`<div class="row r2"><span class="lead">${svg('truck')}</span><b>وصلت ${count(m.delivered, 'order')}</b><small>${m.standingOrders ? `منها ${count(m.standingOrders, 'order')} بالطلب الثابت` : 'العلف والوايت'}</small></div>`);
  const ill = m.fellIll || [], died = Object.values(m.deaths || {}).reduce((n, v) => n + v, 0);
  rows.push(`<div class="row r2"><span class="lead ${ill.length || died ? 'bad' : ''}">${svg('heart')}</span><b>${ill.length ? `مرض ${count(ill.length, 'head')}` : 'ما مرض شي'}</b><small>${[m.treated ? `تعالج ${count(m.treated, 'head')}` : '', died ? `مات ${count(died, 'head')}${(m.diedOfIllnessOrThirst || []).length ? `: ${m.diedOfIllnessOrThirst.map(esc).join('، ')}` : ''}` : 'وما مات شي'].filter(Boolean).join(' · ')}</small></div>`);
  if ((m.born || []).length) rows.push(`<div class="row r2"><span class="lead">${svg('heart')}</span><b>ولد ${count(m.born.length, 'head')}</b><small>${m.born.map(esc).join('، ')}</small></div>`);
  if ((m.built || []).length) rows.push(`<div class="row r2"><span class="lead">${svg('build')}</span><b>خلص البناء</b><small>${m.built.map(FAC_NAME).join('، ')}</small></div>`);
  if ((m.registrationsOpened || []).length) rows.push(`<div class="row r2"><span class="lead fest">${svg('cup')}</span><b>انفتح تسجيل ${count(m.registrationsOpened.length, 'fest')}</b><small>${m.registrationsOpened.map(shortFest).join('، ')}</small></div>`);
  if (m.offers) rows.push(`<div class="row r2"><span class="lead">${svg('haraj')}</span><b>جاك ${count(m.offers, 'bid')}</b><small>شوفها بإعلاناتي</small></div>`);
  if (m.listingsExpired) rows.push(`<div class="row r2"><span class="lead">${svg('haraj')}</span><b>انتهى ${count(m.listingsExpired, 'order')}</b><small>إعلاناتك اللي ما انباعت</small></div>`);
  if (R.stop.kind !== 'target' && R.stop.kind !== 'cancelled') rows.push(`<div class="row r2"><span class="lead bad">${svg('alert')}</span><b>${stopWords(R.stop).title}</b><small>هذا اللي وقّف التقويم</small></div>`);
  return `<div class="body">${back}<div class="title">اللي صار</div>
    <div class="span"><b>${days(R.to - R.from)}</b><small>من ${ddAt(R.from)} لين ${ddAt(R.to)}</small></div>
    <div class="group">${rows.join('')}</div>
    <div class="note">والتفاصيل بالبنك والعزبة.</div></div>`;
}

const S = {
    // home: the date, the balance and the herd (its word: the start's nursing camel and her calf as they are, else the
    // head by the counting rule), and the apps that work on the game (the owner, 13 Nov: the others, and
    // the example content of the design's screens, are not shown until they work on the engine)
    home: () => `<div class="body"><div class="hs">${dateLine()}
      <div class="widgets">
        <div class="wg" data-go="bank" role="button" tabindex="0" aria-label="${G && G.cash < 0 ? `عليك ${n0(-G.cash)} ريال` : `الرصيد ${G ? n0(G.cash) : ''} ريال`}، البنك"><small>${G && G.cash < 0 ? 'عليك' : 'الرصيد'}</small><div class="big2${G && G.cash < 0 ? ' bad' : ''}"><b class="fit">${G ? n0(Math.abs(G.cash)) : '…'}</b></div><div class="ln ink2">ريال</div><div class="ln${G && !G.todayNet ? ' ink2' : ''}">${!G ? '' : G.todayNet > 0 ? `<span class="pos">دخل اليوم ${n0(G.todayNet)}</span>` : G.todayNet < 0 ? `صرفت اليوم ${n0(-G.todayNet)}` : 'ما فيه حركة اليوم'}</div></div>
        <div class="wg"><small>الحلال</small><div class="big2"><b class="fit">${G ? n0(G.herd.total) : '…'}</b></div><div class="ln ink2">${herdWord()}</div><div class="ln ink2">${G && G.herd.total ? `قيمته ${n0(G.herdValue)} ريال` : ''}</div></div>
      </div>
      <div class="apps">
        ${app('water', 'الوايت', badge(lowCount(['water'])))}
        ${app('feed', 'العلف', badge(lowCount(['barley', 'alfalfa'])))}
        ${app('milk', 'الحليب')}
        ${app('build', 'العزبة')}
        ${app('haraj', 'الحراج', badge(G ? G.openOffers : 0))}
        ${app('bank', 'البنك')}
        ${app('cup', 'المزاين', badge(mzBadge()))}
        ${app('talk', 'المحادثات', badge(G ? G.dealer.unread : 0))}
        ${app('cal', 'التقويم')}
      </div></div></div>`,
    water: waterScreen,
    feed: feedScreen,
    milk: milkScreen,
    build: buildScreen,
    haraj: harajScreen,
    listing: listingScreen,
    pick: pickScreen,
    sell: sellScreen,
    bank: bankScreen,
    bankMonth: bankMonthScreen,
    mazayen: mazayenScreen,
    fest: festScreen,
    enter: enterScreen,
    day: dayScreen,
    result: resultScreen,
    chats: chatsScreen,
    chat: chatScreen,
    strength: strengthScreen,
    cal: calScreen,
    calDay: calDayScreen,
    calCard: calCardScreen,
    calGoing: calGoingScreen,
    calStop: calStopScreen,
    calSum: calSumScreen,
  };

// A screen's words kept together where a line must not break: a number with the word after it («20,000 | ريال»),
// «بـ» with its number («بـ 64»), a short preposition or «و» with the word after it («أكبر من | العزبة», «قبل | 3
// شهور»; the audit), and on المزاين's and the chat's screens a number with the word before it too («لين | 100,000»).
// (A preposition right after another, «من بعد المفرودة»: the space before the second was taken by the first match, so
// the pass runs again till nothing changes; no lookbehind, which iOS's WebKit reads only from 16.4, the app from 15.)
export function keepTogether(html, mazayen = false) {
  let out = html.replace(/(\d) (?=[\u0600-\u06FF])/g, '$1\u00a0').replace(/(^|[\s>])بـ (?=\d)/g, '$1بـ\u00a0');
  for (let i = 0; i < 4; i++) {
    const next = out.replace(/(^|[\s>])(من|في|على|عن|مع|إلى|الى|لين|قبل|بعد|كل|و) (?=[^\s<])/g, '$1$2\u00a0');
    if (next === out) break;
    out = next;
  }
  return mazayen ? out.replace(/([\u0600-\u06FF]) (?=\d)/g, '$1\u00a0') : out;
}

export function createPhone({ host }) {
  const el = document.createElement('div'), root = el.attachShadow({ mode: 'open' });
  root.innerHTML = `<style>${CSS}</style><div class="phone" data-state="closed" lang="ar" role="dialog" aria-label="الجوال" aria-hidden="true"><div class="dim"></div><div class="dev" tabindex="-1"><div class="scr" inert></div></div><div class="sr" role="status" aria-live="polite"></div></div>`;
  host.appendChild(el);
  root.addEventListener('selectstart', (e) => { let t = e.composedPath()[0]; if (t && t.nodeType !== 1) t = t.parentElement; if (!t?.closest?.('input, textarea, [contenteditable]:not([contenteditable="false"])')) e.preventDefault(); }, true);      // (it does not leave the shadow tree for the page's guard, farm.html; a text field keeps it)
  const box = root.querySelector('.phone'), dev = root.querySelector('.dev'), scr = root.querySelector('.scr'), dim = root.querySelector('.dim'), sr = root.querySelector('.sr');
  const st = { state: 'closed', play: false, screen: 'home', s: SMALL };
  const listeners = new Set();
  let press = null, lastDown = 0, bigAt = 0, focusBack = null, shownAt = 0;
  const turned = () => document.body.classList.contains('rot');      // (farm.html: a phone held upright, the game turned a quarter)
  const endPress = () => { if (press) { clearTimeout(press.timer); press = null; } };
  let drawn = '';
  function show(v, same = false) {
    if (v !== st.screen) { ERR = null; shownAt = performance.now(); }
    if (v === 'feed' && st.screen !== 'feed') ORD.barley = ORD.alfalfa = null;      // (opened afresh: the order starts at three weeks' need)
    st.screen = v; scr.classList.toggle('home', v === 'home');
    // (المزاين's and the chat's screens, as their design: a number kept with the word before it too, «لين | 100,000»)
    // («بـ 64»: the prefix never left at a line's end either)
    let html = keepTogether(S[v](), MZ_SCREENS.has(v) || v.startsWith('cal'));      // (and التقويم's, as its design)
    if (same && html === drawn) return false;      // (a redraw that would draw the same: left as it is)
    drawn = html;
    scr.innerHTML = `<span class="pill"></span>${sbar()}${html}<div class="hb"></div>`;      // (a number kept on the line of the word after it: «20,000 | ريال» split across lines otherwise)
    fitNumbers();
  }
  // enlarged, a big figure wider than its card is set smaller to fit it, as iOS fits a label to its width (a balance in
  // the millions runs out of its widget); read once as a screen shows or the phone enlarges, never per frame
  function fitNumbers() {
    for (const e of scr.querySelectorAll('.fit')) {
      e.style.fontSize = '';
      if (st.state !== 'big') continue;
      const card = e.closest('.wg, .tank, .balance');      // (the box that holds it)
      let pad = 0;
      for (let q = e.parentElement; q; q = q.parentElement) { const c = getComputedStyle(q); pad += parseFloat(c.paddingLeft) + parseFloat(c.paddingRight); if (q === card) break; }
      const across = (q) => { const r = q.getBoundingClientRect(); return turned() ? r.height : r.width; };      // (along the phone's width on the screen: turned, the screen's height)
      const cw = parseFloat(getComputedStyle(card).width), room = across(card) * (cw - pad) / cw, ew = across(e);      // (computed lengths are unzoomed; boxes are as drawn)
      if (ew > room) e.style.fontSize = (parseFloat(getComputedStyle(e).fontSize) * room / ew * 0.97).toFixed(1) + 'px';
    }
  }
  // a button the keyboard brings the focus to is scrolled into sight, clear of the top bar that stays (focused without
  // the browser's own scrolling, which moved the page). Along the phone: turned, the screen's x the other way
  function reveal(el) {
    const sc = st.state === 'big' && el.closest && el.closest('.body');
    if (!sc || sc.scrollHeight <= sc.clientHeight + 1 || el.closest('.nav')) return;      // (the top bar does not scroll: moved for it, the content stepped 52 pt a Tab)
    const span = (q) => { const r = q.getBoundingClientRect(); return turned() ? [innerWidth - r.right, innerWidth - r.left] : [r.top, r.bottom]; };
    const [s0, s1] = span(sc), k = sc.clientHeight / Math.max(1, s1 - s0), [e0, e1] = span(el);
    const nav = sc.querySelector(':scope > .nav');
    const top = (nav ? span(nav)[1] : s0) + 8, bottom = s1 - 8;
    if (e0 < top) sc.scrollTop -= (top - e0) * k; else if (e1 > bottom) sc.scrollTop += (e1 - bottom) * k;
  }
  const focusIn = (el) => { el.focus({ preventScroll: true }); reveal(el); };
  // the small phone's size and place: by the screen's height (it leaves the top row of buttons clear), at the right
  // edge on the map, and left of the door's buttons and the pedals in play
  function layout() {
    const w = host.clientWidth, h = host.clientHeight, u = Math.min(w / 100, 9.5);
    st.s = Math.max(0.2, Math.min(SMALL, (h - SMALL_ROOM) / H));
    box.style.setProperty('--s', st.s.toFixed(3));
    box.style.setProperty('--r', `calc(${st.play ? Math.round(28 * u) : 56}px + max(0px, var(--edge-r, 12px) - 12px))`);
    box.style.setProperty('--b', 'calc(10px + max(0px, var(--edge-b, 12px) - 12px))');
    place();
  }
  // enlarged, the whole phone in the screen, in the middle: as large as the screen's height allows, never larger than
  // true size (the owner: "half of it under the screen", its dock and buttons out of reach; it must sit balanced)
  const bigScale = () => Math.min(1, (host.clientHeight - 2 * EDGE) / H, (host.clientWidth - 2 * EDGE) / W);
  let sized = '';
  function place() {
    const sb = st.state === 'big' ? bigScale() : 1, key = `${sb.toFixed(4)} ${host.clientHeight}`;
    if (sized === key) return;      // (set only when it changes, as it enlarges or the screen turns)
    sized = key;
    box.style.setProperty('--sb', sb.toFixed(4));
    box.style.setProperty('--y', `${Math.max(EDGE, (host.clientHeight - H * sb) / 2).toFixed(1)}px`);
  }
  function set(state) {
    if (state === st.state) return;
    endPress();
    if (st.state === 'closed') show('home');
    const was = st.state;
    st.state = state; box.dataset.state = state;
    if (state !== 'big' && HJ.sure) { HJ.sure = null; if (state !== 'closed') redraw(); }      // (a sale readied on the enlarged phone does not wait for its return; its button drawn again unreadied)
    // to assistive technology and the keyboard: closed, the phone is not there; small, it is a picture (a tap does
    // nothing); big, it is a modal dialog with the focus in it, given back to where it was when it shrinks
    box.setAttribute('aria-hidden', String(state === 'closed'));
    if (state === 'big') { box.setAttribute('aria-modal', 'true'); scr.inert = false; focusBack = document.activeElement; dev.focus({ preventScroll: true }); }
    else { box.removeAttribute('aria-modal'); scr.inert = true; if (was === 'big' && focusBack && focusBack.isConnected) focusBack.focus({ preventScroll: true }); }
    layout(); fitNumbers();
    box.classList.toggle('turned', turned());
    for (const f of listeners) f(state);
  }
  // is a point of the game's frame on the small phone? (the small phone takes no pointer itself: the page asks)
  function hit(x, y) {
    if (st.state !== 'small') return false;
    const x1 = dev.offsetLeft + W, y1 = dev.offsetTop + H;
    return x <= x1 && x >= x1 - W * st.s && y <= y1 && y >= y1 - H * st.s;
  }
  // a long press on the small phone enlarges it. Watched on the window: the small phone lets every pointer through,
  // so a drag over it still turns the view
  // (when the time is up the press is confirmed one task later, after pointer events already waiting in the queue
  // have been read; not on the next frame: on slow frames the finger had lifted before it came)
  const confirmPress = (mine) => setTimeout(() => { if (press === mine) { press = null; if (st.state === 'small') { bigAt = performance.now(); set('big'); } } }, 0);      // (still small: closed meanwhile, it stays closed)
  addEventListener('pointerdown', (e) => { lastDown = performance.now(); endPress(); if (hit(e.clientX, e.clientY)) { const mine = { id: e.pointerId, x: e.clientX, y: e.clientY }; mine.timer = setTimeout(() => confirmPress(mine), LONG_PRESS); press = mine; } }, true);
  addEventListener('pointermove', (e) => { if (press && e.pointerId === press.id && Math.hypot(e.clientX - press.x, e.clientY - press.y) > SLOP) endPress(); }, true);
  addEventListener('pointerup', (e) => { if (press && e.pointerId === press.id) endPress(); }, true);
  addEventListener('pointercancel', endPress, true);
  // enlarged: a tap outside it makes it small again; a tap on it is the phone's (a finger that slid is not a tap)
  let drag = null, slid = false;
  // The game turned (a phone held upright), the browser's own scrolling goes by the screen's axes and the enlarged phone's
  // content did not scroll at all. There the phone scrolls it itself, by the finger's travel along the phone (the page
  // hands pointer events over in the game's frame, where the phone stands upright), with a fling as it lets go that
  // slows as iOS's does (by 0.998 a millisecond). The phone is drawn at [k] of its size, so the content follows the
  // finger at 1/k of its screen pixels (at 1, the content moved 0.59 of the finger's travel, the review).
  let fling = 0, flinging = false, stopTap = false;
  dev.addEventListener('pointerdown', (e) => {
    if (st.state !== 'big') return;
    stopTap = flinging; cancelAnimationFrame(fling); flinging = false;      // (a tap on a moving list only stops it, as on iOS)
    const sc = turned() ? e.target.closest('.body') : null;
    drag = { id: e.pointerId, y: e.clientY, sc, top: sc ? sc.scrollTop : 0, t: e.timeStamp, last: e.clientY, v: 0, k: bigScale() }; slid = false;
  });
  dev.addEventListener('pointermove', (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    if (!slid && Math.abs(e.clientY - drag.y) > SLOP) slid = true;
    if (!slid || !drag.sc) return;
    drag.sc.scrollTop = drag.top - (e.clientY - drag.y) / drag.k;
    const dt = e.timeStamp - drag.t; if (dt > 0) drag.v = 0.8 * ((drag.last - e.clientY) / drag.k / dt) + 0.2 * drag.v;
    drag.t = e.timeStamp; drag.last = e.clientY;
  });
  const endDrag = (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const { sc, v, t } = drag; drag = null;
    if (!sc || !slid || Math.abs(v) < 0.05 || e.timeStamp - t > 100) return;
    let speed = v, at = performance.now();
    const step = (now) => {
      const dt = now - at; at = now; const before = sc.scrollTop;
      sc.scrollTop += speed * dt; speed *= Math.pow(0.998, dt);
      if (Math.abs(speed) > 0.02 && sc.scrollTop !== before) fling = requestAnimationFrame(step); else flinging = false;
    };
    flinging = true; fling = requestAnimationFrame(step);
  };
  dev.addEventListener('pointerup', endDrag); dev.addEventListener('pointercancel', endDrag); dev.addEventListener('pointerleave', endDrag);
  dim.addEventListener('mousedown', (e) => e.preventDefault());      // (the mouse events after a long press by touch land on the dim and took the focus out of the phone)
  dim.addEventListener('click', () => { if (lastDown > bigAt) set('small'); });      // (not the lift of the very finger whose long press enlarged it: its click lands on the dim, now on top)
  // a page opened: الحراج's camel or listing it is about (its id on the row tapped), the words of the last order and a
  // sale waiting for its second tap left behind
  function pick(t) {
    HJ.msg = null; HJ.sure = null;
    const id = t.dataset.id, to = t.dataset.go;
    if (to === 'listing' && id) { HJ.listing = id; HJ.bid = null; }
    if (to === 'sell' && id) { HJ.camel = id; HJ.ask = null; }
    if (to === 'haraj' && st.screen === 'home') {
      HJ.tab = 'market';      // (the app opened afresh: what is for sale)
      const f = G && G.findings[0];
      if (f) {
        HJ.msg = foundWords(f.name, [f.kind], f.fine, null, myCamel(f.camel)?.sex === 'male');
        engine?.dispatch({ type: 'markFindingsTold', count: 1 }).catch((err) => console.warn('phone:', err));
        sr.textContent = `${HJ.msg.title}. ${HJ.msg.line}`.replace(/<[^>]+>/g, '');      // (said as the other answers are)
      }
    }
    if (to === 'bankMonth' && t.dataset.month) { BK.month = t.dataset.month; BK.data = null; loadMonth(); }
    // المزاين: a festival's page, or an entry's day or result (its festival's page asked of the engine)
    if (to === 'mazayen' && st.screen === 'home') { SEEN.open = [...new Set([...SEEN.open, ...openFests().map((f) => f.id)])]; saveSeen(); }
    if ((to === 'fest' && id) || ((to === 'day' || to === 'result') && t.dataset.f)) {
      const fid = to === 'fest' ? id : t.dataset.f;
      if (fid !== MZ.fest) { MZ.page = MZ.text = null; MZ.fest = fid; }
      if (to !== 'fest') MZ.entry = { round: t.dataset.o, camel: id };
      loadFest();
    }
    if (to === 'enter') MZ.sel = null;
    // التقويم: a day picked from the year's rows; a stop's button to الحراج's listings
    if (to === 'calDay' && t.dataset.day) { CAL.day = Number(t.dataset.day); CAL.month = null; }
    if (to === 'cal' && st.screen === 'home') { CAL.month = null; }
    if (to === 'haraj' && t.dataset.tab) HJ.tab = t.dataset.tab;
    if (to === 'strength' && t.dataset.k) CH.kind = t.dataset.k;
    // the treatment man's messages read as his chat opens
    if (to === 'chat' && G && G.dealer.unread && engine) engine.dispatch({ type: 'readMessages' }).catch((err) => console.warn('phone:', err));
  }
  // a festival's page asked of the engine (again when the festivals change while it is open); a late answer for another
  // festival is dropped
  async function loadFest() {
    if (!engine || !MZ.fest || !engine.festival) return;
    const ask = ++MZ.asked, id = MZ.fest, rev = G ? G.sections.festivals : null;
    let r = null;
    try { r = await engine.festival(id); } catch (err) { console.warn('phone:', err); }
    if (ask !== MZ.asked || id !== MZ.fest) return;
    MZ.rev = rev;
    // (the same page again, the festivals having changed elsewhere: not drawn again)
    const text = r && r.ok && r.festival ? JSON.stringify(r.festival) : null;
    if (text && text === MZ.text) return;
    if (text) { MZ.page = r.festival; MZ.text = text; }
    if (live() && MZ_PAGE.has(st.screen)) redrawKept();
  }
  const MZ_PAGE = new Set(['fest', 'enter', 'day', 'result']);
  // what the المزاين and chat screens show changes only with the festivals, the notices, the day, the money (a debt's
  // card) and the treatments: another snapshot leaves them as they are
  // (by screen: the list counts days to each round; registering's refusals move with the money and the day, so its page
  // is asked again then; a round's day and its result show the debt's card; the chat shows the messages, the
  // treatments bought and whether a round is still to come)
  const mzKey = (g, v) => {
    if (!g) return '';
    const offer = () => { const ms = g.dealer.messages; for (let i = ms.length - 1; i >= 0; i--) if (ms[i].roundDay > g.today && g.yard.some((c) => c.id === ms[i].camel)) return ms[i].camel; return ''; };
    if (v === 'mazayen') return [g.sections.festivals, g.date, g.bannedThrough].join('|');
    if (v === 'fest') return [g.sections.festivals, g.today > (MZ.page ? MZ.page.festival.closesOn : 0)].join('|');
    if (v === 'enter') return [g.sections.festivals, g.date, g.cash].join('|');
    if (v === 'day' || v === 'result') return [g.sections.festivals, g.cash < 0 ? g.cash : 0, g.farm.account.owed].join('|');
    return [g.sections.notices, g.tamperings.length, offer(), g.cash < 0].join('|');
  };
  // drawn again with the keyboard's place kept (the page comes a moment after it opens)
  function redrawKept() {
    const f = root.activeElement, inScr = f && scr.contains(f);
    const key = inScr ? keyOf(f) : null, go = inScr ? f.dataset.go : null;
    if (!redraw(true)) return;
    if (!inScr) return;
    const again = [...scr.querySelectorAll('[data-act], [data-go]')].find((x) => (key && x.dataset.act ? keyOf(x) === key : go && x.dataset.go === go));
    focusIn(again || scr.querySelector('.back') || dev);
  }
  // البنك: the month opened, its kinds asked of the engine (again when money moves while it is open); an answer that
  // comes after another was asked for is dropped
  async function loadMonth() {
    if (!engine || !BK.month) return;
    const ask = ++BK.asked, month = BK.month, rev = G ? G.sections.bank : null;
    let r = null;
    try { r = await engine.bankMonth(month); } catch (err) { console.warn('phone:', err); }
    if (ask !== BK.asked || month !== BK.month) return;
    BK.rev = rev;
    if (r && r.ok && r.month) BK.data = r.month;
    else if (r && r.ok) { BK.month = null; BK.data = null; if (live() && st.screen === 'bankMonth') show('bank'); return; }      // (no money in it: not a month the list has)
    if (live() && st.screen === 'bankMonth') redrawBank();
  }
  // a bank screen drawn again with the keyboard's place kept (its kinds come a moment after the month opens, and a
  // snapshot redraws it: the control that had the focus is the same one drawn again)
  function redrawBank() {
    const f = root.activeElement, inScr = f && scr.contains(f);
    const sel = !inScr ? null : f.classList.contains('back') ? '.back' : f.dataset.month ? `[data-month="${f.dataset.month}"]` : f.dataset.go ? `[data-go="${f.dataset.go}"]` : null;
    redraw();
    if (inScr) focusIn((sel && scr.querySelector(sel)) || scr.querySelector('.back') || dev);
  }
  // what the bank's screens show changes only with the bank's revision, the balance, the day, or (day one's line)
  // whether the day's milk is sold: another snapshot leaves them as they are
  const bankKey = (g) => (g ? [g.sections.bank, g.cash, g.date, g.farm.milk.sold > 0.05].join('|') : '');
  // the screens the game's numbers fill are drawn again when they change, the scroll kept
  const live = () => st.state !== 'closed';      // (every screen shows the game's own numbers)
  function redraw(same = false) {
    const sc = scr.querySelector('.body'), top = sc ? sc.scrollTop : 0;
    if (show(st.screen, same) === false) return false;
    const again = scr.querySelector('.body');
    if (again) again.scrollTop = top;
    return true;
  }
  // التقويم's jump (T15): the engine runs it (EngineCore.away); its progress redraws the screen under way a few times a
  // second at most; at its end the stop or the summary
  const AWAY_NO = { notAhead: 'اختار يوم بعد اليوم.', tooFar: 'التقويم يمشي سنة بالكثير.', sick: 'عندك حلال مريض: عالجه أول، أو اتعاقد مع البيطري.', round: 'شوطك اليوم ما خلص: تمشي بعد ما تخلص مراحله.' };
  async function runAway(target) {
    let r = null;
    try { r = await engine.away(target); } catch (err) { console.warn('phone:', err); }
    CAL.running = false; CAL.progress = null;
    if (!r || !r.ok) {
      ERR = r && r.error ? (AWAY_NO[r.error.params?.reason] || 'ما مشى التقويم، جرّب مرة ثانية.') : 'ما مشى التقويم، جرّب مرة ثانية.';
      if (live()) show('calCard');
      sr.textContent = ERR;
      return;
    }
    CAL.result = r.away;
    const end = r.away.stop.kind === 'target' || r.away.stop.kind === 'cancelled' ? 'calSum' : 'calStop';
    sr.textContent = end === 'calSum' ? `وصل ${ddAt(r.away.to)}` : `وقف التقويم: ${stopWords(r.away.stop).title}`.replace(/<[^>]+>/g, '');
    if (live()) show(end);
  }
  // a button that changes the game: sent to the engine, one at a time (its new view of the game redraws the screen);
  // a refusal is said on the screen, and what was not taken stays in the order
  let engine = null, busy = false, sureAt = 0, sureTimer = 0, orderAt = 0, orderKey = '';
  const keyOf = (t) => ['act', 's', 'd', 'p', 't', 'f', 'o', 'id', 'k'].map((k) => t.dataset[k] ?? '').join('|');
  async function act(t, at = performance.now()) {
    const kind = t.dataset.act, focused = root.activeElement === t ? keyOf(t) : null;
    // an order's second tap on the same button within DOUBLE_TAP of its answer (by the tap's own time, not when it is
    // handled) is dropped before anything is cleared: «سوم» tapped twice used two tries, and the dropped tap wiped the
    // seller's answer (the reviews). Other buttons, and the steppers, are not held back
    const LOCAL = kind === 'step' || kind === 'tab' || kind === 'bidStep' || kind === 'askStep' || kind === 'mzsel' || kind === 'calPick' || kind === 'calMonth';
    // «وقّف هنا»: at once, whatever is under way (the engine takes it outside its queue)
    if (kind === 'calStop') { if (engine && engine.stopAway) engine.stopAway().catch((err) => console.warn('phone:', err)); sr.textContent = 'يوقف'; return; }
    // what cannot be undone is asked twice: a sale, taking a listing down, withdrawing an entry, registering (it costs
    // the trucking), a treatment (illegal, and money)
    const twice = { quick: `quick:${HJ.camel}`, accept: `accept:${t.dataset.o}`, unlist: `unlist:${t.dataset.id}`, withdraw: `withdraw:${t.dataset.id}`, enter: `enter:${t.dataset.id}`, tamper: `tamper:${t.dataset.k}:${t.dataset.p}`,
      // the rush and التقويم (T15): money spent now, a contract, days that will not come back
      treatAll: 'treatAll', rushBuild: `rushBuild:${t.dataset.f}`, buildNow: `buildNow:${t.dataset.f}`, rushWater: 'rushWater', rushFeed: 'rushFeed', tankerNow: `tankerNow:${t.dataset.t}`, feedNow: 'feedNow', rushTruck: `rushTruck:${t.dataset.id}`, buyNow: `buyNow:${HJ.listing}`, vetSign: 'vetSign', vetCancel: 'vetCancel', calGo: 'calGo' }[kind];
    if (!LOCAL && (twice == null || HJ.sure === twice) && keyOf(t) === orderKey && at - orderAt < DOUBLE_TAP) return;
    // الحراج: a sale asked twice (the first tap readies it: HJ.sure); any other tap stands it down. [next]: the screen
    // to go to once the order is done (a camel bought or sold goes back to the market's list)
    // (the second tap comes at least DOUBLE_TAP after the first, else a double tap sold at once; a readied sale stands
    // down by itself after SURE_FOR, as the phone shrinks, and as the day turns: the review)
    const now = at;
    if (twice != null && HJ.sure === twice && now - sureAt < DOUBLE_TAP) return;
    ERR = null;
    const ready = twice != null && HJ.sure === twice;
    HJ.sure = twice != null && !ready ? twice : null;
    clearTimeout(sureTimer);
    if (HJ.sure) { sureAt = now; const key = HJ.sure; sureTimer = setTimeout(() => { if (HJ.sure === key) { HJ.sure = null; if (live()) redraw(); } }, SURE_FOR); }
    if (kind !== 'tab' && kind !== 'bidStep' && kind !== 'askStep' && kind !== 'mzsel') HJ.msg = null;      // (the seller's answer stays while the haggle is set again)
    let next = null;
    let ordered = false;
    const done = () => {
      // said to a screen reader when an order is answered, the same words again for a new answer (the region is emptied
      // as the order goes), and not at a stepper's press
      if (ordered) { sr.textContent = HJ.said || (HJ.msg ? `${HJ.msg.title}. ${HJ.msg.line}`.replace(/<[^>]+>/g, '') : ERR || ''); HJ.said = null; }
      if (!live()) return;
      if (next) { show(next); if (focused) focusIn(scr.querySelector('.back') || dev); return; }
      redraw();
      // the keyboard's place kept: the control is drawn again, so the same one takes the focus; one that is gone (the
      // order went, its button with it) leaves it on the screen's back button, in the phone
      if (focused) { const again = [...scr.querySelectorAll('[data-act]')].find((e) => keyOf(e) === focused && !e.disabled); focusIn(again || scr.querySelector('.back, [data-go], button') || dev); }
    };
    if (kind === 'step') {
      const k = t.dataset.s; ORD[k] = Math.max(0, (ORD[k] ?? 0) + Number(t.dataset.d)); done(); return;
    }
    if (kind === 'tab') { HJ.tab = t.dataset.p; done(); return; }
    if (kind === 'mzsel') { MZ.sel = t.dataset.id; done(); return; }
    if (kind === 'calPick') { CAL.day = Number(t.dataset.day); done(); return; }
    if (kind === 'calMonth') { CAL.month = Math.max(0, Math.min(12, (CAL.month ?? 0) + Number(t.dataset.d))); done(); return; }
    if (kind === 'bidStep') { const l = listingOf(HJ.listing); if (l) HJ.bid += Number(t.dataset.d) * stepOf(l.askPrice); done(); return; }
    if (kind === 'askStep') { const c = myCamel(HJ.camel); if (c) HJ.ask += Number(t.dataset.d) * stepOf(c.estimateHigh); done(); return; }
    if (twice != null && !ready) {      // (the first tap of a sale: it asks again, and says so)
      done();
      const b = [...scr.querySelectorAll('[data-act]')].find((x) => keyOf(x) === keyOf(t));
      if (b) sr.textContent = b.getAttribute('aria-label') || b.textContent;
      return;
    }
    if (!engine || !G || busy) return;
    busy = true; sr.textContent = '';
    const send = async (command) => { const r = await engine.dispatch(command); if (!r.ok) ERR = refusal(r, command); return r.ok; };
    try {
      if (kind === 'plan' && t.dataset.p !== G.farm.feedPlan) await send({ type: 'setFeedPlan', plan: t.dataset.p });
      else if (kind === 'share' && t.dataset.p !== G.farm.milk.calfShare) await send({ type: 'setCalfShare', share: t.dataset.p });
      else if (kind === 'build') await send({ type: 'buildFacility', facility: t.dataset.f });
      else if (kind === 'tanker') await send({ type: 'orderSupply', supply: 'water', units: 1, tanker: t.dataset.t });
      // the rush (T15)
      else if (kind === 'rushBuild') await send({ type: 'rushBuild', facility: t.dataset.f });
      else if (kind === 'buildNow') await send({ type: 'buildFacility', facility: t.dataset.f, now: true });
      else if (kind === 'rushWater') await send({ type: 'rushDelivery', kind: 'water' });
      else if (kind === 'rushFeed') await send({ type: 'rushDelivery', kind: 'feed' });
      else if (kind === 'tankerNow') await send({ type: 'orderSupply', supply: 'water', units: 1, tanker: t.dataset.t, now: true });
      else if (kind === 'feedNow') {
        const b = sup('barley'), a = sup('alfalfa');
        let nb = ORD.barley, na = ORD.alfalfa;
        if (!onAccount(nb * b.unitPrice + na * a.unitPrice)) { ERR = accountFullLine(); return; }
        if (nb > 0 && await send({ type: 'orderSupply', supply: 'barley', units: nb })) nb = 0;
        if (!ERR && na > 0 && await send({ type: 'orderSupply', supply: 'alfalfa', units: na })) na = 0;
        if (!ERR) await send({ type: 'rushDelivery', kind: 'feed' });
        ORD.barley = nb; ORD.alfalfa = na;
      }
      else if (kind === 'rushTruck') {
        const c = onTruck().find((x) => x.camel === t.dataset.id);
        if (await send({ type: 'rushTruck', camel: t.dataset.id, hour: gameHour() }) && c) HJ.msg = { good: true, title: `${esc(c.name)} ${c.male ? 'وصل' : 'وصلت'} عزبتك`, line: `بسواق ثاني، ${c.male ? 'وتقدر تبيعه' : 'وتقدر تبيعها'} من اليوم.` };
      }
      else if (kind === 'buyNow') await buy('now');
      else if (kind === 'standing') { const k = t.dataset.k; await send({ type: 'setStandingOrder', kind: k, on: !(RU().standing || []).includes(k) }); }
      else if (kind === 'standingBoth') { const both = ['water', 'feed'].every((k) => (RU().standing || []).includes(k)); for (const k of ['water', 'feed']) if (!ERR) await send({ type: 'setStandingOrder', kind: k, on: !both }); }
      else if (kind === 'treatAll') { const n = RU().sickCount; if (await send({ type: 'treatAll' })) HJ.said = `عالجت ${count(n, 'head')}`; }
      else if (kind === 'vetSign') await send({ type: 'signVetContract' });
      else if (kind === 'vetCancel') await send({ type: 'cancelVetContract' });
      else if (kind === 'treat') { const x = (RU().sick || []).find((y) => y.camel === t.dataset.id); if (await send({ type: 'treat', camel: t.dataset.id }) && x) HJ.said = `عالجت ${x.name}`; }
      else if (kind === 'calFill') {
        const F = calFill();
        if (t.dataset.s === 'water' && F.tanker) await send({ type: 'orderSupply', supply: 'water', units: 1, tanker: F.tanker.tanker });
        if (t.dataset.s === 'feed') {
          if (F.bags > 0) await send({ type: 'orderSupply', supply: 'barley', units: F.bags });
          if (!ERR && F.bales > 0) await send({ type: 'orderSupply', supply: 'alfalfa', units: F.bales });
        }
      }
      else if (kind === 'calGo') {
        // the jump: not held in this queue (its progress comes as it goes, and «وقّف هنا» must answer meanwhile)
        const target = t.dataset.again && CAL.result ? CAL.result.target : CAL.day;
        if (target != null && engine.away) { CAL.day = target; CAL.from = G.today; CAL.progress = null; CAL.running = true; next = 'calGoing'; runAway(target); }
      }
      else if (kind === 'buy' || kind === 'bid') await buy(kind);
      else if (kind === 'list' || kind === 'quick') await sell(kind);
      else if (kind === 'accept' || kind === 'decline') await answer(kind, t.dataset.o);
      else if (kind === 'unlist' && await send({ type: 'cancelListing', listing: t.dataset.id })) HJ.msg = { good: true, title: 'شلت الإعلان', line: 'الحلال باقي بعزبتك.' };
      else if (kind === 'withdraw') {
        const e = myEntries().find((x) => x.camel === t.dataset.id && x.round === t.dataset.o);
        if (e && await send({ type: 'withdrawEntry', festival: t.dataset.f, round: t.dataset.o, camel: t.dataset.id })) {
          const late = G.today > e.fest.closesOn, c = myCamel(e.camel) || e;
          HJ.msg = { good: true, title: `سحبت ${esc(e.name)} من ${roundTitle(e.kind, e.cat)}`, line: late ? `بعد الإغلاق ما ${her(c, 'ترجع تسجّلها', 'ترجع تسجّله')} بهالمهرجان.` : `تقدر ${her(c, 'تسجّلها', 'تسجّله')} مرة ثانية لين يقفل التسجيل.` };
        }
      } else if (kind === 'enter') {
        const x = MZ.page && MZ.page.register.find((y) => y.camel.id === t.dataset.id), r = x && pageRound(x.round);
        if (x && r) {
          const res = await engine.dispatch({ type: 'enterRound', festival: MZ.page.festival.id, round: r.id, camels: [x.camel.id, ...(x.group || []).map((k) => k.id)] });
          if (res.ok) {
            const fee = (res.events || []).find((e) => e.type === 'entered')?.fee || 0, c = x.camel;
            const group = (x.group || []).length > 0;
            HJ.msg = { good: true, title: `سجّلت ${esc(c.name)} ب${roundTitle(r.kind, r.cat)}`, line: `${her(c, 'شوطها', 'شوطه')} ${dd(r.day)}${fee ? `، وانخصم ${n0(fee)} ريال رسوم التأخير` : ''}، ${group ? 'ونقلهم' : her(c, 'ونقلها', 'ونقله')} ينخصم يوم الشوط.` };
            MZ.sel = null; next = 'mazayen';
          } else ERR = why(x.camel, res.error || { code: '' });
        }
      } else if (kind === 'tamper') {
        const o = dealerOffer();
        if (o) {
          const res = await engine.dispatch({ type: 'tamper', camel: o.c.id, kind: t.dataset.k, strength: Number(t.dataset.p) });
          if (res.ok) { next = 'chat'; HJ.said = `${TAMPER[t.dataset.k]} ${STRENGTH[Number(t.dataset.p) - 1]}: تم.`; }
          else {
            const code = res.error?.code, p = res.error?.params || {};
            ERR = code === 'insufficientFunds' ? `رصيدك ما يكفي: يبي ${n0(p.needed ?? 0)} ريال.` : code === 'alreadyTreated' ? her(o.c, 'فيها هالنوع من قبل.', 'فيه هالنوع من قبل.') : code === 'enteredInContest' ? her(o.c, 'هي بالمهرجان اليوم.', 'هو بالمهرجان اليوم.') : 'جرّب مرة ثانية.';
          }
        }
      }
      else if (kind === 'feed' || kind === 'week') {
        const b = sup('barley'), a = sup('alfalfa');
        let [nb, na] = kind === 'week' ? fitRoom(suggest(b, 1), suggest(a, 1), b, a, storeRoom(G.farm, b, a)) : [ORD.barley, ORD.alfalfa];
        // the whole order's total checked first (the engine takes the two feeds as two orders)
        if (!onAccount(nb * b.unitPrice + na * a.unitPrice)) { ERR = accountFullLine(); return; }
        if (nb > 0 && await send({ type: 'orderSupply', supply: 'barley', units: nb })) nb = 0;
        if (!ERR && na > 0 && await send({ type: 'orderSupply', supply: 'alfalfa', units: na })) na = 0;
        // what went through leaves the order; what did not stays for another try
        if (kind === 'feed') { ORD.barley = nb; ORD.alfalfa = na; }
      }
    } catch (err) {
      ERR = 'ما وصل الطلب، جرّب مرة ثانية.';
      console.warn('phone:', err);
    } finally {
      busy = false; orderAt = performance.now(); orderKey = keyOf(t);
      ordered = true; done();
    }
    // a purchase, at the asking price or by a haggle: the seller's answer is said on the camel's page (a lower price, or
    // no); one bought goes back to the list, with the word that it comes tomorrow
    async function buy(how) {
      const l = listingOf(HJ.listing);
      if (!l) return;
      const command = how === 'buy' ? { type: 'buyListing', listing: l.id } : how === 'now' ? { type: 'buyListing', listing: l.id, now: true, hour: gameHour() } : { type: 'bargain', listing: l.id, amount: HJ.bid };
      const r = await engine.dispatch(command), c = l.camel;
      const bought = r.ok && (r.events || []).find((e) => e.type === 'camelBought');
      if (bought) {
        HJ.msg = how === 'now'
          ? { good: true, title: `اشتريت ${esc(c.name)} بـ ${n0(bought.price)} ريال`, line: `${her(c, 'وصلت', 'وصل')} عزبتك الحين بسواق ثاني، والنقل والاستعجال انخصموا.` }
          : { good: true, title: `اشتريت ${esc(c.name)} بـ ${n0(bought.price)} ريال`, line: `${her(c, 'توصل', 'يوصل')} عزبتك بكرة، والنقل ${n0(l.transport)} ريال.` };
        HJ.bid = null; next = 'haraj';
      } else if (r.error?.code === 'bargainCountered' || r.error?.code === 'bargainRejected') {
        // the answer as the engine gave it: each uses a try; a counter lowers the price (the next try halves the gap
        // again, so it is not his last word), and what can be done next is said only if it can be
        const left = l.bargainsLeft - 1, ask = r.error.params?.ask ?? l.askPrice, afford = G.cash >= ask + l.transport;
        const more = `تسوم مرة ثانية (باقي لك ${count(left, 'bid')})`;
        const then = afford
          ? [her(c, `تقدر تشتريها بـ ${n0(ask)}`, `تقدر تشتريه بـ ${n0(ask)}`), left > 0 ? `أو ${more}` : 'وما عاد يقبل منك سوم']
          : [`رصيدك ما يكفي ${n0(ask + l.transport)} ريال مع النقل`, left > 0 ? `بس تقدر ${more}` : 'وما عاد يقبل منك سوم'];
        HJ.msg = r.error.code === 'bargainCountered'
          ? { title: `${esc(l.sellerName)} نزل لـ ${n0(ask)} ريال`, line: `${then.join('، ')}.` }
          : { title: `${esc(l.sellerName)} رفض سومك`, line: `ما يبيع بهالسعر. ${then.join('، ')}.` };
      } else if (!r.ok) ERR = refusal(r, command);
    }
    // one's own camel listed at one's price (to إعلاناتي, where the offers come) or sold to the broker now
    async function sell(how) {
      const c = myCamel(HJ.camel);
      if (!c) return;
      const command = how === 'list' ? { type: 'listForSale', camel: c.id, askPrice: HJ.ask } : { type: 'quickSale', camel: c.id };
      const r = await engine.dispatch(command);
      if (refusedSale(r, how === 'quick' ? 'الدلال' : null)) { HJ.ask = null; HJ.camel = null; next = 'haraj'; return; }
      if (!r.ok) { ERR = refusal(r, command); return; }
      const sold = (r.events || []).find((e) => e.type === 'camelSold');
      HJ.msg = how === 'list'
        ? { good: true, title: `عرضت ${esc(c.name)} بـ ${n0(HJ.ask)} ريال`, line: 'السومات تجيك هنا، وتقبل أو ترفض.' }
        : { good: true, title: `بعت ${esc(c.name)} للدلال بـ ${n0(sold ? sold.price : c.quickSale)} ريال`, line: 'دخلت الفلوس رصيدك.' };
      HJ.tab = how === 'list' ? 'mine' : 'market'; HJ.ask = null; HJ.camel = null; next = 'haraj';
    }
    // a sale the buyer or the broker refused, a treatment found in her (the owner's decision 12): said on the answer
    // card by the engine's facts (who looked, what he found, the fine or none), its findings told
    function refusedSale(r, who = null) {
      if (r.ok || r.error?.code !== 'saleRefused') return false;
      const ev = (r.events || []).find((e) => e.type === 'saleRefused');
      HJ.msg = ev ? foundWords(ev.name, ev.kinds, ev.fine, who || ev.buyer, myCamel(ev.camel)?.sex === 'male') : foundWords('', [], r.error.params?.fine ?? 0, null);
      return true;
    }
    // an offer on one's listing taken (the camel sold to that buyer) or turned down
    async function answer(how, offer) {
      const l = G.myListings.find((x) => x.offers.some((o) => o.id === offer)), o = l && l.offers.find((x) => x.id === offer);
      if (!o) return;
      if (how === 'decline') { await send({ type: 'declineOffer', offer }); return; }
      const fee = Math.round(o.amount * G.haraj.commission);
      const r = await engine.dispatch({ type: 'acceptOffer', offer });
      if (refusedSale(r)) return;
      if (!r.ok) { ERR = refusal(r, { type: 'acceptOffer', offer }); return; }
      HJ.msg = { good: true, title: `بعت ${esc(l.camel.name)} على ${esc(o.buyerName)} بـ ${n0(o.amount)} ريال`, line: `يوصلك ${n0(o.amount - fee)} بعد السعي.` };
    }
  }
  scr.addEventListener('keydown', (e) => {
    // a key held: its repeats are not more presses, and the browser's own click for each is stopped too (held, Enter
    // clicked once a repeat and Space once on release, and sold a readied camel: the reviews)
    if (e.repeat) { if ((e.key === 'Enter' || e.key === ' ') && e.target.closest('[data-act], [data-go]')) e.preventDefault(); return; }
    const a = (e.key === 'Enter' || e.key === ' ') && e.target.closest('[data-act]');
    if (a) { e.preventDefault(); act(a); return; }
    const t = (e.key === 'Enter' || e.key === ' ') && e.target.closest('[data-go]');
    if (!t) return;
    e.preventDefault(); pick(t); show(t.dataset.go);
    focusIn(scr.querySelector('.back, [data-go], button') || dev);      // (the screen is rebuilt: the focus stays in the phone, not dropped to the page)
  });
  scr.addEventListener('click', (e) => {
    if (e.detail !== 0 && (slid || stopTap)) { slid = stopTap = false; return; }      // (the finger slid the phone or stopped a fling: not a tap; a keyboard's or assistive technology's click is never one of those)
    stopTap = false;
    // a tap that comes just after the screen changed is the second of a double tap, landing on what the new screen put
    // under the finger: not taken (the review: a double tap on a market row bought the camel under it)
    if (e.detail !== 0 && performance.now() - shownAt < DOUBLE_TAP) return;
    const a = e.target.closest('[data-act]');
    if (a) { if (!a.disabled) act(a, e.timeStamp); return; }
    const t = e.target.closest('[data-go], .back');
    if (!t) return;
    pick(t); show(t.dataset.go || 'home');
    if (e.detail === 0) focusIn(scr.querySelector('.back, [data-go], button') || dev);      // (from the keyboard, Enter on the back button: the focus stays in the rebuilt screen)
  });
  addEventListener('resize', () => { if (st.state !== 'closed') { layout(); fitNumbers(); box.classList.toggle('turned', turned()); } });
  setInterval(() => { if (st.state !== 'closed') { const c = scr.querySelector('.clk'), t = clockText(); if (c && c.textContent !== t) c.textContent = t; } }, 15000);
  document.fonts?.addEventListener?.('loadingdone', () => fitNumbers());      // (a figure measured before its font came in: the phone's faces load only as it first shows, after fonts.ready has long resolved)
  // big, Tab goes round the phone's own buttons only (the game behind the dim is not reachable)
  addEventListener('keydown', (e) => {
    if (st.state !== 'big' || e.key !== 'Tab') return;
    const all = [...scr.querySelectorAll('[tabindex="0"], button:not([disabled])')], at = all.indexOf(root.activeElement);      // (a greyed button takes no focus: in the round, the keyboard stuck on it, the review)
    if (!all.length) return;
    e.preventDefault(); focusIn(all[(at + (e.shiftKey ? -1 : 1) + all.length + (at < 0 && e.shiftKey ? 1 : 0)) % all.length]);
  }, true);
  return {
    toggle: () => set(st.state === 'closed' ? 'small' : 'closed'), close: () => set('closed'), hit,
    enlarge: () => { if (st.state !== 'closed') { bigAt = performance.now(); set('big'); } }, shrink: () => { if (st.state === 'big') set('small'); },
    /** Opens the phone enlarged on an app (a place's card: الوايت from the tank, العلف from the feed). */
    openApp: (v) => { if (st.state === 'closed') set('small'); bigAt = performance.now(); set('big'); show(v); focusIn(scr.querySelector('.back') || dev); },
    setPlay: (on) => { st.play = on; if (st.state !== 'closed') layout(); },
    onChange: (f) => listeners.add(f),
    /** The engine's newest view of the game (engine.js), and the engine to send the player's orders to. */
    setGame: (snapshot) => {
      // (the word after an order, and a confirmation readied, are for their day: stood down, drawn again)
      let stood = false;
      if (G && snapshot && snapshot.today !== G.today) { stood = !!(HJ.msg || HJ.sure); HJ.msg = HJ.sure = null; }
      const was = G; G = snapshot;
      if (!live()) return;
      if (st.screen === 'bankMonth') {
        // a past month does not change: asked once; this month (or the one that has just ended) is asked again when
        // money moved, drawn when the answer comes, not before with its old figures; otherwise drawn again only as the
        // month turns (its «لين اليوم»)
        const mon = (g) => (g ? g.date.slice(0, 7) : '');
        if (G && (BK.month === mon(G) || BK.month === mon(was)) && G.sections.bank !== BK.rev) { loadMonth(); return; }
        if (was && mon(was) === mon(G)) return;
        redrawBank(); return;
      }
      if (st.screen === 'bank' && was && bankKey(was) === bankKey(G)) return;
      if (MZ_SCREENS.has(st.screen) && !stood && was && mzKey(was, st.screen) === mzKey(G, st.screen)) return;
      if (MZ_PAGE.has(st.screen) && G) { loadFest(); return; }      // (drawn when the page comes)
      if (MZ_SCREENS.has(st.screen)) { redrawKept(); return; }
      if (st.screen === 'bank') redrawBank(); else redraw();
    },      // (the word after an order, and a sale readied, are for their day)
    setEngine: (e) => { engine = e; },
    /** التقويم's jump under way (engine.js onAway: {done, total, day}, a few a second): the screen under way redrawn. */
    onAway: (m) => { CAL.progress = m; if (live() && st.screen === 'calGoing') redraw(); },
    get state() { return st.state; }, get big() { return st.state === 'big'; },
  };
}
