// الحراج on the engine, approved by the owner on 13 Nov 2026 (phone_haraj.jpg): the listings, a camel's page (buy, or
// haggle: three tries a seller), selling one's own camel (listed at one's price, or to the broker now), and one's
// listings with the offers that come. Drawn in the real phone's CSS plus the approved market styles (phone_haraj.css,
// from design/ui/phone.html) with the engine's own listings and herd, at the owner's screen (956 x 440, enlarged). To
// draw again: build and serve the prototype on port 8765 (tool/proto_app/assemble.py) and run
// `node design/ui/phone_haraj.cjs`; it writes mock_haraj_*.png here.
const { chromium } = require('playwright');
const fs = require('fs');
const HARAJ_CSS = fs.readFileSync(__dirname + '/phone_haraj.css', 'utf8');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  await p.goto('http://127.0.0.1:8765/index.html');
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 300000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(400);
  const screens = await p.evaluate(() => {
    const S = window.marahEngine.snapshot;
    const REG = { riyadh: 'الرياض', qassim: 'القصيم', hail: 'حائل', jouf: 'الجوف', northern: 'الحدود الشمالية', sharqiya: 'الشرقية', tabuk: 'تبوك', najran: 'نجران' };
    const COAT_F = { wodh: 'وضحاء', shoqh: 'شقحاء', shoal: 'شعلاء', sofr: 'صفراء', homr: 'حمراء', majaheem: 'مجهمية' };
    const COAT_M = { wodh: 'وضح', shoqh: 'شقح', shoal: 'شعل', sofr: 'صفر', homr: 'حمر', majaheem: 'مجاهيم' };
    const PHOTO = { wodh: 'camel_side_wodh.png', shoqh: 'thumb_shaqh.png', shoal: 'thumb_shaal.png', sofr: 'thumb_safra.png', majaheem: 'thumb_majaheem.png', homr: 'thumb_shaal.png' };
    const n0 = (v) => Math.round(v).toLocaleString('en-US');
    const rng = (lo, hi) => `<bdi dir="ltr">${n0(lo)}–${n0(hi)}</bdi>`;
    const title = (c) => `${c.ageName} ${c.sex === 'male' ? COAT_M[c.category] : COAT_F[c.category]}`;
    const img = (c) => `<img src="phone/${PHOTO[c.category]}" alt=""${c.category === 'homr' ? ' style="filter: sepia(.6) saturate(1.8) hue-rotate(-12deg) brightness(.82)"' : ''}>`;
    const ic = (d) => `<svg class="i" viewBox="0 0 24 24">${d}</svg>`;
    const back = `<div class="nav"><button class="back">${ic('<path d="M9 6l6 6-6 6"/>')}رجوع</button></div>`;
    const plus = ic('<path d="M12 5v14M5 12h14"/>'), minus = ic('<path d="M5 12h14"/>');
    const list = S.market.slice().sort((a, b) => a.askPrice - b.askPrice);
    const cheap = list.slice(0, 4);
    const it = (l) => `<div class="it"><span class="ph">${img(l.camel)}</span><b>${title(l.camel)}</b><small>${REG[l.region]} · ${l.sellerName} · النقل ${n0(l.transport)} ريال</small><span class="pr"><span class="price num">${n0(l.askPrice)}</span></span><small>يقدّرونها ${rng(l.camel.estimateLow, l.camel.estimateHigh)}</small></div>`;
    const market = `<div class="body">${back}<div class="title">الحراج</div>
      <div class="seg" style="grid-template-columns:1fr 1fr"><span class="on">المعروض</span><span>إعلاناتي</span></div>
      <div class="note" style="margin-top:-4px">${S.market.length} ناقة معروضة · رصيدك ${n0(S.cash)} ريال</div>
      <div class="lst">${cheap.map(it).join('')}</div>
      <button class="sell">${plus}اعرض ناقة للبيع</button></div>`;
    const l = cheap[0], c = l.camel, offer = Math.round(l.askPrice * 0.9 / 500) * 500;
    const detail = `<div class="body">${back}<div class="title" style="font-size:22px">${title(c)}</div>
      <div class="it" style="grid-template-columns:96px 1fr"><span class="ph" style="width:96px;height:96px">${img(c)}</span><b>${c.name}</b><small>${REG[l.region]} · عند ${l.sellerName}</small><small>العمر ${c.ageDays >= 365 ? Math.floor(c.ageDays / 365) + ' سنين' : Math.floor(c.ageDays / 30) + ' شهور'} · الحالة ${Math.round(c.condition)} · ${c.health === 'healthy' ? 'بصحة زينة' : 'مريضة'}</small><small>يقدّرونها ${rng(c.estimateLow, c.estimateHigh)} ريال</small></div>
      <div class="tank"><small>اللي تدفعه</small>
        <div class="kind"><span>سعرها</span><span class="d">${n0(l.askPrice)} ريال</span></div>
        <div class="kind"><span>نقلها لعزبتك</span><span class="d">${n0(l.transport)} ريال</span></div>
        <div class="kind"><span><b>المجموع</b></span><span class="d"><b>${n0(l.askPrice + l.transport)} ريال</b></span></div></div>
      <button class="btn pri" style="width:100%">اشترها بـ ${n0(l.askPrice)}</button>
      <div class="sec">سوم عليها</div>
      <div class="group"><div class="row ord"><span class="lead">${ic('<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>')}</span><b>سومك</b><span class="stp"><button>${minus}</button><span class="n"><b>${n0(offer)}</b> <span>ريال</span></span><button>${plus}</button></span><small>باقي لك 3 سومات عند ${l.sellerName}</small></div></div>
      <button class="btn ghost" style="width:100%">سوم بـ ${n0(offer)}</button>
      <div class="note">يرد عليك على طول: يقبل، أو يرد بسعر، أو يرفض. والنقل يوصلها بكرة لحوشك.</div></div>`;
    const mine = S.yard.find((x) => x.sex === 'female' && x.ageDays > 1000) || S.yard[0];
    const ask = Math.round(mine.estimateHigh / 500) * 500, quick = Math.round(mine.estimateLow * 0.85 / 500) * 500;
    const sell = `<div class="body">${back}<div class="title" style="font-size:22px">بيع ${mine.name}</div>
      <div class="it" style="grid-template-columns:70px 1fr"><span class="ph">${img(mine)}</span><b>${title(mine)}</b><small>يقدّرونها ${rng(mine.estimateLow, mine.estimateHigh)} ريال</small><small>مرضع وعشار</small></div>
      <div class="sec">اعرضها بالحراج</div>
      <div class="group"><div class="row ord"><span class="lead">${ic('<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>')}</span><b>سعرك</b><span class="stp"><button>${minus}</button><span class="n"><b>${n0(ask)}</b> <span>ريال</span></span><button>${plus}</button></span><small>السعي ${n0(ask * 0.025)} ريال · يوصلك ${n0(ask * 0.975)}</small></div></div>
      <button class="btn pri" style="width:100%">اعرضها بـ ${n0(ask)}</button>
      <div class="note">تجيك السومات بإعلاناتي، وتقبل أو ترفض.</div>
      <div class="sec">أو بيعها للدلال الحين</div>
      <button class="btn ghost two"><span>بيعها الحين</span><span>${n0(quick)} ريال</span></button>
      <div class="note">الدلال يدفع على طول بس أقل من الحراج.</div></div>`;
    const mineItem = `<div class="it"><span class="ph">${img(mine)}</span><b>${mine.name} · ${title(mine)}</b><small>معروضة بـ ${n0(ask)} · باقي 12 يوم</small><span class="pr"><span class="price num">${n0(ask)}</span></span><small>سومتين</small></div>`;
    const ofr = (who, amt) => `<div class="row"><span class="lead">${ic('<circle cx="12" cy="8" r="3.2"/><path d="M5.5 19.5c.6-3.3 3-5 6.5-5s5.9 1.7 6.5 5"/>')}</span><b>${who} سام ${n0(amt)}</b><span class="act"><button class="btn pri" style="height:32px;padding-inline:10px">اقبل</button></span><small>يوصلك ${n0(amt * 0.975)} بعد السعي · السوم ينتهي بعد يومين</small></div>`;
    const mylist = `<div class="body">${back}<div class="title">الحراج</div>
      <div class="seg" style="grid-template-columns:1fr 1fr"><span>المعروض</span><span class="on">إعلاناتي</span></div>
      <div class="lst" style="padding-bottom:0">${mineItem}</div>
      <div class="sec">السومات</div>
      <div class="group">${ofr('بو فهد', Math.round(ask * 0.82 / 500) * 500)}${ofr('بو ناصر', Math.round(ask * 0.9 / 500) * 500)}</div>
      <button class="btn ghost" style="width:100%">شيل الإعلان</button></div>`;
    return { market, detail, sell, mylist };
  });
  for (const [k, html] of Object.entries(screens)) {
    await p.evaluate(([html, css]) => {
      const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
      scr.classList.remove('home');
      scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1 ')}<div class="hb"></div>`;
      const st = document.createElement('style'); st.textContent = css + '.btn.two{display:flex;justify-content:space-between;width:100%}'; scr.appendChild(st);
    }, [html, HARAJ_CSS]);
    await p.waitForTimeout(400);
    await p.screenshot({ path: `mock_haraj_${k}.png`, timeout: 180000 });
    console.log(k, await p.evaluate(() => { const bd = R().querySelector('.body'); return [bd.scrollHeight, bd.clientHeight]; }));
  }
  await b.close();
})();
