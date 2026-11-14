# تجربة القفزة الطويلة بالتقويم (على جوالك)

هذي التجربة بعد ما توافق على تصميم الاستعجال والتقويم، ويوصل البناء لجوالك. الهدف: نعرف كم تاخذ سنة كاملة مع حلال كبير، وهل الجوال يعلّق أو يسخن.

## الخطوات

1. نزّل نسخة التجربة اللي يجهزها لك المساعد وافتحها: تبدأ من لعبة محفوظة فيها 10,000 راس (حفظ لعبتك العادية ما يتأثر).
2. افتح الجوال داخل اللعبة، واضغط «التقويم».
3. اضغط «اختار يوم»، وروح لآخر شهر يطلع لك، واختار آخر يوم يخليك تختاره (التقويم يمشي سنة بالكثير)، واضغط «امشِ لين …».
4. في بطاقة «قبل ما تمشي»: شغّل «طلب ثابت للماء والعلف»، واضغط «اتعاقد» عند «عقد البيطري» مرتين.
5. اضغط «امشِ لين …»، وبعدها «اضغط مرة ثانية ويمشي»، وشغّل ساعة الإيقاف بجوال ثاني أو بساعتك.
6. وهو يمشي: تأكد إن التاريخ تحت «وصل» يتغيّر، وإن الشاشة ما تعلّق.
7. اضغط «وقّف هنا» مرة وحدة: لازم يوقف خلال ثانية أو ثانيتين ويطلع «وقف التقويم».
8. اضغط «كمّل لين …» وبعدها «اضغط مرة ثانية ويكمل»، وكل ما وقف كمّل نفس الشي لين توصل اليوم اللي اخترته.
9. لما يطلع «يحفظ اللعبة…» ثم «اللي صار»: وقّف الساعة، واكتب كم دقيقة وثانية أخذت كلها.
10. المس ظهر الجوال: عادي، دافي، ولا حار؟ واكتب كم كانت البطارية قبل وبعد.
11. أرسل للمساعد: الوقت، وكم مرة وقف، وحرارة الجوال، والبطارية قبل وبعد.

## How the large save reaches his phone (English)

The iPhone app keeps its save as files in its own Documents folder, through its local server
(tool/proto_app/README.md); that folder is not reachable from outside the app (no file sharing is enabled), and a
link cannot carry a save into it. So the test needs a **test build** that starts once from a 10,000-head save bundled
with it, kept apart from his own game's save. That build is **not made yet**: it is owed before this test, and the
steps above assume it.

## How his numbers are read (English)

- **The time** is the whole jump of a year at 10,000 head, stops included. On this machine it is 12.8 s in
  JavaScript; a mid-range phone is expected at about 25 to 40 s. Up to about 60 s: the year's jump stays as built.
  Over 60 s, or if the date under «وصل» stops moving for more than a few seconds: the cap goes down to a season
  (the proxy's fallback, batch 4b item 7), one constant in the engine (EngineCore.maxCatchUpDays and the calendar's
  day picker).
- **«وقّف هنا»** must answer within a second or two (the engine reads the stop between its slices of about 6 ms of
  work). If it waits for the end of the jump, the stop flag is not reaching the worker: a fault to fix, not a limit.
- **The stops** expected on a year at 10,000 head with the standing order and the vet's contract on: about 10
  (festivals' registration closing and the breeding season's first day).
- **Heat and battery**: «حار» or more than about 5% of the battery for one year's jump means the jump should be cut
  to a season, as above.
- **«يحفظ اللعبة…»** shows for about a second at the end (the 7 MB save at 10,000 head).
