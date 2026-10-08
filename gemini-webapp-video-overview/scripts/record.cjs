/* Record a real web app being used, on the narration's clock, to DIR/rec/*.webm.
 *
 *   node record.cjs DIR
 *
 * AUDIO IS THE MASTER CLOCK. Run the TTS step and retime.py first: they
 * measure every spoken line and write its true start and end into
 * narration.json. Every action here is scheduled against those numbers
 * ("L4.start+0.6"), so the pointer arrives as the word is spoken. No action
 * carries a hand-typed timestamp; change a word and everything re-times.
 *
 * Every click is a real Playwright click on the real app, and the drawn
 * pointer (cursor.js) glides to the target first, so a viewer sees the cause
 * before the effect. If the app breaks, the video breaks — the property worth
 * having in a video someone will show a customer.
 *
 * "setup" runs the same actions at full speed, before the clock starts — the
 * state a short video needs already in place. The recording covers it, so the
 * instant the clock starts is written to rec/offset.txt and build.sh cuts
 * everything before it. Without that cut every action lands late by the time
 * the page took to load (one take came out two seconds behind its words).
 *
 * Writes rec/final-state.json: what narration.json's "state" selectors showed
 * at each "snap" and at the end, so a take can be checked without watching it.
 * The schema of narration.json is in references/narration-format.md.
 */
const path = require('path');
const fs = require('fs');
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  console.error('playwright is not importable: set NODE_PATH, or `npm i -D playwright && npx playwright install chromium`');
  process.exit(1);
}

const DIR = path.resolve(process.argv[2] || '.');
const nar = JSON.parse(fs.readFileSync(path.join(DIR, 'narration.json'), 'utf8'));
const [W, H] = nar.size || [1280, 800];

