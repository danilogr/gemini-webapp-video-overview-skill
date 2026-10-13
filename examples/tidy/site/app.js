/* Tidy: an invented sample app for the video examples. Tasks live in
 * localStorage, so they survive the move to a task's own page and back. */
const KEY = 'tidy-tasks';
const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; } };
const store = (t) => localStorage.setItem(KEY, JSON.stringify(t));
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const say = (m) => { const s = $('status'); if (s) s.textContent = m; };

/* ?reset clears the list: every video starts from the same empty state. */
if (new URLSearchParams(location.search).has('reset')) {
  store([]);
  history.replaceState(null, '', location.pathname);
}

if ($('tasks')) {
  let filter = 'all';
  const paint = () => {
    const tasks = load();
    const shown = tasks.filter((t) => filter === 'all' || (filter === 'done') === t.done);
    $('tasks').innerHTML = shown.length ? shown.map((t) => `
      <li class="${t.done ? 'done' : ''}" id="task-${t.id}">
        <input type="checkbox" ${t.done ? 'checked' : ''} data-id="${t.id}" aria-label="Done: ${esc(t.title)}">
        <a href="task.html?id=${t.id}">${esc(t.title)}</a>
        <span class="badge ${t.priority}">${t.priority}</span>
        <button class="del" data-id="${t.id}" aria-label="Delete ${esc(t.title)}">✕</button>
      </li>`).join('') : `<li class="empty">${tasks.length ? 'Nothing here.' : 'No tasks yet. Add one above.'}</li>`;
    const open = tasks.filter((t) => !t.done).length;
    $('left').textContent = `${open} open`;
    document.querySelectorAll('.filter').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.f === filter)));
  };

  $('add-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const title = $('new-title').value.trim();
    if (!title) return;
    const tasks = load();
    tasks.push({ id: Date.now().toString(36), title, priority: $('new-priority').value, done: false, notes: '' });
    store(tasks);
    $('new-title').value = '';
    paint();
    say(`Added “${title}”`);
  });

  $('tasks').addEventListener('change', (e) => {
    if (!e.target.matches('input[type=checkbox]')) return;
    const tasks = load();
    const t = tasks.find((x) => x.id === e.target.dataset.id);
    t.done = e.target.checked;
    store(tasks);
    paint();
    say(t.done ? `Done: ${t.title}` : `Reopened: ${t.title}`);
  });

  let pending = null;
  $('tasks').addEventListener('click', (e) => {
    const b = e.target.closest('.del');
    if (!b) return;
    pending = b.dataset.id;
    $('confirm-text').textContent = `“${load().find((t) => t.id === pending).title}” will be removed.`;
    $('confirm').showModal();
  });
  $('cancel').addEventListener('click', () => $('confirm').close());
  $('really-delete').addEventListener('click', () => {
    const tasks = load();
    const t = tasks.find((x) => x.id === pending);
    store(tasks.filter((x) => x.id !== pending));
    $('confirm').close();
    paint();
    say(`Deleted “${t.title}”`);
  });

  document.querySelectorAll('.filter').forEach((b) => b.addEventListener('click', () => {
    filter = b.dataset.f;
    paint();
    say(`Showing ${b.textContent.toLowerCase()} tasks`);
  }));

  paint();
}
