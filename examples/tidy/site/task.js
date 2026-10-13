/* A task's own page: its title, priority and notes. */
(() => {
  const id = new URLSearchParams(location.search).get('id');
  const tasks = load();
  const t = tasks.find((x) => x.id === id);
  if (!t) { $('detail').innerHTML = '<p class="empty">That task no longer exists.</p>'; return; }
  $('title').textContent = t.title;
  $('priority').textContent = t.priority;
  $('priority').classList.add(t.priority);
  $('state').textContent = t.done ? 'Done' : 'Open';
  $('notes').value = t.notes || '';
  $('save').addEventListener('click', () => {
    t.notes = $('notes').value;
    store(tasks);
    $('saved').textContent = 'Saved';
  });
})();
