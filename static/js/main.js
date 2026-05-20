/* ═══════════════════════════════════════════
   УчимсяВместе — main.js
   ═══════════════════════════════════════════ */

// ── Тема (тёмная/светлая) ────────────────────
function toggleTheme() {
  const body = document.body;
  const btn = document.getElementById('themeBtn');
  if (body.classList.contains('dark')) {
    body.classList.remove('dark');
    btn.textContent = '🌙';
    localStorage.setItem('theme', 'light');
  } else {
    body.classList.add('dark');
    btn.textContent = '☀️';
    localStorage.setItem('theme', 'dark');
  }
}

// ── Размер шрифта ─────────────────────────────
function setFontSize(size) {
  const body = document.body;
  body.classList.remove('font-size-small', 'font-size-normal', 'font-size-large');
  body.classList.add('font-size-' + size);
  localStorage.setItem('fontSize', size);
}

// ── Мобильное меню ────────────────────────────
function toggleMobileMenu() {
  const menu = document.getElementById('mobileMenu');
  menu.classList.toggle('open');
}

// ── Загрузка настроек из localStorage ─────────
document.addEventListener('DOMContentLoaded', function () {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark');
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = '☀️';
  }

  const savedSize = localStorage.getItem('fontSize') || 'normal';
  document.body.classList.remove('font-size-small', 'font-size-normal', 'font-size-large');
  document.body.classList.add('font-size-' + savedSize);

  // Закрыть алерты автоматически через 5 сек
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (a) {
    setTimeout(function () {
      a.style.opacity = '0';
      a.style.transition = 'opacity 0.5s';
      setTimeout(function () { a.remove(); }, 500);
    }, 5000);
  });

  // Плавная прокрутка к якорям
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Анимация прогресс-баров при загрузке
  const fills = document.querySelectorAll('.big-progress-fill, .progress-fill-sm');
  fills.forEach(function (f) {
    const w = f.style.width;
    f.style.width = '0';
    setTimeout(function () { f.style.width = w; }, 200);
  });
});

// ── Подтверждение опасных действий ───────────
document.querySelectorAll('[data-confirm]').forEach(function (el) {
  el.addEventListener('click', function (e) {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});
