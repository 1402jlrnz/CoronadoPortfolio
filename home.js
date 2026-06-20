const roles = ['Creative', 'Fullstack', 'Founder', 'Scholar'];
let roleIndex = 0;
const roleText = document.getElementById('role-text');
const topbar = document.getElementById('topbar');
let roleTimer;

function updateRole() {
  if (!roleText) return;
  roleIndex = (roleIndex + 1) % roles.length;
  roleText.textContent = roles[roleIndex];
  roleText.classList.remove('role-word');
  void roleText.offsetWidth;
  roleText.classList.add('role-word');
}

function handleScroll() {
  if (!topbar) return;
  if (window.scrollY > 100) {
    topbar.classList.add('topbar-shadow');
  } else {
    topbar.classList.remove('topbar-shadow');
  }
}

function initHls(videoId) {
  const video = document.getElementById(videoId);
  if (!video) return;
  const source = 'https://stream.mux.com/Aa02T7oM1wH5Mk5EEVDYhbZ1ChcdhRsS2m1NYyx4Ua1g.m3u8';

  if (Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(source);
    hls.attachMedia(video);
    hls.on(Hls.Events.MEDIA_ATTACHED, () => {
      video.play().catch(() => null);
    });
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = source;
    video.addEventListener('loadedmetadata', () => {
      video.play().catch(() => null);
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  roleTimer = window.setInterval(updateRole, 2000);
  window.addEventListener('scroll', handleScroll, { passive: true });
  initHls('hero-video');
  initHls('contact-video');
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (event) => {
      const href = anchor.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
});

window.addEventListener('beforeunload', () => {
  window.clearInterval(roleTimer);
});