/* "L4.start", "L4.end", "L4.start+0.8", or seconds -> seconds. */
function resolve(at) {
  if (typeof at === 'number') return at;
  if (/^-?\d+(\.\d+)?$/.test(String(at))) return Number(at);
  const m = /^L(\d+)\.(start|end)([+-][\d.]+)?$/.exec(at);
  if (!m) throw new Error(`cannot resolve time: ${at}`);
  const line = nar.lines.find((l) => l.id === Number(m[1]));
  if (!line) throw new Error(`no line ${m[1]}`);
  if (line.start === undefined) throw new Error('no timings in narration.json — run TTS, then retime.py');
  return line[m[2]] + (m[3] ? Number(m[3]) : 0);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const recDir = path.join(DIR, 'rec');
  const saved = {}, states = {};
  fs.rmSync(recDir, { recursive: true, force: true });
  fs.mkdirSync(recDir, { recursive: true });

  // "launch_args": some networks stall Chromium's HTTP/2 (every page load
  // timed out until --disable-http2), and some apps need a flag of their own.
  const browser = await chromium.launch({ args: nar.launch_args || [] });
  const context = await browser.newContext({
    viewport: { width: W, height: H },
    deviceScaleFactor: 1,
    acceptDownloads: true,
    colorScheme: nar.color_scheme || 'light',
    recordVideo: { dir: recDir, size: { width: W, height: H } },
  });
  await context.addInitScript(`window.__curConfig = ${JSON.stringify({
    accent: nar.accent || '#2563EB', outline: nar.outline || '#111827' })};`);
  await context.addInitScript({ path: path.join(__dirname, 'cursor.js') });
  // "block": URL globs to refuse — third-party trackers and chat widgets
  // that would otherwise count the recording as a visitor, or pop up mid-take.
  for (const pattern of nar.block || []) await context.route(pattern, (r) => r.abort());
  const page = await context.newPage();
  page.setDefaultNavigationTimeout(nar.goto_timeout_ms || 60000);
  const v0 = Date.now();                                 // the webm starts about here

  /* Where the drawn pointer was last. Every page load makes a new document
   * with a new pointer; put it back where it was, so it never vanishes after
   * a login or a link and never flies in from a corner. */
  let last = null;
  page.on('load', () => {
    if (last) page.evaluate(([x, y]) => window.__cur && window.__cur.place(x, y), last).catch(() => {});
  });

  /* Load a page and wait until it is really ready: "ready" is a selector that
   * only exists once the app has rendered what the video needs. A video that
   * starts on a spinner wastes its first line. */
  const open = async (url) => {
    await page.goto(url, { waitUntil: nar.wait_until || 'load' });
    if (nar.ready) await page.waitForSelector(nar.ready, { timeout: nar.ready_timeout_ms || 60000 });
    await sleep(nar.settle_ms ?? 800);
  };

  /* What the app shows: the text (or value, for a field) of each "state"
   * selector. */
  const readState = () => page.evaluate((sel) => {
    const out = {};
    for (const [k, s] of Object.entries(sel || {})) {
      const els = [...document.querySelectorAll(s)];
      const text = (e) => ('value' in e && e.tagName !== 'BUTTON' ? e.value : e.textContent)
        .replace(/\s+/g, ' ').trim();
      out[k] = els.length === 0 ? null : els.length === 1 ? text(els[0]) : els.map(text);
    }
    return out;
  }, nar.state);

  await open(nar.url);
  await page.evaluate(([x, y]) => window.__cur.place(x, y), nar.cursor_start || [Math.round(W * 0.2), Math.round(H * 0.6)]);

  const centre = async (sel) => {
    const loc = page.locator(sel).first();
    // Scroll first, or the pointer glides to where the target was before
    // Playwright scrolled it into view for the click.
    await loc.scrollIntoViewIfNeeded({ timeout: 5000 }).catch(() => {});
    const box = await loc.boundingBox();
    if (!box) throw new Error(`no box for ${sel} — hidden, or not on the page`);
    return { x: Math.round(box.x + box.width / 2), y: Math.round(box.y + box.height / 2) };
  };
  let fast = false;                                      // true during setup
  const glide = async (sel, ms = nar.glide_ms || 620) => {
    const { x, y } = await centre(sel);
    last = [x, y];
    if (fast) { await page.evaluate(([x, y]) => window.__cur.place(x, y), [x, y]); return; }
    await page.evaluate(([x, y, ms]) => window.__cur.move(x, y, ms), [x, y, ms]);
    await sleep(ms + 90);
  };
  const tap = async (after = 120) => {
    if (fast) return;
    await page.evaluate(() => window.__cur.tap());
    await sleep(after);
  };

  /* The vocabulary the timeline is written in. Anything that acts on an
   * element moves the drawn pointer to it first. */
  const ACTIONS = {
    async cursor(sel) { await glide(sel); },
    async hover(sel) { await glide(sel); await page.locator(sel).first().hover(); },
    async click(sel) { await glide(sel); await tap(); await page.locator(sel).first().click(); },
    async dblclick(sel) { await glide(sel); await tap(); await page.locator(sel).first().dblclick(); },

    /* A native <select> popup is drawn by the operating system and never
     * appears in the recording. Show the pointer reaching the menu, then set
     * it — rather than record a click that opens nothing visible. */
    async select(sel, value) {
      await glide(sel); await tap(200);
      await page.locator(sel).first().selectOption(value);
    },

    /* Types character by character: a field that fills instantly does not
     * read as typing. Selects all first, or a field that already holds a
     * value gets appended to. Tab at the end commits the field. */
    async type(sel, text, opts = {}) {
      await glide(sel); await tap();
      const loc = page.locator(sel).first();
      await loc.click();
      if (opts.clear !== false) await page.keyboard.press('ControlOrMeta+a');
      await loc.pressSequentially(String(text), { delay: fast ? 0 : (nar.type_delay_ms ?? 55) });
      if (opts.commit !== false) await page.keyboard.press(opts.commit || 'Tab');
    },

    async press(key) { await page.keyboard.press(key); },
    async focus(sel) { await page.locator(sel).first().focus(); },

    async ring(sel, ms) {
      const box = await page.locator(sel).first().boundingBox();
      if (!box) throw new Error(`no box for ${sel}`);
      await page.evaluate(([b, ms]) => window.__cur.ring(b, ms), [box, ms ?? 1600]);
    },

    /* Scroll by wheel at an element, as a person would. */
    async scroll(sel, dy) {
      await glide(sel);
      await page.locator(sel).first().hover();
      await page.mouse.wheel(0, dy);
    },
    /* Scroll a scrollable element to "top", "bottom" or a pixel offset. */
    async scrollTo(sel, where) {
      await page.locator(sel).first().evaluate((el, [where, behavior]) => el.scrollTo({
        top: where === 'bottom' ? el.scrollHeight : where === 'top' ? 0 : Number(where), behavior,
      }), [where, fast ? 'instant' : 'smooth']);
    },
    /* Scroll whatever holds sel until sel is at its top. */
    async reveal(sel) {
      await page.locator(sel).first().evaluate((el, behavior) =>
        el.scrollIntoView({ block: 'start', behavior }), fast ? 'instant' : 'smooth');
    },

    /* Click something that downloads; the file is kept in rec/ as <name>
     * for a later "upload". */
    async download(sel, name) {
      await glide(sel); await tap();
      const [dl] = await Promise.all([
        page.waitForEvent('download', { timeout: 30000 }),
        page.locator(sel).first().click(),
      ]);
      const file = path.join(recDir, dl.suggestedFilename());
      saved[name || 'last'] = dl.saveAs(file).then(() => file);
    },
    /* Give a file input a file: a name saved by "download", or a path
     * relative to DIR. The pointer goes to the input; the file is handed
     * over as a file dialog would — which never appears in a recording. */
    async upload(sel, file) {
      const f = saved[file] ? await saved[file] : path.resolve(DIR, file);
      await glide(sel); await tap(250);
      await page.locator(sel).first().setInputFiles(f);
    },

    async goto(url) { await open(new URL(url, nar.url).href); },
    /* After a click that loads another page, wait for something on it before
     * the next action — "ready" applies only to the first page and to goto. */
    async waitFor(sel, ms) {
      await page.waitForSelector(sel, { timeout: ms || nar.ready_timeout_ms || 60000 });
    },
    async wait(ms) { await sleep(ms); },
    async snap(label) { states[label] = await readState(); },
  };

  // ---- setup: full speed, before the clock --------------------------------
  if (nar.setup && nar.setup.length) {
    fast = true;
    for (const [name, ...args] of nar.setup) {
      if (!ACTIONS[name]) throw new Error(`unknown setup action: ${name}`);
      await ACTIONS[name](...args);
      await sleep(60);
    }
    fast = false;
    await page.evaluate(() => document.activeElement?.blur());
    await page.evaluate(([x, y]) => window.__cur.place(x, y), nar.cursor_start || [Math.round(W * 0.2), Math.round(H * 0.6)]);
    await sleep(nar.setup_settle_ms ?? 2000);            // let toasts from setup fade
  }

  // ---- the clock ----------------------------------------------------------
  const timeline = (nar.actions || [])
    .map((a) => ({ t: resolve(a.at), do: a.do }))
    .sort((a, b) => a.t - b.t);
  for (const s of timeline) if (!ACTIONS[s.do[0]]) throw new Error(`unknown action: ${s.do[0]}`);

  const t0 = Date.now();
  fs.writeFileSync(path.join(recDir, 'offset.txt'), ((t0 - v0) / 1000).toFixed(3));
  const elapsed = () => (Date.now() - t0) / 1000;
  let late = 0, prevT = null;

  for (const step of timeline) {
    const wait = step.t - elapsed();
    if (wait > 0) await sleep(wait * 1000);
    // An action that shares its time with the one before it (a waitFor after
    // its click) runs after it on purpose; only a separate beat can be late.
    else if (wait < -0.25 && step.t !== prevT) late++;
    prevT = step.t;
    const [name, ...args] = step.do;
    const show = args.map((a) => (typeof a === "string" ? a : JSON.stringify(a))).join(", ");
    try {
      await ACTIONS[name](...args);
    } catch (e) {
      // One failed decoration must not cost the whole take. Report it; the
      // frames and final-state.json decide whether the take is good.
      console.error(`  ! ${step.t.toFixed(2)}s ${name}(${show}): ${e.message.split('\n')[0]}`);
    }
    console.log(`  ${step.t.toFixed(2)}s  ${name}(${show})  [done ${elapsed().toFixed(2)}s]`);
  }
  if (late) console.error(`  ! ${late} action(s) started more than 0.25 s late — space them further apart`);

  const remaining = nar.total_seconds - elapsed();
  if (remaining > 0) await sleep(remaining * 1000);
  await sleep(400);

  states.final = await readState();
  fs.writeFileSync(path.join(recDir, 'final-state.json'), JSON.stringify(states, null, 1));
  console.log('final state:', JSON.stringify(states.final));

  const video = page.video();
  await context.close();                                 // finalizes the webm
  await browser.close();
  console.log('VIDEO:' + (await video.path()));
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
