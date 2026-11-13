// The in-game phone: a complete device, always upright (the owner's word of 11 Nov 2026). It opens small at the side
// of the screen, the game going on beside it: a look at the balance and at the red dots, nothing more (a tap on it
// does nothing; a drag over it turns the view as anywhere else). A long press on it enlarges it, whole, in the middle
// of the screen, the scene dimmed behind: the same phone drawn larger, as large as the screen's height allows (the
// owner, 13 Nov); a tap outside it makes it small again. It shows the player's own game only, from the rules engine
// (setGame), and sends the player's orders to it (setEngine): the home screen (the date and its season, the balance,
// the herd), الوايت and العلف (approved 12 Nov: design/ui/phone_supplies.html), الحليب and العزبة (13 Nov:
// design/ui/phone_start_*.jpg), الحراج (13 Nov: design/ui/phone_haraj.jpg) and البنك (13 Nov: design/ui/phone_bank.jpg).
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
  .phone { font-family: "IBM Plex Sans Arabic", system-ui, sans-serif; font-size: 13px; line-height: 1.35; -webkit-font-smoothing: antialiased; font-variant-numeric: tabular-nums; direction: rtl; text-align: start; --bg: #f2f2f7; --card: #ffffff; --ink: #111114; --ink2: #6e6e73; --line: #e5e5ea; --acc: #0b8a5c; --acc-soft: #e3f4ec; --red: #e5372b; --amber: #c27a12; }
  b.fit { font: inherit; }
  .num { font-family: "Alexandria", "IBM Plex Sans Arabic", sans-serif; }
  svg.i { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; flex: none; }
  button { font: inherit; color: inherit; border: 0; background: none; cursor: pointer; }
  .scr { position: relative; width: 100%; height: 100%; border-radius: 42px; overflow: hidden; background: var(--bg); color: var(--ink); display: flex; flex-direction: column; }
  .scr .pill { position: absolute; top: 9px; left: 50%; translate: -50% 0; width: 92px; height: 27px; border-radius: 14px; background: #000; z-index: 5; }
  .sbar { height: 46px; flex: none; display: flex; align-items: center; justify-content: space-between; padding: 6px 26px 0; font: 600 14px/1 "Alexandria", sans-serif; }
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
  .title { font: 700 27px/1.1 "Alexandria", sans-serif; letter-spacing: -.01em; }
  .group { background: var(--card); border-radius: 16px; overflow: hidden; }
  .row { display: grid; grid-template-columns: 36px 1fr auto; column-gap: 11px; align-items: center; padding: 9px 12px; min-height: 52px; position: relative; }
  .row + .row::before { content: ""; position: absolute; top: 0; inset-inline: 59px 0; height: .5px; background: var(--line); }
  .row .lead { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; background: var(--acc-soft); color: var(--acc); grid-row: span 2; }
  .row .lead svg { width: 18px; height: 18px; }
  .row b { font-size: 13.5px; font-weight: 600; }
  .row small { font-size: 11.5px; color: var(--ink2); }
  .row .qty { grid-row: span 2; font: 600 14px/1 "Alexandria", "IBM Plex Sans Arabic", sans-serif; white-space: nowrap; }
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
  .wg .big2 { font: 700 21px/1.1 "Alexandria", sans-serif; margin-top: 8px; }
  .wg .big2.bad { color: var(--red); }      /* (a balance under zero: «عليك», what the player owes) */
  .wg .ln { font-size: 11.5px; font-weight: 500; margin-top: auto; }
  .apps { display: grid; grid-template-columns: repeat(4, 1fr); row-gap: 14px; }
  .app { display: flex; flex-direction: column; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; color: #2b2116; position: relative; }
  .app .ic { width: 56px; height: 56px; border-radius: 15px; display: grid; place-items: center; background: #fff; color: var(--acc); box-shadow: 0 3px 8px rgba(70,50,20,.14); }
  .app .ic svg { width: 27px; height: 27px; stroke-width: 1.8; }
  .app .bd { position: absolute; top: -5px; left: 2px; min-width: 20px; height: 20px; border-radius: 10px; background: var(--red); color: #fff; font: 700 11px/20px "Alexandria", sans-serif; text-align: center; padding: 0 5px; }
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
  .tank .v { font: 700 30px/1.1 "Alexandria", sans-serif; letter-spacing: -.01em; display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 4px; }
  .tank .v span { font-size: 14px; font-weight: 600; color: var(--ink2); }
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
  .stp .n b { font: 700 15px/1 "Alexandria", sans-serif; }
  .row.ord .lead { grid-column: 1; grid-row: 1 / span 2; }
  .row.ord b { grid-column: 2; grid-row: 1; }
  .row.ord small { grid-column: 2; grid-row: 2; }
  .row.ord .stp { grid-column: 3; grid-row: 1 / span 2; }
  .order { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 6px 10px; background: var(--card); border-radius: 16px; padding: 10px 12px; }
  .order > span > small { font-size: 11.5px; color: var(--ink2); display: block; }
  .order .t { font: 700 18px/1.1 "Alexandria", sans-serif; }
  .order .t small { font-size: 11.5px; color: var(--ink2); }
  .order .btn { padding-inline: 26px; }
  .note { font-size: 11.5px; color: var(--ink2); padding-inline: 4px; margin-top: -6px; }
  .way .row { grid-template-columns: 36px 1fr; }
  .way .lead { background: #e6eef8; color: #2f7fcf; }
  .cmp { display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: center; font-size: 11px; color: var(--ink2); margin-top: -4px; }
  .cmp b { display: block; font: 700 12px/1.3 "Alexandria", sans-serif; color: var(--ink); }
  .seg span { cursor: pointer; }
  .hs .datebar { align-self: center; font-size: 12px; font-weight: 700; color: #2b2116; background: rgba(255,255,255,.7); border-radius: 12px; padding: 4px 12px; text-align: center; }
  .datebar span { white-space: nowrap; }
  /* ---------- البنك (approved 13 Nov 2026: design/ui/phone_bank.jpg, its styles from design/ui/phone.html) ---------- */
  .balance { background: var(--card); border-radius: 20px; padding: 14px 16px; display: flex; flex-direction: column; gap: 3px; }
  .balance small { font-size: 12px; color: var(--ink2); font-weight: 500; }
  .balance .v { font: 700 30px/1.1 "Alexandria", sans-serif; margin-top: 2px; letter-spacing: -.01em; white-space: nowrap; }
  .balance .v span { font-size: 15px; font-weight: 600; color: var(--ink2); margin-inline-start: 4px; }
  .balance .ln { font-size: 12px; font-weight: 500; }
  .balance .v.bad { color: var(--red); }      /* (a balance under zero: what the player owes, «عليك») */
  .row .amt { grid-row: span 2; font: 600 14px/1 "Alexandria", sans-serif; direction: ltr; unicode-bidi: isolate; white-space: nowrap; }
  .row .amt.pos { color: var(--acc); }
  .row .lead.out { background: #f1f1f4; color: #55555b; }
  /* ---------- الحراج (approved 13 Nov 2026: design/ui/phone_haraj.jpg, its list styles from design/ui/phone.html) ---------- */
  .seg.two { grid-template-columns: 1fr 1fr; }
  .seg .dot { display: inline-block; min-width: 17px; height: 17px; border-radius: 9px; background: var(--red); color: #fff; font: 700 10.5px/17px "Alexandria", sans-serif; text-align: center; padding: 0 4px; margin-inline-start: 3px; font-style: normal; vertical-align: 1px; }
  .lst { display: flex; flex-direction: column; gap: 8px; padding-bottom: 56px; }
  .lst.flat { padding-bottom: 0; }
  .it { display: grid; grid-template-columns: 70px 1fr; column-gap: 11px; padding: 8px; border-radius: 16px; background: var(--card); align-items: center; }
  .it .ph { width: 70px; height: 70px; border-radius: 12px; background: linear-gradient(180deg, #f3eadc, #e2cfae); overflow: hidden; grid-row: span 4; }
  .it .ph img { width: 100%; height: 100%; object-fit: contain; }
  .it .ph img.homr { filter: sepia(.6) saturate(1.8) hue-rotate(-12deg) brightness(.82); }      /* (no red camel's photo yet: the sorrel's, tinted, as the approved design has it) */
  .it b { font-size: 13.5px; font-weight: 700; }
  .it small { font-size: 11.5px; color: var(--ink2); }
  .it .pr { display: flex; align-items: center; }
  .it .pr .price { font: 700 15px/1 "Alexandria", sans-serif; margin-inline-end: auto; }
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
    bank: '<path d="M3.5 9.5 12 4l8.5 5.5"/><path d="M5.5 10v7.5M10 10v7.5M14 10v7.5M18.5 10v7.5"/><path d="M3.5 20h17"/>',
  };
const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
// the status bar: the time is the player's own clock (kept to the minute while the phone is out)
const clockText = () => { const d = new Date(); return `${d.getHours() % 12 || 12}:${String(d.getMinutes()).padStart(2, '0')}`; };
const sbar = () => `<div class="sbar"><span class="clk">${clockText()}</span><span class="r"><svg width="16" height="11" viewBox="0 0 18 12" fill="currentColor"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1" opacity=".35"/></svg><span class="bat"></span></span></div>`;
// the top bar: رجوع goes home, or to the screen [to] (الحراج's pages, one inside another)
const nav = (end = '', to = '') => `<div class="nav"><button class="back"${to ? ` data-go="${to}"` : ''}>${svg('back')}رجوع</button>${end ? `<span class="end">${end}</span>` : ''}</div>`;
const APP_GO = { water: 'water', feed: 'feed', milk: 'milk', build: 'build', haraj: 'haraj', bank: 'bank' };      // the apps that open a screen
const badgeSaid = (extra, k) => { const m = extra.match(/class="bd">(\d+)</); return !m ? '' : k === 'haraj' ? `، ${count(Number(m[1]), 'bid')}` : k === 'water' ? '، الماء يخلص' : m[1] === '1' ? '، صنف يخلص' : '، الشعير والبرسيم يخلصون'; };
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
function onAccount(cost) {
  const A = G.farm.account, short = cost - Math.max(0, Math.min(G.cash, cost));
  if (short <= 0) return { short: 0, owed: A.owed };
  return A.owed + short <= A.limit ? { short, owed: A.owed + short } : null;
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
    : `ما تتغرم لأنك ما دريت، والحين صرت تدري. التجميل يروح مع الوقت، ولو ${hf('بعتها', 'بعته')} قبل وانكشف تتغرم.`;
  return { title, line: off ? `${off}، ${rest}` : rest };
}
// treatments found while the phone was shut (the daily look, the vet): told once on الحراج's answer card, the oldest
// not yet told first; those told with a refused sale are told already
const FOUND_SEEN = new Set();
const foundKey = (e) => `${e.day}|${e.camel}|${e.kind}`;
function unseenFound() {
  if (!G) return null;
  const sales = new Set(G.recentEvents.filter((e) => e.type === 'saleRefused').map((e) => `${e.day}|${e.camel}`));
  return G.recentEvents.find((e) => e.type === 'tamperingFound' && e.festival == null && !FOUND_SEEN.has(foundKey(e)) && !sales.has(`${e.day}|${e.camel}`)) || null;
}
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
    const acc = onAccount(t.price);
    if (t.room > 0 && acc && acc.short > 0) line = `${n0(t.price)} ريال · ${accountLine(acc.owed)}`;
    else if (t.room > 0 && !acc) line = `${n0(t.price)} ريال · ${accountFullLine()}`;
    const can = t.room > 0 && acc != null;
    return `<div class="row"><span class="lead">${svg('water')}</span><b>${name}</b><span class="act"><button class="btn ${can ? 'pri' : ''}" data-act="tanker" data-t="${t.tanker}" aria-label="اطلب ${name}" ${can ? '' : 'disabled'}>اطلب</button></span><small>${line}</small></div>`;
  };
  const bar = `<div class="bar${f.dryDays > 0 ? ' low' : ''}"><i style="width:${pct(have).toFixed(1)}%"></i>${coming ? `<i class="in" style="width:${(pct(have + coming) - pct(have)).toFixed(1)}%"></i>` : ''}</div>`;
  return `<div class="body">${nav()}<div class="title">الوايت</div>${errCard()}${warn}
    <div class="tank"><small>خزان العزبة · ${n0(f.tankL)} لتر</small><div class="v"><b class="fit">${n0(have)}</b><span>لتر</span></div>
      ${bar}
      <div class="ln">${lasts ? `يكفي ${days(lasts)} · ` : ''}يشربون ${n0(need)} لتر باليوم</div></div>
    <div class="sec">اطلب وايت</div>
    <div class="group">${f.tankers.map(row).join('')}</div>
    <div class="note">${coming ? `بالطريق: ${n0(coming)} لتر، يوصل بكرة${coming > f.tankL - have ? ' ويعبّي الخزان، والباقي يرجع' : ''}.` : 'بالطريق: ما فيه وايت.'}</div></div>`;
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
      ${alertCard('حساب التاجر وصل حده', `${accountFullLine()}${week ? ` يكفي لأسبوع: ${[wb ? count(wb, 'bag') : '', wa ? count(wa, 'bale') : ''].filter(Boolean).join(' و')}.` : ''}`)}
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
  const way = ordered ? `<div class="sec">بالطريق</div><div class="group way">${[[b, 'شعير', 'bag'], [a, 'برسيم', 'bale']].filter(([x]) => x.onTheWayAmount).map(([x, nm, k]) => `<div class="row"><span class="lead">${svg('truck')}</span><b>${nm} · ${count(x.onTheWay, k)}</b><small>${n0(x.onTheWayAmount)} كجم · ${n0(x.onTheWay * x.unitPrice)} ريال · يوصل بكرة</small></div>`).join('')}</div>` : '';
  let order;
  if (usedKg > room) order = `<div class="order"><span><small>${ST.the} ${ST.holds} ${n0(Math.max(0, room))} كجم بعد</small><span class="t num">${n0(total)} <small>ريال</small></span></span><button class="btn" disabled>اطلب</button></div>`;
  else if (total > 0) order = `<div class="order"><span><small>المجموع · يوصل بكرة ${ST.to}</small><span class="t num">${n0(total)} <small>ريال</small></span></span><button class="btn pri" data-act="feed">اطلب</button></div>${acc.short > 0 ? `<div class="note">${accountLine(acc.owed)}.</div>` : ''}`;
  else order = `<div class="note">${suggest(b) + suggest(a) > 0 || ordered ? 'زد الكمية ويطلع لك المجموع وزر الطلب.' : `${ST.the} ${ST.lasts} أكثر من 3 أسابيع.`}</div>`;
  return `<div class="body">${nav()}<div class="title">العلف</div>${errCard()}${warn}
    ${store}${ration}${way}${heading(ordered)}${rows(canUp)}${order}</div>`;
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
      out.push(`<div class="row"><span class="lead">${svg(d.icon)}</span><b>${nameOf(x.has + k)}</b><small>ينبني، يخلص ${soon <= 1 ? 'بكرة' : `بعد ${days(soon)}`}</small></div>`);
    }
    if (made < x.most) {
      const debt = x.cannot === 'inDebt', poor = debt || x.cannot === 'insufficientFunds', name = nameOf(made);
      const line = [d.what, `${n0(x.price)} ريال`, debt ? `عليك دين ${n0(-G.cash)} ريال` : poor ? 'رصيدك ما يكفي' : ''].filter(Boolean).join(' · ');
      out.push(`<div class="row"><span class="lead">${svg(d.icon)}</span><b>${name}</b><span class="act"><button class="btn ${poor ? '' : 'pri'}" data-act="build" data-f="${x.facility}" aria-label="ابنِ ${name}" ${poor ? 'disabled' : ''}>ابنه</button></span><small>${line}</small></div>`);
    } else if (!x.building) {
      out.push(`<div class="row"><span class="lead">${svg(d.icon)}</span><b>${x.facility === 'pen' ? 'الشبوك' : d.name}</b><small>${x.facility === 'pen' ? 'بنيت الشبوك كلها' : 'مبني'}</small></div>`);
    }
    return out.join('');
  };
  return `<div class="body">${nav()}<div class="title">العزبة</div>${errCard()}
    ${have}
    <div class="sec">ابنِ ووسّع</div>
    <div class="group">${f.facilities.map(row).join('')}</div>
    ${G.cash < 0 ? `<div class="note">${debtLine()}</div>` : ''}
    <div class="note">اللي تبنيه يخلص بعد 3 أيام ويطلع مكانه في العزبة.</div></div>`;
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
const photo = (c) => `<img src="phone/${PHOTO[c.category]}" alt=""${c.category === 'homr' ? ' class="homr"' : ''}>`;
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
  return `<div class="body">${nav()}<div class="title">الحراج</div>${tabs()}${msgCard()}${errCard()}${mine ? myListings() : marketList()}</div>${mine ? '' : `<button class="sell" data-go="pick">${svg('plus')}اعرض حلالك للبيع</button>`}`;
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
  const ins = m.lines.filter((l) => l.amount > 0), outs = m.lines.filter((l) => l.amount <= 0);
  // a month without milk says so
  const noMilk = m.lines.some((l) => l.kind === 'milk') ? '' : `<div class="row"><span class="lead out">${svg('milk')}</span><b>الحليب</b><span class="amt"></span><small>ما فيه حليب ${cur ? 'هالشهر' : `في ${monName(ym)}`}</small></div>`;
  return `<div class="body">${nav('', 'bank')}<div class="title">${monthName(ym)}</div>
    <div class="balance"><small>${cur ? 'الصافي لين اليوم' : 'الصافي'}</small><div class="v${net > 0 ? ' pos' : ''}"><bdi dir="ltr">${signed(net)}</bdi><span>ريال</span></div>
      <div class="ln ink2">${inOut(m.in, m.out)}</div></div>
    <div class="sec">الدخل</div><div class="group">${ins.map(line).join('')}${noMilk}</div>
    ${outs.length ? `<div class="sec">المصروف</div><div class="group">${outs.map(line).join('')}</div>` : ''}</div>`;
}

const herdWord = () => {
  if (!G) return '';
  const m = G.farm.milk.camels;
  return G.herd.total === 2 && m.length === 1 && m[0].calfName ? (m[0].calfSex === 'female' ? 'ناقة وحوارتها' : 'ناقة وحوارها') : unitWord(G.herd.total, 'head');
};

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
  };

export function createPhone({ host }) {
  const el = document.createElement('div'), root = el.attachShadow({ mode: 'open' });
  root.innerHTML = `<style>${CSS}</style><div class="phone" data-state="closed" lang="ar" role="dialog" aria-label="الجوال" aria-hidden="true"><div class="dim"></div><div class="dev" tabindex="-1"><div class="scr" inert></div></div><div class="sr" role="status" aria-live="polite"></div></div>`;
  host.appendChild(el);
  const box = root.querySelector('.phone'), dev = root.querySelector('.dev'), scr = root.querySelector('.scr'), dim = root.querySelector('.dim'), sr = root.querySelector('.sr');
  const st = { state: 'closed', play: false, screen: 'home', s: SMALL };
  const listeners = new Set();
  let press = null, lastDown = 0, bigAt = 0, focusBack = null, shownAt = 0;
  const turned = () => document.body.classList.contains('rot');      // (farm.html: a phone held upright, the game turned a quarter)
  const endPress = () => { if (press) { clearTimeout(press.timer); press = null; } };
  function show(v) {
    if (v !== st.screen) { ERR = null; shownAt = performance.now(); }
    if (v === 'feed' && st.screen !== 'feed') ORD.barley = ORD.alfalfa = null;      // (opened afresh: the order starts at three weeks' need)
    st.screen = v; scr.classList.toggle('home', v === 'home');
    scr.innerHTML = `<span class="pill"></span>${sbar()}${S[v]().replace(/(\d) (?=[\u0600-\u06FF])/g, '$1\u00a0')}<div class="hb"></div>`;      // (a number kept on the line of the word after it: «20,000 | ريال» split across lines otherwise)
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
      const f = unseenFound();
      if (f) {
        FOUND_SEEN.add(foundKey(f)); HJ.msg = foundWords(f.name, [f.kind], f.fine, null, myCamel(f.camel)?.sex === 'male');
        sr.textContent = `${HJ.msg.title}. ${HJ.msg.line}`.replace(/<[^>]+>/g, '');      // (said as the other answers are)
      }
    }
    if (to === 'bankMonth' && t.dataset.month) { BK.month = t.dataset.month; BK.data = null; loadMonth(); }
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
  function redraw() {
    const sc = scr.querySelector('.body'), top = sc ? sc.scrollTop : 0;
    show(st.screen);
    const again = scr.querySelector('.body');
    if (again) again.scrollTop = top;
  }
  // a button that changes the game: sent to the engine, one at a time (its new view of the game redraws the screen);
  // a refusal is said on the screen, and what was not taken stays in the order
  let engine = null, busy = false, sureAt = 0, sureTimer = 0, orderAt = 0, orderKey = '';
  const keyOf = (t) => ['act', 's', 'd', 'p', 't', 'f', 'o', 'id'].map((k) => t.dataset[k] ?? '').join('|');
  async function act(t, at = performance.now()) {
    const kind = t.dataset.act, focused = root.activeElement === t ? keyOf(t) : null;
    // an order's second tap on the same button within DOUBLE_TAP of its answer (by the tap's own time, not when it is
    // handled) is dropped before anything is cleared: «سوم» tapped twice used two tries, and the dropped tap wiped the
    // seller's answer (the reviews). Other buttons, and the steppers, are not held back
    const LOCAL = kind === 'step' || kind === 'tab' || kind === 'bidStep' || kind === 'askStep';
    const twice = { quick: `quick:${HJ.camel}`, accept: `accept:${t.dataset.o}`, unlist: `unlist:${t.dataset.id}` }[kind];
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
    if (kind !== 'tab' && kind !== 'bidStep' && kind !== 'askStep') HJ.msg = null;      // (the seller's answer stays while the haggle is set again)
    let next = null;
    let ordered = false;
    const done = () => {
      // said to a screen reader when an order is answered, the same words again for a new answer (the region is emptied
      // as the order goes), and not at a stepper's press
      if (ordered) sr.textContent = HJ.msg ? `${HJ.msg.title}. ${HJ.msg.line}`.replace(/<[^>]+>/g, '') : ERR || '';
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
    if (kind === 'bidStep') { const l = listingOf(HJ.listing); if (l) HJ.bid += Number(t.dataset.d) * stepOf(l.askPrice); done(); return; }
    if (kind === 'askStep') { const c = myCamel(HJ.camel); if (c) HJ.ask += Number(t.dataset.d) * stepOf(c.estimateHigh); done(); return; }
    if (twice != null && !ready) { done(); return; }      // (the first tap of a sale: it asks again)
    if (!engine || !G || busy) return;
    busy = true; sr.textContent = '';
    const send = async (command) => { const r = await engine.dispatch(command); if (!r.ok) ERR = refusal(r, command); return r.ok; };
    try {
      if (kind === 'plan' && t.dataset.p !== G.farm.feedPlan) await send({ type: 'setFeedPlan', plan: t.dataset.p });
      else if (kind === 'share' && t.dataset.p !== G.farm.milk.calfShare) await send({ type: 'setCalfShare', share: t.dataset.p });
      else if (kind === 'build') await send({ type: 'buildFacility', facility: t.dataset.f });
      else if (kind === 'tanker') await send({ type: 'orderSupply', supply: 'water', units: 1, tanker: t.dataset.t });
      else if (kind === 'buy' || kind === 'bid') await buy(kind);
      else if (kind === 'list' || kind === 'quick') await sell(kind);
      else if (kind === 'accept' || kind === 'decline') await answer(kind, t.dataset.o);
      else if (kind === 'unlist' && await send({ type: 'cancelListing', listing: t.dataset.id })) HJ.msg = { good: true, title: 'شلت الإعلان', line: 'الحلال باقي بعزبتك.' };
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
      const command = how === 'buy' ? { type: 'buyListing', listing: l.id } : { type: 'bargain', listing: l.id, amount: HJ.bid };
      const r = await engine.dispatch(command), c = l.camel;
      const bought = r.ok && (r.events || []).find((e) => e.type === 'camelBought');
      if (bought) {
        HJ.msg = { good: true, title: `اشتريت ${esc(c.name)} بـ ${n0(bought.price)} ريال`, line: `${her(c, 'توصل', 'يوصل')} عزبتك بكرة، والنقل ${n0(l.transport)} ريال.` };
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
      for (const e of r.events || []) if (e.type === 'tamperingFound') FOUND_SEEN.add(foundKey(e));
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
      if (G && snapshot && snapshot.today !== G.today) HJ.msg = HJ.sure = null;
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
      if (st.screen === 'bank') redrawBank(); else redraw();
    },      // (the word after an order, and a sale readied, are for their day)
    setEngine: (e) => { engine = e; },
    get state() { return st.state; }, get big() { return st.state === 'big'; },
  };
}
