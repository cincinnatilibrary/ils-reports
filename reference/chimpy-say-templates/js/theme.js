/**
 * CHPL Design System - Theme Toggle
 * Handles dark/light mode switching with system preference detection
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'chpl-theme';
  const DARK = 'dark';
  const LIGHT = 'light';

  /**
   * Get the current theme preference
   * Priority: localStorage > system preference > default (light)
   */
  function getPreferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === DARK || stored === LIGHT) {
      return stored;
    }

    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return DARK;
    }

    return LIGHT;
  }

  /**
   * Apply theme to the document
   */
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    // Also add/remove class for compatibility
    if (theme === DARK) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }

    // Dispatch custom event for other components to react
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  /**
   * Save theme preference
   */
  function saveTheme(theme) {
    localStorage.setItem(STORAGE_KEY, theme);
  }

  /**
   * Toggle between dark and light themes
   */
  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
    const next = current === DARK ? LIGHT : DARK;
    setTheme(next);
    saveTheme(next);
    return next;
  }

  /**
   * Initialize theme on page load
   */
  function initTheme() {
    const theme = getPreferredTheme();
    setTheme(theme);

    // Listen for system preference changes
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only auto-switch if user hasn't set a preference
        if (!localStorage.getItem(STORAGE_KEY)) {
          setTheme(e.matches ? DARK : LIGHT);
        }
      });
    }
  }

  /**
   * Setup theme toggle buttons
   * Looks for elements with [data-theme-toggle] attribute
   */
  function setupToggleButtons() {
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        toggleTheme();
      });
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initTheme();
      setupToggleButtons();
    });
  } else {
    initTheme();
    setupToggleButtons();
  }

  // Expose API for programmatic control
  window.CHPLTheme = {
    toggle: toggleTheme,
    set: (theme) => {
      if (theme === DARK || theme === LIGHT) {
        setTheme(theme);
        saveTheme(theme);
      }
    },
    get: () => document.documentElement.getAttribute('data-theme') || getPreferredTheme(),
    DARK,
    LIGHT
  };
})();
