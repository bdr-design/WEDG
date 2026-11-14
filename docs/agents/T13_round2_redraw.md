# Task T13, round 2: redraw the hunting season for the owner's answers and the trapping business

For the same pair as round 1 (worker's worktree /home/user/wt/t13, branch wt/t13: rebase it onto the session
branch's head first; reviewer's folder $SC/t13_review). Read docs/agents/GUIDE.md again for the rules, and the
round-1 brief docs/agents/T13_hunting_design.md. Design only: nothing is built in the game. Commit often.

## What changed since the design was shown

1. **The owner's seven answers on the shown design** (docs/agents/hunting_owner_decisions.md, word for word): he
   drives and casts the falcon himself; falcons are a second business; a card opens in play only by his own tap;
   in a banned place or time the falcon button warns and does not cast; a falcons' room at the farm with its pin
   and card; a falcon is lost rarely and found with the tracker; the outing takes hours and the farm runs as on
   any day.
2. **The business is trapping (الطرح).** His words: «اصيده صيد وفيه طيور بس قيمتها عاليه جدًا», and on the night of
   13–14 Nov: «ايه مخيم وايام والطرح يعتمد على تجهيزاتك وحمامك وغيره والخيمه المتنقله وغيره»: a camp for days; the catch
   depends on his gear, his pigeons, the mobile tent and the rest.
3. **The research on trapping** (task T6; until it lands on the session branch read it in /home/user/wt/t6:
   docs/proposals/hunting.md section 9, docs/proposals/gdd_hunting_section.md 13.2 and 13.7,
   docs/research-realism.md): the season 1 Oct–30 Nov; the grounds; the gear and what each item really does; the
   trapping auction sells ONLY the peregrine of the year (فرخ شاهين بحري), from about 50,000 riyals; no saker and
   no قرناس is sold there; there is no "sell next autumn as a قرناس"; the odds are a range, not a figure; where
   the rules clash. hunting.md 9.6 lists every wrong place in the round-1 design by file and line
   (design/ui/phone_falcon.cjs, design/hunt/season.cjs, docs/proposals/hunting_season_design.md): fix every one.
4. **The proxy's answers** for the sleeping owner (docs/agents/proxy_decisions.md, batches 2 and 3: provisional,
   his to overturn; draw to them and mark on the README rows and in the design note that they are the proxy's):
   the odds range and gear moving the player along it; alone first, partners drawn as the next step; banned birds,
   the saker and the قرناس released by the game with a line saying why (the lines are in the file); the player's
   own falcon from three real routes each in its month; a trapped bird may be kept for hunting and the contests,
   resale not offered; the farm runs by its own rules during the camp and he can break camp and drive back at any
   time, with a card before leaving that says how long the feed and water last; trapping lawful only on a
   trapping ground, in its season, with a trapping permit (price and terms a marked game choice), the hunting
   rules holding everywhere else.
5. **The birds exist now** (task T11, /home/user/wt/t11: design/birds/*.jpg, assets_src/birds/*.glb; awaiting the
   owner's approval of their look): replace the stand-ins in the storyboard with the real models where a frame
   shows the falcon on the fist, the perch, the houbara or the stone-curlew, and say on the frame that the model
   awaits approval. The peregrine is not built: keep a stand-in for it, marked.
6. **The calendar and rushing are being designed by another pair** (task T15, /home/user/wt/t15: read its design
   note and pictures as they are; do not edit them): the card before a jump that says what the stretch needs, and
   how game days pass without the player. The camp's days must use the same card and the same way of passing
   time, not a second invention: say exactly how the camp's days pass for the player (what he does himself in a
   day at camp, what is passed over, when the game hands back to him: a bird in the net, the feed running low at
   the farm, an alert) and where it differs from the calendar's jump, with the reason.

## Redraw and add (the same manner as round 1: the phone's real pieces at 956x440; storyboard frames on real
screenshots of the game with what is drawn marked as drawn; every figure sourced by number or marked a game choice)

1. The year: add the trapping season, the three routes to a falcon each in its month, the two auctions told
   apart (the farm-bred auction in August; the trapping auction 1 Oct–30 Nov), against the camel year.
2. The phone, corrected: «نادي الصقور» (buying at the August auction; the trapping auction as the place the player
   SELLS his trapped bird: entering a bird, what the bidders see, the hammer price, what the club takes if the
   research says, the money in the bank; his falcons: each with its passport, age, species, how it came to him
   (bought, trapped), its results; a kept trapped bird; the contests) and «تصريح الصيد» (the hunting permit and the
   trapping permit, the seasons, where each is banned, the fines in words). Whether gear is bought in the phone
   or at a place on the map is a question: propose, with your recommendation first.
3. The trapping camp, new, as a storyboard: the trapping ground as an icon pin; the card before leaving (the gear
   he has, what is missing, how many days the feed and water last at the farm); the drive in the Land Cruiser; the
   camp pitched (the mobile tent, the vehicle, the gear laid out: what must be modelled, with a triangle estimate
   for each new thing); a day at camp as the player plays it (decision 1's spirit: he does the work himself:
   propose what he does with his hands: staking the pigeon, laying the net, watching with the binoculars, the
   pull; and what is worked out from his gear, the ground, the month and luck: bring two or three ways with your
   recommendation, as round 1 did for the outing); a falcon over the decoy; the bird in the net; the card that
   tells what it is (a sellable peregrine; a banned or refused bird released, with the proxy's lines); an empty
   day; breaking camp; the result at the end. The HUD exactly as the rules allow in every frame (icon buttons at
   the edges; no words outside a card he opened; the net button warning and not acting off the ground or out of
   season).
4. The falcons' room at the farm (غرفة الصقور: perches, المقيض): its pin, its card, what it costs to build (a
   game choice unless sourced), how many falcons it holds, what the player does there (the daily care, الدعو),
   drawn on a real screenshot of the farm.
5. The falcon outing, redrawn to decisions 1, 3, 4, 6 and 7 (he drives, searches, stops, unhoods and casts; the
   result from the falcon, the ground and luck; cards only by his tap; the warning button; the rare lost falcon
   and the tracker; a few hours of the game's day).
6. The money, as he can judge it: a season of trapping as a range (the reviewer's arithmetic in hunting.md 9:
   chance about 0.08 to 0.34; about −13,000 to +34,000 riyals; a dear bird at least one season in 80 to one in
   20; the camp's 20,000 marked invented), the gear's prices marked game choices, beside falconry's costs and the
   contests' prizes. No single "expected profit" figure anywhere.
7. The design note (docs/proposals/hunting_season_design.md) rewritten to match, with: what is the owner's own
   word, what is the proxy's provisional answer, what is our reading to be confirmed (above all: that his decision
   7 stays for the falcon outing and the camp of days is trapping only), the gaps told plainly (the trapping
   regulation's text not found; resale of a kept bird; what each item of gear changes is unmeasured), and the
   questions for him, recommendation first, numbered as in hunting.md.

## Deliver

The same files as round 1, updated (design/ui/phone_falcon.cjs / .jpg, design/hunt/*, the README rows still
"awaiting the owner's approval", the design note). Report with the pictures' paths, every view's Arabic words in
full as text, each figure with its source or its game-choice mark, the estimate of what each new scene costs to
draw, and the questions for the owner. The reviewer checks every view against the research, the owner's words,
the proxy's answers and the rules for screens, and every line in hunting.md 9.6 as fixed.
