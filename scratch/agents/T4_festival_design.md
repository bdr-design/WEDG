# Task T4: the المزاين app's design in the phone (a design to show the owner, not yet a build)

Read $SC/agents/GUIDE.md first. Base commit: a20b49d. Worker's worktree: /home/user/wt/t4, branch wt/t4.

## What is wanted

The festivals are the heart of the game (docs/GDD.md section 7 and 7.1, approved; docs/research-realism.md for the real
thing; docs/plan-gameplay.md G4: registration in the phone's المزاين app, the day's six stages and the results,
cheating as an action with its risk). The owner's rule: the design is shown before it is adopted. Draw the app's
screens for his approval, in the phone's real CSS and pieces (design/prototype3d/phone.js) at his screen (956x440,
the phone enlarged), the way design/ui/phone_haraj.cjs drew الحراج (read it and design/ui/phone_haraj.jpg: that is
the standard; the approved phone design language is design/ui/phone.html and design/ui/README.md).

Screens (propose better where the GDD's rules suggest it, and say why):
1. The festivals: what is coming and when (the engine's festivals: window.marahEngine.snapshot.festivals in the page,
   and packages/marah_domain's contest model), the one open for registration, the player's entries.
2. A festival opened: its rounds by colour family, age class and type (فردي, جمل...), the prizes, the closing time
   (72 hours before the round; a late fee after), who may enter.
3. Registering: choosing the camel for a round from the player's own, with why a camel cannot enter (wrong colour,
   wrong age class, owned too recently, sick, listed for sale, the one-entry rules), the fee, withdrawing.
4. The day: the six stages as the GDD names them, each able to remove an entry, told one by one as they pass
   (what the player sees while it happens, and after).
5. The results: the placings, the prize, what it did to the camel's worth and the owner's name.
6. Cheating (GDD 7.1: allowed, with its danger): where the player chooses a secret treatment, what it raises, the risk
   said honestly (the fine's cap, the ban, the disqualification), and the screen when caught.
Use a real game's camels and festivals for the data (a fixed game: newGame seed 4242; play forward for a festival
that is open). Where the engine does not yet have what the GDD says (a task beside this one is building the round
system and cheating), draw to the GDD and mark the figures that are placeholders on a list in your report, never on
the picture as if real.

Rules that bind the design: Gulf Arabic as the phone already speaks, the camel's sex in every word, the counting rule
(GDD section 8), numbers kept with their word, real Saudi festival terms from the research (say which term comes
from where), nothing floating over the game (this is inside the phone), no hidden values (never another owner's
treatment, never an exact value or a judge's hidden score).

## Deliver

In the worktree: design/ui/phone_mazayen.cjs (draws the screens; a header saying how to run it), design/ui/phone_mazayen.jpg
(the screens side by side), a row in design/ui/README.md marked "awaiting the owner's approval". In your report:
the pictures' paths, each screen's words in Arabic as text, the list of what the engine must provide for each screen,
the placeholders, and the questions that are the owner's (with your recommendation first).
