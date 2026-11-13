# Task T13: the design of the hunting season (موسم القنيص), to show the owner before anything is built

Read $SC/agents/GUIDE.md first (SC = /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad),
then /home/user/WEDG/CLAUDE.md. Base commit: the session branch's head when you start
(`git -C /home/user/WEDG rev-parse claude/vigilant-noether-nydua2`). Worker's worktree: /home/user/wt/t13, branch
wt/t13. Reviewer's folder: $SC/t13_review.

## What the owner asked (13 Nov 2026)

«ابي تدخل الحيوانات الان وتعرضها علي كذالك موسم القنيص»: he wants to see the hunting season. Nothing of it is built or
designed yet. His decisions so far, word for word, are at the top of docs/proposals/gdd_hunting_section.md (the
draft of GDD section 13) and docs/proposals/hunting.md; the real rules and their sources are in
docs/research-realism.md section 8. In short: falconry first (buy a falcon at the auction, its passport and the
hunting permit, train it, go out in the Land Cruiser in season), the falcon contests (الملواح ومزاين الصقور) built
with it, generic names for the apps and bodies («تصريح الصيد»، «نادي الصقور»، «مهرجان الصقور»), the air rifle after,
the Kalashnikov entering with its risk and never shown as lawful (a fine and seizure only), wolves and stray dogs
at the calves (a rare danger at night; killing a wolf never lowers the danger). The owner's rule: a design is shown
before it is adopted, and decisions that are his (layout, scope, a trade-off between realism and weight) are asked,
not assumed. The rules that bind every screen: the map is the centre of play; nothing permanent covers it; nothing
written floats over the game (icon buttons at the screen's edges and icon pins on places; words only in a card the
player opened); places are reached by tapping them on the map; landscape only; player-facing text is Gulf Arabic
with the counting rule (docs/GDD.md section 9); views never expose hidden values (a falcon's skill is never a
number: only its price and its results).

## Design (pictures and words for approval; build nothing in the game)

A season the player can read from start to end, as a set of design views in the manner of the approved ones
(design/ui/phone_haraj.cjs, phone_bank.cjs, phone_mazayen.cjs draw the phone's real pieces at the owner's screen,
956x440 with the phone enlarged; design/ui/README.md lists them). There is no hunting engine yet, so the figures
cannot be the game's own: every figure on a view must be a real one from the research (named by its source number
in the script) or marked a game choice, and the script's header must list which is which. Views to draw (propose
better if the real practice suggests it, and say why):

1. The calendar of the season as the player meets it, against the camel year the game already has (the breeding
   season, the festivals): the falcon auctions (August; 1 Oct–30 Nov), the permit, the training weeks (الدعو), the
   season 1 Sep–31 Jan with its autumn and winter parts, the falcon festival (the two date ranges the research
   holds, marked as disagreeing), so he sees what a year asks of him and where it collides with the camels.
2. The phone: «نادي الصقور» (the auction: a falcon's page with what a buyer really sees and what stays hidden;
   bidding; his falcons, each with its passport, age (فرخ / قرناس), species, its results; registering for the
   contests) and «تصريح الصيد» (the permit, the season's dates, where hunting is banned, the fines in words). Decide
   whether these are two apps or one, how they sit on the home screen beside the six there now, and show the home
   screen with them. The training (الدعو) as the short care the draft describes: what the player does, how often,
   what he sees change.
3. The outing (الطلعة) in the 3D world, as storyboard frames composed on real screenshots of the game (build the
   page and shoot the real map, the car and the player; draw the new things on top, marked as drawn): the hunting
   grounds and the licensed estate (المحازة) as icon pins on the map; driving out in the Land Cruiser; parking;
   the falcon on the fist; the icon button at the screen's edge that casts it off (only when the car is parked
   outside, as the draft says); the flight; the catch or the miss; the card that tells the result; what a banned
   place or a closed season does (the warning before, the fine after, in a card). Show each frame's HUD exactly as
   the rules allow, and say what the frame costs to draw in the real game (new models on screen, their triangles
   from the brief of task T11: $SC/agents/T11_hunt_birds.md; draws) as an estimate to be measured at build.
4. The contests: الملواح (the 400 m lure race: entering, the race as the player sees it, the time on the result
   card) and مزاين الصقور (the entry, the result: places and prizes, no scores), with the real classes and prizes.
5. What it costs and what it brings in a season, in a small table the owner can read: the falcon, its keep, the
   permit, the fuel or the trip, against the contests' prizes and a trained falcon's resale (real figures where
   the research has them; the rest marked game choices), so he can judge whether hunting stays a pastime that
   costs or becomes a second business, which is his decision.

Also bring, each with your recommendation first and the options: how the outing is played (how much the player
does himself: steering to the quarry, casting off at the right moment, or a result worked out from the falcon and
the ground); whether the falcon lives at the farm as a place on the map (a perch, a mews) with its own pin and
card; what happens to the camels while he is away hunting; the questions the draft still lists as open.

## Deliver

design/ui/phone_falcon.cjs (and others if it reads better split) with headers saying how to run them and where each
figure comes from; the pictures as JPEG in design/ui/ with README rows marked "awaiting the owner's approval"; the
storyboard frames in design/hunt/; a short design note docs/proposals/hunting_season_design.md (English) tying the
views to the draft GDD section and listing the owner's questions. In your report: the pictures' paths, every view's
Arabic words in full as text, the figures and their sources, the questions for the owner.

## Left open on purpose

- Building anything in phone.js, the engine or the 3D page.
- The air rifle, the Kalashnikov's outing, the wolves at the farm: name where they will attach, design them later.
- The birds' models themselves (task T11, another pair, in /home/user/wt/t11: its pictures will land in
  design/birds/; use a plain stand-in drawn by you in the storyboard until they exist, and mark it as a stand-in).
