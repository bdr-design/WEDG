// ---------------------------------------------------------------- «نادي الصقور» and «تصريح الصيد» (task T18 part B: the
// approved design design/ui/phone_falcon.jpg, views 2-8 and 13-18, on the engine of part A). The engine's facts are
// G.falcons (falconFacts: his permits, gear, room, falcons, birds held, today's lots, the news) and its catalog
// (falconCatalogOf: asked once when either app first opens, kept: FC.cat). The phone works out none of the rules:
// what may be bought is the engine's `cannot`, a refusal's words are the engine's own lines (FC.cat.lines). Not built:
// the festival and the contests (views 9-12), partners, the air rifle (their views stay out).
// FC: the app's own state (the tab, the route and lot looked at, the ceiling set, the bird looked at, the gear order
// being made up, the word to say after an order).
const FC = { tab: 'auction', route: 'trapping', lot: null, upTo: null, bird: null, falcon: null, order: null, msg: null, cat: null, asking: false, trip: null };
const FC_SCREENS = new Set(['club', 'lots', 'lot', 'bird', 'hammer', 'train', 'permit', 'tripCard']);
const HF = () => (G && G.falcons) || null;
// the news read (what became of his birds and lots: G.falcons.news), kept on this device as المزاين's are, so the app's
// badge counts only what he has not opened the app since
const FSEEN = (() => { try { return JSON.parse(localStorage.getItem('marah.phone.falconSeen') || '[]'); } catch { return []; } })();
const saveFSeen = () => { try { localStorage.setItem('marah.phone.falconSeen', JSON.stringify(FSEEN.slice(-200))); } catch { /* storage blocked: told again next time */ } };
const fcBadge = () => (HF() ? (HF().news || []).filter((x) => x.kind !== 'lotLost' && !FSEEN.includes(x.key)).length : 0);
// the bird's picture: the saker is task T11's render (awaiting the owner's approval, cut out); the peregrine is not
// built yet, a flat STAND-IN as the design has it (dark helmet and moustache, barred breast)
const PERE = '<svg viewBox="0 0 60 60" aria-hidden="true"><path d="M22 58 C18 44 20 30 28 22 C32 16 40 15 44 20 C48 26 47 40 42 58 Z" fill="#5d6670"/><path d="M28 30 C33 34 39 34 44 30 L44 56 L24 56 Z" fill="#e9e1d2"/><path d="M27 38 h16 M26 44 h18 M25 50 h19" stroke="#59606a" stroke-width="1.6" stroke-dasharray="2 2"/><path d="M29 22 C28 12 34 7 40 8 C46 9 48 15 45 22 Z" fill="#2f3338"/><path d="M45 14 l6 2 -5 3" fill="#e9c84a"/><circle cx="41" cy="14" r="2.2" fill="#111"/><path d="M38 16 c1 4 0 7 -2 9" stroke="#1d2024" stroke-width="3" fill="none"/></svg>';
const birdPic = (species) => `<span class="ph fb">${species === 'saker' || species === 'حر' ? '<img src="phone/thumb_saker.png" alt="" draggable="false">' : PERE}</span>`;
const SPECIES_SHORT = { 'شاهين بحري': 'شاهين', 'حر': 'حر', 'شاهين جبلي': 'شاهين جبلي', 'وكري': 'وكري' };
const GROUND_OF = (name) => (FC.cat ? FC.cat.grounds.find((g) => g.name === name) : null);
// a date in the season's own year: [month, day]
const md = ([m, d]) => `${d} ${MONTH[m - 1]}`;
const fdayShort = (day) => dShortAt(day);
// the engine's words for a refusal of the hunting season (its catalog's lines), or the phone's own for money
function fcRefusal(r, command) {
  const code = r.error?.code, p = r.error?.params || {};
  if (code === 'insufficientFunds') return `رصيدك ما يكفي: تبي ${n0(p.needed ?? 0)} ريال من رصيدك.`;
  if (code === 'inDebt') return `عليك دين ${n0(-G.cash)} ريال: الصقور وعدتها نقد من رصيدك بس.`;
  if (code !== 'huntRefused') return command.type === 'buildFacility' ? refusal(r, command) : 'جرّب مرة ثانية.';
  const L = FC.cat ? FC.cat.lines.refusals : {};
  const reason = p.reason;
  if (reason === 'routeClosed') return L[`routeClosed.${p.route}`] || L.routeClosed || 'جرّب مرة ثانية.';
  if (reason === 'gearFull' && p.room) return `تقدر تطلب ${p.room} بس`;      // (the engine's line with its figure)
  return L[p.kind === 'trapping' ? `${reason}.trapping` : p.lure === 'birdNet' ? `${reason}.birdNet` : reason] || L[reason] || 'جرّب مرة ثانية.';
}
const fcNav = (to = '') => nav('', to);
const fcMsg = () => (FC.msg ? `<div class="msgc${FC.msg.good ? ' good' : ''}"><span class="lead">${svg(FC.msg.good ? 'check' : 'talk')}</span><b>${FC.msg.title}</b><small>${FC.msg.line}</small></div>` : '');
const fcSeg = (on) => `<div class="seg" style="grid-template-columns:repeat(3,1fr)" role="tablist">${[['auction', 'المزاد'], ['mine', 'صقوري'], ['trap', 'الطرح']].map(([k, t]) => `<span data-act="fcTab" data-p="${k}" role="tab" tabindex="0" aria-selected="${k === on}"${k === on ? ' class="on"' : ''}>${t}</span>`).join('')}</div>`;
const fcRow = (icon, name, line, right = '', cls = '', attrs = '') => `<div class="row${cls ? ' ' + cls : ''}"${attrs}><span class="lead">${svg(icon)}</span><b>${name}</b>${right ? `<span class="qty${/^<span/.test(right) ? '' : ''}">${right}</span>` : ''}<small>${line}</small></div>`;
const fcRow2 = (icon, name, line, cls = '') => `<div class="row two${cls ? ' ' + cls : ''}"><span class="lead">${svg(icon)}</span><b>${name}</b><small>${line}</small></div>`;
const routeOf = (k) => (FC.cat ? FC.cat.routes.find((r) => r.route === k) : null);
const isOpen = (k) => !!HF() && HF().open.includes(k);
const howCame = (f) => (f.how === 'trapped' ? `طرحته ب${esc(f.ground || '')} ${fdayShort(f.on)}${f.keep ? ' وخليته لك' : ''}` : `اشتريته من ${esc(f.route || '')} ${fdayShort(f.on)}${f.price ? ` بـ ${n0(f.price)}` : ''}`);
// الدعو's four weeks (the design's view 8) by the engine's days done (dauDays of dauNeeded)
const DAU = [['يرضى بالبرقع والدس', 'الأسبوع الأول', 'check'], ['ياكل على يدك', 'الأسبوع الثاني', 'check'], ['يجي للملواح من قريب', 'الأسبوع الثالث', 'dot'], ['يجي للملواح من بعيد', 'الأسبوع الرابع', 'lure']];
const dauWord = (f) => (f.ready ? 'جاهز للمقناص' : `الدعو ${DAU[Math.min(3, Math.floor(f.dauDays / 7))][1]}`);
const takenWord = (f) => { const t = Object.entries(f.taken || {}); return t.length ? `صاد ${t.map(([q, n]) => `${q} ${count(n, 'time')}`).join(' و')}` : f.flights ? `طار ${count(f.flights, 'time')} وما صاد` : ''; };

