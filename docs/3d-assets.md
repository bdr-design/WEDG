# مجسمات الثري دي (توليد بالذكاء الاصطناعي)

القرار: عالم ثري دي حقيقي، والمالك يولّد المجسمات بأدوات ذكاء اصطناعي ([ADR 0005](adr/0005-3d-world.md)).

صور الإبل من فوق في [image-prompts.md](image-prompts.md) **ما عاد نحتاجها**. أما الصور الجانبية فنستخدمها مدخل للتوليد.

## الأداة

- **Tripo**: فيها هيكل جاهز للحيوانات اللي تمشي على أربع، وحركات جاهزة له.
- **Meshy**: بديل، وفيها هيكل "Quadruped Dog"، لكن حركاتها للحيوانات أقل.

## أول شي: تجربة ناقة وحدة

ما نولد الكل قبل ما نتأكد من وحدة.

### 1. صورة إلى مجسم (Image to 3D)
- **الصورة:** الصورة الجانبية للناقة الوضحاء (`05_camels_profile/wodh/female.png`).
- **الإعدادات:** أعلى جودة، وخامات PBR، وخامة 2K، وعدد الأوجه بين 30 و50 ألف.
- **وصف مرافق** إذا طلبته الأداة:
```
Photorealistic adult Saudi dromedary she-camel, Wadh breed, bright pure white coat, single hump, long lean neck carried high, prominent nose, long drooping lower lip, short ears set back, chest pad, two-toed padded feet, standing square in a neutral pose, realistic proportions, no saddle, no rope, no decorations
```

### 2. التحريك (Rig + Animation)
- **الهيكل:** Quadruped.
- **الحركات:** خذ اللي متوفر من هذي:
  - وقوف (Idle)
  - مشي (Walk)
  - هرولة (Trot/Run)
  - أكل أو رعي (Eat/Graze)
  - بروك (Lie down / Sit)
  - قيام (Stand up)

### 3. التصدير
- **الصيغة:** GLB، والحركات داخل الملف.
- **إذا ما طلعت الحركات في GLB:** صدّر FBX.

### 4. أرسله لي
أفحص فيه:
- النسب مقارنة بالناقة الحقيقية: السنام الواحد، وطول الرقبة، والخف.
- الأوجه وجودة الخامة.
- انثناء الرقبة والرجول مع الحركة.
- الحركات نفسها.

## بعد ما تنجح التجربة

### الإبل
- **المجسمات الأساسية ست:**
  - **المجاهيم:** ناقة وفحل وحوار، لأن إطارها أكبر وعظمها أثقل.
  - **المغاتير:** ناقة وفحل وحوار، بلون الوضح.
- **ألوان المغاتير الباقية** (الشقح والشعل والصفر والحمر): أسويها أنا خامات على نفس المجسم، عشان التطبيق يبقى خفيف. إذا ما طلعت واقعية، تعيد تلوينها بأداة Retexture.

### السيارات والأغراض
ثابتة بدون تحريك.
- **أولًا:** ولّد صورة بزاوية ثلاثة أرباع بهذا الوصف، وحط مكان `[ITEM]` الغرض:
```
Photorealistic three-quarter view photo of [ITEM], plain flat solid magenta (#FF00FF) background, soft even daylight, no text, no logos, no people
```
- **بعدين:** حوّل الصورة لمجسم بخاصية صورة إلى مجسم.
- **الأغراض** (انسخ الوصف الإنجليزي مكان `[ITEM]`):
  - **ونيت:**
    `a white pickup truck commonly used on Saudi camel farms, no brand logos`
  - **لوري نقل الإبل:**
    `a white medium truck with a tall galvanized steel cage on the back for carrying camels, no brand logos`
  - **وايت:**
    `a white water tanker truck with a cylindrical steel tank, no brand logos`
  - **بيت شعر:**
    `a traditional black goat-hair Bedouin tent with wooden poles and guy ropes, a red and white Sadu rug at the open front`
  - **بالة برسيم:**
    `a rectangular bale of green-gold alfalfa hay`
  - **كيس شعير:**
    `a white woven polypropylene sack of barley, 50 kg`
  - **خزان:**
    `a white cylindrical polyethylene water tank on a low concrete base`

**الحدود:**

| النوع | الأوجه | الخامة |
|---|---|---|
| الأغراض | لا تزيد عن 10 آلاف | 1K |
| السيارات | لا تزيد عن 20 ألف | 2K |

## اللي أسويه أنا بالكود
- الشبوك والسياج والمظلات والأحواض بمقاساتها الحقيقية.
- أرض العزبة وحبوب الرمل والشجيرات.
- **أرض المملكة:** ثري دي من بيانات ارتفاع حقيقية، وعليها صور أقمار صناعية.
