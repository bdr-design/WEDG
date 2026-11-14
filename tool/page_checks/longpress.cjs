// A long press selects nothing and calls nothing out, on every surface of the 3D prototype (design/prototype3d), and
// the long press that enlarges the small phone still works. (The owner, 14 Nov 2026: a long press on his iPhone
// selected the screen.)
//
// Chromium with touch emulation, the owner's screen (956 x 440). Chromium is not iOS: a touch held here comes as a
// press and a click, not iOS's long-press gesture, so what is checked is what both engines read: for each surface,
//   1. a touch held 0.9 s leaves no selection (the page's and the phone's shadow root's) and no selectstart,
//      contextmenu or dragstart whose default went through;
//   2. those three events dispatched on the surface itself are all cancelled;
//   3. the surface computes user-select: none (WebKit's long-press selection, its magnifier and its callout go by it
//      and by -webkit-touch-callout, which Chromium does not compute: that one is checked in the style sheets).
// And a text field added to the page keeps its selection and its events.
//
// Run: build the page (THREE_DIR=<three@0.170.0> python3 tool/proto_app/assemble.py), serve it
// (python3 -m http.server PORT --bind 127.0.0.1 -d tool/proto_app/assets/web), then
//   PORT=<port> NODE_PATH=$(npm root -g) node tool/page_checks/longpress.cjs
// Exit code 1 on any failure.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8940;
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };

