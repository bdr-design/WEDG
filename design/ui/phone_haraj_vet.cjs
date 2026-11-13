// الحراج's rules its screens do not show yet, as a DESIGN awaiting the owner's approval (not built, not in phone.js):
//   1 check      a camel's page with the vet's look before buying (CheckListing, SAR 500): the button, and after a look
//                «انفحصت مرة، ما لقى شي» (a look on another day is a fresh one; never a chance in numbers)
//   2 found      the look found a treatment: what was found, that only the buyer knows, and his choice
//   3 declare    selling one's own camel known to be treated, for one who bought her unknowing and was told (decision
//                15): listed «معلنة» at his price (the buyers know), or to the broker «معلنة» now, at her natural price
//                with no examination and no fine. Her natural price sits under the estimate the cards show (15,000 to
//                18,000 here), because the cards and the market see her look with a share of the treatment's lift
//                (Balance.tamperPriceShare) and a declared sale pays for her own look only
//   4 own        for one who treated her himself the engine refuses the declared sale (ownTreatment), and the page
//                says why
// Drawn from real games on seed 4242 (1 October 2026, the page's new game) in the phone's own CSS and pieces: the
// listings, the vet's looks (the engine's checkListing answers, run on the cheapest listings until one finds something
// or the cash runs short) and the engine's own refusal of a declared sale for نورة, dyed by her owner. What the engine
// could not give honestly in one sitting is marked PLACEHOLDER (a camel bought treated unknowing and told: the market's
// 3%, the vet's 60%, a purchase and a day's wait).
// To draw: build and serve the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py; serve
// tool/proto_app/assets/web on PORT, default 8765) and run `NODE_PATH=$(npm root -g) node design/ui/phone_haraj_vet.cjs`
// from the repository's root; it writes mock_haraj_vet_<n>.png in OUT (default .) and design/ui/phone_haraj_vet.jpg.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const PORT = process.env.PORT || 8765, OUT = process.env.OUT || '.';
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 600000 });
  const game = await p.evaluate(async () => {
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 25));
    const S0 = e.snapshot, list = S0.market.slice().sort((a, b) => a.askPrice - b.askPrice);
    // the vet's look: once on the cheapest (the "nothing found" page), then on the others till one finds something
    const first = list[0];
    const r1 = await e.dispatch({ type: 'checkListing', listing: first.id });
    let found = null, looks = 1;
    for (const l of list.slice(1)) {
      if (e.snapshot.cash < 1500) break;
      const r = await e.dispatch({ type: 'checkListing', listing: l.id });
      looks++;
      await new Promise((res) => setTimeout(res, 50));
      const seen = e.snapshot.market.find((x) => x.id === l.id);
      if (r.ok && seen && seen.treatments && seen.treatments.length) { found = seen; break; }
    }
    // نورة dyed by her owner, then offered declared: the engine's answer
    const noura = S0.yard.find((c) => c.sex === 'female');
    await e.dispatch({ type: 'tamper', camel: noura.id, kind: 'dye', strength: 1 });
    const own = await e.dispatch({ type: 'quickSale', camel: noura.id, declared: true });
    await new Promise((res) => setTimeout(res, 300));
    const S = e.snapshot;
    return { checked: S.market.find((x) => x.id === first.id), r1: r1.ok, found, looks, own: own.error, noura: S.yard.find((c) => c.id === noura.id), cash: S.cash, fee: 500 };
  });
  console.log('looks', game.looks, 'found', game.found ? game.found.treatments : null, 'own', JSON.stringify(game.own));
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(400);
  const screens = await p.evaluate((G) => {
    const REG = { riyadh: 'الرياض', qassim: 'القصيم', hail: 'حائل', jouf: 'الجوف', northern: 'الحدود الشمالية', sharqiya: 'الشرقية', tabuk: 'تبوك', najran: 'نجران' };
    const COAT = { wodh: ['وضحاء', 'وضح'], shoqh: ['شقحاء', 'شقح'], shoal: ['شعلاء', 'شعل'], sofr: ['صفراء', 'صفر'], homr: ['حمراء', 'حمر'], majaheem: ['مجهمية', 'مجاهيم'] };
    const PHOTO = { wodh: 'camel_side_wodh.png', shoqh: 'thumb_shaqh.png', shoal: 'thumb_shaal.png', sofr: 'thumb_safra.png', majaheem: 'thumb_majaheem.png', homr: 'thumb_shaal.png' };
    const TAMPER = { botox: 'بوتوكس', filler: 'فيلر', hormones: 'هرمونات', lipStretch: 'شد الشفة', teethFiling: 'برد الأسنان', tailCut: 'قص الذيل', dye: 'صبغ' };
    const n0 = (v) => Math.round(v).toLocaleString('en-US');
    const her = (c, f, m) => (c.sex === 'female' ? f : m);
    const title = (c) => `${c.ageName} ${COAT[c.category][c.sex === 'female' ? 0 : 1]}`;
    const img = (c) => `<img src="phone/${PHOTO[c.category]}" alt=""${c.category === 'homr' ? ' class="homr"' : ''}>`;
    const ic = (d) => `<svg class="i" viewBox="0 0 24 24">${d}</svg>`;
    const back = `<div class="nav"><button class="back">${ic('<path d="M9 6l6 6-6 6"/>')}رجوع</button></div>`;
    const scope = ic('<path d="M6 3.5v6a4 4 0 0 0 8 0v-6"/><path d="M10 13.5v2a4.5 4.5 0 0 0 9 0v-2"/><circle cx="19" cy="11.5" r="2"/>');
    const check = ic('<path d="M5 12.5l4.5 4.5L19 7.5"/>'), alert = ic('<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>');
    const rng = (c) => `<bdi dir="ltr">${n0(c.estimateLow)}–${n0(c.estimateHigh)}</bdi>`;
    const page = (l, vetRow, extra) => {
      const c = l.camel;
      return `<div class="body">${back}<div class="title" style="font-size:22px">${title(c)}</div>
        <div class="it big"><span class="ph">${img(c)}</span><b>${c.name}</b><small>${REG[l.region]} · عند ${l.sellerName}</small><small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${rng(c)} ريال</small></div>
        ${vetRow}
        <div class="tank"><small>اللي تدفعه</small>
          <div class="kind"><span>${her(c, 'سعرها', 'سعره')}</span><span class="d">${n0(l.askPrice)} ريال</span></div>
          <div class="kind"><span>${her(c, 'نقلها', 'نقله')} لعزبتك</span><span class="d">${n0(l.transport)} ريال</span></div></div>
        ${extra}</div>`;
    };
    // 1 the vet's look, and its answer when he found nothing
    const l1 = G.checked, c1 = l1.camel, n = l1.checked || 1;
    const check1 = page(l1, `<div class="group"><div class="row"><span class="lead">${scope}</span><b>البيطري ${her(c1, 'فحصها', 'فحصه')} ${n === 1 ? 'مرة' : n === 2 ? 'مرتين' : `${n} مرات`}</b><span class="act"><button class="btn ghost">افحص بكرة</button></span><small>ما لقى شي · الفحص بـ ${n0(G.fee)} ريال، وكل يوم فحص جديد</small></div></div>`,
      `<button class="btn pri wide">${her(c1, 'اشترها', 'اشتره')} بـ ${n0(l1.askPrice)}</button>
       <div class="note">البيطري يدوّر على التجميل قبل لا تشتري، بس ممكن يفوته شي. واللي يلقاه ما يدري عنه غيرك.</div>`);
    // before any look: the button
    const fresh = G.found || l1;
    // 2 found (the engine's answer, or a PLACEHOLDER from the cheapest listing when no look found anything)
    const l2 = G.found || { ...l1, treatments: ['dye'] }, c2 = l2.camel, what = l2.treatments.map((k) => TAMPER[k]).join(' و');
    const found2 = page(l2, `<div class="warn"><span class="lead">${alert}</span><b>البيطري لقى ${her(c2, 'فيها', 'فيه')} ${what}</b><small>${G.found ? '' : '[PLACEHOLDER] '}محد يدري غيرك. لو ${her(c2, 'اشتريتها', 'اشتريته')} ${her(c2, 'وسجلتها', 'وسجلته')} بمزاين وانكشف، الغرامة والحرمان عليك. والتجميل يروح مع الوقت.</small></div>`,
      `<button class="btn ghost wide">${her(c2, 'اشترها', 'اشتره')} بـ ${n0(l2.askPrice)} وأنت تدري</button>
       <div class="note">تقدر ${her(c2, 'تتركها', 'تتركه')}، أو ${her(c2, 'تشتريها', 'تشتريه')} وتنتظر لين يروح التجميل، أو ${her(c2, 'تبيعها', 'تبيعه')} بعدين معلن إن ${her(c2, 'فيها', 'فيه')} تجميل.</div>`);
    // 3 selling one's own treated camel: the declared sale, and the engine's refusal for one who treated her himself
    const nr = G.noura, ownCode = G.own && G.own.code;
    const nat = Math.round(nr.estimateLow * 0.95 / 500) * 500;      // PLACEHOLDER: the engine's declaredSale price, for a camel that may be declared
    const minus = ic('<path d="M5 12h14"/>'), plusI = ic('<path d="M12 5v14M5 12h14"/>');
    const tag = ic('<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>');
    const head = `<div class="body">${back}<div class="title" style="font-size:22px">بيع ${nr.name}</div>
      <div class="it"><span class="ph">${img(nr)}</span><b>${title(nr)}</b><small>${her(nr, 'يقدّرونها', 'يقدّرونه')} ${rng(nr)} ريال</small><small>${her(nr, 'فيها', 'فيه')} صبغ خفيف، وأنت ما دريت لين انقال لك</small></div>`;
    const declare = `${head}
      <div class="note">[PLACEHOLDER: اشتريتها مجمّلة وأنت ما تدري، وانقال لك]</div>
      <div class="sec">${her(nr, 'اعرضها', 'اعرضه')} معلنة إن ${her(nr, 'فيها', 'فيه')} تجميل</div>
      <div class="group"><div class="row ord full"><span class="lead">${tag}</span><b>سعرك</b><span class="stp"><button>${minus}</button><span class="n"><b>${n0(nat)}</b> <span>ريال</span></span><button>${plusI}</button></span><small>المشتري يدري إن ${her(nr, 'فيها', 'فيه')} صبغ، وما يفحصون ولا تتغرم</small></div></div>
      <button class="btn pri wide">${her(nr, 'اعرضها', 'اعرضه')} معلنة بـ ${n0(nat)}</button>
      <div class="sec">أو ${her(nr, 'بيعها', 'بيعه')} معلنة للدلال الحين</div>
      <button class="btn ghost two wide"><span>${her(nr, 'بيعها', 'بيعه')} معلنة الحين</span><span>${n0(nat)} ريال</span></button>
      <div class="note">${her(nr, 'سعرها', 'سعره')} الطبيعي بدون زيادة التجميل، فهو تحت تقديرهم. أو ${her(nr, 'انتظرها', 'انتظره')} لين يروح الصبغ.</div></div>`;
    const own = `${head.replace('، وأنت ما دريت لين انقال لك', '، أنت اللي جمّلتها')}
      <div class="sec">لو جمّلتها أنت (${ownCode === 'ownTreatment' ? 'جواب اللعبة' : ownCode || 'ما رد'})</div>
      <div class="warn"><span class="lead">${alert}</span><b>ما تقدر ${her(nr, 'تعلنها', 'تعلنه')}</b><small>أنت اللي ${her(nr, 'جمّلتها', 'جمّلته')}، والتجميل ممنوع برا المهرجان بعد، وإعلانه اعتراف. ${her(nr, 'انتظرها', 'انتظره')} لين يروح الصبغ، أو ${her(nr, 'بيعها', 'بيعه')} ساكت ويفحصونها قبل ما يدفعون.</small></div></div>`;
    return { check: check1, found: found2, declare, own };
  }, game);
  const files = [];
  let i = 0;
  for (const [k, html] of Object.entries(screens)) {
    await p.evaluate((html) => {
      const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
      scr.classList.remove('home');
      scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1 ').replace(/([؀-ۿ]) (?=\d)/g, '$1 ')}<div class="hb"></div>`;
    }, html);
    await p.waitForTimeout(400);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    const file = path.join(OUT, `mock_haraj_vet_${++i}_${k}.png`);
    await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
    console.log(k, await p.evaluate(() => { const bd = R().querySelector('.body'); return [bd.scrollHeight, bd.clientHeight]; }));
    files.push(file);
  }
  await b.close();
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_haraj_vet.jpg')]);
})();
