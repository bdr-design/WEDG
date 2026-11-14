# Festivals: the owner's decisions of 13 Nov 2026 (bind T3 and T4), and the director's directions

The T3 reviewer's audit of the base commit found the engine's rounds are colour x sex x age-year (not the Saudi
system), 3 entries an owner a round, closing 7 days before, one judging pass, no cheating, no reputation, and that
GameView.festivals returns the raw Festival model (every owner's entries and per-trait marks: a hidden-value risk).

## The owner decided

1. Scope now: the individual rounds. الفردي for each colour (دق and جل), مفاريد and دق for القعدان and البكار, and
   الفحل وإنتاجه. The group rounds (الجمل, المنقية, البداوة, الهجيج, الطبع) come later with more farms: the player
   cannot enter them yet; rivals do, and they show in the news. Model the round types so the group ones can be added
   (the type exists, entering it is not built), and draw them in the design only as "later", never as working.
2. «لكل مالك شوط فردي واحد»: in one festival the player enters ONE camel in ONE فردي round. المفاريد, الدق of
   القعدان and البكار, and الفحل وإنتاجه are other rounds and do not count against it.
3. A ban for cheating covers EVERY festival in the game: the current edition and five more years of editions, the
   owner and his camels.
4. The first stage of the day is «الشريحة والشاهد» (the chip and the witness), as the rule is since 2020, not
   «الوسم والشاهد». Change GDD section 7 to say so, with the research's source.

## The director's directions (game choices: mark each "(balance)" or "اختيار لعب" where it is written)

- The fine: scaled with the treatment's strength, up to the type's cap (the GDD says «حتى»).
- The late fee's amount, the normal closing day, the DNA check's delay for الفحل وإنتاجه, the detection chances:
  game choices, marked.
- A treatment acts on judging only for now. How long it lasts and whether it also raises what buyers pay is a
  question for the owner: list it, do not build it.
- Reputation (الصيت): build only what GDD section 8 defines and 7.1 needs (a fall when caught), no more.
- The research's rules the GDD does not repeat (the جمل size by colour, البداوة entrants barred from فردي and جمل):
  with the group rounds, later; list them.
- GameView.festivals must not hand a player other owners' entries' hidden marks: fix it in T3.

## More decisions (the owner, 13 Nov 2026, later the same day; the option texts he chose)

5. How much cheating helps: «يفرق فعلاً: التجميل القوي يرفع الناقة الوسط كم مركز فعلاً، مثل الواقع (الناس تغش لأنه ينفع)،
   والخطر يبقى كبير: غرامة وحرمان ست دورات. فيصير إغراء حقيقي بخطره.» (Not "stays weak". The size of the gain is then
   a game choice to tune so that a strong treatment lifts a middling camel a few places; the detection chances, fines
   and ban stay as they are.)
6. How long a treatment lasts and the sale price: «يبقى أشهر ويرفع السعر: مثل الواقع: يبقى كم شهر، والمشتري يشوفها أزين
   فيدفع أكثر، بس ممكن ينكشف بالحراج أو عند البيطري وتتغرم. المدة بالضبط ندوّر مصدرها أو نكتبها اختيار لعب.»
7. A treated camel that is sold: «يروح معها: مثل الواقع: التجميل في الناقة نفسها. اللي يشتريها يشيل خطرها لو سجّلها
   بمزاين، وأنت بعد ممكن تشتري من الحراج ناقة مجمّلة وأنت ما تدري، وفحص البيطري قبل الشراء يكشفها.»
8. A fine larger than the player's cash: «الرصيد ينزل بالسالب: الغرامة تنخصم كلها والرصيد يصير سالب، وما تقدر تشتري حلال
   ولا تبني لين تسدد (العلف والماء يمشون). يعني لازم تبيع من حلالك.»

Settled by the director from the standing rules (not asked): the chance of being found is never a number on the
phone (the views never expose hidden values): words only, in bands. الصيت does what GDD 8 says.
Still open: whether several kinds of treatment may be stacked on one camel.

## Still more (the owner, 13 Nov 2026; the option texts he chose)

9. Feed and water when cash is short: «على الحساب لين حد: العلف والماء ينطلبون على الحساب دايم لو الرصيد ما يكفي، مثل ما
   التاجر يسجل على المربي، لين حد معين (نحدده اختيار لعب). وبعد الحد لازم تبيع من حلالك. الحلال ما يجوع بسبب ريالات
   ناقصة.» (So: one rule whether the shortfall comes from a fine or not; a credit limit, a game choice, listed in the
   GDD; past the limit the orders are refused.)
10. The vet's treatment of a sick camel while short or in debt: «يمشي مثل العلف: العلاج من ضروريات الحلال مثل العلف
    والماء، فينطلب على الحساب بنفس الحد.»
11. Several kinds of treatment on one camel: «مسموح والخطر يتجمع: مثل الواقع: كل نوع يزيد زينها وله فحصه وغرامته، فاللي
    يجمع يكبر عليه احتمال الكشف والغرامات.»

## And two more (the owner, 13 Nov 2026, evening; the option texts he chose)

12. Selling a treated camel (the farming gap: treat for 4,500, sell to the broker at once for 87k more, unchecked):
    «فحص عند البيع وزيادة أصغر: الدلال والمشتري أهل خبرة ويفحصون قبل ما يدفعون: لو لقوه تنلغي البيعة وتتغرم وينزل
    صيتك، وكل ما قوي التجميل سهل ينلقى. ولو ما لقوه يزيد السعر بس أقل من زيادته في التحكيم. يصير مغامرة بخطرها مثل
    المزاين.»
13. Who is examined at a festival: «كل المشاركات ينفحصن: مثل الواقع: الفحص السريري على كل ناقة دخلت الشوط، قبل
    التحكيم الأولي. وترتيب إعلان المراحل في يوم الشوط يبقى مثل ما هو.»

## Two more (the owner, 13 Nov 2026, night; the option texts he chose)

14. The share of treated camels among الحراج's listings: «قليل، حوالي 3%: اللي يشتري 10 نياق في عشر سنين ويفحص كل وحدة
    ويسجلها بمزاين، احتمال ينحرم بسبب ناقة ما درى عنها حوالي 7%. خطر موجود يخلي الفحص مهم، بس ما يظلم اللاعب النظيف.»
    (Its own constant, apart from the rivals' festival rate of 9%; a game choice with no source.)
15. A treatment found outside a festival on a camel her owner bought without knowing: «ما تتغرم وتبيعها معلنة: تنبلغ
    إنها مجمّلة وما تتغرم لأنك ما دريت. بعدها تقدر تبيعها وأنت معلن إنها مجمّلة بسعرها الطبيعي بدون غرامة، أو تنتظر
    لين يروح التجميل. ولو حاولت تبيعها ساكت وانكشفت تتغرم.» (This confirms the director's narrow reading and adds a
    declared sale: at her natural price, no examination risk, no fine; the buyer then knows.)

## The المزاين design approved (the owner, 13 Nov 2026, night)

16. The nine-view design (wt/t4 ec58c5f, design/ui/phone_mazayen.jpg) is approved for building: «اعتمده».
17. Where cheating lives: «محادثة من رجّال بالسر: مثل المرسوم: تطبيق «المحادثات» جديد في الجوال، وبعد ما تسجّل ناقة
    يراسلك واحد يعرض عليك يجمّلها. التطبيق الرسمي للمهرجان ما يعرض الغش.»
18. The round's day: «مرحلة مرحلة على مدار اليوم: مثل المرسوم: المراحل الست تنعلن وحدة ورا وحدة (الصبح، الظهر، العصر،
    المغرب) ويجيك خبر مع كل مرحلة، فتعيش الترقب. الأوقات نفسها اختيار لعب.»
