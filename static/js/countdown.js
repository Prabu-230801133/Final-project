/**
 * countdown.js — Countdown Timer Component
 * Automatically initializes all .countdown elements with [data-end] attribute.
 * Supports: days, hours, minutes, seconds display.
 */

function updateCountdown(container, targetDate) {
  const now = new Date().getTime();
  const distance = targetDate - now;

  if (distance <= 0) {
    // Election ended
    container.querySelectorAll('.countdown-number').forEach(el => {
      el.textContent = '00';
    });
    container.innerHTML = '<span style="color:var(--danger);font-size:0.9rem;font-weight:600;">⏹ Election Ended</span>';
    return;
  }

  const days = Math.floor(distance / (1000 * 60 * 60 * 24));
  const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((distance % (1000 * 60)) / 1000);

  const pad = n => String(n).padStart(2, '0');

  const dEl = container.querySelector('[data-days]');
  const hEl = container.querySelector('[data-hours]');
  const mEl = container.querySelector('[data-mins]');
  const sEl = container.querySelector('[data-secs]');

  if (dEl) dEl.textContent = pad(days);
  if (hEl) hEl.textContent = pad(hours);
  if (mEl) mEl.textContent = pad(minutes);
  if (sEl) {
    // Flash effect on seconds change
    if (sEl.textContent !== pad(seconds)) {
      sEl.style.transform = 'scale(1.2)';
      setTimeout(() => { sEl.style.transform = 'scale(1)'; }, 150);
    }
    sEl.textContent = pad(seconds);
    sEl.style.transition = 'transform 0.15s ease';
  }
}

function initCountdowns() {
  const countdowns = document.querySelectorAll('.countdown[data-end]');

  countdowns.forEach(container => {
    const endStr = container.getAttribute('data-end');
    const targetDate = new Date(endStr).getTime();

    if (isNaN(targetDate)) {
      console.warn('Invalid countdown date:', endStr);
      return;
    }

    // Initial update
    updateCountdown(container, targetDate);

    // Update every second
    const interval = setInterval(() => {
      updateCountdown(container, targetDate);
      const now = new Date().getTime();
      if (now >= targetDate) clearInterval(interval);
    }, 1000);
  });
}

// Run after DOM load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCountdowns);
} else {
  initCountdowns();
}
