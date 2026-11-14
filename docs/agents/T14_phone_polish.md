# Task T14: the long press, the typography, and money without limit for testing

Read docs/agents/GUIDE.md first (in it, $SC is the work machine's scratch folder:
/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad), then /home/user/WEDG/CLAUDE.md.
Base: the session branch's head when you start (it must already hold the المزاين and المحادثات apps; if it does
not, stop and say so). Worker's worktree: /home/user/wt/t14, branch wt/t14. Reviewer's folder: $SC/t14_review.
Commit often: the machine was restarted once tonight (disk kept, processes lost).

## What the owner asked (docs/agents/owner_instructions_2026-11-14_night.md, word for word)

- «فيه مشكلة لمن اضغط ضغطه مطوله على الجوال يحدد لي الشاشة عدلها»: a long press on the phone selects the screen. Fix it.
- «والحرص كذالك على تنسيق الخطوط بالجوال وغيره»: care for the typography in the phone and elsewhere.
- «حط لي good mood اللفلوس فقط»: read as a god mode for money only, for his own testing.
- He wants to wake to work with no errors, nothing heavy on the phone, thought through.

A proxy agent answers the questions that are his tonight (docs/agents/PROXY.md): bring each with options, facts and
your recommendation first; the director puts it to the proxy.

## 1. The long press

He plays in the iPhone app (the page in a WKWebView, tool/proto_app; the in-game phone lives in a shadow root:
design/prototype3d/phone.js; the page: farm.html / index.html, play.js). In the game a long press on the small phone
enlarges it (his own design), and long presses also happen on the map, the pedals and buttons. On iOS a long press
on web content starts a text selection, the magnifier, the callout menu, or an image's save sheet. Reproduce what
can be reproduced here (Playwright's WebKit is not installed and must not be installed: use Chromium with touch
emulation for what it shows, and reason from WebKit's documented behaviour for the rest: say plainly what you could
not reproduce), then remove every way a press can select or call out anything on the game's surfaces: the page,
the canvas, the HUD buttons, the place cards, the phone's whole shadow tree, images and SVG icons (user-select and
-webkit-user-select, -webkit-touch-callout, -webkit-tap-highlight-color, draggable images, the contextmenu and
selectstart events, touch-action where a gesture is the game's), and in the app's own shell if it sets anything
(tool/proto_app's WKWebView settings: look). Keep what must stay: any real text field can still be typed in and
selected (find them; the phone has steppers, not fields, but check), screen readers still read the phone, the
long press that enlarges the phone still works, and nothing changes in how taps, drags and the car's controls feel
(the guards' timings untouched). A test in the page for each surface (a long touch leaves no selection:
getSelection is empty, no selectstart or contextmenu default goes through). Write for the owner, in Gulf Arabic,
the exact thing to try on his phone to confirm it, since only his phone can.

## 2. The typography, in the phone and elsewhere

An audit first, then fixes, both measured:
- every screen of every app in the phone (الوايت، العلف، الحليب، العزبة، الحراج، البنك، المزاين، المحادثات: play real games
  to reach their states; the earlier harnesses: $SC/haraj/run.js, $SC/t8/bank_run.cjs, $SC/t10/h/run.cjs,
  $SC/t3/page/money_run.cjs), the place cards on the map, the camel's card, the test meter, and any other text the
  game shows, at the owner's screen (956x440, the phone small and enlarged);
- what to look for, each counted: a number split from its word or its unit at a line's end («بـ 64» has been
  flagged in العلف three times tonight); a preposition or «و» left alone at a line's end; lines of one word
  (widows); text clipped, cut with an ellipsis, or overflowing; sizes under what is readable on his phone (state
  the smallest size in CSS pixels on each screen, small and enlarged, and the real millimetres on a 6.1 inch
  screen); more sizes and weights on a screen than its hierarchy needs (list each screen's type scale); line
  heights that crowd Arabic's marks; digits: one numeral system everywhere (the phone uses Latin digits: find any
  place that does not, and any face whose 1 reads as ١ at small sizes, as happened in a design picture tonight);
  the faces themselves (which load, from where, their weights and file sizes, what the fallback is on iOS if one
  fails to load, and whether a flash of the fallback shows at start); the minus sign and the thousands separator
  in money; mixed Arabic and Latin runs (direction marks around numbers, «−96,784 ريال» reading right to left
  correctly, parentheses and the middle dot in right-to-left text); alignment of numbers in lists (tabular
  figures so columns of prices line up); letter-spacing misapplied to Arabic (it breaks the joins); contrast of
  the small grey text against its ground (the ratio, per WCAG);
- a tool that repeats the audit (extend the layout audit in $SC/t4_review/h/audit.js; copy it into
  tool/ in the repository so it is not lost with the scratch folder) and a before/after table.
Fix what is plainly a fault (splits, widows, clipping, a wrong digit, a broken direction, misaligned figures,
letter-spacing on Arabic, a size under the floor you justify) across the phone and the other texts, keeping every
approved screen's layout and words. What changes the look he approved (another face, a different scale, bigger
text that moves a layout) is his: bring it as options with pictures for the proxy; build nothing of that kind
before an answer. No per-frame work added; fonts must not delay the first frame (measure the page's start).

## 3. Money without limit, for his testing only

A switch for him as the tester, off by default: with it on, the player's money never runs short. Nothing else
changes: prices, rushing costs, fines, the cheating risk, reputation, bans, the account, every rule still runs.
Study and propose before building (questions to the proxy with your recommendation first): where the switch lives
so a player cannot meet it by accident (the test meter the owner already uses, opened with #fps, is the likely
place: design/prototype3d/farm.html's meter; the instanced herd's task just added two lines there: read how);
what "without limit" is in the engine (a top-up to a large sum whenever cash falls under a floor, through a
command that exists only for testing; or a flag that makes every affordability check pass: say which keeps the
bank's ledger honest and the engine's invariants true: the ledger must still add up to the cash, so a top-up is a
ledger row of its own kind, named plainly in the bank, e.g. «فلوس تجربة»); how a game that used it is marked (a
flag in the save, shown where? so results from a tested game are never mistaken for an honest one); that it
cannot be reached from a normal game's screens; that turning it off leaves the game playable. Then build it with
tests (the switch on: an order that could not be afforded goes through and the ledger adds up; off: unchanged; the
save's flag; same seed on the VM and in JavaScript unaffected when off).

## Measure and report

The guide's checks, all of them. The audit's before/after table. The page's start time and the phone's rebuild
counts unchanged. Pictures of every screen that changed, before beside after. Every question for the proxy. What
could not be reproduced without his phone, and the steps for him to confirm in the morning, in Gulf Arabic.

## Left open on purpose

- Rushing and the calendar (task T15, another pair). Anything about hunting.
