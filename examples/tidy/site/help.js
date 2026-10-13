/* The video list comes from videos/videos.json, which build_all.sh writes, so a
 * new video appears here with no change to this page. */
const list = document.getElementById('videos');
const player = document.getElementById('player');
const mss = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

fetch('videos/videos.json').then((r) => r.json()).then((videos) => {
  list.innerHTML = '';
  for (const v of videos) {
    const b = document.createElement('button');
    b.id = `video-${v.slug}`;
    b.innerHTML = `${v.title}<span>${mss(v.seconds)}</span>`;
    b.addEventListener('click', () => {
      player.hidden = false;
      player.poster = `videos/${v.slug}.jpg`;
      player.innerHTML = `<source src="videos/${v.slug}.mp4" type="video/mp4">` +
        `<track kind="captions" src="videos/${v.slug}.vtt" srclang="en" label="English" default>`;
      player.load();
      player.play().catch(() => {});
    });
    list.appendChild(b);
  }
}).catch(() => { list.innerHTML = '<p class="empty">No videos have been built yet.</p>'; });
