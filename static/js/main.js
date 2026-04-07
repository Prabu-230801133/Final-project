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
document.querySelectorAll('a').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    const targetHref = this.getAttribute('href');
    if (!targetHref) return;

    if (targetHref.startsWith('#')) {
      const target = document.querySelector(targetHref);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } else {
      try {
        const url = new URL(this.href);
        if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) {
          const target = document.querySelector(url.hash);
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            history.pushState(null, '', url.hash);
          }
        }
      } catch (err) {}
    }
  });
});

// ─── Circular Ripple Page Transition ───
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('pageTransition');

  if (overlay) {
    // On page arrival: overlay covers screen, now collapse it away
    overlay.classList.add('circle-shown');
    void overlay.offsetWidth; // force reflow
    overlay.classList.remove('circle-shown');
    overlay.classList.add('circle-collapse');

    // After collapse animation, check if we need to scroll to a stored hash anchor
    const pendingHash = sessionStorage.getItem('scrollToHash');
    if (pendingHash) {
      sessionStorage.removeItem('scrollToHash');
      // Wait for collapse to finish (~600ms), then smooth-scroll to section
      setTimeout(() => {
        const target = document.querySelector(pendingHash);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          history.replaceState(null, '', pendingHash);
        }
      }, 650);
    }
  }

  // Intercept all internal navigation link clicks
  document.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', (e) => {
      const rawTarget = link.getAttribute('href');

      // Skip non-navigating links
      if (
        !rawTarget ||
        rawTarget.startsWith('#') ||
        rawTarget.startsWith('javascript:') ||
        link.target === '_blank' ||
        link.hasAttribute('download') ||
        e.ctrlKey || e.metaKey ||
        rawTarget.match(/^(mailto|tel):/)
      ) return;

      let url;
      try {
        url = new URL(link.href);
        if (url.origin !== window.location.origin) return;
      } catch (err) { return; }

      // If on the same page and only the hash differs, just smooth-scroll — no transition
      if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) {
        e.preventDefault();
        const target = document.querySelector(url.hash);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          history.pushState(null, '', url.hash);
        }
        return;
      }

      if (link.classList.contains('no-transition')) return;

      e.preventDefault();

      if (overlay) {
        overlay.classList.remove('circle-collapse', 'circle-shown');
        void overlay.offsetWidth; // force reflow
        overlay.classList.add('circle-expand');

        // If the destination has a hash, store it and navigate without the hash
        // so the browser doesn't jump the page before the overlay collapses
        const destHash = url.hash;
        const destUrl = destHash
          ? url.pathname + url.search  // strip the hash
          : link.href;

        if (destHash) {
          sessionStorage.setItem('scrollToHash', destHash);
        }

        setTimeout(() => {
          window.location.assign(destUrl);
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
