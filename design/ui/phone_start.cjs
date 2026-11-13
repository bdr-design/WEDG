// The new start's phone screens (الحليب, العزبة, the home screen), approved by the owner on 13 Nov 2026
// (phone_start_*.jpg). Drawn in the real phone's CSS at the owner's screen (956 x 440, enlarged), with the start's
// numbers: a nursing she-camel four months after calving and her calf, SAR 20,000. To draw them again: build and serve
// the prototype (tool/proto_app/assemble.py, then a static server on port 8765 over tool/proto_app/assets/web) and run
// `node design/ui/phone_start.cjs`; it writes mock_home.png, mock_milk.png and mock_build.png here.
const { chromium } = require('playwright');
const ic = (d) => `<svg class="i" viewBox="0 0 24 24">${d}</svg>`;
const P = {
  water: '<path d="M12 3.5s6 6.4 6 10.6a6 6 0 0 1-12 0C6 9.9 12 3.5 12 3.5z"/>',
  feed: '<rect x="4" y="7" width="16" height="11" rx="2"/><path d="M9.5 7v11M14.5 7v11"/>',
  milk: '<path d="M8.5 3.5h7M9 3.5v3l-2.2 3.3a3 3 0 0 0-.5 1.7v7.5a1.5 1.5 0 0 0 1.5 1.5h8.4a1.5 1.5 0 0 0 1.5-1.5V11.5a3 3 0 0 0-.5-1.7L15 6.5v-3"/><path d="M6.4 13h11.2"/>',
  build: '<path d="M3.5 20.5h17"/><path d="M5.5 20.5V10l6.5-5 6.5 5v10.5"/><path d="M10 20.5v-5h4v5"/>',
  tag: '<path d="M3.5 12.4V5c0-.8.7-1.5 1.5-1.5h7.4l8.1 8.1c.6.6.6 1.5 0 2.1l-7.4 7.4c-.6.6-1.5.6-2.1 0z"/><circle cx="8.2" cy="8.2" r="1.6"/>',
  camel: '<path d="M3 8.5c0-1 .8-1.6 1.7-1.6h.9c.9 0 1.5.7 1.4 1.6l-.2 1.2c-.1.8.2 1.5.8 2 .5.4 1.1.4 1.6 0 .5-.5.9-1 1.1-1.6.9-1.7 2.5-2.8 4.4-2.7 1.1.1 2.1.8 2.7 1.8.5.8 1.1 1.3 2 1.6 1.1.4 1.9 1.5 1.9 2.8V15c0 .6-.4 1.2-.9 1.5V20"/><path d="M6.4 12.2V20M9.5 15.5V20M15 15.5V20"/>',
  fence: '<path d="M4 20V7l2-2 2 2v13M16 20V7l2-2 2 2v13M8 10h8M8 15h8"/>',
  tank: '<rect x="6" y="4" width="12" height="11" rx="3"/><path d="M8 15v5M16 15v5M6 9h12"/>',
  shed: '<path d="M3 11 12 5l9 6"/><path d="M5 10v10h14V10"/><path d="M9 20v-5h6v5"/>',
  caravan: '<rect x="3" y="7" width="15" height="9" rx="2"/><path d="M18 13h3M6 16v2M7 10h3v3H7zM12 10h3"/>',
  room: '<path d="M4 20V9l8-5 8 5v11z"/><path d="M9 20v-6h6v6M8 11h2M14 11h2"/>',
  tent: '<path d="M2.5 18 8 8h8l5.5 10z"/><path d="M8 8l-2 10M16 8l2 10M12 8v10"/>',
  back: '<path d="M9 6l6 6-6 6"/>',
};
const nav = `<div class="nav"><button class="back">${ic(P.back)}رجوع</button></div>`;
const app = (k, n, extra = '') => `<div class="app" data-go="x" role="button" tabindex="0">${extra}<span class="ic">${ic(P[k])}</span><span>${n}</span></div>`;
const act = (t, on = true) => `<span class="act"><button class="btn ${on ? 'pri' : ''}" ${on ? '' : 'disabled'}>${t}</button></span>`;
const SCREENS = {
  home: `<div class="body"><div class="hs"><div class="datebar"><span>الخميس 1 أكتوبر</span><span class="sep"> · </span><span>سهيل</span></div>
    <div class="widgets">
      <div class="wg"><small>الرصيد</small><div class="big2"><b class="fit">20,000</b></div><div class="ln ink2">ريال</div><div class="ln"><span class="pos">دخل اليوم 27</span></div></div>
      <div class="wg"><small>الحلال</small><div class="big2"><b class="fit">2</b></div><div class="ln ink2">ناقة وحوارها</div><div class="ln ink2">قيمته 9,500 ريال</div></div>
    </div>
    <div class="apps">${app('water', 'الوايت')}${app('feed', 'العلف')}${app('milk', 'الحليب')}${app('build', 'العزبة')}${app('tag', 'الحراج')}</div></div></div>`,
  milk: `<div class="body">${nav}<div class="title">الحليب</div>
    <div class="tank"><small>حليب اليوم</small><div class="v"><b class="fit">5.4</b><span>لتر</span></div>
      <div class="ln">بعت 2.7 لتر بـ 27 ريال، وخليت لحوارها 2.7 لتر</div>
      <div class="ln ink2">دخل الحليب هالشهر 810 ريال</div></div>
    <div class="sec">الحلايب</div>
    <div class="group"><div class="row"><span class="lead">${ic(P.camel)}</span><b>الهيفاء</b><span class="amt">5.4 لتر</span><small>مرضع من 4 شهور · حوارها مزعل</small></div></div>
    <div class="sec">كم تخلي للحوار</div>
    <div class="seg"><span>كله</span><span class="on">النص</span><span>الربع</span></div>
    <div class="cmp"><span><b>0 ريال</b>باليوم<br>يكبر أحسن</span><span><b>27 ريال</b>باليوم<br>يكبر عادي</span><span><b>41 ريال</b>باليوم<br>يكبر أبطأ</span></div>
    <div class="note">المشتري يمر كل يوم وياخذ الحليب، اللتر بـ 10 ريال. الحوار يرضع لين يكمل سنة، وأول 3 شهور يبي حليب أمه كله.</div></div>`,
  build: `<div class="body">${nav}<div class="title">العزبة</div>
    <div class="tank"><small>عزبتك</small>
      <div class="kind"><span>الحوش</span><span class="d">يشيل 6 روس · عندك 2</span></div>
      <div class="kind"><span>الخزان</span><span class="d">6,000 لتر</span></div>
      <div class="kind"><span>مظلة العلف</span><span class="d">1,000 كجم</span></div>
      <div class="kind"><span>الرعاية</span><span class="d">أنت ترعاها لين 10 روس</span></div></div>
    <div class="sec">ابنِ ووسّع</div>
    <div class="group">
      <div class="row"><span class="lead">${ic(P.fence)}</span><b>شبك ثاني</b>${act('ابنه')}<small>يشيل 10 روس زيادة · 12,000 ريال</small></div>
      <div class="row"><span class="lead">${ic(P.tank)}</span><b>خزان 30 طن</b>${act('ابنه')}<small>يشيل وايت 19 طن · 14,110 ريال</small></div>
      <div class="row"><span class="lead">${ic(P.shed)}</span><b>مستودع علف</b>${act('ابنه')}<small>يشيل 10 طن علف · 18,000 ريال</small></div>
      <div class="row"><span class="lead">${ic(P.caravan)}</span><b>كرفان الراعي</b>${act('ابنه', false)}<small>لازم قبل الراعي · 25,000 ريال · رصيدك ما يكفي</small></div>
      <div class="row"><span class="lead">${ic(P.tent)}</span><b>بيت الشعر</b>${act('ابنه')}<small>للضيوف والقهوة · 15,000 ريال</small></div>
      <div class="row"><span class="lead">${ic(P.room)}</span><b>غرفة العزبة</b>${act('ابنه', false)}<small>جلسة ومكيفات · 60,000 ريال · رصيدك ما يكفي</small></div>
    </div>
    <div class="note">اللي تبنيه يخلص بعد 3 أيام ويطلع مكانه في العزبة.</div></div>`,
};
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  await p.goto('http://127.0.0.1:8765/index.html');
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 300000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(400);
  for (const [k, html] of Object.entries(SCREENS)) {
    await p.evaluate(([k, html]) => {
      const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
      scr.classList.toggle('home', k === 'home');
      scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1 ')}<div class="hb"></div>`;
      const st = document.createElement('style'); st.textContent = '.row .amt{grid-row:span 2;font:600 14px/1 "Alexandria",sans-serif}'; scr.appendChild(st);
    }, [k, html]);
    await p.waitForTimeout(300);
    await p.screenshot({ path: `mock_${k}.png`, timeout: 180000 });
    console.log(k, await p.evaluate(() => { const bd = R().querySelector('.body'); return [bd.scrollHeight, bd.clientHeight]; }));
  }
  await b.close();
})();
