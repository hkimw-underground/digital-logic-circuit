## 2024-04-25 - Playwright Screenshot Timeouts in Headless Mode
**Learning:** In headless sandbox environments with restricted network access, Playwright `page.screenshot` can hang indefinitely waiting for external fonts or images to load, resulting in a `Timeout 30000ms exceeded` error.
**Action:** When writing Playwright verification scripts in this project, explicitly abort font and image requests using `page.route` before taking screenshots, or use locator-specific screenshots to avoid full page rendering hangs.

## 2024-04-25 - Button State Transitions
**Learning:** Added loading spinners to delete/save buttons. It is important to check if the DOM element still exists (`document.body.contains(btnElement)`) in the `finally` block before re-enabling the button, as successful deletions may remove the row entirely, leading to console errors if we attempt to modify the unmounted element.
**Action:** Always include a DOM presence check when resetting loading states for destructive actions that remove the element from the view.
