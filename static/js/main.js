/**
 * QuizHub Client Controller
 * High-performance, vanilla JavaScript (no dependencies, instant load)
 * Loam House interactions: scroll reveal, curtain menu, sticky blur nav
 */

(function () {
  'use strict';

  // 1. Sticky Header Blur on Scroll
  function initHeader() {
    const header = document.querySelector('[data-header]');
    if (!header) return;

    const onScroll = () => {
      if (window.scrollY > 40) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // 2. Mobile Menu Staggered Curtain Reveal
  function initMobileMenu() {
    const toggleBtn = document.querySelector('[data-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');
    if (!toggleBtn || !mobileMenu) return;

    const toggle = () => {
      const isOpen = mobileMenu.classList.contains('open');
      if (isOpen) {
        mobileMenu.classList.remove('open');
        toggleBtn.classList.remove('is-open');
        document.body.style.overflow = '';
      } else {
        mobileMenu.classList.add('open');
        toggleBtn.classList.add('is-open');
        document.body.style.overflow = 'hidden';
      }
    };

    toggleBtn.addEventListener('click', toggle);

    // Close on link click
    mobileMenu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        toggleBtn.classList.remove('is-open');
        document.body.style.overflow = '';
      });
    });
  }

  // 3. Scroll Reveal via IntersectionObserver
  function initScrollReveal() {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) return;

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('visible');
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
      );

      items.forEach((item) => observer.observe(item));
    } else {
      items.forEach((item) => item.classList.add('visible'));
    }
  }

  // 4. Interactive Multi-Step Form Logic (Step Indicator "You / Reach you / Enquiry")
  function initMultiStepForm() {
    const multiForms = document.querySelectorAll('[data-multistep-form]');
    multiForms.forEach((form) => {
      const steps = form.querySelectorAll('[data-step]');
      const dots = form.querySelectorAll('[data-step-dot]');
      const nextBtns = form.querySelectorAll('[data-next-step]');
      const prevBtns = form.querySelectorAll('[data-prev-step]');
      let currentStep = 1;

      const showStep = (stepNumber) => {
        steps.forEach((s) => {
          const sNum = parseInt(s.getAttribute('data-step'), 10);
          if (sNum === stepNumber) {
            s.style.display = 'block';
            s.classList.add('reveal', 'visible');
          } else {
            s.style.display = 'none';
          }
        });

        dots.forEach((dot) => {
          const dNum = parseInt(dot.getAttribute('data-step-dot'), 10);
          dot.classList.remove('active', 'completed');
          if (dNum === stepNumber) {
            dot.classList.add('active');
          } else if (dNum < stepNumber) {
            dot.classList.add('completed');
          }
        });
      };

      nextBtns.forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          // Validate current step inputs
          const currentPanel = form.querySelector(`[data-step="${currentStep}"]`);
          const inputs = currentPanel.querySelectorAll('input, select, textarea');
          let valid = true;
          inputs.forEach((input) => {
            if (input.hasAttribute('required') && !input.value.trim()) {
              valid = false;
              input.style.borderBottomColor = 'var(--clay)';
              input.focus();
            }
          });

          if (valid && currentStep < steps.length) {
            currentStep++;
            showStep(currentStep);
          }
        });
      });

      prevBtns.forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          if (currentStep > 1) {
            currentStep--;
            showStep(currentStep);
          }
        });
      });

      showStep(currentStep);
    });
  }

  // 5. Corner Toast Notification Controller
  function initToasts() {
    // Auto-dismiss any server-rendered toasts
    const existingToasts = document.querySelectorAll('.zh-toast');
    existingToasts.forEach((toast) => {
      setTimeout(() => {
        dismissToast(toast);
      }, 4500);
    });
  }

  function dismissToast(toast) {
    if (!toast || toast.classList.contains('toast-fadeout')) return;
    toast.classList.add('toast-fadeout');
    setTimeout(() => {
      toast.remove();
    }, 350);
  }

  // Global showToast function for real-time notifications
  window.showToast = function (message, type = 'info', duration = 4500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'zh-toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `zh-toast ${type === 'error' ? 'toast-error' : type === 'success' ? 'toast-success' : ''}`;
    toast.setAttribute('role', 'alert');

    let tagLabel = 'Notification';
    if (type === 'error') tagLabel = 'Alert / Verification';
    if (type === 'success') tagLabel = 'Success / Verified';

    toast.innerHTML = `
      <div style="flex-grow: 1;">
        <span class="zh-toast-tag">${tagLabel}</span>
        <p class="zh-toast-text">${message}</p>
      </div>
      <button type="button" class="zh-toast-close" aria-label="Dismiss">×</button>
    `;

    toast.querySelector('.zh-toast-close').addEventListener('click', () => {
      dismissToast(toast);
    });

    container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => {
        dismissToast(toast);
      }, duration);
    }
  };

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initHeader();
      initMobileMenu();
      initScrollReveal();
      initMultiStepForm();
      initToasts();
    });
  } else {
    initHeader();
    initMobileMenu();
    initScrollReveal();
    initMultiStepForm();
    initToasts();
  }
})();
