# The herd's drawing: the test on the owner's phone

Three ways of drawing the herd (ADR 0005, "On the owner's phone: three ways of drawing the herd") are measured on the
owner's iPhone with the page's frame meter, which the app always shows. The labels below are the page's own
(design/prototype3d/farm.html: `HERD_MODES`, `meterFrame`, the meter's click and touch handlers).

## الخطوات (للمالك)

**قبل لا تبدأ:** شغّل اللعبة في الجوال وهو بالعرض، وخله على الشاحن، وطفّ أي شي ثاني شغّال. عداد اللعبة مربع صغير
فوق على **اليمين**. أول ما تفتح يكتب «يسخّن…» ثلاث ثواني، وبعدها يطلع فيه رقمين وجنبهم اسم طريقة الرسم، مثلًا:
«60 · 18 م.ث · مزج إطارين».

1. **افتح العداد:** اضغط على المربع الصغير اللي فوق يمين. يكبر ويطلع فيه أكثر من سطر. السطر الثاني فيه:
   «رسم القطيع: مزج إطارين · قطيع تجربة: طافي · 2 راس» (الرقم الأخير عدد نوقك في العزبة).
2. **شغّل قطيع التجربة:** اضغط على كلمة «قطيع تجربة: طافي». تصير «قطيع تجربة: شغّال»، والعدد يصير «40 راس». هذي نسخ
   من نوقك، توزّعت على الحظاير الست عشان نقيس ثقل عزبة مليانة. ما تدخل في حلالك ولا في عدّ الحظاير، ولا تنفتح لها
   بطاقة.
3. **اختر الطريقة:** كل ضغطة على «رسم القطيع: …» تنقلك للي بعدها، بهالترتيب: «مزج إطارين» ← «أقرب إطار» ← «كلها
   بالمعالج» ← وترجع لـ«مزج إطارين». أول مرة ابدأ بـ«مزج إطارين». كل ما تغيّر، العداد يرجع يحسب من الصفر (يكتب
   «يسخّن…» ثلاث ثواني).
4. **اللقطة الأولى، الخريطة من قريب:** سكّر العداد بضغطة على حافته (مو على السطرين). يصير مربع صغير، وآخر شي
   مكتوب فيه «تجربة 40» بالبرتقالي. على يسار الشاشة فوق فيه ثلاث أزرار مدوّرة، واحد تحت الثاني. اضغط **الثاني**، اللي
   عليه صورة كاميرا. الكاميرا تروح لحالها لنفس المكان كل مرة: داخل الحظيرة الكبيرة والنوق قدامك. لا تسحب الخريطة.
   شيل يدك وخل الجوال ثابت **دقيقة كاملة** بدون ما تلمس الشاشة. بعد الدقيقة افتح العداد وصوّره، وبعدين اضغط زر
   الكاميرا مرة ثانية عشان ترجع الخريطة البعيدة.
5. **اللقطة الثانية، تمشي بين النوق:** اضغط **الأول** من الأزرار اللي على اليسار فوق، اللي عليه صورة رجّال يمشي.
   للمشي، حط إبهامك اليسار في أي مكان بالنص اليسار من الشاشة، وتطلع تحته دايرة المشي، وحرّكه للجهة اللي تبيها.
   وللالتفات، اسحب بإبهامك اليمين في النص اليمين. امش لين توصل عند سياج الحظيرة الكبيرة، وتشوف النوق داخلها
   قدامك ومعبّية الشاشة. شيل يدك وخل الجوال ثابت **دقيقة كاملة** بدون ما تلمس. بعد الدقيقة افتح العداد (فوق يمين)
   وصوّره. وعشان ترجع للخريطة، اضغط الزر المدوّر اللي فوق على اليسار وعليه علامة «›».
6. **عِد الخطوات 3 و4 و5** للطريقتين الثانيتين: «أقرب إطار»، وبعدها «كلها بالمعالج».
7. **أرسل لنا ست صور:** ثلاث طرق، ولكل طريقة لقطتين. لازم يبين في كل صورة اسم الطريقة («رسم القطيع: …») والسطور
   هذي من العداد:
   - «N لقطة/ث · أبطأ 1٪: N م.ث»
   - «تقطيع: N»
   - «الحساب X · تجهيز الرسم Y م.ث بالمعدل · أبطأ 1٪: a وb»

   وإذا حسّيت إن الجوال حمي، أو شفت تقطيع، أو إن وحدة من الطرق شكل النوق فيها غريب، قل لنا.
8. **إذا خلصت:** افتح العداد واضغط «قطيع تجربة: شغّال» لين يرجع «طافي» (أو سكّر اللعبة وافتحها). خل «رسم القطيع» على
   «مزج إطارين»، إلا إذا قلنا لك غير كذا.

## Reading his numbers

For each variant and view there are three numbers. The first is the frames a second over the last 2 s («N لقطة/ث»).
The second is the slowest 1% of frame times since the variant was chosen («أبطأ 1٪: N م.ث»). The third is the stutters
over 50 ms («تقطيع»). The CPU line splits the frame into the game's computing (الحساب) and three.js issuing the draws
(تجهيز الرسم), each an average and its slowest 1% in whole milliseconds.

- **0 مزج إطارين** (as built: two baked frames blended in the shader, 32 texture reads a vertex). If its slowest 1% is
  within about 1 ms of the other two in both views, the vertex fetches cost nothing on his phone: keep 0.
- **1 أقرب إطار** (16 reads a vertex; the pose steps at 60 frames a second, up to 8 ms of a clip off) and
  **2 كلها بالمعالج** (16 reads a vertex; every camel posed on the CPU, about 97 kB sent to the GPU a frame). If either
  is clearly smoother than 0 (a lower slowest 1%, fewer stutters, the frame rate held at 60 where 0 drops), the
  vertex fetches are the cost. Prefer 2, because its poses are exact. Choose 1 instead if 2's الحساب or تجهيز الرسم
  rises by more than it saves.
- If all three are the same and still under 60 by the herd, the herd's vertex work is not the cause. Look next at the
  draws, the triangles up close (ADR 0005's options) and the rest of the frame.
- The variant is kept in the browser's storage. The owner's choice is made the default in code by changing
  `HERD.mode`'s starting value, not by leaving it on his phone.
