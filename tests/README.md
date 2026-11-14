# UI contrast regression tests

From the repository root:

```sh
python -m pip install -r tests/requirements-ui.txt
python -m playwright install chromium
python tests/ui_contrast_test.py --output /tmp/chatty-ui-results.json --screenshots /tmp/chatty-ui-screenshots
node --check springboot_chatapp/src/main/resources/static/script1.js
```

If the browser cache is nonstandard, set `PLAYWRIGHT_BROWSERS_PATH` to that cache directory before running.

The test serves the actual HTML, CSS, and JavaScript on loopback and substitutes an explicitly mocked SockJS/STOMP transport. It does not contact a production chat room. It covers 320×800, 768×1024, and 1280×900 viewports, each with both light and dark OS color preferences, across 16 UI states. It measures computed text/placeholder contrast against the composed background (minimum 4.5:1), control boundaries (minimum 3:1), light-surface consistency, keyboard focus, input labels, validation, error states, safe dynamic message rendering, logout, text spacing, and horizontal reflow. It also verifies that all three tracked static build mirrors match their source files.

This is a focused regression suite, not a complete accessibility certification. Live two-client WebSocket integration, screen-reader usability, Safari/Firefox behavior, user forced-color modes, and manual zoom/visual review still require separate checks. The current Maven test attempt was blocked by Surefire dependency resolution; no Java test pass is claimed. See [the audit](../docs/UI_CONTRAST_AUDIT.md).
