/** 2105315 labs: start the shared view switch and concept gate with this course's own storage key.
 * The implementation lives in teaching/shared/labs-kit/mode.js (source: _teaching-src/shared/labs-kit/). */
import { initLabs } from '/teaching/shared/labs-kit/mode.js';

export { currentMode, applyMode } from '/teaching/shared/labs-kit/mode.js';

initLabs({ storageKey: 'skh-2105315-mode' });
