# T4 round 3: the reviewer's findings on 34b3e63 (to send when T3's engine has settled)

Redraw on T3's final engine (rebase wt/t4 onto wt/t3's head at that time). Findings (file: design/ui/phone_mazayen.cjs):
1. The grand festival's row promises a prize the player cannot enter for (cjs:242, :246, f.topPrize = 5,000,000 is
   منقية الجزيرة's, a group round). Take the top first prize over the ENTERABLE rounds (1,000,000, الفحل وإنتاجه, real
   [42]; الفردي جل 800,000 a game choice), better named: «جايزة الأول لين 1,000,000 (الفحل وإنتاجه)». Same for every
   festival row (Hail's 190,000 is honest only by coincidence).
2. Risk words must be T3's bands (festivalRisk low/medium/high; the numeric festivalCatch is gone): low «قليل ما
   ينكشف», medium «ينكشف أحيان», high «ينكشف أغلب المرات»; optionally foundMostlyBy («أكثر ما تلقاه اللجنة الطبية»).
3. The debt warning (cjs:375) must follow decisions 8–10: «ما تقدر تشتري حلال ولا تبني لين تسدد. والعلف والماء
   والبيطري ينطلبون على الحساب لين حد، وبعده لازم تبيع من حلالك.»
4. Decision 11 (stacking) unsaid: a line under the strength note «وتقدر تجمع أكثر من نوع، وكل نوع له فحصه وغرامته،
   فالخطر يتجمع.»; a kind already on the camel shown on her strip.
5. Copied feature labels wrong (cjs:307): ears «الأذان» is the call to prayer (engine: «الأذن»); coat → the engine's
   «اللون والوبر» (dye: «يصفّي اللون»); back → «الغارب والظهر». Take each label from the engine's catalog through
   the snapshot; botox's features at T3's head are four, not two.
6. README: say the caught view is drawn from the engine's rules, not reached by this seed's game.
7. Minor: the kind rows look tappable but are not buttons (role/button for a screen reader); refusals probed by real
   enterRound dispatches (a side effect: the engine should give the reasons); reputation compared with a hard-coded 10.
Not the owner's (state, do not ask): results without scores; the late fee as a marked game choice.
The owner's: where cheating lives (the reviewer and worker both recommend the secret dealer's chat) and how the chat
is reached (no chat app in the phone yet).
For the phone's build (what the snapshot/page must give): ownerName on result rows; a festival(id) call in engine.js;
the player's camels that cannot enter with round + refusal code; camels on the truck in the herd list; the top prize
over enterable rounds with its kind; features' Arabic labels; reputation as a band; risk bands (already there).
