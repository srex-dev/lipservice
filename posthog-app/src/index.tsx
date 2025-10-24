import React from 'react';
import { createRoot } from 'react-dom/client';
import LipServiceApp from './LipServiceApp';

// PostHog App entry point
const initializeApp = () => {
  const container = document.getElementById('root');
  if (!container) {
    console.error('Root container not found');
    return;
  }

  const root = createRoot(container);
  
  // Get PostHog instance from global scope
  const posthog = (window as any).posthog;
  if (!posthog) {
    console.error('PostHog instance not found');
    return;
  }

  root.render(<LipServiceApp posthog={posthog} />);
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
