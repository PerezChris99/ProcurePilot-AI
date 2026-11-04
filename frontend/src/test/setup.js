import '@testing-library/jest-dom/vitest';
import {afterEach} from 'vitest';
import {cleanup} from '@testing-library/react';

// Vitest runs with globals:false. Testing Library's automatic cleanup only
// registers when a global afterEach is available, so enforce it explicitly.
// Otherwise, DOM from one test remains mounted and subsequent queries find
// stale cards, duplicate buttons, or the wrong asynchronous result.
afterEach(() => {
  cleanup();
});
