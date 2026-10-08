/* The pointer you see in the recording.
 *
 * A headless browser captures no operating-system cursor, so a screencast of a
 * real app shows things happening with nothing causing them. This draws one in
 * the page, and record.cjs glides it to a target before every real click — so
 * to a viewer the pointer and the effect are one event.
 *
 * It sits in its own fixed layer with `pointer-events: none`, so it can never
 * intercept the click it is illustrating, and it is injected with
 * addInitScript, so it survives navigation. Colours come from
 * window.__curConfig, which record.cjs sets from narration.json's "accent".
 */
(() => {
  if (window.__cur) return;
  const cfg = Object.assign({ accent: '#2563EB', outline: '#111827' }, window.__curConfig || {});

  /* A popover, so it is in the top layer. A modal <dialog> renders above every
   * z-index in the page, so a pointer in an ordinary layer goes BEHIND a
   * confirm dialog — exactly the click a viewer needs to see. The top layer
   * stacks by arrival, so the layer is shown again whenever a dialog opens. */
  const layer = document.createElement('div');
  layer.id = '__cursor_layer';
  layer.setAttribute('popover', 'manual');
  layer.style.cssText =
    'position:fixed;inset:0;width:100vw;height:100vh;max-width:none;max-height:none;' +
    'margin:0;padding:0;border:0;background:transparent;' +
    'pointer-events:none;z-index:2147483647;overflow:hidden';

  const dot = document.createElement('div');
  dot.style.cssText =
    'position:absolute;left:0;top:0;width:26px;height:26px;' +
    'transform:translate(-100px,-100px);will-change:transform';
  dot.innerHTML =
    '<svg width="26" height="26" viewBox="0 0 26 26" style="filter:drop-shadow(0 2px 4px rgba(0,0,0,.45))">' +
    '<path d="M5 3 L5 20 L9.6 15.6 L12.4 22 L15.6 20.6 L12.8 14.4 L19 14.2 Z" ' +
    `fill="#fff" stroke="${cfg.outline}" stroke-width="1.6" stroke-linejoin="round"/></svg>`;

  /* The ripple marks the instant of a click. Without it, a click on a control
   * that does not visibly change reads as nothing having happened. */
  const ripple = document.createElement('div');
  ripple.style.cssText =
    'position:absolute;left:0;top:0;width:34px;height:34px;margin:-17px 0 0 -17px;' +
    `border-radius:50%;background:${cfg.accent};opacity:0;transform:scale(.3)`;

  layer.append(ripple, dot);
  const raise = () => {
    if (!layer.isConnected || !layer.showPopover) return;
    if (layer.matches(':popover-open')) layer.hidePopover();
    layer.showPopover();
  };
  const attach = () => {
    document.documentElement.appendChild(layer);
    raise();
    new MutationObserver((ms) => {
      if (ms.some((m) => m.target.tagName === 'DIALOG')) raise();
    }).observe(document.documentElement,
      { subtree: true, attributes: true, attributeFilter: ['open'] });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attach);
  else attach();

  /* A page load makes a new document, and a new pointer at (-100,-100): after
   * a login or a form submit the pointer vanished, then flew in from the top
   * left. So the position is kept in sessionStorage and restored on load;
   * record.cjs also puts it back after every load, which covers a move to
   * another origin. */
  let x = -100, y = -100;
  const KEY = '__cur_xy';
  const remember = () => { try { sessionStorage.setItem(KEY, `${x},${y}`); } catch (_) {} };
  try {
    const s = sessionStorage.getItem(KEY);
    if (s) {
      [x, y] = s.split(',').map(Number);
      dot.style.transform = `translate(${x}px,${y}px)`;
    }
  } catch (_) {}

  window.__cur = {
    at: () => ({ x, y }),

    place(nx, ny) {
      x = nx; y = ny; remember();
      dot.style.transition = 'none';
      dot.style.transform = `translate(${nx}px,${ny}px)`;
    },

    /* Ease-in-out, not linear: a pointer that starts and stops at constant
     * speed looks like a machine, which distracts from what it is doing. */
    move(nx, ny, ms) {
      dot.style.transition = `transform ${ms}ms cubic-bezier(.33,0,.2,1)`;
      dot.style.transform = `translate(${nx}px,${ny}px)`;
      x = nx; y = ny; remember();
    },

    tap() {
      ripple.style.transition = 'none';
      ripple.style.transform = `translate(${x}px,${y}px) scale(.3)`;
      ripple.style.opacity = '.45';
      requestAnimationFrame(() => {
        ripple.style.transition = 'transform 420ms ease-out, opacity 420ms ease-out';
        ripple.style.transform = `translate(${x}px,${y}px) scale(1.5)`;
        ripple.style.opacity = '0';
      });
    },

    /* A ring around something the narration points at but nobody clicks —
     * a total, a status line, a new button. */
    ring(rect, ms) {
      const r = document.createElement('div');
      r.style.cssText =
        `position:absolute;left:${rect.x - 6}px;top:${rect.y - 6}px;` +
        `width:${rect.width + 12}px;height:${rect.height + 12}px;` +
        `border:3px solid ${cfg.accent};border-radius:10px;opacity:0;` +
        `box-shadow:0 0 0 6px ${cfg.accent}24`;
      layer.appendChild(r);
      requestAnimationFrame(() => {
        r.style.transition = 'opacity 260ms ease-out';
        r.style.opacity = '1';
      });
      setTimeout(() => {
        r.style.opacity = '0';
        setTimeout(() => r.remove(), 400);
      }, ms);
    },
  };
})();
