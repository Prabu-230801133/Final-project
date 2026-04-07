/**
 * main.js — Global JavaScript for VoteX
 * Handles: alert auto-dismiss, navbar scroll effects, page transitions
 */

// ─── Auto-dismiss flash messages ───
document.querySelectorAll('.alert').forEach(alert => {
  // Auto-remove after 5 seconds
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100px)';
    alert.style.transition = 'all 0.4s ease-out';
    setTimeout(() => alert.remove(), 400);
  }, 5000);
});

// ─── Navbar scroll effect ───
const navbar = document.getElementById('mainNavbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });
}

// ─── Smooth scroll for anchor links ───
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ─── Circular Ripple Page Transition ───
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('pageTransition');

  if (overlay) {
    // On page arrival: overlay is already covering (circle-shown), now collapse it away
    overlay.classList.add('circle-shown');
    // Force reflow so the snap is applied before we start the collapse animation
    void overlay.offsetWidth;
    overlay.classList.remove('circle-shown');
    overlay.classList.add('circle-collapse');
  }

  // Intercept all internal navigation link clicks
  document.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', (e) => {
      const target = link.getAttribute('href');

      // Skip non-navigating links
      if (
        !target ||
        target.startsWith('#') ||
        target.startsWith('javascript:') ||
        link.target === '_blank' ||
        link.hasAttribute('download') ||
        e.ctrlKey || e.metaKey ||
        target.match(/^(mailto|tel):/)
      ) return;

      try {
        const url = new URL(target, window.location.origin);
        if (url.origin !== window.location.origin) return;
      } catch (err) { return; }

      if (link.classList.contains('no-transition')) return;

      e.preventDefault();

      if (overlay) {
        // Reset to tiny dot (no animation)
        overlay.classList.remove('circle-collapse', 'circle-shown');
        void overlay.offsetWidth; // force reflow
        // Expand circle to cover screen
        overlay.classList.add('circle-expand');
        // After expand animation, navigate
        setTimeout(() => {
          window.location.assign(link.href);
        }, 520);
      } else {
        window.location.assign(link.href);
      }
    });
  });
});

// BFCache: browser Back/Forward restores page from cache — collapse overlay
window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    const overlay = document.getElementById('pageTransition');
    if (overlay) {
      overlay.classList.remove('circle-expand', 'circle-collapse');
      overlay.classList.add('circle-shown');
      void overlay.offsetWidth;
      overlay.classList.remove('circle-shown');
      overlay.classList.add('circle-collapse');
    }
  }
});

// ─── Animate stat values on scroll ───
function animateCounter(element, target, duration = 1500) {
  const start = 0;
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    element.textContent = Math.round(eased * target);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// Observe stat values entering viewport
const statObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const value = parseInt(entry.target.textContent, 10);
      if (!isNaN(value)) {
        animateCounter(entry.target, value);
      }
      statObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-value').forEach(el => statObserver.observe(el));

// ─── Progress bar animation on scroll ───
const progressObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const bar = entry.target;
      const width = bar.style.width;
      bar.style.width = '0';
      setTimeout(() => { bar.style.width = width; }, 100);
      progressObserver.unobserve(bar);
    }
  });
}, { threshold: 0.3 });

document.querySelectorAll('.progress-bar').forEach(el => progressObserver.observe(el));

// ─── Bounce animation style ───
const bounceStyle = document.createElement('style');
bounceStyle.textContent = `
@keyframes bounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(-8px); }
}
`;
document.head.appendChild(bounceStyle);

console.log('%c🗳️ VoteX Voting System', 'color:#6C63FF;font-size:16px;font-weight:bold;');
console.log('%cBuilt with Django + MySQL', 'color:#FF6B9D;font-size:12px;');

// ─── Theme Switcher Logic ───
function setTheme(themeName) {
  document.documentElement.setAttribute('data-theme', themeName);
  localStorage.setItem('theme', themeName);
  
  const themeIcon = document.getElementById('themeIcon');
  const themeLabel = document.getElementById('themeLabel');
  
  if (themeIcon && themeLabel) {
    if (themeName === 'light') {
      themeIcon.textContent = '🌙';
      themeLabel.textContent = 'Dark';
    } else {
      themeIcon.textContent = '☀️';
      themeLabel.textContent = 'Light';
    }
  }
}

function toggleTheme() {
  if (localStorage.getItem('theme') === 'light') {
    setTheme('dark');
  } else {
    setTheme('light');
  }
}

// Initial script execution: Apply saved theme immediately
(function() {
  if (localStorage.getItem('theme') === 'light') {
    setTheme('light');
  } else {
    setTheme('dark'); // default
  }
})();
