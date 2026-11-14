// The page's start and its faces: when the first frame is drawn and the yard is in (the loading line hidden), whether
// any frame of the first 120 drew text before its face had come (a fallback shown), the layout shifts, and at the
// phone's first opening whether its faces are already in and how many times its figures were fitted again for a face
// that came late (document.fonts' loadingdone after it opened: each runs the phone's fitNumbers).
//   PORT=<port> RUNS=2 NODE_PATH=$(npm root -g) node tool/page_checks/fonts_start.cjs
const { chromium } = require('playwright');
const PORT = process.env.PORT || 8940, RUNS = +(process.env.RUNS || 2);
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
(async () => {
  const b = await chromium.launch(LAUNCH);
  const rows = [];
  for (let i = 0; i < RUNS; i++) {
    const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    await p.addInitScript(() => {
      const F = { frames: 0, fallbackFrames: 0, firstFrame: null, shifts: 0, shiftScore: 0, loadingdone: 0 };
      window.__F = F;
      const want = ['14px "Readex Pro"', '600 14px "Readex Pro"'];
      const step = (t) => {
        if (F.frames === 0) F.firstFrame = performance.now();
        F.frames++;
        // (text on screen before its face: the loading line's)
        if (document.getElementById('status') && !want.every((w) => document.fonts.check(w, 'تحميل'))) F.fallbackFrames++;
        if (F.frames < 120) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
      try { new PerformanceObserver((l) => { for (const e of l.getEntries()) { F.shifts++; F.shiftScore += e.value; } }).observe({ type: 'layout-shift', buffered: true }); } catch { /* (not Chromium) */ }
      document.fonts.addEventListener('loadingdone', () => F.loadingdone++);
    });
    const t0 = Date.now();
    await p.goto(`http://127.0.0.1:${PORT}/index.html`);
    await p.waitForFunction(() => document.getElementById('status').hidden, null, { timeout: 900000 });
    const yardIn = await p.evaluate(() => performance.now());
    await p.waitForTimeout(1500);
    const r = await p.evaluate(async () => {
      const F = window.__F, before = F.loadingdone;
      const phoneFaces = () => ['400 13px "IBM Plex Sans Arabic"', '600 13px "IBM Plex Sans Arabic"', '700 13px "IBM Plex Sans Arabic"', '700 21px Alexandria'].map((w) => document.fonts.check(w, 'ا1'));
      const atOpen = phoneFaces();
      window.__phone.toggle();
      await new Promise((res) => setTimeout(res, 3000));
      return { firstFrame: Math.round(F.firstFrame), fallbackFrames: F.fallbackFrames, frames: F.frames, shifts: F.shifts, shiftScore: +F.shiftScore.toFixed(4), phoneFacesInAtOpen: atOpen.filter(Boolean).length + '/4', refitsAfterOpen: F.loadingdone - before, phoneFacesAfter: phoneFaces().filter(Boolean).length + '/4' };
    });
    rows.push({ run: i + 1, yardIn: Math.round(yardIn), ...r, wall: Date.now() - t0 });
    console.log(JSON.stringify(rows[rows.length - 1]));
    await ctx.close();
  }
  await b.close();
})();
