# T16 reviewer: الحراج's four vet views (owner's items 10–13), baseline at b73bd06 and the phase-2 checks

Folder: $SC/t16_review. base/ = b73bd06 (session head) + .dart_tool. h/: vet_design_audit.cjs (the design script, dsf 1,
with the layout audit and t14's typography audit after each view, words to approved/words_<view>.txt), type_audit.js
+ type_audit.cjs (copied from /home/user/wt/t14/tool/page_checks @ fca63e8), weight.cjs (start, draws, rebuild
counts on الحراج's screens), sizes.dart, fonts_start.cjs (t14). vet.json = the design's save from
tool/proto_engine/bin/vet_design_save.dart (the same game as the approved jpg: verified, same camels and figures).

## 1. The approved views, word by word (approved/words_*.txt; the jpg at approved/approved.jpg)
check (a listing after one look, nothing found; male «مخلول صفر» فهّاد):
  رجوع | مخلول صفر | فهّاد | الرياض · عند أبو ماجد | يقدّرونه 4,200–5,100 ريال | البيطري فحصه مرة | [افحص بكرة] |
  ما لقى شي · الفحص بـ 500 ريال، وكل يوم فحص جديد | اللي تدفعه | سعره 5,700 ريال | نقله لعزبتك 1,248 ريال |
  [اشتره بـ 5,700] | البيطري يدوّر على التجميل قبل لا تشتري، بس ممكن يفوته شي. واللي يلقاه ما يدري عنه غيرك.
found (the look found a treatment; male «حق مجاهيم» شامخ):
  البيطري لقى فيه قص الذيل | محد يدري غيرك. لو اشتريته وسجلته بمزاين وانكشف، الغرامة والحرمان عليك. والتجميل يروح مع
  الوقت. | اللي تدفعه | سعره 14,500 ريال | نقله لعزبتك 1,366 ريال | [اشتره بـ 14,500 وأنت تدري] |
  تقدر تتركه، أو تشتريه وتنتظر لين يروح التجميل.
declare (owner told after buying unknowing; female «مفرودة وضحاء» غزيّل):
  بيع غزيّل | مفرودة وضحاء | يقدّرونها 57,500–70,000 ريال | فيها تجميل، وأنت ما دريت لين انقال لك |
  اعرضها معلن إن فيها تجميل | سعرك [−] 50,500 ريال [+] | المشتري يدري، وما يفحصون ولا تتغرم | [اعرضها معلن بـ 50,500] |
  أو بيعها معلن للدلال الحين | [بيعها معلن الحين | 50,500 ريال] |
  سعرها الطبيعي بدون زيادة التجميل، فهو تحت تقديرهم. أو انتظرها لين يروح التجميل.
own (his own treatment; نورة «سديسة وضحاء»):
  بيع نورة | سديسة وضحاء | يقدّرونها 15,000–18,500 ريال | فيها صبغ خفيف، أنت اللي جمّلتها | ما تقدر تعلنها |
  أنت اللي جمّلتها، والتجميل ممنوع برا المهرجان بعد، وإعلانه اعتراف. انتظرها لين يروح الصبغ، أو بيعها ساكت ويفحصونها قبل ما يدفعون.
Sex forms in the template: every verb/pronoun by her() (both sexes must be checked: check/found are male, declare/own female).

The approved design's OWN typography faults (t14 audit at 956x440, dsf 1) — the build must NOT copy them (the owner:
«التدقيق في التنسيق»):
  check: number/unit split «الفحص بـ 500 | ريال،»; declare: «أو» alone at a line's end («… تحت تقديرهم. أو | انتظرها»);
  every view: letter-spacing −0.22px on the Arabic .title (the phone's existing CSS; T14's matter, note only);
  the clock's figures proportional; contrast under 4.5:1 on رجوع (3.92), the ghost/sure buttons (3.83) and the primary
  button (4.37) at their drawn size; smallest text 11.5 css px (6.78 px drawn). Layout audit: nothing clipped,
  outside or scrolling (all four fit: 628/628).

## 2. Every state each screen can be in (from the engine's rules at b73bd06)
Engine facts read (handlers.dart _checkListing, cannotDeclare, quickSalePrice; Balance):
 - a look costs Balance.vetCheckFee 500, cash only: cash < 500 (debt included) -> insufficientFunds {needed: 500}
   (NOT inDebt, NOT on the merchant's account: decision 10's account covers a sick camel's treatment, not this look);
 - each look finds each active treatment with 0.6 (vetCheckChance); its rng is keyed by the day, so two looks the same
   day give the same answer and the second still charges 500 -> the phone must not offer a same-day second look
   (the design's «افحص بكرة»); `checks` counts looks per player (shown «فحصه مرة / مرتين / N مرات»);
 - a found treatment joins knownBy: the listing then carries `treatments` in the snapshot for this player only;
 - own listing -> ownListing; listing gone (sold/expired while open) -> notFound;
 - the declared sale: cannotDeclare: ownTreatment (he had it done) / nothingToDeclare (none he knows of) / null;
   to the broker at quickSalePrice(declared: true) = natural value (no treatment share); a declared listing's offers
   must never exceed her natural worth (the proxy's batch 1 item 6; the worker's test).
States to drive in the page (each shot + layout/type audit + words):
  check: never looked (the button with its price) / one look nothing / two-and-more looks on later days («مرتين»,
  «3 مرات») / a same-day second tap (refused or not offered: no 500 charged twice) / cash 499 / in debt / a male and a
  female listing / the listing gone while open (sold to a rival, or expired at the day's turn) / own listing;
  found: found on the 1st look / found on a later look / more than one kind found («و» join) / bought knowing (the
  purchase's words) / the found camel then in his herd (sell page: no declared option: item 12);
  declare: as a listing (stepper; price above natural allowed? its offers capped at natural worth) / to the broker now
  (two-tap: a sale) / the finding told once on الحراج's card (untold list) and never again / after the treatment
  wears off (no declared option, nothing to declare);
  own: ownTreatment words; with two kinds on her; the ordinary sale still offered with its examination risk words.

BASELINE FINDING (engine): the owner's item 12 (a buyer who knew before buying may NOT sell declared) is NOT in the
engine at b73bd06: knew_base.txt — a buyer whose vet found the treatment before buying gets cannotDeclare == null and
QuickSale(declared) Ok. cannotDeclare only asks knownBy. The build must add the rule (e.g. the knowledge's moment: told
after the purchase vs known at it; or a flag set at BuyListing when knownBy already held him) with a test, a save
migration if it is state, and the phone must show the right page («تتركها، أو تنتظر لين يروح التجميل، أو تبيعها ساكت»).

## 3. FORMATTING checks (phase 2, every built state above, and every other phone screen once: shared code)
 - layout audit (t4_review/h/audit.js): clipped, ellipsis, outside, split, scroll;
 - t14 typography audit (type_audit.js): split, prepNum («بـ 500 | ريال»), prepEnd (a preposition or «و»/«أو» at a
   line's end), widow (one word alone on the last line), digits (Arabic-Indic), noSep, minus/hyphenMinus (U+2212 and
   its side), parens, dot order, letter-spacing on Arabic, proportional figures where tabular wanted (prices in
   columns: the «اللي تدفعه» table, the stepper), contrast, smallest size — against the approved design's own counts
   above: none worse, the two faults above gone;
 - words lint (t4_review/h/words.py): Gulf, counting nouns 4 forms («مرة/مرتين/مرات»), numbers with their words,
   no hidden value (no chance in numbers, no «60%»); sex forms by the camel on every line (both sexes driven);
 - word-for-word diff against approved/words_*.txt (names and figures of the game aside); every difference listed;
 - the owner's item 15 (figures in IBM Plex Sans Arabic) and 14 (sizes as they are) if they land in the same build:
   the vet views must follow them, no new size.

## 4. WEIGHT baselines to hold (base, machine load 25–33: times noisy, compare under like load)
 - page start: engine's first snapshot 27–33 s under this load (re-measure base and build back to back);
 - draws a frame at start, phone closed: 96 draws, ~136k tris, shadow 20 draws / ~19k tris; enlarged phone: 0 (the
   3D pauses under it) — must stay;
 - fast clock rebuilds (new game, 6 s each): الحراج list 10/10 snapshots, a listing 9/9, the pick list 10/10, a sell
   page 10/10 (one per snapshot: the build must not add more; ideally fewer on a page whose figures did not change);
 - snapshot (sizes_base.txt): day1 33,243 B; 1 y 35,908; rich 10 y 64,017; 10k 58,692 B; the listing's new fields
   (checked, treatments, declaredSale) must not grow it beyond a few dozen bytes per listing;
 - 10k budgets pass (budget_base.txt; times noisy under load);
 - no new setInterval / setTimeout loops / requestAnimationFrame in phone.js or engine.js (diff grep).

## 5. Hidden values (look_base.txt)
 - before a look: the listing carries no `treatments`; a failed look adds nothing but `checked`; a found look adds
   the kind(s) for this player only (another player's view, a rival, the market list for others: nothing);
 - recentEvents' listingChecked carries found:[] or the kinds: no strength, no chance, no "missed";
 - the price/estimate of a treated listing must not differ from a clean twin's in a way that tells (T3's
   tamperPriceShare already: estimate equal to the cards; check the new screens add no field that tells);
 - the declared price = natural value: the treatment's share never shown as a number;
 - snapshot at each moment: before / after a look / after buying knowing / after the daily look's finding / after a
   declared listing / after its sale: diff the whole JSON like hidden_hours.dart.

## 6. Mutations (phone path and the engine rules it leans on)
 E1 vetCheckFee read from a phone constant instead of the engine (change Balance to 600: the screen must follow);
 E2 vetCheckChance shown or used in the phone; E3 cannotDeclare without the item-12 rule (the new test must fail);
 E4 knownBy added at purchase for an undeclared listing; E5 a same-day second look allowed to charge (if the build
 refuses it in the engine) ; E6 declared broker price with the treatment share (natural: false); E7 declared listing
 offers above natural worth; E8 the finding told twice (untold not cleared) / never; E9 ownTreatment and
 nothingToDeclare swapped; E10 the look's result shown to another player (knownBy check removed in views.dart
 knownTreatments). Phone: P1 two-tap removed from «بيعها معلن الحين»; P2 the screen-change tap guard bypassed on the
 look button; P3 the look's double-tap guard; P4 her() replaced by the female form (a male listing must catch it in
 the page check); P5 the vet row's count noun («مرتين») from a fixed string.
Plus the standing: CI (format, analyze, tests incl. node, proto vm,node, same seed VM = JS, smoke, engine page,
simulate 10 4), a v9 save (the owner's) migrating if the state changes.
