# Chatty UI & Contrast Audit

## Scope and provenance

Base: `sauravnrai/chatty@2c88f23ba590540ad2fd397b7b44ad3600201d86` (`master`). Intended review branch: `fix/light-contrast-refresh`. The final published commit SHA and PR URL must be recorded in the Notion audit after publication. No merge or production deployment is part of this refresh.

All 14 authored text files were read, including all four Java backend classes, the Java context test, application properties, Maven configuration/wrappers, and project docs. The complete recursive tree was inventoried. The only authored frontend page is `index.html`, with login and chat states; there are no other custom pages, layouts, navigation bars, or modal components in the source. The three tracked frontend build mirrors have the same original Git blob SHAs as their source files and are synchronized here. Historical PNGs and compiled Java artifacts are not runtime theme source and are unchanged. Framework-generated error pages and production infrastructure are outside this authored-UI test coverage.

## Exact files changed or added

- `README.md`: Adds Accessibility & Theme Standards with the complete five-color palette, measured ratios, limitations, and a historical-screenshot label.
- `springboot_chatapp/src/main/resources/static/index.html`: Removes Bootstrap bg-primary/btn-dark styling and the Bootstrap CSS import. Styles both login and full chat views; adds visible labels, a skip link, semantic landmarks, an ordered live log, complete view hiding, and a light color-scheme declaration. Fixes the name-title id typo.
- `springboot_chatapp/src/main/resources/static/style.css`: Introduces only #FFFFFF, #F8FAFC, #0F172A, #334155, and #2563EB. Defines text, placeholders, inputs, cards, log, header/footer, primary/secondary buttons, hover/active/focus/disabled/invalid states, 3px focus rings, and responsive layouts. No dark surfaces or OS-dark override.
- `springboot_chatapp/src/main/resources/static/script1.js`: Keeps the same SockJS/STOMP endpoints. Styles generated messages through classes and textContent rather than raw HTML; replaces the native alert with inline feedback; supports keyboard form submission, full chat-view visibility, focus restoration, and readable connection/send/error states.
- `springboot_chatapp/target/classes/static/index.html`: Synchronizes the already-tracked build mirror with springboot_chatapp/src/main/resources/static/index.html; identical colors and behavior. No compiled Java binaries are included in this change.
- `springboot_chatapp/target/classes/static/style.css`: Synchronizes the already-tracked build mirror with springboot_chatapp/src/main/resources/static/style.css; identical colors and behavior. No compiled Java binaries are included in this change.
- `springboot_chatapp/target/classes/static/script1.js`: Synchronizes the already-tracked build mirror with springboot_chatapp/src/main/resources/static/script1.js; identical colors and behavior. No compiled Java binaries are included in this change.
- `tests/ui_contrast_test.py`: Adds the repeatable mocked-transport Chromium UI, contrast, keyboard, state, and reflow regression test. Every input placeholder and disabled state remains subject to the 4.5:1 test; control borders must reach 3:1.
- `tests/requirements-ui.txt`: Pins the browser test dependency to Playwright 1.65.2; no production color changes.
- `tests/README.md`: Documents repeatable test setup, commands, coverage, and mocked-transport/manual-testing limits; no production color changes.
- `docs/UI_CONTRAST_AUDIT.md`: Records this file manifest, every palette assignment and observed text ratio, all browser-state results, source digests, blocked backend tests, and the review checklist; no production color changes.

## Exact color assignments

Before: `style.css` only set login height; the page and login used Bootstrap `bg-primary`, all three action buttons used `btn-dark`, and text/inputs/cards inherited Bootstrap defaults. This refresh removes the Bootstrap stylesheet from the runtime rather than relying on late overrides. There were no authored hex color literals in the old frontend source to replace; the assignments below are explicit new tokens.

| Token/value | Assignments |
| --- | --- |
| `#FFFFFF` | Page, header/footer, input fields, message log, secondary buttons, alternating message cards, inline feedback surfaces, primary-button labels, selection text. |
| `#F8FAFC` | Login/chat cards, card header, composer, alternating message cards, secondary-button hover/active, disabled inputs/buttons, scrollbar track. |
| `#0F172A` | Headings, labels, primary/body/message text, inline validation and connection-error text. |
| `#334155` | Secondary/helper/status copy, input placeholders, author names, footer text, all card/input boundaries, invalid borders, disabled labels/borders. |
| `#2563EB` | Primary buttons and their borders, links/brand, secondary-button text/borders, 3px keyboard-focus outlines, focused-input border, selection fill, scrollbar thumb. |

Primary-button hover/active states keep white-on-blue text and add an underline rather than introducing a darker fill. Secondary hover/active states use blue-on-off-white. Disabled controls keep full opacity. Light color-scheme is declared in HTML and CSS; user forced-color overrides are not suppressed. Incoming names/content are rendered as text so they cannot inject dark HTML or styles.

## Observed text and placeholder contrast

All calculations use WCAG relative luminance and unrounded comparison against 4.5:1 (including large text, even where a lower threshold would be allowed).

