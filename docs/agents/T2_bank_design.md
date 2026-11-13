# Task T2: the bank app's design on the engine's own data (a design to show the owner, not yet a build)

Read $SC/agents/GUIDE.md first. Base commit: a20b49d. Worker's worktree: /home/user/wt/t2, branch wt/t2.

## What is wanted

The in-game phone (design/prototype3d/phone.js) has الوايت, العلف, الحليب, العزبة and الحراج working on the rules engine.
The bank is next: where the player sees his money, what came in and what went out. The owner's rule: the design is
shown before it is adopted, and no example content: every figure on the screen is the game's own.

The approved phone design (design/ui/phone.html and its pictures in design/ui/, see design/ui/README.md) has a bank
screen drawn with example data. Draw it again as it would be in a real game: the phone's real CSS and pieces (phone.js),
at the owner's screen (956x440, the phone enlarged), with a real game's data from the engine, the way
design/ui/phone_haraj.cjs drew الحراج for approval (read it and design/ui/phone_haraj.jpg: that is the standard).

Screens to draw (propose better if the engine's data suggests it, and say why):
1. The bank's main screen: the balance, today's movement, this month in and out, and the months before.
2. A month opened: its rows by kind (the engine's LedgerCategory: milk, feed, water, purchases, sales, commission,
   transport, wages, building, prizes, vet...), each with its Arabic name, in and out apart, the net.
3. The states a new game really has: day one (nothing yet but the opening balance), a month with only milk and feed,
   a game some months in (play one forward on a fast clock or with the engine in Dart to get real rows).
Take the data from the engine as it is (packages/marah_domain: the ledger in model/player.dart, views.dart;
packages/marah_runtime: view_models.dart, presenter.dart, snapshot_json.dart). List exactly what the snapshot JSON
lacks for these screens (fields, their source in the domain, their cost at 10,000 head), but do not add them yet:
the build comes after the owner approves.

Rules that bind the design: Gulf Arabic as the phone already speaks (read phone.js's words), the counting rule (GDD
section 8), numbers kept with their word, nothing that the engine does not do (no loans, transfers or interest unless
the GDD has them: check docs/GDD.md and say what it says about the bank), no hidden values.

## Deliver

In the worktree: design/ui/phone_bank.cjs (draws the screens; a header saying how to run it), design/ui/phone_bank.jpg
(the screens side by side, as phone_haraj.jpg), a row in design/ui/README.md marked "awaiting the owner's approval".
In your report: the pictures' paths, each screen's words in Arabic as text (so they can be read without the picture),
what the snapshot lacks, the questions that are the owner's (with your recommendation first).
