// الحراج's rules its screens do not show yet, as a DESIGN awaiting the owner's approval (not built, not in phone.js):
//   1 check      a camel's page with the vet's look before buying (CheckListing, SAR 500): the button, and after a look
//                «انفحصت مرة، ما لقى شي» (a look on another day is a fresh one; never a chance in numbers)
//   2 found      the look found a treatment: what was found, that only the buyer knows, and his choice
//   3 declare    selling one's own camel known to be treated, for one who bought her unknowing and was told (decision
//                15): listed «معلنة» at his price (the buyers know), or to the broker «معلنة» now, at her natural price
//                with no examination and no fine. Her natural price sits under the estimate the cards show
//                because the cards and the market see her look with a share of the treatment's lift
//                (Balance.tamperPriceShare) and a declared sale pays for her own look only
//   4 own        for one who treated her himself the engine refuses the declared sale (ownTreatment), and the page
//                says why
// Drawn in the phone's own CSS and pieces from a game the engine played (seed 4242, 1 October 2026: tool/proto_engine/
// bin/vet_design_save.dart): a seller's treated listing the player's vet looked at until he found it, a treated camel
// bought unchecked and found the next day by the daily look (he did not know: told, not fined, and the engine prices
// her declared sale), and نورة treated by her owner (the engine's refusal, ownTreatment); and a look at a clean listing
// made in the page (nothing found). Every figure is the engine's.
// To draw: `dart run bin/vet_design_save.dart <save.json>` in tool/proto_engine; build and serve the prototype
// (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py; serve tool/proto_app/assets/web on PORT,
// default 8765) and run `SAVE=<save.json> NODE_PATH=$(npm root -g) node design/ui/phone_haraj_vet.cjs` from the
// repository's root; it writes mock_haraj_vet_<n>.png in OUT (default .) and design/ui/phone_haraj_vet.jpg.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const PORT = process.env.PORT || 8765, OUT = process.env.OUT || '.', SAVE = fs.readFileSync(process.env.SAVE, 'utf8');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  await p.addInitScript(([v]) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', v); sessionStorage.setItem('seeded', '1'); } }, [SAVE]);
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  const game = await p.evaluate(async () => {
    const e = window.marahEngine, S0 = e.snapshot;
    // the vet's finding, played in the save; a look at a clean listing now (nothing found)
    const found = S0.market.find((l) => l.treatments && l.treatments.length);
    const clean = S0.market.filter((l) => !l.treatments && !l.checked).sort((a, b) => a.askPrice - b.askPrice)[0];
    await e.dispatch({ type: 'checkListing', listing: clean.id });
    // نورة (treated by her owner) offered declared: the engine's answer
    const noura = S0.yard.find((c) => c.name === 'نورة');
    const own = await e.dispatch({ type: 'quickSale', camel: noura.id, declared: true });
    await new Promise((res) => setTimeout(res, 500));
    const S = e.snapshot;
    return { checked: S.market.find((x) => x.id === clean.id), found, own: own.error, noura: S.yard.find((c) => c.id === noura.id), bought: S.yard.find((c) => c.declaredSale != null), cash: S.cash, fee: 500, looks: 1 };
  });
  console.log('found', game.found && game.found.treatments, 'bought', game.bought && [game.bought.name, game.bought.declaredSale], 'own', JSON.stringify(game.own), 'clean', game.checked && game.checked.checked);
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
    // 2 found: the vet's look in the save, which found the seller's treatment
    const l2 = G.found, c2 = l2.camel, what = l2.treatments.map((k) => TAMPER[k]).join(' و');
    const found2 = page(l2, `<div class="warn"><span class="lead">${alert}</span><b>البيطري لقى ${her(c2, 'فيها', 'فيه')} ${what}</b><small>محد يدري غيرك. لو ${her(c2, 'اشتريتها', 'اشتريته')} ${her(c2, 'وسجلتها', 'وسجلته')} بمزاين وانكشف، الغرامة والحرمان عليك. والتجميل يروح مع الوقت.</small></div>`,
      `<button class="btn ghost wide">${her(c2, 'اشترها', 'اشتره')} بـ ${n0(l2.askPrice)} وأنت تدري</button>
       <div class="note">تقدر ${her(c2, 'تتركها', 'تتركه')}، أو ${her(c2, 'تشتريها', 'تشتريه')} وتنتظر لين يروح التجميل.</div>`);
    // 3 selling one's own treated camel: the declared sale, and the engine's refusal for one who treated her himself
    const nr = G.noura, ownCode = G.own && G.own.code, bc = G.bought, nat = bc.declaredSale;
    const minus = ic('<path d="M5 12h14"/>'), plusI = ic('<path d="M12 5v14M5 12h14"/>');
    const tag = ic('<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>');
    const top = (c, line) => `<div class="body">${back}<div class="title" style="font-size:22px">بيع ${c.name}</div>
      <div class="it"><span class="ph">${img(c)}</span><b>${title(c)}</b><small>${her(c, 'يقدّرونها', 'يقدّرونه')} ${rng(c)} ريال</small><small>${line}</small></div>`;
    const declare = `${top(bc, `${her(bc, 'فيها', 'فيه')} تجميل، وأنت ما دريت لين انقال لك`)}
      <div class="sec">${her(bc, 'اعرضها', 'اعرضه')} معلن إن ${her(bc, 'فيها', 'فيه')} تجميل</div>
      <div class="group"><div class="row ord full"><span class="lead">${tag}</span><b>سعرك</b><span class="stp"><button>${minus}</button><span class="n"><b>${n0(nat)}</b> <span>ريال</span></span><button>${plusI}</button></span><small>المشتري يدري، وما يفحصون ولا تتغرم</small></div></div>
      <button class="btn pri wide">${her(bc, 'اعرضها', 'اعرضه')} معلن بـ ${n0(nat)}</button>
      <div class="sec">أو ${her(bc, 'بيعها', 'بيعه')} معلن للدلال الحين</div>
      <button class="btn ghost two wide"><span>${her(bc, 'بيعها', 'بيعه')} معلن الحين</span><span>${n0(nat)} ريال</span></button>
      <div class="note">${her(bc, 'سعرها', 'سعره')} الطبيعي بدون زيادة التجميل، فهو تحت تقديرهم. أو ${her(bc, 'انتظرها', 'انتظره')} لين يروح التجميل.</div></div>`;
    const own = `${top(nr, `${her(nr, 'فيها', 'فيه')} صبغ خفيف، أنت اللي ${her(nr, 'جمّلتها', 'جمّلته')}`)}
      <div class="warn"><span class="lead">${alert}</span><b>ما تقدر ${her(nr, 'تعلنها', 'تعلنه')}${ownCode === 'ownTreatment' ? '' : ` (${ownCode || ''})`}</b><small>أنت اللي ${her(nr, 'جمّلتها', 'جمّلته')}، والتجميل ممنوع برا المهرجان بعد، وإعلانه اعتراف. ${her(nr, 'انتظرها', 'انتظره')} لين يروح الصبغ، أو ${her(nr, 'بيعها', 'بيعه')} ساكت ويفحصونها قبل ما يدفعون.</small></div></div>`;
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