| Foreground / background | Contrast | Result |
| --- | ---: | --- |
| `#0F172A` / `#F8FAFC` | 17.06293:1 | PASS |
| `#0F172A` / `#FFFFFF` | 17.85253:1 | PASS |
| `#2563EB` / `#F8FAFC` | 4.93996:1 | PASS |
| `#2563EB` / `#FFFFFF` | 5.16856:1 | PASS |
| `#334155` / `#F8FAFC` | 9.89676:1 | PASS |
| `#334155` / `#FFFFFF` | 10.35475:1 | PASS |
| `#FFFFFF` / `#2563EB` | 5.16856:1 | PASS |

## Executed tests

Browser: Chromium 159.0.8154.6. Python Playwright 1.65.2. Actual application HTML/CSS/JavaScript with an explicitly mocked SockJS/STOMP transport. No real shared chat room was contacted.

- 6/6 configurations passed; 282 assertions passed.
- 96 UI-state audits; 1746 computed text/placeholder contrast samples passed.
- Lowest observed text contrast: 4.93996:1 (blue on off-white). White primary-button text on blue: 5.16856:1.
- All measured control boundaries meet at least 3:1; all keyboard focus rings are solid 3px blue and are not clipped by an overflow-hidden card.
- No unexpected dark application surface, horizontal page overflow, uncaught JavaScript error, or native dialog occurred in the tested states.
- `node --check springboot_chatapp/src/main/resources/static/script1.js`: PASS.
- All three source/build frontend mirror byte comparisons: PASS.

### Full UI-state matrix

| State | 320 light | 320 dark OS | 768 light | 768 dark OS | 1280 light | 1280 dark OS |
| --- | --- | --- | --- | --- | --- | --- |
| login | PASS | PASS | PASS | PASS | PASS | PASS |
| login-validation | PASS | PASS | PASS | PASS | PASS | PASS |
| connecting-disabled | PASS | PASS | PASS | PASS | PASS | PASS |
| empty-chat | PASS | PASS | PASS | PASS | PASS | PASS |
| message-validation | PASS | PASS | PASS | PASS | PASS | PASS |
| messages-long-and-untrusted | PASS | PASS | PASS | PASS | PASS | PASS |
| primary-hover | PASS | PASS | PASS | PASS | PASS | PASS |
| primary-active-and-focus | PASS | PASS | PASS | PASS | PASS | PASS |
| secondary-hover | PASS | PASS | PASS | PASS | PASS | PASS |
| secondary-focus | PASS | PASS | PASS | PASS | PASS | PASS |
| malformed-message-feedback | PASS | PASS | PASS | PASS | PASS | PASS |
| send-failure-feedback | PASS | PASS | PASS | PASS | PASS | PASS |
| wcag-text-spacing-and-reflow | PASS | PASS | PASS | PASS | PASS | PASS |
| connection-loss | PASS | PASS | PASS | PASS | PASS | PASS |
| logout | PASS | PASS | PASS | PASS | PASS | PASS |
| connection-failure | PASS | PASS | PASS | PASS | PASS | PASS |

### Backend test attempt and explicit limitations

`mvn test` compiled all four application Java classes and the single test class, then failed before test execution because Maven could not resolve Surefire 3.5.2 dependency descriptors for `surefire-api` and `surefire-extensions-api`. This is a dependency-resolution/build failure, not a passing backend test. Zero Java tests are claimed as executed. The initial offline attempt also lacked the Spring Boot parent in its cache.

The suite above is not axe-core and is not a WCAG certification. axe-core was downloaded for possible follow-up but was not executed, so no axe pass is claimed. Live server/two-client broadcasting, screen-reader interaction, other browser engines, user forced-color modes, framework error screens, manual 200% zoom/400% reflow, and production visual review are not signed off. The browser suite does test 320px CSS-width reflow and the WCAG text-spacing overrides; these are not substitutes for all manual zoom checks.

## Source SHA-256 digests

- `springboot_chatapp/src/main/resources/static/index.html`: `956ed7b4781344891322f1ef9f4300714a89752329a762f12590a3bf4cb59149`
- `springboot_chatapp/src/main/resources/static/style.css`: `36e3508e7173c31aa91203f1120d0e02ffe44d34ee350f9e9d103946ddbc2b89`
- `springboot_chatapp/src/main/resources/static/script1.js`: `94355f00ba877cee016962b4fddfff735a2e07a94bc5fc0ead8bcdeb468ab9f1`

## Review and sign-off checklist

- [x] Inspect every authored source file and inventory all frontend/build paths.
- [x] Apply only white/off-white application surfaces (blue action controls are intentional).
- [x] Verify every observed text/placeholder state at or above 4.5:1.
- [x] Verify readable disabled states and control boundaries at or above 3:1.
- [x] Verify keyboard skip link, focus visibility/transfer, explicit labels, live feedback, and complete view hiding.
- [x] Verify long and untrusted messages cannot break layout or inject styled markup.
- [x] Run all six viewport/OS-preference configurations and all 96 UI-state audits.
- [x] Add README Accessibility & Theme Standards and repeatable test instructions.
- [ ] Resolve Maven dependencies and rerun the backend test suite.
- [ ] Verify real two-client WebSocket messaging against the running application.
- [ ] Complete screen-reader, cross-browser, forced-colors, zoom, and human visual review.
- [ ] Publish and verify the feature branch and PR; add final commit SHA and PR URL to the Notion audit.
- [ ] Send/reply with the verified review links and these exact test limitations.
- [ ] Human reviewer approval.

Contrast regression checks passed for the tested authored UI. Full accessibility release approval and production deployment are not asserted.