(async () => {
  // the style sheets: -webkit-touch-callout: none for every element, in the page and in the phone's shadow tree
  const proto = path.join(__dirname, '..', '..', 'design', 'prototype3d');
  const css = { page: fs.readFileSync(path.join(proto, 'farm.html'), 'utf8'), phone: fs.readFileSync(path.join(proto, 'phone.js'), 'utf8') };
  const fails = [];
  for (const [k, s] of Object.entries(css)) if (!/\*, \*::before, \*::after \{[^}]*-webkit-touch-callout: none/.test(s)) fails.push(`${k}: no -webkit-touch-callout: none for every element`);

  const b = await chromium.launch(LAUNCH);
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 1, hasTouch: true, isMobile: true });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => fails.push('page error: ' + e.message));
  await p.goto(`http://127.0.0.1:${PORT}/index.html#fps`);
  await p.waitForFunction(() => document.getElementById('status').hidden && window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  const cdp = await ctx.newCDPSession(p);
  await p.evaluate(() => {
    window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot;
    window.__ev = [];
    // on the window, the last stop of a composed event's way; selectstart stays in the shadow tree: watched on its root
    for (const type of ['selectstart', 'contextmenu', 'dragstart']) addEventListener(type, (e) => window.__ev.push({ type, through: !e.defaultPrevented }));
    R().addEventListener('selectstart', (e) => window.__ev.push({ type: 'selectstart (phone)', through: !e.defaultPrevented }));
    window.__find = (sel, shadow) => (shadow ? R() : document).querySelector(sel);
  });
  const held = async (pt, ms = 900) => {
    await p.evaluate(() => { window.__ev = []; document.getSelection().removeAllRanges(); R().getSelection?.()?.removeAllRanges(); });
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [pt] });
    await p.waitForTimeout(ms);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await p.waitForTimeout(250);
    return p.evaluate(() => {
      const s = document.getSelection(), ss = R().getSelection ? R().getSelection() : null;
      return { sel: s.toString() + (ss ? ss.toString() : ''), type: s.type, through: window.__ev.filter((e) => e.through).map((e) => e.type) };
    });
  };
  // the three events dispatched on the element; and its user-select
  const direct = (sel, shadow) => p.evaluate(([sel, shadow]) => {
    const e = window.__find(sel, shadow); if (!e) return null;
    const out = {};
    out.selectstart = !e.dispatchEvent(new Event('selectstart', { bubbles: true, cancelable: true }));
    out.contextmenu = !e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, composed: true }));
    out.dragstart = !e.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, composed: true }));
    out.userSelect = getComputedStyle(e).userSelect || getComputedStyle(e).webkitUserSelect;
    return out;
  }, [sel, shadow]);
  const centre = (sel, shadow) => p.evaluate(([sel, shadow]) => { const e = window.__find(sel, shadow); if (!e) return null; const r = e.getBoundingClientRect(); return r.width ? { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) } : null; }, [sel, shadow]);
  const rows = [];
  async function surface(name, sel, shadow = false, pt = null) {
    const at = pt || (await centre(sel, shadow));
    if (!at) { fails.push(`${name}: not found (${sel})`); return; }
    const d = sel ? await direct(sel, shadow) : null, h = await held(at);      // (the events first: a held touch can also click, and change the screen)
    const bad = [];
    if (h.sel || h.type === 'Range' || h.type === 'Caret') bad.push(`selection ${h.type} "${h.sel}"`);
    if (h.through.length) bad.push('went through: ' + h.through.join(', '));
    if (d) { for (const k of ['selectstart', 'contextmenu', 'dragstart']) if (!d[k]) bad.push(k + ' not cancelled'); if (d.userSelect !== 'none') bad.push('user-select ' + d.userSelect); }
    rows.push(`${bad.length ? 'FAIL' : 'ok  '}  ${name}${bad.length ? ': ' + bad.join('; ') : ''}`);
    if (bad.length) fails.push(`${name}: ${bad.join('; ')}`);
  }
  const home = () => p.evaluate(async () => { for (let i = 0; i < 4; i++) { const b = R().querySelector('.back'); if (!b) break; b.click(); await new Promise((r) => setTimeout(r, 450)); } });

  await surface('the map (canvas)', '#stage canvas');
  await surface('a map button', '#phone-btn');
  await surface('a map button icon (svg)', '#phone-btn svg');
  await surface('the test meter', '#meter');
  // a place's card, from a pin
  const pin = await p.evaluate(() => { const e = [...document.querySelectorAll('#labels .lbl')].find((l) => { const r = l.getBoundingClientRect(); return r.width && r.x > 80 && r.x < 560 && r.y > 60 && r.y < 400; }); if (!e) return null; const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 15) }; });
  if (pin) { await p.touchscreen.tap(pin.x, pin.y); await p.waitForTimeout(800); }
  if (!(await p.evaluate(() => !document.getElementById('pop').hidden))) fails.push('no place card opened from a pin');
  else {
    await surface('a card: its title', '#pop h2');
    await surface('a card: its body', '#pop .body');
    await surface('a card: an icon (svg)', '#pop svg');
    await surface('a card: the Sadu band', '#pop .sadu');
    await p.evaluate(() => document.querySelector('#pop .x')?.click()); await p.waitForTimeout(400);
  }
  // the phone, small: a long press on it enlarges it (its own design), selecting nothing
  await p.evaluate(() => document.getElementById('phone-btn').click()); await p.waitForTimeout(600);
  const small = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: Math.round(r.right - r.width / 3), y: Math.round(r.bottom - r.height / 2) }; });
  await surface('the small phone (held: it enlarges)', null, false, small);
  const st = await p.evaluate(() => window.__phone.state);
  rows.push(`${st === 'big' ? 'ok  ' : 'FAIL'}  the long press enlarged the phone (${st})`);
  if (st !== 'big') { fails.push('the long press did not enlarge the phone: ' + st); await p.evaluate(() => window.__phone.enlarge()); }
  await p.waitForTimeout(500);
  // enlarged: its texts, icons, a photo (a held touch here also clicks, as Chromium has it: back home after each)
  await surface('the phone: the status bar', '.sbar .clk', true);
  await surface('the phone: the date', '.datebar', true);
  await surface('the phone: a widget', '.wg small', true); await home();
  await surface('the phone: an app name', '.app > span:last-child', true); await home();
  await surface('the phone: an app icon (svg)', '.app .ic svg', true); await home();
  await surface('the phone: the dim around it', null, false, { x: 60, y: 400 });
  if (await p.evaluate(() => window.__phone.state) !== 'big') await p.evaluate(() => window.__phone.enlarge());
  await p.evaluate(() => R().querySelector('[data-go="haraj"]').click()); await p.waitForTimeout(800);
  await surface('the phone: الحراج, a photo (img)', '.it .ph img', true);
  await home(); await p.evaluate(() => R().querySelector('[data-go="haraj"]').click()); await p.waitForTimeout(800);
  await surface('the phone: الحراج, a title', '.title', true);
  await surface('the phone: رجوع', '.back', true);
  await p.evaluate(() => window.__phone.close()); await p.waitForTimeout(400);
  // play, on foot: its buttons and the ground under the walk stick
  await p.waitForFunction(() => window.__play, null, { timeout: 300000 }).catch(() => {});      // (play comes with the car's model)
  await p.evaluate(() => document.getElementById('cam-play').click());
  await p.waitForFunction(() => { const u = document.querySelector('.play'); return u && !u.hidden; }, null, { timeout: 120000 }).catch(() => {});
  await p.waitForTimeout(500);
  await surface('play: the ground (walk stick)', null, false, { x: 200, y: 330 });
  await surface('play: a button', '.pl-tl [data-a="exit"]');      // (last: held, it also clicks, and play ends)
  // a text field keeps its selection and its events
  const field = await p.evaluate(() => {
    const i = document.createElement('input'); i.value = 'نص'; i.style.cssText = 'position:fixed;left:10px;top:10px;z-index:99'; document.getElementById('root').appendChild(i);
    const r = { userSelect: getComputedStyle(i).userSelect, selectstart: i.dispatchEvent(new Event('selectstart', { bubbles: true, cancelable: true })) };
    i.focus(); i.select(); r.selected = i.selectionEnd - i.selectionStart; i.remove(); return r;
  });
  const fieldOk = field.userSelect !== 'none' && field.selectstart && field.selected === 2;
  rows.push(`${fieldOk ? 'ok  ' : 'FAIL'}  a text field keeps its selection (${JSON.stringify(field)})`);
  if (!fieldOk) fails.push('a text field lost its selection: ' + JSON.stringify(field));
  // and inside the phone's shadow tree: focused, typed in, its text selected (the phone has no field today: one is
  // put in its screen for the check and taken out)
  await p.evaluate(() => { window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(600);
  await p.evaluate(() => { const i = document.createElement('input'); i.id = 'lp-field'; i.style.cssText = 'position:absolute;left:20px;top:60px;z-index:9;font-size:16px;width:200px'; R().querySelector('.scr').appendChild(i); });
  const fb = await centre('#lp-field', true);
  if (fb) await p.touchscreen.tap(fb.x, fb.y);
  await p.waitForTimeout(300);
  await p.keyboard.type('نص 12');
  const inPhone = await p.evaluate(() => {
    const i = R().querySelector('#lp-field');
    const r = { focused: R().activeElement === i, value: i.value, userSelect: getComputedStyle(i).userSelect, selectstart: i.dispatchEvent(new Event('selectstart', { bubbles: true, cancelable: true })) };
    i.select(); r.selected = i.selectionEnd - i.selectionStart; i.remove(); return r;
  });
  const phoneOk = inPhone.focused && inPhone.value === 'نص 12' && inPhone.userSelect !== 'none' && inPhone.selectstart && inPhone.selected === 5;
  rows.push(`${phoneOk ? 'ok  ' : 'FAIL'}  a text field in the phone is focused, typed in and selected (${JSON.stringify(inPhone)})`);
  if (!phoneOk) fails.push('a text field in the phone: ' + JSON.stringify(inPhone));
  await b.close();
  console.log(rows.join('\n'));
  if (fails.length) { console.log('\nFAILED:\n' + fails.join('\n')); process.exit(1); }
  console.log('\nall surfaces: nothing selected, nothing called out');
})();