// view 2: the auctions told apart, each route in its month (and his birds held, the news)
function clubAuction() {
  const H = HF(), C = FC.cat;
  const tr = routeOf('trapping'), open = isOpen('trapping');
  const news = (H.news || []).filter((x) => (x.kind === 'sold' || x.kind === 'freedAtClose') && G.today - x.day <= 7);
  const newsCards = news.map((x) => x.kind === 'sold'
    ? `<div class="msgc good" data-go="hammer" data-k="${esc(x.key)}" role="button" tabindex="0"><span class="lead">${svg('gavel')}</span><b>رسى المزاد على ${esc(x.name)}</b><small>بـ ${n0(x.price)} ريال، نزلت برصيدك كاملة · ${fdayShort(x.day)}</small></div>`
    : `<div class="msgc"><span class="lead">${svg('net')}</span><b>${esc(x.name)} انطلق</b><small>${esc(C.lines.release.freedAtClose)} · ${fdayShort(x.day)}</small></div>`).join('');
  const held = (H.held || []).map((f) => `<div class="row r3" data-go="bird" data-id="${esc(f.id)}" role="button" tabindex="0"><span class="lead now">${svg('net')}</span><b>${esc(f.name)} · فرخ ${esc(f.speciesName)}</b><span class="chev">${svg('chev')}</span><small>${f.entered ? 'بمزاد الليلة، ويرسى الليلة' : `طرحته ب${esc(f.ground || '')} ${fdayShort(f.on)} · اعرضه أو خله لك`}</small></div>`).join('');
  // a route's month: open now, or when it opens (the first open one «الحين», as the design has it)
  let first = true;
  const when = (r) => {
    if (isOpen(r.route)) { const w = first ? 'الحين' : `لين ${md(r.to)}`; first = false; return w; }
    return r.from[0] === r.to[0] ? MONTH[r.from[0] - 1] : `من ${md(r.from)}`;
  };
  const LINE = { trapping: 'فرخ شاهين بحري · من حوالي 50,000', exhibition: 'حر مستورد، وأسعاره عالية', breeders: 'ملهم · حر فرخ إنتاج مزارع' };
  const ICON = { trapping: 'gavel', exhibition: 'star', breeders: 'falcon' };
  const order = ['trapping', 'exhibition', 'breeders'].map(routeOf).filter(Boolean);
  const rows = order.map((r) => { const w = when(r); return `<div class="row r3"${isOpen(r.route) ? ` data-go="lots" data-k="${r.route}" role="button" tabindex="0" aria-label="${r.name}، طيور اليوم"` : ''}><span class="lead">${svg(ICON[r.route])}</span><b>${r.name}</b><span class="qty">${w}</span><small>${LINE[r.route]}</small></div>`; }).join('');
  return `${newsCards}
    ${held ? `<div class="sec">طيرك المطروح</div><div class="group">${held}</div>` : ''}
    <div class="open"${open ? ` data-go="lots" data-k="trapping" role="button" tabindex="0"` : ''}><span class="tag${open ? '' : ' amb'}">${open ? 'مفتوح الحين' : `يفتح ${md(tr.from)}`}</span><b>مزاد الطرح</b><small>ملهم · من ${md(tr.from)} لين ${md(tr.to)}، كل ليلة</small><small>فروخ الشاهين البحري المطروحة بالمملكة بس</small><small>تبيع فيه طيرك اللي طرحته، أو تشتري</small></div>
    <div class="sec">وصقرك له ثلاث طرق، كل وحدة بشهرها</div>
    <div class="group">${rows}</div>
    <div class="tank"><small>مزاد الطرح ما يقبل الحر ولا القرناس</small><div class="kind"><span>حرين مستوردة بالمعرض</span><span class="d">700,000 و100,000 ريال</span></div><div class="kind"><span>حر المزارع</span><span class="d">حوالي 19,000 ريال</span></div></div>`;
}
// view 7: his falcons, each with how it came, its passport, الدعو and its tracker
function clubMine() {
  const H = HF(), fs = H.falcons || [], hold = FC.cat.room.holds;
  const news = (H.news || []).filter((x) => (x.kind === 'steppedBack' || x.kind === 'found' || x.kind === 'gone') && G.today - x.day <= 7);
  const cards = news.map((x) => x.kind === 'steppedBack'
    ? `<div class="msgc"><span class="lead">${svg('alert')}</span><b>${esc(x.name)} رجع خطوة بالدعو</b><small>تركته أسبوعين بدون دعو · ${fdayShort(x.day)}</small></div>`
    : `<div class="msgc${x.kind === 'found' ? ' good' : ''}"><span class="lead">${svg(x.kind === 'found' ? 'check' : 'alert')}</span><b>${x.kind === 'found' ? `لقيت ${esc(x.name)}` : `${esc(x.name)} راح`}</b><small>${fdayShort(x.day)}</small></div>`).join('');
  const room = H.room;
  const where = room.built ? `بغرفة الصقور · ${fs.length ? count(fs.length, 'falcon') : 'ما فيها صقر'} من ${hold}` : room.building.length ? `غرفة الصقور تنبني، تخلص ${fdayShort(room.building[0])}` : 'ما عندك غرفة صقور: تنبنى من العزبة';
  const item = (f) => {
    const third = [f.passport ? 'جوازه باسمك' : '', f.where === 'lost' ? 'ضايع' : dauWord(f), f.tracker ? 'عليه جهاز تتبع' : '', takenWord(f)].filter(Boolean).join(' · ');
    return `<div class="it two" data-go="train" data-id="${esc(f.id)}" role="button" tabindex="0">${birdPic(f.species)}<b>${esc(f.name)} · ${esc(f.speciesName)} ${esc(f.age)}</b><small>${howCame(f)}</small><small>${third}</small></div>`;
  };
  const cared = room.wantCare.length === 0, moult = room.moult, home = fs.filter((f) => f.where === 'home').length;
  const care = !fs.length ? '' : moult ? `<button class="btn wide" disabled>بالمقيض ما فيه دعو</button>` : cared ? `<button class="btn wide" disabled>${home > 1 ? 'دعيتهم اليوم' : 'دعيته اليوم'}</button>` : `<button class="btn pri wide" data-act="care">${home > 1 ? 'ادعهم اليوم' : 'ادعه اليوم'}</button>`;
  // the trackers: one each falcon (the engine counts them by the falcons' order)
  const tr = H.gear.tracker, price = FC.cat.gear.find((g) => g.gear === 'tracker').price, can = tr[2] > 0 && G.cash >= price, key = 'tracker';
  const trackerRow = fs.length ? `<div class="group"><div class="row r3"><span class="lead">${svg('chip')}</span><b>جهاز التتبع</b>${tr[2] > 0 ? rushLike(key, 'data-act="tracker"', 'اطلب', `اطلب جهاز تتبع بـ ${n0(price)} ريال`, can) : ''}<small>${tr[0] ? `عندك ${tr[0]}` : 'ما عندك'}${tr[1] ? ` · ${tr[1]} توصل بكرة` : ''} · الجهاز ${n0(price)} لكل صقر${tr[2] > 0 && G.cash < price ? ' · رصيدك ما يكفي' : ''}</small>${HJ.sure === key ? `<small class="rush now">تدفع ${n0(price)} ريال، ويوصل بكرة</small>` : ''}</div></div>` : '';
  return `${cards}<div class="note" style="margin-top:-4px">${where}</div>
    ${fs.length ? `<div class="lst flat">${fs.map(item).join('')}</div>` : '<div class="note">ما عندك صقر للحين: تشتريه من المزاد بشهره، أو تطرحه وتخليه لك.</div>'}
    <div class="group">${fcRow2('rule', 'الطير اللي تطرحه وتخليه لك ما ينعرض للبيع بعدين', 'ما لقينا له طريق نظامي')}</div>
    ${trackerRow}${care}`;
}
// view 4: الطرح: the trapping permit, the gear he has, has coming and lacks, with prices, ordered here (cash, next day)
const GEAR_LINE = { pigeon: 'الحمامة', pigeonNet: 'الشبك على ظهر الحمامة', birdNet: 'لو الصقر ما يبي الحمام', binoculars: 'تشوف الصقر من بعيد', mobileTent: 'تلحق الصقور لأرض ثانية', supplies: 'ماء وأكل وبنزين' };
const GEAR_ICON = { pigeon: 'pigeon', pigeonNet: 'net', birdNet: 'net', binoculars: 'binoc', mobileTent: 'tent', supplies: 'box' };
const TRAP_GEAR = ['pigeon', 'pigeonNet', 'birdNet', 'binoculars', 'mobileTent', 'supplies'];
function gearOrder() {
  const H = HF();
  if (!FC.order) {      // (opened afresh: what he lacks, as the design's «اشتر الناقص»: six pigeons and ten days' supplies when he has none)
    FC.order = {};
    for (const k of TRAP_GEAR) { const [has, way, room] = H.gear[k]; FC.order[k] = has + way > 0 || room === 0 ? 0 : k === 'pigeon' ? Math.min(6, room) : k === 'supplies' ? Math.min(10, room) : 1; }
  }
  for (const k of TRAP_GEAR) FC.order[k] = Math.max(0, Math.min(FC.order[k], H.gear[k][2]));
  return FC.order;
}
function clubTrap() {
  const H = HF(), C = FC.cat, P = H.permits.find((p) => p.kind === 'trapping'), tr = routeOf('trapping');
  const permitLine = P.valid ? `ساري لين ${md(tr.to)} · بأراضي الطرح بس` : P.held != null ? `لموسم ${P.held}، يبدأ ${fdayShort(P.opens)}` : 'تشتريه من «تصريح الصيد»';
  const O = gearOrder(), price = (k) => C.gear.find((g) => g.gear === k).price;
  const total = TRAP_GEAR.reduce((n, k) => n + O[k] * price(k), 0), poor = G.cash < total;
  const row = (k) => {
    const [has, way, room] = H.gear[k], name = C.gear.find((g) => g.gear === k).name, p = price(k), many = k === 'pigeon' || k === 'supplies';
    const line = k === 'pigeon' ? `${has ? `عندك ${count(has, 'pigeon')} · ` : ''}الحمامة ${n0(p)}` : k === 'supplies' ? `${GEAR_LINE[k]} · ${n0(p)} لليوم` : `${GEAR_LINE[k]} · ${n0(p)}`;
    const said = k === 'supplies' && has ? `تكفي ${days(has)}` : has ? 'عندك' : '';
    const coming = way ? `<small class="rush">${many ? `${count(way, k === 'pigeon' ? 'pigeon' : 'day')} ` : ''}توصل بكرة</small>` : '';
    let right = '';
    if (many && room > 0) right = `<span class="stp"><button data-act="gearStep" data-k="${k}" data-d="-1" aria-label="${name} أقل" ${O[k] ? '' : 'disabled'}>${svg('minus')}</button><span class="n"><b>${O[k]}</b></span><button data-act="gearStep" data-k="${k}" data-d="1" aria-label="${name} أكثر" ${O[k] < room ? '' : 'disabled'}>${svg('plus')}</button></span>`;
    else if (!many && room > 0) right = `<span class="act"><span class="sw${O[k] ? ' on' : ''}" data-act="gearPick" data-k="${k}" role="switch" tabindex="0" aria-checked="${!!O[k]}" aria-label="اطلب ${name} بـ ${n0(p)} ريال"><i></i></span></span>`;
    else right = `<span class="qty ${has ? 'ok' : 'wait'}">${said || 'توصل بكرة'}</span>`;
    if (many && room > 0 && said) right = `<span class="qty ok" style="grid-row:1">${said}</span>${right}`;
    return `<div class="row ${many && room > 0 ? 'ord' : ''} ${!many && room > 0 ? 'r3' : ''}"><span class="lead">${svg(GEAR_ICON[k])}</span><b>${name}</b>${right}<small>${line}</small>${coming}</div>`;
  };
  const key = 'gearOrder', sure = HJ.sure === key, can = total > 0 && !poor && G.cash >= 0;
  const all = TRAP_GEAR.every((k) => { const [has, way, room] = H.gear[k]; return room === 0 || has + way > 0; });
  return `<div class="group">${fcRow('permit', 'تصريح الطرح', permitLine, P.valid ? '<span class="qty ok">عندك</span>' : '', '', P.valid ? '' : ' data-go="permit" role="button" tabindex="0"')}</div>
    <div class="sec">عدة الطاروح · السعر بالريال</div>
    <div class="group fg">${TRAP_GEAR.map(row).join('')}</div>
    <button class="btn ${!can ? '' : sure ? 'sure' : 'pri'} wide" data-act="gearOrder" ${can ? '' : 'disabled'}>${sure ? `اضغط مرة ثانية: تدفع ${n0(total)} ريال` : total ? `${all ? 'اطلب' : 'اشتر الناقص'} بـ ${n0(total)}` : 'اختار اللي تبيه'}</button>
    <div class="note">${poor && total ? `رصيدك ${n0(G.cash)} ريال ما يكفي. ` : ''}نقد من رصيدك، وتوصل عزبتك بكرة. والعدة تقرّبك من الطير وما تضمنه: كثير من المواسم تخلص بدون طير.</div>`;
}
function clubScreen() {
  const H = HF();
  if (!H || !FC.cat) return `<div class="body">${fcNav()}<div class="title">نادي الصقور</div>${waiting()}</div>`;
  const body = FC.tab === 'mine' ? clubMine() : FC.tab === 'trap' ? clubTrap() : clubAuction();
  return `<div class="body">${fcNav()}<div class="title">نادي الصقور</div>${fcSeg(FC.tab)}${fcMsg()}${errCard()}${body}</div>`;
}
// view 3: tonight's lots as the bidders see them (length, width, weight, where it was trapped); a lot gone says so
const lotTitle = (l) => `${esc(l.age)} ${esc(SPECIES_SHORT[l.species] || l.species)}`;
const daysAgo = (n) => (n <= 0 ? 'طرح اليوم' : n === 1 ? 'طرح أمس' : n === 2 ? 'طرح قبل يومين' : `طرح قبل ${days(n)}`);
const lotLost = (key) => (HF().news || []).find((x) => x.kind === 'lotLost' && x.lot === key) || null;
function lotsScreen() {
  const back = fcNav('club');
  const H = HF();
  if (!H || !FC.cat) return `<div class="body">${back}<div class="title">مزاد الليلة</div>${waiting()}</div>`;
  const r = routeOf(FC.route), trap = FC.route === 'trapping', lots = H.lots.filter((l) => l.route === FC.route);
  const item = (l) => {
    const lost = l.gone ? lotLost(l.lot) : null;
    const line = [l.ground ? esc(l.ground) : '', `${l.size} إنش`, `${n0(l.weight)} غرام`].filter(Boolean).join(' · ');
    const last = trap ? `${esc(l.species)} · ${daysAgo(l.trappedDaysAgo ?? 0)}` : `${esc(l.species)} ${esc(l.age)}`;
    const pr = l.gone ? `<span class="pr"><small class="${lost ? '' : 'pos'}">${lost ? `راح بـ ${n0(lost.price)}` : 'انباع لك'}</small></span>` : `<span class="pr"><span class="price num">${n0(l.opening)}</span><small>الافتتاح</small></span>`;
    return `<div class="it lot${l.gone ? ' off' : ''}"${l.gone ? '' : ` data-go="lot" data-id="${esc(l.lot)}" role="button" tabindex="0" aria-label="${lotTitle(l)}، ${line.replace(/<[^>]+>/g, '')}، الافتتاح ${n0(l.opening)} ريال"`}>${birdPic(l.species)}<b>${lotTitle(l)}</b><small>${line}</small>${pr}<small>${last}</small></div>`;
  };
  return `<div class="body">${back}<div class="title">${trap ? 'مزاد الليلة' : r.name}</div>
    <div class="note" style="margin-top:-4px">${trap ? 'مزاد الطرح · ملهم · كل طير بطوله وعرضه ووزنه ومكان طرحه' : `طيور اليوم · ${FC.route === 'exhibition' ? 'حر مستورد' : 'حر إنتاج مزارع'} · كل طير بطوله وعرضه ووزنه`}</div>
    ${lots.length ? `<div class="lst flat">${lots.map(item).join('')}</div>` : `<div class="note">${isOpen(FC.route) ? 'ما فيه طيور الليلة: يجي غيرها بكرة.' : esc(FC.cat.lines.refusals[`routeClosed.${FC.route}`])}</div>`}
    <div class="group">${fcRow2('eye', 'وش يسوي بالصيد ما ينعرف', 'ولا قيمته قبل المزاد: المزاد يقولها')}${trap ? fcRow2('rule', 'ما فيه رسوم', 'لا على البايع ولا على المشتري') : ''}</div></div>`;
}
// DESIGN FIRST (not in the approved pictures; drawn for the owner): buying a lot with his own ceiling («أعلى مبلغ
// تدفعه», the engine's BuyFalcon(lot, upTo)): the phone's stepper from the opening up to his balance, two taps, and the
// two outcomes (bought at the hammer; gone to another bidder at a told price)
function lotScreen() {
  const back = fcNav('lots');
  const H = HF();
  if (!H || !FC.cat) return `<div class="body">${back}<div class="title">مزاد الليلة</div>${waiting()}</div>`;
  const l = H.lots.find((x) => x.lot === FC.lot);
  if (!l) return `<div class="body">${back}<div class="title">مزاد الليلة</div>${fcMsg()}<div class="note" style="margin-top:6px">هالطير مو من طيور اليوم.</div></div>`;
  const trap = l.route === 'trapping', lost = l.gone ? lotLost(l.lot) : null;
  const facts = `<b>${lotTitle(l)} · ${esc(l.species)}</b><small>${[l.ground ? `${trap ? 'انطرح ب' : ''}${esc(l.ground)}` : '', trap ? daysAgo(l.trappedDaysAgo ?? 0) : ''].filter(Boolean).join(' · ') || esc(routeOf(l.route).name)}</small><small>${l.size} إنش · ${n0(l.weight)} غرام</small><small>الافتتاح ${n0(l.opening)} ريال</small>`;
  if (l.gone) return `<div class="body hjl">${back}<div class="title" style="font-size:22px">${trap ? 'مزاد الليلة' : esc(routeOf(l.route).name)}</div>${fcMsg()}
    <div class="it big off">${birdPic(l.species)}${facts}</div>
    <div class="note">${lost ? `راح لغيرك بـ ${n0(lost.price)} ريال.` : 'انباع لك، وهو بغرفة الصقور.'}</div></div>`;
  const k = stepOf(l.opening), top = Math.max(0, Math.floor(G.cash / k) * k);
  if (FC.upTo == null) FC.upTo = l.opening;
  FC.upTo = Math.max(l.opening, Math.min(FC.upTo, Math.max(l.opening, top)));
  const noRoom = H.room.cannot, poor = G.cash < l.opening;
  const can = !noRoom && !poor && G.cash >= 0, key = `buyFalcon:${l.lot}`, sure = HJ.sure === key;
  const why = noRoom ? alertCard(esc(FC.cat.lines.refusals[noRoom]), H.room.building.length ? `غرفتك تنبني، تخلص ${fdayShort(H.room.building[0])}.` : 'تنبنى من العزبة بـ 18,000 ريال، وتخلص بعد 3 أيام.') : '';
  const stepRow = `<div class="group"><div class="row ord full"><span class="lead">${svg('gavel')}</span><b>أعلى مبلغ تدفعه</b><span class="stp"><button data-act="upStep" data-d="-1" aria-label="أقل" ${can && FC.upTo > l.opening ? '' : 'disabled'}>${svg('minus')}</button><span class="n"><b>${n0(FC.upTo)}</b> <span>ريال</span></span><button data-act="upStep" data-d="1" aria-label="أكثر" ${can && FC.upTo + k <= G.cash ? '' : 'disabled'}>${svg('plus')}</button></span><small>${poor ? `رصيدك ${n0(G.cash)} ريال ما يوصل الافتتاح` : `من الافتتاح لين رصيدك ${n0(G.cash)} ريال`}</small></div></div>`;
  return `<div class="body hjl">${back}<div class="title" style="font-size:22px">${trap ? 'مزاد الليلة' : esc(routeOf(l.route).name)}</div>${fcMsg()}${errCard()}
    <div class="it big">${birdPic(l.species)}${facts}</div>
    ${why}${stepRow}
    <button class="btn ${!can ? '' : sure ? 'sure' : 'pri'} wide" data-act="buyFalcon" data-id="${esc(l.lot)}" ${can ? '' : 'disabled'}>${sure ? `اضغط مرة ثانية: تدفع لين ${n0(FC.upTo)}` : `زايد لين ${n0(FC.upTo)}`}</button>
    <div class="note">يرسى الليلة بسعره: لو وصله حدك تدفع سعر المطرقة بس، ولو ما وصله يروح لغيرك وتعرف بكم. ${trap ? 'وما فيه رسوم.' : ''}</div>
    <div class="note">نقد من رصيدك، والطير يجي بجوازه باسمك${trap ? ' وحجله الإلكتروني' : ''} لغرفة الصقور.</div></div>`;
}
// view 5, and DESIGN FIRST: a held bird's three ways: entered tonight (the hammer falls tonight, no fee), kept (the
// club's check and the passport: a free place in the room), and what the auction's close does to one neither sold nor kept
function birdScreen() {
  const back = fcNav('club');
  const H = HF();
  if (!H || !FC.cat) return `<div class="body">${back}<div class="title">اعرض طيرك</div>${waiting()}</div>`;
  const f = (H.held || []).find((x) => x.id === FC.bird);
  if (!f) return `<div class="body">${back}<div class="title" style="font-size:22px">اعرض طيرك</div>${fcMsg()}<div class="note" style="margin-top:6px">هالطير ما عاد عندك.</div></div>`;
  const open = isOpen('trapping'), tr = routeOf('trapping');
  const noRoom = H.room.cannot;
  const eKey = `enterBird:${f.id}`, kKey = `keepBird:${f.id}`;
  const enterBtn = f.entered ? '<button class="btn wide" disabled>دخل مزاد الليلة</button>' : `<button class="btn ${!open ? '' : HJ.sure === eKey ? 'sure' : 'pri'} wide" data-act="enterBird" data-id="${esc(f.id)}" ${open ? '' : 'disabled'}>${HJ.sure === eKey ? 'اضغط مرة ثانية ويدخل الليلة' : 'اعرضه الليلة'}</button>`;
  const keepBtn = `<button class="btn ${noRoom ? '' : HJ.sure === kKey ? 'sure' : 'ghost'} wide" data-act="keepBird" data-id="${esc(f.id)}" ${noRoom ? 'disabled' : ''}>${HJ.sure === kKey ? 'اضغط مرة ثانية ويصير لك' : 'خله لك'}</button>`;
  const keepWhy = noRoom ? `<div class="note">${esc(FC.cat.lines.refusals[noRoom])}${noRoom === 'noRoom' ? (H.room.building.length ? `، وغرفتك تخلص ${fdayShort(H.room.building[0])}.` : '، وتنبنى من العزبة.') : '.'}</div>` : '';
  const left = open ? Math.max(0, H.permits.find((p) => p.kind === 'trapping').closes - G.today) : 0;
  return `<div class="body hjl">${back}<div class="title" style="font-size:22px">اعرض طيرك</div>${fcMsg()}${errCard()}
    <div class="it big">${birdPic(f.species)}<b>${esc(f.name)} · فرخ ${esc(f.speciesName)}</b><small>طرحته ب${esc(f.ground || '')} ${fdayShort(f.on)}</small><small>${f.size} إنش · ${n0(f.weight)} غرام</small><small>${H.room.built ? 'بالبرقع بالعزبة، لين تبيعه أو تخليه لك' : 'بالبرقع معك، لين تبيعه أو تخليه لك'}</small></div>
    <div class="group">${fcRow2('check', 'فريق النادي يفحصه ويوثّق الطرح', 'ويعطيك وثيقة تسجيل طرح')}${fcRow2('box', 'النقل والسكن لملهم عليهم', 'وما فيه رسوم على البيع')}</div>
    <div class="tank"><small>${f.entered ? 'دخل مزاد الليلة' : 'يدخل مزاد الليلة'}</small>
      <div class="kind"><span>يرسى</span><span class="d">الليلة، والسعر كامل برصيدك</span></div>
      <div class="kind"><span>تشاركه</span><span class="d">لحالك: السعر كله لك</span></div></div>
    ${enterBtn}${keepBtn}${keepWhy}
    <div class="note">المزايدين يشوفون طوله وعرضه ووزنه ومكان طرحه، وقيمته ما تنعرف إلا بالمزاد. واللي تخليه لك يصير صقرك وما ينعرض للبيع بعدين.</div>
    <div class="note">${open ? `لو قفل المزاد ${md(tr.to)}${left <= 0 ? '، الليلة،' : ''} وهو لا انباع ولا خليته لك، ينطلق.` : 'المزاد قفل: لو ما خليته لك ينطلق.'}</div></div>`;
}
// view 6: the hammer, as the engine tells it after the night (its price, in full); the bidders are not drawn: the
// engine has none (no bidding game)
function hammerScreen() {
  const back = fcNav('club');
  const H = HF();
  const x = H && (H.news || []).find((n) => n.key === FC.falcon);
  if (!x) return `<div class="body">${back}<div class="title">رسى المزاد</div>${H ? '' : waiting()}</div>`;
  return `<div class="body">${back}<div class="title">رسى المزاد</div>
    <div class="it big">${birdPic('passagePeregrine')}<b>${esc(x.name)}</b><small>رسى بـ ${n0(x.price)} ريال</small><small>نزلت برصيدك كاملة، بدون رسوم</small><small>الحجل الإلكتروني والجواز للمشتري</small></div>
    <div class="note">رسى ليلة ${fdayShort(x.day - 1)}. وسعر الطير يختلف كثير من ليلة لليلة.</div></div>`;
}
// view 8: الدعو by the engine's rule (the days since count; two weeks left steps back; none in the moult); releasing a
// kept trapped peregrine in its months
function trainScreen() {
  const back = fcNav('club');
  const H = HF();
  const f = H && (H.falcons || []).find((x) => x.id === FC.falcon);
  if (!f || !FC.cat) return `<div class="body">${back}<div class="title">الدعو</div>${H ? '<div class="note" style="margin-top:6px">هالصقر ما عاد عندك.</div>' : waiting()}</div>`;
  const wk = Math.floor(f.dauDays / 7), need = f.dauNeeded;
  const step = (i) => {
    const [name, when, icon] = DAU[i], done = f.dauDays >= (i + 1) * 7, now = !done && i === wk;
    return `<div class="row${now ? ' now' : done ? '' : ' next'}"><span class="lead">${svg(done ? 'check' : now ? 'dot' : icon)}</span><b>${name}</b><span class="qty ${done ? 'ok' : now ? 'now' : 'wait'}">${done ? 'تم' : now ? 'الحين' : 'بعدين'}</span><small>${when}${now ? ` · يوم ${f.dauDays - i * 7 + 1} من 7` : ''}</small></div>`;
  };
  const readyRow = `<div class="row${f.ready ? '' : ' next'}"><span class="lead">${svg(f.ready ? 'check' : 'falcon')}</span><b>جاهز للمقناص</b><span class="qty ${f.ready ? 'ok' : 'wait'}">${f.ready ? 'تم' : 'بعدين'}</span><small>بعد الدعو</small></div>`;
  const room = H.room, home = (H.falcons || []).filter((x) => x.where === 'home').length;
  const caredToday = !room.wantCare.includes(f.id);
  const care = f.where !== 'home' ? '' : room.moult ? '<button class="btn wide" disabled>بالمقيض ما فيه دعو</button>' : caredToday ? `<button class="btn wide" disabled>${home > 1 ? 'دعيتهم اليوم' : 'دعيته اليوم'}</button>` : `<button class="btn pri wide" data-act="care">${home > 1 ? 'ادعهم اليوم' : 'ادعه اليوم'}</button>`;
  const rel = FC.cat.release, rKey = `release:${f.id}`;
  const inMonths = (() => { const d = dateAt(G.today), m = d.getUTCMonth() + 1, day = d.getUTCDate(), a = rel[0] * 100 + rel[1], z = rel[2] * 100 + rel[3], v = m * 100 + day; return v >= a && v <= z; })();
  const release = f.keep && f.species === 'passagePeregrine' ? `<div class="sec">تطلقه للبر</div><div class="group"><div class="row r3"><span class="lead">${svg('falcon')}</span><b>تطلق ${esc(f.name)}</b>${rushLike(rKey, `data-act="release" data-id="${esc(f.id)}"`, 'اطلقه', `اطلق ${esc(f.name)}`, inMonths)}<small>من ${md([rel[0], rel[1]])} لين ${md([rel[2], rel[3]])} مع رجعة الشاهين للشمال، أو يبقى عندك</small>${HJ.sure === rKey ? '<small class="rush now">ينطلق للأبد وما يرجع</small>' : ''}</div></div>` : '';
  const lost = f.where === 'lost' ? `<div class="warn"><span class="lead">${svg('alert')}</span><b>${esc(f.name)} ضايع</b><small>${f.tracker ? 'عليه جهاز تتبع: غالبًا تلقاه.' : 'ما عليه جهاز تتبع: تدوره بعيونك.'}</small></div><button class="btn pri wide" data-act="search" data-id="${esc(f.id)}">دوّره</button>` : '';
  const back2 = f.stepsBackOn != null && !room.moult && !f.ready ? ` ولو ما دعيته يرجع خطوة ${fdayShort(f.stepsBackOn)}.` : f.stepsBackOn != null && !room.moult ? ` ولو ما دعيته يرجع أسبوع ${fdayShort(f.stepsBackOn)}.` : '';
  return `<div class="body">${back}<div class="title">الدعو · ${esc(f.name)}</div>${fcMsg()}${errCard()}
    <div class="note" style="margin-top:-4px">${f.ready ? `دعيته ${need} يوم، وهو جاهز للمقناص` : `صقر جديد يبي ${need} يوم دعو قبل أول طلعة · دعيته ${count(f.dauDays, 'day')}`}</div>
    ${lost}
    <div class="group">${[0, 1, 2, 3].map(step).join('')}${readyRow}</div>
    <div class="group">${fcRow('scale', 'الميزان', 'تزنه كل يوم قبل أكله', `${n0(f.weight)} غرام`)}</div>
    ${care}
    <div class="note">مرة باليوم لكل صقور الغرفة، وتنحسب لك الأيام اللي فاتت لين أسبوعين. ولو تركته أسبوعين يرجع أسبوع. وبالمقيض من مايو لين أغسطس ما فيه دعو.${back2}</div>
    ${release}</div>`;
}
// views 13-15: «تصريح الصيد»: the two permits (season, open or closed, held, the fee, two taps to buy, the refusal's
// words), where each is banned, what is released (the engine's four lines word for word), the fines in words
function permitScreen() {
  const back = fcNav();
  const H = HF();
  if (!H || !FC.cat) return `<div class="body">${back}<div class="title">تصريح الصيد</div>${waiting()}</div>`;
  const C = FC.cat, R = C.lines.release;
  const tank = (kind) => {
    const P = H.permits.find((p) => p.kind === kind), fee = C.permits.find((p) => p.kind === kind).fee, name = C.permits.find((p) => p.kind === kind).name;
    const state = P.valid ? 'ساري' : P.held != null ? 'عندك' : P.open ? 'ما عندك' : 'مسكّر';
    const key = `permit:${kind}`, sure = HJ.sure === key, can = !P.cannot && !P.valid && P.held == null;
    const why = P.cannot && P.cannot !== 'permitHeld' ? (C.lines.refusals[P.cannot] || (P.cannot === 'insufficientFunds' ? `رصيدك ما يكفي: ${n0(fee)} ريال` : P.cannot === 'inDebt' ? `عليك دين ${n0(-G.cash)} ريال` : '')) : '';
    const line = kind === 'hunting' ? `من ${fdayShort(P.opens)} لين ${fdayShort(P.closes)}، بالنهار بس` : `من ${fdayShort(P.opens)} لين ${fdayShort(P.closes)}، بأراضي الطرح بس`;
    const btn = P.valid || P.held != null ? '' : `<button class="btn ${!can ? '' : sure ? 'sure' : 'pri'} wide" style="margin-top:8px" data-act="permit" data-k="${kind}" ${can ? '' : 'disabled'}>${sure ? `اضغط مرة ثانية: تدفع ${n0(fee)} ريال` : `اشتره بـ ${n0(fee)} ريال`}</button>`;
    const kinds = kind === 'hunting'
      ? `<div class="kind"><span>فترة الخريف</span><span class="d">لين 30 نوفمبر</span></div><div class="kind"><span>فترة الشتاء</span><span class="d">من 1 ديسمبر</span></div>`
      : `<div class="kind"><span>الرسوم</span><span class="d">${n0(fee)} ريال</span></div>`;
    const held = P.held != null && !P.valid ? `<div class="ln" style="color:var(--acc)">لموسم ${P.held}، يبدأ ${fdayShort(P.opens)}</div>` : '';
    return `<div class="tank"><small>${name}</small><div class="v">${state}</div><div class="ln" style="margin-top:4px">${line}</div>${held}${kinds}${btn}${why ? `<div class="ln" style="color:var(--red);margin-top:4px">${esc(why)}</div>` : ''}</div>`;
  };
  return `<div class="body">${back}<div class="title">تصريح الصيد</div>${errCard()}${fcMsg()}
    ${tank('hunting')}${tank('trapping')}
    <div class="group">${fcRow2('falcon', 'المقناص بالصقر', 'الكروان بالبر، والحبارى بالمحازة المرخصة بس')}${fcRow2('net', 'الطرح', 'فرخ الشاهين البحري، بأرض طرح، بشبك على الحمام')}${fcRow2('user', 'شخصي', 'ما ينعطى لغيرك، وتشيله معك')}</div>
    <div class="sec">ممنوع الصيد فيه</div>
    <div class="group">${fcRow2('ban', 'المدن والقرى والمزارع', 'يعني عزبتك وحولها، والاستراحات')}${fcRow2('ban', 'المحميات والمشاريع الكبرى', 'والمحميات الملكية كلها')}${fcRow2('ban', 'الساحل', 'لين 20 كيلو داخل البر، إلا أرض طرح بموسمها')}</div>
    <div class="sec">بالطرح: لو جا بالشبك</div>
    <div class="group">${fcRow2('ban', 'الشاهين الجبلي', esc(R['mountainPeregrine.farkh']))}${fcRow2('ban', 'الوكري', esc(R['lanner.farkh']))}${fcRow2('falcon', 'الحر', esc(R['saker.farkh']))}${fcRow2('falcon', 'القرناس', esc(R['passagePeregrine.qarnas']))}${fcRow2('ban', 'بالليل وبالضو', 'ما فيه طرح')}</div>
    <div class="sec">الغرامات</div>
    <div class="group">${fcRow2('alert', 'صيد بدون تصريح', 'غرامته 10,000 ريال')}${fcRow2('alert', 'صيد بمكان أو وقت ممنوع', 'غرامته 5,000 ريال')}${fcRow2('alert', 'الشبك برا أرض الطرح', 'غرامته 100,000 ريال')}${fcRow2('alert', 'الصيد من سيارة تمشي', 'غرامته 100,000 ريال')}</div>
    <div class="note">والصيد نفسه ما ينباع: بيع الصيد ممنوع. اللي ينباع فرخ الشاهين البحري المطروح، بمزاد الطرح بس.</div></div>`;
}
// the calendar's stops in words, with الدعو's when he has a falcon at the farm (the engine's falconCare stop: a jump
// stops the morning a falcon would step back)
const stopsText = (camp = '') => STOPS_TEXT + (HF() && (HF().falcons || []).some((f) => f.where === 'home') ? ' · صقر بالعزبة بيرجع خطوة بالدعو' : '') + camp;
// views 16-17, DESIGN FIRST for its words: the card before leaving for a camp or an outing, the calendar's own card with
// the trip's lines (the engine's Trips.card: the ground and its road, the gear he has and lacks, the camp's supplies).
// Opened by the map's ground card (part C) through openTrip; the phone itself starts no trip: «اطلع» hands back to
// the caller that opened it
const hoursWord = (h) => { const n = Math.max(1, Math.round(h)); return n === 1 ? 'ساعة' : n === 2 ? 'ساعتين' : `${n} ${n <= 10 ? 'ساعات' : 'ساعة'}`; };
function tripCardScreen() {
  const back = fcNav();
  const T = FC.trip && FC.trip.card;
  if (!G || !T || !FC.cat) return `<div class="body">${back}<div class="title">قبل ما تمشي</div>${waiting()}</div>`;
  const N = T.nights, t = T.to, trap = T.kind === 'trapping';
  const { block, guard, stopAt, supply, due, prep } = cardParts(t, Math.max(1, N));
  const what = T.oneDay ? `طلعة يوم ل${esc(T.groundName)}` : `${trap ? 'مخيم طرح' : 'رحلة مقناص'} ب${esc(T.groundName)} · لين ${dShortAt(t)}`;
  const road = `${n0(T.km)} كم، حوالي ${hoursWord(T.hours)} سواقة`;
  const has = T.has.map((x) => (x === 'الحمام' && T.pigeons ? count(T.pigeons, 'pigeon') : x));
  const camp = [
    `<div class="row two"><span class="lead">${svg(trap ? 'pigeon' : 'falcon')}</span><b>${has.length ? `عدتك: ${list(has)}` : 'ما عندك عدة'}</b><small>${T.lacks.length ? `ناقصك: ${T.lacks.join('، ')}` : 'عندك العدة كلها'}</small></div>`,
    !trap && T.falcons ? `<div class="row two"><span class="lead">${svg('falcon')}</span><b>${T.falcons.length ? `معك ${T.falcons.map(esc).join(' و')}` : 'ما عندك صقر جاهز'}</b><small>${T.falcons.length ? 'خلصوا الدعو' : 'الصقر يبي يخلص الدعو قبل أول طلعة'}</small></div>` : '',
    T.oneDay ? '' : `<div class="row two"><span class="lead${T.suppliesEnough ? '' : ' bad'}">${svg('box')}</span><b>مؤونة المخيم · ${T.supplyDays ? `تكفي ${days(T.supplyDays)}` : 'ما عندك'}</b><small>ماء وأكل وبنزين${T.suppliesEnough ? '' : `: ما تكفي ${count(N, 'night')}`}</small></div>`,
  ].join('');
  const refused = T.refused ? alertCard(esc(FC.cat.lines.refusals[T.refused] || 'ما تقدر تطلع الحين'), 'جهّز وارجع للبطاقة.') : '';
  const key = 'tripGo', sure = HJ.sure === key, can = !block && !T.refused && !!FC.trip.onGo;
  const goWord = T.oneDay ? 'اطلع' : trap ? 'اطلع للمخيم' : 'اطلع للرحلة';
  return `<div class="body">${back}<div class="title">قبل ما تمشي</div>${errCard()}
    <div class="span"><b>${what}</b><small>${T.oneDay ? 'ترجع نفس اليوم' : count(N, 'night')} · من ${ddAt(T.from)} · ${road}</small></div>
    ${guard}${refused}
    <div class="sec">${T.oneDay ? 'العزبة اليوم' : `يكفي ${count(N, 'night')}؟`}</div>
    <div class="group">
      ${supply}</div>
    ${stopAt < N ? `<div class="note">حتى لو عبّيت، ما يكفي الليالي كلها: يوقف حوالي ${dShortAt(G.today + Math.max(1, stopAt))} عشان تطلب، وبعدها تكمل.</div>` : ''}
    ${T.oneDay ? '' : `<div class="sec">اللي يجي بالطريق</div><div class="group">${due}</div>`}
    <div class="sec">${trap ? 'مخيمك' : 'رحلتك'}</div>
    <div class="group">${camp}</div>
    ${T.oneDay ? '' : `<div class="sec">تقدر تجهّز قبل</div>
    <div class="group">
      ${prep}</div>
    <div class="sec">يوقف ويرجع لك لو</div>
    <div class="stops">${stopsText(` · خلصت مؤونة المخيم · ${trap ? 'خلص موسم الطرح' : 'خلص موسم المقناص'} · جا يوم رجعتك`)}</div>
    <div class="note">${trap ? 'وكل يوم بالمخيم يرجع لك من الفجر لين الساعة 10، وبالمسا ساعة: الشغل بيدك.' : 'وكل يوم بالرحلة يرجع لك بعد الشروق بساعة: الطلعات بيدك.'} وتقدر تفك المخيم وترجع أي وقت.</div>`}
    ${FC.trip.onGo ? `<button class="btn ${!can ? '' : sure ? 'sure' : 'pri'} wide" data-act="tripGo" ${can ? '' : 'disabled'}>${sure ? 'اضغط مرة ثانية وتطلع' : goWord}</button>` : ''}
    <div class="note">التقويم يمشي لقدام بس: الأيام اللي تمضي ما ترجع.</div></div>`;
}
// the trip's lines in the calendar's summary, above its own (view 18: the engine's AwaySummary.extra by the trip's
// counters; the words FalconLines.summary)
function tripSumRows(m) {
  const x = m.extra || {};
  if (!Object.keys(x).length) return '';
  const rows = [];
  if (x.caught) rows.push(`<div class="row r2"><span class="lead">${svg('net')}</span><b>${x.caught === 1 ? 'طرحت فرخ شاهين بحري' : `طرحت ${count(x.caught, 'bird')} فروخ شاهين بحري`}</b><small>شوفه بنادي الصقور: تعرضه أو تخليه لك</small></div>`);
  if (x.released) rows.push(`<div class="row r2"><span class="lead">${svg('falcon')}</span><b>طلقت ${count(x.released, 'bird')}</b><small>المزاد ما يقبلها</small></div>`);
  if (x.stooped) rows.push(`<div class="row r2"><span class="lead">${svg('falcon')}</span><b>نزل على الطعم وما علق ${count(x.stooped, 'time')}</b><small>بالمخيم</small></div>`);
  if (x.flights) rows.push(`<div class="row r2"><span class="lead">${svg('falcon')}</span><b>طلعات الصقر ${n0(x.flights)}</b><small>${x.taken ? `صاد ${count(x.taken, 'time')}` : 'وما صاد شي'}</small></div>`);
  if (x.suppliesUsed && FC.cat) { const p = FC.cat.gear.find((g) => g.gear === 'supplies').price; rows.push(`<div class="row r2"><span class="lead">${svg('box')}</span><b>المؤونة والبنزين</b><small>${count(x.suppliesUsed, 'day')} مؤونة، بـ ${n0(x.suppliesUsed * p)} ريال</small></div>`); }
  if (!rows.length) rows.push(`<div class="row r2"><span class="lead">${svg('net')}</span><b>ما طاح شي بالشبك</b><small>${count(x.nights || 0, 'night')} بالمخيم</small></div>`);
  return `<div class="group">${rows.join('')}</div>`;
}
