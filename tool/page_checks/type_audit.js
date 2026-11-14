// The typography audit of what the 3D prototype shows (design/prototype3d): injected into the page, it reads one
// surface as drawn (the phone's screen in its shadow root, a place's card, the test meter, or any element) and counts
// what tool/page_checks/type_audit.cjs tabulates. Grown from the layout audit of 13 Nov (its clipped, ellipsis,
// outside and split checks). Use: await page.addScriptTag({ path }); await page.evaluate(() => window.__typeAudit('phone')).
// Argument: 'phone' (the phone's .scr), or a CSS selector in the page (e.g. '#pop', '#meter').
//
// What it counts, each with the text it found:
//  - split: a number and its word or unit on two lines (either order); prepNum: «بـ» or another preposition at a
//    line's end with its number on the next; prepEnd: a preposition or «و» alone at a line's end; widow: a block of
//    two lines or more whose last line is one word;
//  - clipped (overflow hidden, wider than its box), ellipsis (cut with …), outside (past the screen's sides);
//  - sizes: every text's size as drawn (its CSS size times the phone's scale), the smallest, and the screen's type
//    scale (size/weight/face, and how many texts use each);
//  - lineHeight: multi-line Arabic text whose line height is under 1.3 of its size (crowds the marks);
//  - digits: Arabic-Indic digits (٠-٩, ۰-۹) anywhere; noSep: 5 digits or more without a thousands separator;
//  - minus: a minus drawn to the right of its digits (in right-to-left text the hyphen-minus moves there unless the
//    number is isolated left to right); hyphenMinus: «-» used as a minus (U+2212 «−» is the sign);
//  - parens: a pair of parentheses drawn the wrong way round; dot: runs either side of « · » drawn out of order;
//  - spacing: letter-spacing on Arabic text (it breaks the joins);
//  - proportional: figures that are not tabular where the face and its settings draw 0 and 1 at different widths;
//  - contrast: text under 4.5:1 against its ground (3:1 for large text), WCAG 2.x, the ground composited from the
//    element's ancestors (an image ground is said, not guessed).
window.__typeAudit = function (where = 'phone') {
  const phoneRoot = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone'))?.shadowRoot;
  const scope = where === 'phone' ? phoneRoot().querySelector('.scr') : document.querySelector(where);
  if (!scope) return { error: 'not found: ' + where };
  const AR = /[؀-ۿ]/, DIGIT = /[0-9٠-٩۰-۹]/;
  const PREP = new Set(['بـ', 'ب', 'و', 'في', 'من', 'على', 'عن', 'مع', 'إلى', 'الى', 'لين', 'ل', 'بعد', 'قبل', 'كل', 'عند', 'حتى', 'أو', 'او', 'يا']);
  const dev = where === 'phone' ? phoneRoot().querySelector('.dev') : null;
  const scale = dev ? dev.getBoundingClientRect().height / dev.offsetHeight : 1;      // (not turned: the audit runs landscape)
  const sr = (dev ? phoneRoot().querySelector('.scr') : document.documentElement).getBoundingClientRect();
  const label = (e) => (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : e.tagName.toLowerCase()) + ': ' + (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 48);
  const out = { where, scale: +scale.toFixed(3), split: [], prepNum: [], prepEnd: [], widow: [], clipped: [], ellipsis: [], outside: [], sizes: {}, smallest: null, lineHeight: [], digits: [], noSep: [], minus: [], hyphenMinus: [], parens: [], dot: [], spacing: [], proportional: [], contrast: [], texts: 0 };
  const visible = (e) => { const cs = getComputedStyle(e); return cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity !== 0 && e.getClientRects().length > 0; };
  const directText = (e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.nodeValue.trim());
  const isBlock = (e) => !/^inline$/.test(getComputedStyle(e).display);
  const blockOf = (n) => { let e = n.parentElement; while (e && e !== scope && !isBlock(e)) e = e.parentElement; return e || scope; };
  const rectOf = (node, a, b) => { const r = document.createRange(); r.setStart(node, a); r.setEnd(node, b); return [...r.getClientRects()].filter((q) => q.width > 0.3); };

  // ---- each element with text of its own: clipping, size, face, line height, spacing, contrast
  const els = [scope, ...scope.querySelectorAll('*')].filter((e) => !e.closest('svg') && e.textContent.trim() && visible(e));
  const parseRGBA = (s) => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const v = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return { r: v[0], g: v[1], b: v[2], a: v.length > 3 ? v[3] : 1 }; };
  const over = (top, bot) => ({ r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1 });
  const lum = (c) => { const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  function ground(e) {
    const layers = [];
    for (let q = e; q; q = q.parentElement || (q.getRootNode() !== document ? q.getRootNode().host : null)) {
      const cs = getComputedStyle(q);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return { image: true, layers };
      const c = parseRGBA(cs.backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 0.999) break; }
    }
    let g = { r: 185, g: 138, b: 94, a: 1 };      // (nothing opaque under it: the canvas, taken as the sand, #b98a5e)
    for (let i = layers.length - 1; i >= 0; i--) g = over(layers[i], g);
    return { colour: g };
  }
  for (const e of els) {
    const cs = getComputedStyle(e);
    if ((cs.overflowX === 'hidden' || cs.overflow === 'hidden' || cs.overflowX === 'clip') && e.scrollWidth > e.clientWidth + 1) out.clipped.push(label(e));
    if (cs.textOverflow === 'ellipsis' && e.scrollWidth > e.clientWidth + 1) out.ellipsis.push(label(e));
    const r = e.getBoundingClientRect();
    if (r.width && (r.left < sr.left - 1 || r.right > sr.right + 1)) out.outside.push(label(e));
    if (!directText(e)) continue;
    out.texts++;
    const fs = parseFloat(cs.fontSize), eff = +(fs * scale).toFixed(2), face = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
    const key = `${+fs.toFixed(2)}px ${cs.fontWeight} ${face}`;
    out.sizes[key] = (out.sizes[key] || 0) + 1;
    if (!out.smallest || eff < out.smallest.px) out.smallest = { px: eff, css: fs, text: label(e) };
    const own = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.nodeValue).join(' ');
    if (AR.test(own) && cs.letterSpacing !== 'normal' && Math.abs(parseFloat(cs.letterSpacing)) > 0.01) out.spacing.push(`${label(e)} (${cs.letterSpacing})`);
    const col = parseRGBA(cs.color), g = ground(e);
    if (col && g.colour) {
      const c = over(col, g.colour), L1 = lum(c), L2 = lum(g.colour), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      const large = eff >= 24 || (eff >= 18.66 && +cs.fontWeight >= 700);
      if (ratio < (large ? 3 : 4.5)) out.contrast.push(`${label(e)} ${ratio.toFixed(2)}:1 at ${eff}px`);
    } else if (g.image) out.contrast.push(`${label(e)}: on an image (not measured)`);
  }
  // ---- figures: tabular or not, as each face and its settings draw them (a probe beside the text, removed)
  const seenFig = new Map();
  for (const e of els) {
    if (!directText(e) || !DIGIT.test([...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.nodeValue).join(''))) continue;
    const cs = getComputedStyle(e), k = `${cs.fontFamily}|${cs.fontWeight}|${cs.fontSize}|${cs.fontVariantNumeric}`;
    if (!seenFig.has(k)) {
      const mk = (t) => { const s = document.createElement('span'); s.textContent = t; s.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font:inherit;font-variant-numeric:inherit;letter-spacing:inherit'; e.appendChild(s); const w = s.getBoundingClientRect().width; s.remove(); return w; };
      const w1 = mk('1111111111'), w0 = mk('0000000000');
      seenFig.set(k, Math.abs(w1 - w0) < 0.5);
    }
    if (!seenFig.get(k)) out.proportional.push(`${label(e)} (${cs.fontFamily.split(',')[0]} ${cs.fontWeight}, ${cs.fontVariantNumeric})`);
  }
  // ---- the words as laid out: each block's lines (its text nodes' words, in their logical order)
  const blocks = new Map();
  const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode());) {
    const t = n.nodeValue; if (!t.trim() || !n.parentElement || n.parentElement.closest('svg') || !visible(n.parentElement)) continue;
    if (/[٠-٩۰-۹]/.test(t)) out.digits.push(t.trim().slice(0, 40));
    for (const m of t.matchAll(/(?<![\d,.])\d{5,}(?![\d,.])/g)) out.noSep.push(t.trim().slice(0, 40));
    for (const m of t.matchAll(/-(?=\d)/g)) out.hyphenMinus.push(t.trim().slice(0, 40));
    const rtl = getComputedStyle(n.parentElement).direction === 'rtl';
    // the minus beside its first digit
    for (const m of t.matchAll(/[-−](?=\d)/g)) {
      const a = rectOf(n, m.index, m.index + 1)[0], d = rectOf(n, m.index + 1, m.index + 2)[0];
      if (a && d && Math.abs(a.top - d.top) < 2 && a.left > d.left) out.minus.push(t.trim().slice(0, 40));
    }
    // parentheses and the middle dot, on one line, in right-to-left text
    if (rtl) {
      for (const m of t.matchAll(/\(([^()]*)\)/g)) {
        const o = rectOf(n, m.index, m.index + 1)[0], c = rectOf(n, m.index + m[0].length - 1, m.index + m[0].length)[0];
        if (o && c && Math.abs(o.top - c.top) < 2 && o.left < c.left) out.parens.push(m[0].slice(0, 40));
      }
      const parts = t.split(' · ');
      if (parts.length > 1) {
        let at = 0; const xs = [];
        for (const p of parts) { const rs = rectOf(n, at, at + p.length); if (rs.length) xs.push({ l: Math.min(...rs.map((q) => q.left)), top: rs[0].top }); at += p.length + 3; }
        for (let i = 1; i < xs.length; i++) if (Math.abs(xs[i].top - xs[i - 1].top) < 2 && xs[i].l > xs[i - 1].l) { out.dot.push(t.trim().slice(0, 48)); break; }
      }
    }
    const b = blockOf(n);
    if (!blocks.has(b)) blocks.set(b, []);
    const list = blocks.get(b);
    for (const m of t.matchAll(/[^ \n\t]+/g)) {
      const rs = rectOf(n, m.index, m.index + m[0].length);
      if (!rs.length) continue;
      list.push({ w: m[0], y: (rs[0].top + rs[0].bottom) / 2, h: rs[0].height });
    }
  }
  for (const [b, toks] of blocks) {
    if (toks.length < 2) continue;
    const lines = []; let cur = null;
    for (const tk of toks) { if (!cur || Math.abs(tk.y - cur.y) > tk.h * 0.5) { cur = { y: tk.y, w: [] }; lines.push(cur); } cur.w.push(tk.w); }
    // (a block's text in logical order: a line is a run of words at one height; an inline-block's words keep their own)
    if (lines.length < 2 || new Set(lines.map((l) => Math.round(l.y))).size < 2) continue;
    const whole = toks.map((x) => x.w).join(' ').slice(0, 60);
    for (let i = 0; i < lines.length - 1; i++) {
      const end = lines[i].w[lines[i].w.length - 1], next = lines[i + 1].w[0];
      if (lines[i + 1].y <= lines[i].y) continue;      // (not the next line down: another column of the same block)
      const endNum = /\d[\d,.]*$/.test(end), nextNum = /^[\d−-]/.test(next);
      if (endNum && AR.test(next[0])) out.split.push(`${end} | ${next}  (${whole})`);
      else if (nextNum && (PREP.has(end) || /بـ$/.test(end))) out.prepNum.push(`${end} | ${next}  (${whole})`);
      else if (nextNum && AR.test(end.slice(-1))) out.split.push(`${end} | ${next}  (${whole})`);
      else if (PREP.has(end)) out.prepEnd.push(`${end} |  (${whole})`);
    }
    const last = lines[lines.length - 1];
    // (words kept together by no-break spaces count one by one: «بـ 64 ريال» alone on a line is three words)
    if (last.w.join(' ').split(/[ \u00a0]+/).length === 1 && lines[lines.length - 2].y < last.y) out.widow.push(`${last.w[0]}  (${whole})`);
    // a line height that crowds Arabic's marks: under 1.3 of the size, on text that runs to two lines or more
    const bs = getComputedStyle(b), lh = bs.lineHeight === 'normal' ? null : parseFloat(bs.lineHeight);
    if (lh && AR.test(whole) && lh / parseFloat(bs.fontSize) < 1.3) out.lineHeight.push(`${label(b)} (${(lh / parseFloat(bs.fontSize)).toFixed(2)})`);
  }
  for (const k of Object.keys(out)) if (Array.isArray(out[k])) out[k] = [...new Set(out[k])];
  return out;
};
// the faces the page knows, with their state: loaded, loading, unloaded (not asked for yet) or error
window.__faces = () => [...document.fonts].map((f) => `${f.family.replace(/["']/g, '')} ${f.weight} ${f.status}${f.unicodeRange && f.unicodeRange !== 'U+0-10FFFF' ? ' [' + f.unicodeRange.slice(0, 14) + ']' : ''}`);
