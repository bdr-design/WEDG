// The in-game phone: a complete device, always upright (the owner's word of 11 Nov 2026). It opens small at the side
// of the screen, the game going on beside it: a look at the balance and at the red dots, nothing more (a tap on it
// does nothing; a drag over it turns the view as anywhere else). A long press on it enlarges it to a phone's true size
// in the middle of the screen, the scene dimmed behind: it is taller than the landscape screen, so it is slid up and
// down by the finger; a tap outside it makes it small again. Its screens are the approved design's (design/ui/
// phone.html: home, bank, market, auction, a talk with a buyer, weather and grazing), unchanged; what they show is
// example content until the game's engine feeds them. The other apps on the home screen are not built yet.
// Light: plain DOM in a shadow root (its styles and the page's cannot touch each other), no canvas, no blur; while it
// is enlarged the page stops drawing the 3D scene (farm.html).
const SMALL = 0.4, SMALL_ROOM = 105;      // the small phone's scale at most, and the height left clear above it (the top row of buttons), px
const LONG_PRESS = 450, SLOP = 10;        // ms held, and px moved at most, for a long press
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
  [data-go], .liveban, .back, button { cursor: pointer; }
  /* enlarged on a short screen the whole upright phone is drawn smaller than true size (0.59 at 956 x 440), so its own
     content is magnified back (--k, set once as it enlarges): what the phone shows sits at its true size on the screen,
     the smallest text 11 pt and every target at least 44 x 44 pt (Apple's minimums; the owner's proxy, 12 Nov: the
     buttons were 12 px tall and the text 6.5 px). Only an app's content scrolls; its top bar and the dock stay. */
  .phone[data-state="big"] .scr { width: calc(${W - 18}px / var(--k, 1)); height: calc(${H - 18}px / var(--k, 1)); zoom: var(--k, 1); border-radius: calc(42px / var(--k, 1)); }      /* (lengths, not percentages: a zoomed box's percentage size is not magnified, and it shrank into a corner) */
  .phone[data-state="big"] .scr .pill { top: calc(9px / var(--k, 1)); width: calc(92px / var(--k, 1)); height: calc(27px / var(--k, 1)); border-radius: calc(14px / var(--k, 1)); }
  .phone[data-state="big"] .body { overflow-y: auto; overscroll-behavior: contain; touch-action: pan-y; }
  .phone[data-state="big"] .nav { position: sticky; top: -1px; z-index: 3; min-height: 44px; background: var(--bg); box-shadow: 0 -3px 0 var(--bg); }      /* (held a pixel past the scroll's top edge and painted a little above itself: that edge falls between two of the screen's pixels, and a row of the scrolled content showed there) */
  .phone[data-state="big"] .dock { position: sticky; bottom: 0; z-index: 3; }
  .phone[data-state="big"] .back, .phone[data-state="big"] [data-go], .phone[data-state="big"] .liveban, .phone[data-state="big"] button { min-height: 44px; min-width: 44px; }
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
  .row .amt { grid-row: span 2; font: 600 14px/1 "Alexandria", sans-serif; direction: ltr; unicode-bidi: isolate; }
  .pos { color: var(--acc); }
  .ltr { direction: ltr; unicode-bidi: isolate; display: inline-block; }
  .sec { font-size: 12px; font-weight: 600; color: var(--ink2); padding-inline: 4px; margin-bottom: -6px; }
  .btn { height: 44px; border-radius: 14px; font-weight: 700; font-size: 14px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding-inline: 16px; }
  .btn.pri { background: var(--acc); color: #fff; }
  .btn.ghost { background: var(--acc-soft); color: var(--acc); }
  .badge { font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 7px; background: var(--acc-soft); color: var(--acc); display: inline-flex; align-items: center; gap: 3px; white-space: nowrap; }
  .badge svg { width: 11px; height: 11px; stroke-width: 2.6; }
  .badge.amber { background: #fdf0dc; color: var(--amber); }
  .badge.red { background: #fde6e4; color: var(--red); }
  /* ---------- home ---------- */
  .home { background: url(phone/wall_camel.png) 0% 104% / 124% auto no-repeat, linear-gradient(180deg, #cfe3f2 0%, #efe3cf 55%, #e2c9a2 100%); }
  .home .body { padding: 6px 18px 0; gap: 14px; }
  .widgets { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .wg { border-radius: 22px; padding: 12px 13px; background: rgba(255,255,255,.78); -webkit-backdrop-filter: none; height: 136px; display: flex; flex-direction: column; box-shadow: 0 4px 14px rgba(70,50,20,.10); }
  .wg small { font-size: 11.5px; font-weight: 600; color: var(--ink2); }
  .wg .big { font: 700 34px/1 "Alexandria", sans-serif; margin-top: 6px; }
  .wg .big2 { font: 700 21px/1.1 "Alexandria", sans-serif; margin-top: 8px; }
  .wg .ln { font-size: 11.5px; font-weight: 500; margin-top: auto; }
  .wg .rain { color: #1f6fd6; font-weight: 700; }
  .apps { display: grid; grid-template-columns: repeat(4, 1fr); row-gap: 14px; }
  .app { display: flex; flex-direction: column; align-items: center; gap: 5px; font-size: 11px; font-weight: 600; color: #2b2116; position: relative; }
  .app .ic { width: 56px; height: 56px; border-radius: 15px; display: grid; place-items: center; background: #fff; color: var(--acc); box-shadow: 0 3px 8px rgba(70,50,20,.14); }
  .app .ic svg { width: 27px; height: 27px; stroke-width: 1.8; }
  .app .bd { position: absolute; top: -5px; left: 2px; min-width: 20px; height: 20px; border-radius: 10px; background: var(--red); color: #fff; font: 700 11px/20px "Alexandria", sans-serif; text-align: center; padding: 0 5px; }
  .app .live { position: absolute; top: -5px; left: -2px; height: 18px; padding: 0 6px; border-radius: 9px; background: var(--red); color: #fff; font-size: 11px; font-weight: 700; line-height: 18px; }
  .dock { margin-top: auto; border-radius: 28px; padding: 10px 10px; background: rgba(255,255,255,.55); display: grid; grid-template-columns: repeat(4, 1fr); }
  .dock .app span:last-child { display: none; }
  /* ---------- bank ---------- */
  .balance { background: var(--card); border-radius: 20px; padding: 14px 16px; }
  .balance small { font-size: 12px; color: var(--ink2); font-weight: 500; }
  .balance .v { font: 700 32px/1.1 "Alexandria", sans-serif; margin-top: 4px; letter-spacing: -.01em; }
  .balance .v span { font-size: 15px; font-weight: 600; color: var(--ink2); margin-inline-start: 4px; }
  .quick { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 14px; }
  .q { display: flex; flex-direction: column; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 600; }
  .q .c { width: 46px; height: 46px; border-radius: 50%; display: grid; place-items: center; background: var(--acc-soft); color: var(--acc); }
  .q.pri .c { background: var(--acc); color: #fff; }
  .q .c svg { width: 20px; height: 20px; stroke-width: 2; }
  .due { background: var(--card); border-radius: 16px; padding: 10px 12px; display: grid; grid-template-columns: 36px 1fr auto; column-gap: 11px; align-items: center; }
  .due .lead { width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center; background: #fdf0dc; color: var(--amber); grid-row: span 2; }
  .due b { font-size: 13.5px; font-weight: 600; }
  .due small { font-size: 11.5px; color: var(--ink2); }
  .due .btn { height: 36px; border-radius: 11px; font-size: 13px; padding-inline: 14px; grid-row: span 2; }
  /* ---------- haraj ---------- */
  .seg { display: grid; grid-template-columns: 1fr 1fr 1fr; padding: 2px; border-radius: 10px; background: #e3e3e8; }
  .seg span { text-align: center; padding: 6px 0; border-radius: 8px; font-weight: 600; font-size: 12.5px; color: #3a3a3f; }
  .seg span.on { background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.12); color: var(--ink); }
  .liveban { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 16px; background: #fff; box-shadow: inset 0 0 0 1.5px #f3c2bd; }
  .liveban .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--red); box-shadow: 0 0 0 4px #fde6e4; flex: none; }
  .liveban b { font-size: 13.5px; }
  .liveban small { font-size: 11.5px; color: var(--ink2); display: block; }
  .liveban .go { margin-inline-start: auto; color: var(--red); font-weight: 700; font-size: 13px; }
  .lst { display: flex; flex-direction: column; gap: 8px; padding-bottom: 56px; }
  .it { display: grid; grid-template-columns: 70px 1fr; column-gap: 11px; padding: 8px; border-radius: 16px; background: var(--card); align-items: center; }
  .it .ph { width: 70px; height: 70px; border-radius: 12px; background: linear-gradient(180deg, #f3eadc, #e2cfae); overflow: hidden; grid-row: span 4; }
  .it .ph img { width: 100%; height: 100%; object-fit: contain; }
  .it b { font-size: 13.5px; font-weight: 700; }
  .it small { font-size: 11.5px; color: var(--ink2); }
  .it .pr { display: flex; align-items: center; }
  .it .bgs { display: flex; gap: 5px; margin-top: 3px; }
  .it .pr .price { font: 700 15px/1 "Alexandria", sans-serif; margin-inline-end: auto; }
  .it .pr .price.open { font: 700 13px/1 "IBM Plex Sans Arabic", sans-serif; color: var(--amber); }
  .sell { position: absolute; bottom: 26px; inset-inline: 14px; height: 46px; border-radius: 15px; background: var(--acc); color: #fff; font-weight: 700; font-size: 14.5px; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 6px 16px rgba(11,138,92,.35); z-index: 4; }
  .sell svg { width: 18px; height: 18px; stroke-width: 2.4; }
  /* ---------- auction ---------- */
  .lot { background: var(--card); border-radius: 20px; padding: 12px; display: flex; flex-direction: column; align-items: center; }
  .lot .ph { width: 100%; height: 150px; border-radius: 14px; background: linear-gradient(180deg, #f3eadc, #e2cfae); display: grid; place-items: center; overflow: hidden; }
  .lot .ph img { height: 150px; }
  .lot .hd { width: 100%; display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
  .lot .hd b { font-size: 15px; }
  .lot .cur { width: 100%; display: flex; align-items: flex-end; justify-content: space-between; margin-top: 8px; }
  .lot .cur .v { font: 700 30px/1 "Alexandria", sans-serif; color: var(--acc); }
  .lot .cur .v span { font-size: 13px; color: var(--ink2); margin-inline-start: 3px; font-weight: 600; }
  .timer { display: flex; align-items: center; gap: 6px; font: 700 18px/1 "Alexandria", sans-serif; color: var(--red); }
  .timer svg { width: 30px; height: 30px; }
  .bids { display: flex; gap: 8px; }
  .bids .btn { flex: 1; }
  .bids .btn.step { flex: 0 0 auto; background: #fff; color: var(--ink); box-shadow: inset 0 0 0 1px var(--line); }
  /* ---------- chat ---------- */
  .chathd { display: flex; align-items: center; gap: 9px; }
  .chathd .av { width: 34px; height: 34px; border-radius: 50%; background: #d9cbb4; display: grid; place-items: center; font: 700 15px/1 "Alexandria", sans-serif; color: #4a3720; }
  .chathd b { font-size: 14.5px; display: block; line-height: 1.2; }
  .chathd small { font-size: 11px; color: var(--ink2); }
  .strip { display: flex; align-items: center; gap: 10px; padding: 7px; border-radius: 14px; background: var(--card); }
  .strip .ph { width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(180deg, #f3eadc, #e2cfae); overflow: hidden; }
  .strip .ph img { width: 100%; height: 100%; object-fit: contain; }
  .strip b { font-size: 13px; display: block; }
  .strip small { font-size: 11px; color: var(--ink2); }
  .strip .lim { margin-inline-start: auto; text-align: end; font-size: 11px; color: var(--ink2); }
  .strip .lim span { display: block; font: 700 14px/1.1 "Alexandria", sans-serif; color: var(--ink); }
  .chat { flex: 1; display: flex; flex-direction: column; gap: 6px; justify-content: flex-end; min-height: 0; }
  .msg { max-width: 76%; padding: 7px 11px; border-radius: 17px; font-size: 13.5px; line-height: 1.4; }
  .msg.them { align-self: flex-start; background: #e9e9eb; border-end-start-radius: 5px; }
  .msg.me { align-self: flex-end; background: var(--acc); color: #fff; border-end-end-radius: 5px; }
  .ofr { align-self: flex-start; padding: 8px 12px; border-radius: 16px; background: #fff; box-shadow: inset 0 0 0 1.5px #f1d4a3; border-end-start-radius: 5px; }
  .ofr small { font-size: 11px; color: var(--amber); font-weight: 600; display: block; }
  .ofr span { font: 700 19px/1.2 "Alexandria", sans-serif; }
  .ofr span em { font-style: normal; font-size: 12px; color: var(--ink2); margin-inline-start: 3px; }
  .sum { background: var(--card); border-radius: 16px; padding: 10px 12px; display: grid; grid-template-columns: 1fr auto; row-gap: 3px; font-size: 12.5px; }
  .sum .n { font: 600 13px/1.3 "Alexandria", sans-serif; text-align: end; direction: ltr; unicode-bidi: isolate; }
  .sum .tot { font-weight: 700; font-size: 13.5px; }
  .sum .tot + .n { font-weight: 700; color: var(--acc); font-size: 14px; }
  .sum .chk { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
  .deal { display: grid; grid-template-columns: 1fr auto auto; gap: 8px; }
  .deal .x { width: 44px; padding: 0; background: #fff; color: var(--ink2); box-shadow: inset 0 0 0 1px var(--line); }
  /* ---------- weather ---------- */
  .wnow { background: linear-gradient(170deg, #5aa8ea, #2f7fcf); color: #fff; border-radius: 20px; padding: 14px 16px; display: grid; grid-template-columns: 1fr auto; }
  .wnow small { font-size: 12px; font-weight: 600; opacity: .9; }
  .wnow .t { font: 600 46px/1 "Alexandria", sans-serif; margin-top: 4px; }
  .wnow .d { font-size: 12.5px; font-weight: 500; margin-top: 4px; }
  .wnow svg { width: 54px; height: 54px; stroke: #fff; stroke-width: 1.5; }
  .days { background: var(--card); border-radius: 16px; display: grid; grid-template-columns: repeat(6, 1fr); padding: 10px 4px; text-align: center; }
  .days div { display: flex; flex-direction: column; align-items: center; gap: 3px; font-size: 11.5px; font-weight: 600; }
  .days svg { width: 22px; height: 22px; color: #e59c1a; }
  .days .r svg { color: #1f6fd6; }
  .days em { font-style: normal; font-size: 11px; color: #1f6fd6; font-weight: 700; }
  .days b { font: 600 12.5px/1 "Alexandria", sans-serif; }
  .graze .lead { background: #e6f3dc; color: #3d8a1f; }
  .green { display: inline-flex; gap: 2px; }
  .green i { width: 9px; height: 5px; border-radius: 2px; background: #dfe7d6; display: block; }
  .green i.on { background: #4f9e2a; }
  .row .move { font-size: 11px; font-weight: 600; color: var(--amber); }
  /* ---------- enlarged: the same screens re-flowed for the narrow width the magnified content has (186 pt across at
     956 x 440, 164 at 844 x 390), as an iPhone lays its screens out at its largest text sizes: nothing cut short and
     nothing dropped, the content, colours, icons and order kept, only the arrangement changed (the owner's proxy,
     12 Nov). The small phone is the approved design untouched. One attribute switches it, once, as the phone enlarges. */
  .phone[data-state="big"] .body { padding-inline: 10px; padding-top: 0; }      /* (none above the top bar that stays: scrolled content showed in it) */
  .phone[data-state="big"] .body > * { flex-shrink: 0; }      /* (the content scrolls; squeezed, the talk's messages ran over the deal under them) */
  .phone[data-state="big"] .nav { height: auto; }
  .phone[data-state="big"] .title { text-wrap: balance; }
  .phone[data-state="big"] .badge { white-space: normal; }
  .phone[data-state="big"] .row { grid-template-columns: 36px 1fr; padding-inline: 10px; }
  .phone[data-state="big"] .row + .row::before { inset-inline-start: 57px; }
  .phone[data-state="big"] .row .lead { grid-row: span 3; align-self: start; }
  .phone[data-state="big"] .row .amt, .phone[data-state="big"] .row .green { grid-row: auto; justify-self: start; margin-block: 3px 2px; }      /* (the amount under its title) */
  /* home: the widgets one above the other, the apps three to a row, the dock two by two */
  .hs { display: contents; }      /* (the home's widgets and apps: as before, small) */
  .phone[data-state="big"] .scr.home .body { overflow: hidden; }
  .phone[data-state="big"] .scr.home .hs { display: flex; flex-direction: column; gap: 14px; flex: 1 1 0; min-height: 0; overflow-y: auto; overscroll-behavior: contain; touch-action: pan-y; padding-top: 6px; }      /* (they scroll above the dock, never under it: under its round corners they showed) */
  .phone[data-state="big"] .widgets { grid-template-columns: 1fr; gap: 10px; }
  .phone[data-state="big"] .wg { height: auto; gap: 2px; }
  .phone[data-state="big"] .wg .big, .phone[data-state="big"] .wg .big2 { margin-block: 2px 4px; }
  .phone[data-state="big"] .apps { grid-template-columns: repeat(3, 1fr); column-gap: 3px; }
  .phone[data-state="big"] .app .ic { width: 46px; height: 46px; border-radius: 13px; }      /* (three of them and their gaps in 144 pt) */
  .phone[data-state="big"] .app .ic svg { width: 24px; height: 24px; }
  .phone[data-state="big"] .dock { grid-template-columns: 1fr 1fr; row-gap: 8px; padding: 8px; }
  /* bank */
  .phone[data-state="big"] .balance { padding: 12px; }
  .phone[data-state="big"] .balance .v { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 4px; }
  .phone[data-state="big"] .balance .v span { margin: 0; }
  .phone[data-state="big"] .quick { grid-template-columns: 1fr 1fr; row-gap: 12px; }
  .phone[data-state="big"] .due { grid-template-columns: 36px 1fr; row-gap: 2px; }
  .phone[data-state="big"] .due small { grid-column: 2; grid-row: 2; }
  .phone[data-state="big"] .due .btn { grid-column: 1 / -1; grid-row: 3; margin-top: 8px; height: 44px; }
  /* market */
  .phone[data-state="big"] .seg span { display: grid; place-items: center; min-height: 44px; padding-inline: 2px; line-height: 1.2; }
  .phone[data-state="big"] .liveban > span:nth-child(2) { flex: 1; min-width: 0; }
  .phone[data-state="big"] .liveban .go { flex: none; }
  .phone[data-state="big"] .it { grid-template-columns: 1fr; row-gap: 2px; }
  .phone[data-state="big"] .it .ph { width: 100%; height: 72px; grid-row: auto; margin-bottom: 6px; }      /* (the camel's picture above its words, as wide as the card) */
  .phone[data-state="big"] .it .bgs { flex-wrap: wrap; }
  .phone[data-state="big"] .sell { inset-inline: 10px; }
  /* auction */
  .phone[data-state="big"] .lot { padding: 10px; }
  .phone[data-state="big"] .lot .ph { height: auto; }
  .phone[data-state="big"] .lot .ph img { width: 100%; height: auto; }      /* (the whole camel: at a fixed height the picture was wider than the card) */
  .phone[data-state="big"] .lot .hd { flex-wrap: wrap; justify-content: flex-start; gap: 4px; }
  .phone[data-state="big"] .lot .hd b { flex-basis: 100%; }
  .phone[data-state="big"] .lot .cur { flex-wrap: wrap; align-items: center; row-gap: 6px; }
  .phone[data-state="big"] .lot .cur .v { display: inline-flex; flex-wrap: wrap; align-items: baseline; column-gap: 3px; }
  .phone[data-state="big"] .lot .cur .v span { margin: 0; }
  .phone[data-state="big"] .bids { flex-wrap: wrap; }
  .phone[data-state="big"] .bids .btn.step { flex: 1 1 0; padding-inline: 8px; }
  .phone[data-state="big"] .bids .btn.pri { flex: 1 1 100%; }
  /* the talk: its header stacked, as Messages does */
  .phone[data-state="big"] .chathd { flex: 1; min-width: 0; flex-direction: column; gap: 3px; padding-block: 2px; text-align: center; }
  .phone[data-state="big"] .strip { display: grid; grid-template-columns: 42px minmax(0, 1fr); column-gap: 10px; row-gap: 2px; }      /* (minmax: a plain 1fr column grew to a long figure and ran it past the strip) */
  .phone[data-state="big"] .strip .ph { grid-row: span 2; align-self: start; }
  .phone[data-state="big"] .strip .lim { margin: 0; text-align: start; }
  .phone[data-state="big"] .fit { display: inline-block; white-space: nowrap; }      /* (a big number: shrunk to its card when it is wider, see fitNumbers) */
  .phone.turned[data-state="big"] .body, .phone.turned[data-state="big"] .hs { touch-action: none; }      /* (the game turned: the phone scrolls them itself, see drag) */
  .phone[data-state="big"] .chat { flex: none; }
  .phone[data-state="big"] .deal { grid-template-columns: 1fr 44px; }
  .phone[data-state="big"] .deal .pri { grid-column: 1 / -1; }
  /* weather: the days a list, as the iPhone's Weather shows them (the rain's chance under its cloud) */
  .phone[data-state="big"] .wnow { padding: 12px; column-gap: 6px; }
  .phone[data-state="big"] .wnow > span { display: contents; }
  .phone[data-state="big"] .wnow small, .phone[data-state="big"] .wnow .t { grid-column: 1; }
  .phone[data-state="big"] .wnow .d { grid-column: 1 / -1; }
  .phone[data-state="big"] .wnow svg { grid-column: 2; grid-row: 1 / 3; align-self: center; }
  .phone[data-state="big"] .days { grid-template-columns: 1fr; padding: 0 12px; text-align: start; }
  .phone[data-state="big"] .days div { display: grid; grid-template-columns: 1fr 30px 34px; align-content: center; align-items: center; column-gap: 4px; min-height: 42px; padding-block: 4px; }
  .phone[data-state="big"] .days div + div { border-top: .5px solid var(--line); }
  .phone[data-state="big"] .days div > span { grid-column: 1; grid-row: 1 / 3; }
  .phone[data-state="big"] .days svg { grid-column: 2; grid-row: 1; justify-self: center; }
  .phone[data-state="big"] .days em { grid-column: 2; grid-row: 2; text-align: center; }
  .phone[data-state="big"] .days b { grid-column: 3; grid-row: 1 / 3; text-align: end; }
`;

const I = {
    bank: '<path d="M3.5 9.5 12 4l8.5 5.5"/><path d="M5.5 10v7.5M10 10v7.5M14 10v7.5M18.5 10v7.5"/><path d="M3.5 20h17"/>',
    tag: '<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>',
    gavel: '<path d="m13 4 7 7M10.5 6.5l7 7M14.5 5.5l-5 5M18.5 9.5l-5 5"/><path d="M11.5 12.5 4 20"/><path d="M3.5 20.5h8"/>',
    chat: '<path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4.1A8 8 0 1 1 20 12z"/>',
    cloud: '<path d="M7 18.5a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 18 10.5a4 4 0 0 1-.5 8z"/>',
    rain: '<path d="M7 15.5a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 18 7.5a4 4 0 0 1-.5 8z"/><path d="M8 18.5l-1 2M12 18.5l-1 2M16 18.5l-1 2"/>',
    sun: '<circle cx="12" cy="12" r="4.5"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    truck: '<path d="M2.5 6.5h11v9.5h-11z"/><path d="M13.5 9.5h4.2l3.3 3.6V16h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    vet: '<path d="M6 3.5v5a4 4 0 0 0 8 0v-5"/><path d="M10 12.5v2.5a4.5 4.5 0 0 0 9 0v-2"/><circle cx="19" cy="11" r="2"/>',
    water: '<path d="M12 3.5s6 6.4 6 10.6a6 6 0 0 1-12 0C6 9.9 12 3.5 12 3.5z"/>',
    feed: '<rect x="4" y="7" width="16" height="11" rx="2"/><path d="M9.5 7v11M14.5 7v11"/>',
    cup: '<path d="M7.5 4h9v5.5a4.5 4.5 0 0 1-9 0z"/><path d="M7.5 6H4.8c0 2.4 1.2 3.8 3.2 4.2M16.5 6h2.7c0 2.4-1.2 3.8-3.2 4.2"/><path d="M12 14v3.5M9.5 17.5h5v3h-5z"/>',
    people: '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19.5c.6-3.3 2.8-5 5.5-5s4.9 1.7 5.5 5"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.6c2.3.1 4 1.6 4.5 4.4"/>',
    up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
    down: '<path d="M12 5v14M6 13l6 6 6-6"/>',
    doc: '<path d="M6 3.5h8l4 4V20a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 20z"/><path d="M14 3.5V8h4M9 12h6M9 15.5h6"/>',
    back: '<path d="M9 6l6 6-6 6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    camel: '<path d="M3 8.5c0-1 .8-1.6 1.7-1.6h.9c.9 0 1.5.7 1.4 1.6l-.2 1.2c-.1.8.2 1.5.8 2 .5.4 1.1.4 1.6 0 .5-.5.9-1 1.1-1.6.9-1.7 2.5-2.8 4.4-2.7 1.1.1 2.1.8 2.7 1.8.5.8 1.1 1.3 2 1.6 1.1.4 1.9 1.5 1.9 2.8V15c0 .6-.4 1.2-.9 1.5V20"/><path d="M6.4 12.2V20M9.5 15.5V20M15 15.5V20"/>',
    leaf: '<path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z"/><path d="M5 19 13 11"/>',
  };
const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
const sbar = `<div class="sbar"><span>3:20</span><span class="r"><svg width="16" height="11" viewBox="0 0 18 12" fill="currentColor"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1" opacity=".35"/></svg><span class="bat"></span></span></div>`;
const nav = (end = '') => `<div class="nav"><button class="back">${svg('back')}رجوع</button>${end ? `<span class="end">${end}</span>` : ''}</div>`;
const ok = (t) => `<span class="badge">${svg('check')}${t}</span>`;
const APP_GO = { gavel: 'auction', bank: 'bank', tag: 'haraj', chat: 'chat', cloud: 'weather' };      // the apps that open a screen (the rest are not built yet)
const badgeSaid = (extra) => { const m = extra.match(/class="bd">(\d+)</); return /class="live"/.test(extra) ? '، مباشر' : m ? `، ${m[1]} جديدة` : ''; };
const app = (k, n, extra = '') => `<div class="app"${APP_GO[k] ? ` data-go="${APP_GO[k]}" role="button" tabindex="0" aria-label="${n}${badgeSaid(extra)}"` : ''}>${extra}<span class="ic">${svg(k)}</span><span>${n}</span></div>`;      // (named by the app and its badge: in the dock the name is hidden, and the badge alone was read)

const S = {
    home: () => `<div class="body"><div class="hs">
      <div class="widgets">
        <div class="wg"><small>أبانات</small><div class="big">27°</div><div class="ln">مشمس</div><div class="ln rain" style="margin-top:2px">مطر الخميس <span class="ltr">60%</span></div></div>
        <div class="wg"><small>الرصيد</small><div class="big2"><b class="fit">486,300</b></div><div class="ln ink2">ريال</div><div class="ln"><span class="pos ltr">+4,875</span> اليوم</div></div>
      </div>
      <div class="apps">
        ${app('gavel', 'المزاد', '<span class="live">مباشر</span>')}
        ${app('people', 'الرعاة')}
        ${app('truck', 'النقل')}
        ${app('vet', 'البيطري')}
        ${app('water', 'الوايت')}
        ${app('feed', 'العلف')}
        ${app('cup', 'المزاين')}
        ${app('doc', 'الأوراق')}
      </div></div>
      <div class="dock">
        ${app('bank', 'البنك')}
        ${app('tag', 'الحراج', '<span class="bd">2</span>')}
        ${app('chat', 'المحادثات', '<span class="bd">3</span>')}
        ${app('cloud', 'الطقس')}
      </div></div>`,
    bank: () => `<div class="body">${nav()}<div class="title">البنك</div>
      <div class="balance"><small>حساب عزبة الصفوة</small><div class="v"><b class="fit">486,300</b><span>ريال</span></div>
        <div class="quick">
          <div class="q pri"><span class="c">${svg('up')}</span>تحويل</div>
          <div class="q"><span class="c">${svg('down')}</span>طلب مبلغ</div>
          <div class="q"><span class="c">${svg('people')}</span>الرواتب</div>
          <div class="q"><span class="c">${svg('doc')}</span>الكشف</div>
        </div></div>
      <div class="due"><span class="lead">${svg('people')}</span><b>رواتب الرعاة</b><button class="btn pri">ادفع</button><small>3 رعاة · 3,900 ريال · بعد 5 أيام</small></div>
      <div class="sec">آخر العمليات</div>
      <div class="group">
        <div class="row"><span class="lead">${svg('camel')}</span><b>بيع حقة وضحاء</b><span class="amt pos">+4,875</span><small>5,000 ناقص السعي · اليوم</small></div>
        <div class="row"><span class="lead">${svg('water')}</span><b>وايت ماء</b><span class="amt">−350</span><small>أمس</small></div>
        <div class="row"><span class="lead">${svg('feed')}</span><b>علف: برسيم وشعير</b><span class="amt">−6,800</span><small>قبل 3 أيام</small></div>
        <div class="row"><span class="lead">${svg('vet')}</span><b>البيطري: علاج جرب</b><span class="amt">−1,200</span><small>قبل 4 أيام</small></div>
      </div></div>`,
    haraj: () => `<div class="body">${nav()}<div class="title">الحراج</div>
      <div class="seg"><span class="on">بسعر</span><span>على السوم</span><span>إعلاناتي</span></div>
      <div class="liveban" role="button" tabindex="0"><span class="dot"></span><span><b>مزاد بريدة · مباشر</b><small>12 ناقة · المعروضة الحين: لقية وضحاء</small></span><span class="go">ادخل</span></div>
      <div class="lst">
        <div class="it"><span class="ph"><img src="phone/thumb_shaqh.png" alt=""></span><b>جذعة شقحاء مقانية</b><small>حائل · 225 كم · بو مشعل</small><span class="pr"><span class="price num">33,500</span></span><span class="bgs">${ok('محصنة')}${ok('شهادة صحية')}</span></div>
        <div class="it"><span class="ph"><img src="phone/thumb_shaal.png" alt=""></span><b>ثنية شعلاء فردية</b><small>الخرج · 480 كم · بو ناصر</small><span class="pr"><span class="price num">85,000</span></span><span class="bgs">${ok('محصنة')}${ok('شهادة صحية')}</span></div>
        <div class="it"><span class="ph"><img src="phone/thumb_safra.png" alt=""></span><b>حقة صفراء</b><small>عنيزة · 113 كم · بو عبدالله</small><span class="pr"><span class="price num">4,500</span></span><span class="bgs">${ok('محصنة')}${ok('شهادة صحية')}</span></div>
      </div>
      <button class="sell">${svg('plus')}اعرض ناقة للبيع</button></div>`,
    auction: () => `<div class="body">${nav('<span class="badge red">مباشر</span>')}<div class="title">مزاد بريدة</div>
      <div class="lot"><span class="ph"><img src="phone/camel_side_wodh.png" alt=""></span>
        <div class="hd"><b>لقية وضحاء مقانية</b>${ok('محصنة')}${ok('شهادة صحية')}</div>
        <div class="cur"><span><small class="ink2" style="font-size:11.5px;display:block">آخر سوم · بو ناصر</small><span class="v"><b class="fit">21,500</b><span>ريال</span></span></span><span class="timer"><svg viewBox="0 0 30 30"><circle cx="15" cy="15" r="12" fill="none" stroke="#fde6e4" stroke-width="3"/><circle cx="15" cy="15" r="12" fill="none" stroke="#e5372b" stroke-width="3" stroke-linecap="round" stroke-dasharray="45 75.4" transform="rotate(-90 15 15) scale(1 -1) translate(0 -30)"/></svg>0:18</span></div></div>
      <div class="group">
        <div class="row"><span class="lead">${svg('gavel')}</span><b>بو ناصر</b><span class="amt">21,500</span><small>قبل 4 ثواني</small></div>
        <div class="row"><span class="lead">${svg('gavel')}</span><b>أنت</b><span class="amt pos">21,000</span><small>قبل 9 ثواني</small></div>
        <div class="row"><span class="lead">${svg('gavel')}</span><b>بو مشعل</b><span class="amt">20,000</span><small>قبل 15 ثانية</small></div>
      </div>
      <div class="bids"><button class="btn step num"><span class="ltr">+500</span></button><button class="btn step num"><span class="ltr">+1,000</span></button><button class="btn pri">زايد 22,000</button></div></div>`,
    chat: () => `<div class="body">
      <div class="nav"><button class="back" aria-label="رجوع">${svg('back')}</button><div class="chathd"><span class="av">ف</span><span><b>بو فهد</b><small>حائل · من الحراج</small></span></div></div>
      <div class="strip"><span class="ph"><img src="phone/thumb_majaheem.png" alt=""></span><span><b>الهيفاء</b><small>ثنية · مجاهيم · مقانية</small></span><span class="lim">حدّك<span class="fit">40,000</span></span></div>
      <div class="chat">
        <div class="msg them">السلام عليكم، الهيفاء للبيع؟</div>
        <div class="msg me">وعليكم السلام، إيه وعليها شهادة</div>
        <div class="ofr"><small>سوم بو فهد</small><span><b class="fit">30,000</b><em>ريال</em></span></div>
        <div class="msg me">ما تجي، حدها 40</div>
        <div class="ofr"><small>آخر سوم</small><span><b class="fit">34,000</b><em>ريال</em></span></div>
        <div class="msg them">أعطيك 34 ونقضي</div>
      </div>
      <div class="sum"><span>السعر</span><span class="n">34,000</span><span>السعي <span class="ltr">2.5%</span></span><span class="n">−850</span><span class="tot">يوصلك (ريال)</span><span class="n">33,150</span>
        <span class="chk">${ok('محصنة')}${ok('شهادة صحية')}${ok('نقل الشريحة والجواز')}<span class="badge amber">تصريح نقل لحائل</span></span></div>
      <div class="deal"><button class="btn pri">أبيعها بـ 34,000</button><button class="btn ghost">حدّي…</button><button class="btn x" aria-label="رفض">${svg('x')}</button></div></div>`,
    weather: () => `<div class="body">${nav()}<div class="title">الطقس والمرعى</div>
      <div class="wnow"><span><small>أبانات · الآن</small><div class="t">27°</div><div class="d">مشمس · رياح شمالية خفيفة</div></span>${svg('sun')}</div>
      <div class="days">
        <div><span>اليوم</span>${svg('sun')}<b>28°</b></div>
        <div><span>الثلاثاء</span>${svg('sun')}<b>27°</b></div>
        <div><span>الأربعاء</span>${svg('cloud')}<b>25°</b></div>
        <div class="r"><span>الخميس</span>${svg('rain')}<b>22°</b><em class="ltr">60%</em></div>
        <div class="r"><span>الجمعة</span>${svg('rain')}<b>21°</b><em class="ltr">40%</em></div>
        <div><span>السبت</span>${svg('cloud')}<b>23°</b></div>
      </div>
      <div class="sec">وين المرعى</div>
      <div class="group graze">
        <div class="row"><span class="lead">${svg('leaf')}</span><b>وادي الرمة بين الأبانين</b><span class="green"><i class="on"></i><i class="on"></i><i class="on"></i><i></i></span><small>سال قبل 3 أسابيع · 10 كم</small></div>
        <div class="row"><span class="lead">${svg('leaf')}</span><b>جنوب أبان الأسمر</b><span class="green"><i class="on"></i><i class="on"></i><i></i><i></i></span><small>عشب خفيف · 9 كم</small></div>
        <div class="row"><span class="lead">${svg('leaf')}</span><b>عقلة الصقور</b><span class="green"><i class="on"></i><i></i><i></i><i></i></span><small>مطر 8 ملم · 72 كم · <span class="move" style="white-space:nowrap">يبي نقلة</span></small></div>
      </div></div>`,
  };

export function createPhone({ host }) {
  const el = document.createElement('div'), root = el.attachShadow({ mode: 'open' });
  root.innerHTML = `<style>${CSS}</style><div class="phone" data-state="closed" lang="ar" role="dialog" aria-label="الجوال" aria-hidden="true"><div class="dim"></div><div class="dev" tabindex="-1"><div class="scr" inert></div></div></div>`;
  host.appendChild(el);
  const box = root.querySelector('.phone'), dev = root.querySelector('.dev'), scr = root.querySelector('.scr'), dim = root.querySelector('.dim');
  const st = { state: 'closed', play: false, screen: 'home', y: EDGE, s: SMALL };
  const listeners = new Set();
  let press = null, lastDown = 0, bigAt = 0, focusBack = null;
  const turned = () => document.body.classList.contains('rot');      // (farm.html: a phone held upright, the game turned a quarter)
  const endPress = () => { if (press) { clearTimeout(press.timer); press = null; } };
  function show(v) {
    st.screen = v; scr.classList.toggle('home', v === 'home');
    scr.innerHTML = `<span class="pill"></span>${sbar}${S[v]().replace(/(\d) (?=[\u0600-\u06FF])/g, '$1\u00a0')}<div class="hb"></div>`;      // (a number kept on the line of the word after it: enlarged, «3,900 | ريال» and «9 | كم» split)
    fitNumbers();
  }
  // enlarged, a big figure wider than its card is set smaller to fit it, as iOS fits a label to its width (a balance or a
  // bid in the millions ran out of its card at 844 x 390); read once as a screen shows or the phone enlarges, never per frame
  function fitNumbers() {
    for (const e of scr.querySelectorAll('.fit')) {
      e.style.fontSize = '';
      if (st.state !== 'big') continue;
      const card = e.closest('.balance, .lot, .lim, .wg, .chat');      // (the box that holds it: the chat's limit has its own column beside the camel's picture)
      let pad = 0;
      for (let q = e.parentElement; q; q = q.parentElement) { const c = getComputedStyle(q); pad += parseFloat(c.paddingLeft) + parseFloat(c.paddingRight); if (q === card) break; }
      const across = (q) => { const r = q.getBoundingClientRect(); return turned() ? r.height : r.width; };      // (along the phone's width on the screen: turned, the screen's height)
      const cw = parseFloat(getComputedStyle(card).width), room = across(card) * (cw - pad) / cw, ew = across(e);      // (computed lengths are unzoomed; boxes are as drawn)
      if (ew > room) e.style.fontSize = (parseFloat(getComputedStyle(e).fontSize) * room / ew * 0.97).toFixed(1) + 'px';
    }
  }
  // the small phone's size and place: by the screen's height (it leaves the top row of buttons clear), at the right
  // edge on the map, and left of the door's buttons and the pedals in play
  function layout() {
    const w = host.clientWidth, h = host.clientHeight, u = Math.min(w / 100, 9.5);
    st.s = Math.max(0.2, Math.min(SMALL, (h - SMALL_ROOM) / H));
    box.style.setProperty('--s', st.s.toFixed(3));
    box.style.setProperty('--r', `calc(${st.play ? Math.round(28 * u) : 56}px + max(0px, var(--edge-r, 12px) - 12px))`);
    box.style.setProperty('--b', 'calc(10px + max(0px, var(--edge-b, 12px) - 12px))');
    pan(st.y);
  }
  // enlarged, the whole phone in the screen, in the middle: as large as the screen's height allows, never larger than
  // true size (the owner: "half of it under the screen", its dock and buttons out of reach; it must sit balanced)
  const bigScale = () => Math.min(1, (host.clientHeight - 2 * EDGE) / H, (host.clientWidth - 2 * EDGE) / W);
  let sized = '';
  function pan(y) {
    const sb = st.state === 'big' ? bigScale() : 1, room = host.clientHeight - H * sb;
    const k = (st.state === 'big' ? Math.max(1, 1 / sb) : 1).toFixed(4);      // (the content's magnification: true size on the screen)
    if (sized !== sb.toFixed(4) + k) {      // (set only when they change, as it enlarges or the screen turns: --k sizes the screen's content, and a finger sliding the phone moves it by transform alone)
      sized = sb.toFixed(4) + k;
      box.style.setProperty('--sb', sb.toFixed(4)); box.style.setProperty('--k', k);
    }
    st.y = room >= 2 * EDGE - 0.5 ? room / 2 : Math.max(room - EDGE, Math.min(EDGE, y));
    box.style.setProperty('--y', st.y.toFixed(1) + 'px');
  }
  function set(state) {
    if (state === st.state) return;
    endPress();
    if (st.state === 'closed') show('home');
    const was = st.state;
    st.state = state; box.dataset.state = state;
    if (state === 'big') st.y = EDGE;
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
  // enlarged: a drag slides the phone up and down; a tap outside it makes it small again; a tap on it is the phone's
  let drag = null, slid = false;
  // The game turned (a phone held upright), the browser's own scrolling goes by the screen's axes and the enlarged phone's
  // content did not scroll at all. There the phone scrolls it itself, by the finger's travel along the phone (the page
  // hands pointer events over in the game's frame, where the phone stands upright, at true size), with a fling as it
  // lets go that slows as iOS's does (by 0.998 a millisecond). A finger slides the phone instead when it is taller than
  // the screen.
  let fling = 0;
  const fits = () => host.clientHeight - H * bigScale() >= 2 * EDGE - 0.5;
  dev.addEventListener('pointerdown', (e) => {
    if (st.state !== 'big') return;
    cancelAnimationFrame(fling);
    const sc = turned() && fits() ? e.target.closest('.hs, .body') : null;
    drag = { id: e.pointerId, y: e.clientY, y0: st.y, sc, top: sc ? sc.scrollTop : 0, t: e.timeStamp, last: e.clientY, v: 0 }; slid = false;
  });
  dev.addEventListener('pointermove', (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    if (!slid && Math.abs(e.clientY - drag.y) > SLOP) slid = true;
    if (!slid) return;
    if (drag.sc) {
      drag.sc.scrollTop = drag.top - (e.clientY - drag.y);
      const dt = e.timeStamp - drag.t; if (dt > 0) drag.v = 0.8 * ((drag.last - e.clientY) / dt) + 0.2 * drag.v;
      drag.t = e.timeStamp; drag.last = e.clientY;
    } else pan(drag.y0 + e.clientY - drag.y);
  });
  const endDrag = (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const { sc, v, t } = drag; drag = null;
    if (!sc || !slid || Math.abs(v) < 0.05 || e.timeStamp - t > 100) return;
    let speed = v, at = performance.now();
    const step = (now) => {
      const dt = now - at; at = now; const before = sc.scrollTop;
      sc.scrollTop += speed * dt; speed *= Math.pow(0.998, dt);
      if (Math.abs(speed) > 0.02 && sc.scrollTop !== before) fling = requestAnimationFrame(step);
    };
    fling = requestAnimationFrame(step);
  };
  dev.addEventListener('pointerup', endDrag); dev.addEventListener('pointercancel', endDrag); dev.addEventListener('pointerleave', endDrag);
  dim.addEventListener('mousedown', (e) => e.preventDefault());      // (the mouse events after a long press by touch land on the dim and took the focus out of the phone)
  dim.addEventListener('click', () => { if (lastDown > bigAt) set('small'); });      // (not the lift of the very finger whose long press enlarged it: its click lands on the dim, now on top)
  scr.addEventListener('keydown', (e) => {
    const t = (e.key === 'Enter' || e.key === ' ') && e.target.closest('[data-go], .liveban');
    if (!t) return;
    e.preventDefault(); show(t.dataset.go || 'auction');
    (scr.querySelector('.back, [data-go], button') || dev).focus({ preventScroll: true });      // (the screen is rebuilt: the focus stays in the phone, not dropped to the page)
  });
  scr.addEventListener('click', (e) => {
    if (slid) { slid = false; return; }                 // (the finger slid the phone: not a tap)
    const t = e.target.closest('[data-go], .back, .liveban');
    if (!t) return;
    show(t.dataset.go || (t.classList.contains('liveban') ? 'auction' : 'home'));
    if (e.detail === 0) (scr.querySelector('.back, [data-go], button') || dev).focus({ preventScroll: true });      // (from the keyboard, Enter on the back button: the focus stays in the rebuilt screen)
  });
  addEventListener('resize', () => { if (st.state !== 'closed') { layout(); fitNumbers(); box.classList.toggle('turned', turned()); } });
  document.fonts?.ready.then(() => fitNumbers());      // (a figure measured before its font came in)
  // big, Tab goes round the phone's own buttons only (the game behind the dim is not reachable)
  addEventListener('keydown', (e) => {
    if (st.state !== 'big' || e.key !== 'Tab') return;
    const all = [...scr.querySelectorAll('[tabindex="0"], button')], at = all.indexOf(root.activeElement);
    if (!all.length) return;
    e.preventDefault(); all[(at + (e.shiftKey ? -1 : 1) + all.length + (at < 0 && e.shiftKey ? 1 : 0)) % all.length].focus({ preventScroll: true });
  }, true);
  return {
    toggle: () => set(st.state === 'closed' ? 'small' : 'closed'), close: () => set('closed'), hit,
    enlarge: () => { if (st.state !== 'closed') { bigAt = performance.now(); set('big'); } }, shrink: () => { if (st.state === 'big') set('small'); },
    setPlay: (on) => { st.play = on; if (st.state !== 'closed') layout(); },
    onChange: (f) => listeners.add(f),
    get state() { return st.state; }, get big() { return st.state === 'big'; },
  };
}
