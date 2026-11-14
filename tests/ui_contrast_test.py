#!/usr/bin/env python3
"""Browser UI tests with an explicitly mocked SockJS/STOMP transport (no backend claims)."""
import argparse
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "springboot_chatapp/src/main/resources/static"
TRANSPORT = r"""
window.SockJS = function (url) { this.url = url; };
window.Stomp = { over: function (socket) {
    let receiver;
    const client = {
        connected: false,
        debug: null,
        connect: function (headers, success, failure) {
            window.__transport = {
                complete: function () { client.connected = true; success({}); },
                fail: function () { client.connected = false; failure("Test failure"); },
                deliver: function (value) { receiver({body: JSON.stringify(value)}); },
                deliverRaw: function (value) { receiver({body: value}); },
                failSend: false,
                sent: []
            };
        },
        subscribe: function (destination, callback) {
            if (destination !== "/topic/return-to") throw new Error("Wrong subscription");
            receiver = callback;
            return {unsubscribe: function () {}};
        },
        send: function (destination, headers, body) {
            if (destination !== "/chatty/message") throw new Error("Wrong send destination");
            if (window.__transport.failSend) throw new Error("Test send failure");
            window.__transport.sent.push(JSON.parse(body));
            receiver({body: body});
        },
        disconnect: function (callback) { client.connected = false; if (callback) callback(); }
    };
    return client;
}};
"""
AUDIT = r"""() => {
    const issues = [], pairs = {}, surfaces = new Set();
    let samples = 0, borders = 0;
    const rgba = c => (c.match(/[\d.]+/g) || []).map(Number);
    const blend = (f, b) => {
        const a = f.length > 3 ? f[3] : 1;
        return [0, 1, 2].map(i => f[i] * a + b[i] * (1 - a));
    };
    const bg = el => el ? blend(rgba(getComputedStyle(el).backgroundColor), bg(el.parentElement)) : [255,255,255];
    const lum = c => c.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
        .reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
    const contrast = (a,b) => (Math.max(lum(a),lum(b)) + .05) / (Math.min(lum(a),lum(b)) + .05);
    const hex = c => '#' + c.map(v => Math.round(v).toString(16).padStart(2,'0')).join('').toUpperCase();
    const test = (el, fg, background, kind) => {
        const ratio = contrast(blend(fg, background), background);
        samples++;
        const key = hex(blend(fg,background)) + ' / ' + hex(background);
        pairs[key] = ratio;
        if (ratio < 4.5) issues.push(`${kind}: ${el.id || el.tagName}: ${key}: ${ratio}`);
    };
    for (const el of document.querySelectorAll('body *')) {
        const s = getComputedStyle(el), r = el.getBoundingClientRect();
        if (!r.width || !r.height || s.visibility !== 'visible' || !el.getClientRects().length) continue;
        const background = bg(el), fill = rgba(s.backgroundColor);
        if ((fill[3] ?? 1) > 0) {
            const color = hex(background);
            surfaces.add(color);
            const primaryButton = el.matches('button.button:not(.button-secondary)');
            if (!['#FFFFFF','#F8FAFC'].includes(color) && !(primaryButton && color === '#2563EB')) {
                issues.push(`Unexpected surface: ${el.id || el.tagName}: ${color}`);
            }
        }
        const ownText = [...el.childNodes].some(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
        if (ownText || el.matches('input')) test(el, rgba(s.color), background, 'text');
        if (el.matches('input') && el.placeholder) {
            const placeholder = getComputedStyle(el, '::placeholder');
            if (Number(placeholder.opacity) !== 1) issues.push('Translucent placeholder: ' + el.id);
            test(el, rgba(placeholder.color), background, 'placeholder');
        }
        if (el.matches('input, button')) {
            const outside = bg(el.parentElement);
            if (contrast(rgba(s.borderTopColor), outside) < 3) issues.push('Control boundary contrast: '+el.id);
            if (Number(s.opacity) !== 1) issues.push('Translucent control: ' + el.id);
            borders++;
        }
    }
    if (document.documentElement.scrollWidth > innerWidth + 1) issues.push('Horizontal page overflow');
    return {issues, samples, borders, pairs, surfaces: [...surfaces]};
}"""

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def exercise(browser, url, width, height, scheme, screenshots):
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme)
    page = context.new_page()
    page.set_default_timeout(5000)
    errors, dialogs, checks, audits, pairs = [], [], [], [], {}
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
    page.route("**/webjars/sockjs-client/sockjs.min.js", lambda route: route.fulfill(content_type="application/javascript", body=TRANSPORT))
    page.route("**/webjars/stomp-websocket/stomp.min.js", lambda route: route.fulfill(content_type="application/javascript", body="/* Supplied by the test SockJS/STOMP transport. */"))
    name = f"{width}x{height}-{scheme}"
    def check(condition, label):
        assert condition, label
        checks.append(label)
    def audit(stage):
        data = page.evaluate(AUDIT)
        check(not data["issues"], stage + ": " + repr(data["issues"]))
        audits.append({"stage": stage, **data})
        pairs.update(data["pairs"])
    def focus_outline(selector):
        data = page.locator(selector).evaluate("el => { const s=getComputedStyle(el); return {width:parseFloat(s.outlineWidth),style:s.outlineStyle,color:s.outlineColor,visible:el.matches(':focus-visible')}; }")
        check(data["visible"] and data["width"] >= 3 and data["style"] == "solid" and data["color"] == "rgb(37, 99, 235)", "Visible keyboard focus: " + selector)
    try:
        page.goto(url, wait_until="networkidle")
        check(page.locator("#chat-room").is_hidden(), "Chat and composer hidden before login")
        check(page.locator("h1:visible").count() == 1, "One visible primary heading")
        for field in ["#name-value", "#message-value"]:
            check(page.locator(field).evaluate("el => el.labels.length === 1"), "Explicit field label: " + field)
        check(page.locator("#message-log").get_attribute("role") == "log", "Named live message log")
        audit("login")
        page.keyboard.press("Tab")
        check(page.locator(".skip-link").evaluate("el => el === document.activeElement"), "Skip link first in keyboard order")
        focus_outline(".skip-link")
        page.keyboard.press("Enter")
        check(page.locator("#main-content").evaluate("el => el === document.activeElement"), "Skip link moves focus to main")
        page.keyboard.press("Tab")
        check(page.locator("#name-value").evaluate("el => el === document.activeElement"), "Name input reachable by keyboard")
        focus_outline("#name-value")
        page.keyboard.press("Enter")
        check(page.locator("#login-error").is_visible(), "Inline login validation (no native modal)")
        check(page.locator("#name-value").get_attribute("aria-invalid") == "true", "Invalid name announced")
        audit("login-validation")
        page.locator("#name-value").fill("Contrast reviewer")
        page.keyboard.press("Tab")
        focus_outline("#login")
        page.keyboard.press("Enter")
        check(page.locator("#login").is_disabled(), "Connecting button disabled without low opacity")
        audit("connecting-disabled")
        page.evaluate("window.__transport.complete()")
        check(page.locator("#name-form").is_hidden() and page.locator("#chat-room").is_visible(), "Complete chat view shown after connection")
        check(page.locator("#message-value").evaluate("el => el === document.activeElement"), "Focus moves to composer after login")
        audit("empty-chat")
        page.keyboard.press("Enter")
        check(page.locator("#message-error").is_visible(), "Inline empty-message validation")
        audit("message-validation")
        page.locator("#message-value").fill("Hello, high-contrast chat.")
        page.keyboard.press("Enter")
        check(page.locator(".message-content").first.inner_text() == "Hello, high-contrast chat.", "Send and receive rendering with mock transport")
        check(page.locator("#message-value").input_value() == "", "Composer clears after successful send")
        check(page.evaluate("window.__transport.sent[0].name") == "Contrast reviewer", "Display name preserved in outgoing payload")
        page.evaluate("window.__transport.deliver({name:'Participant '+ 'N'.repeat(120),content:'L'.repeat(1800)})")
        page.evaluate("window.__transport.deliver({name:'<img src=x onerror=alert(1)>',content:'<style>body{background:black}</style>'})")
        check(page.locator("#message-list img, #message-list style").count() == 0, "Incoming markup is text, not injected dark styles or scripts")
        audit("messages-long-and-untrusted")
        page.locator("#send-btn").hover()
        audit("primary-hover")
        page.locator("#message-value").focus()
        page.keyboard.press("Tab")
        focus_outline("#send-btn")
        page.keyboard.down("Space")
        audit("primary-active-and-focus")
        page.keyboard.up("Space")
        page.locator("#logout").hover()
        audit("secondary-hover")
        page.locator("#message-value").focus()
        page.keyboard.press("Shift+Tab")
        page.keyboard.press("Shift+Tab")
        focus_outline("#logout")
        audit("secondary-focus")
        page.evaluate("window.__transport.deliverRaw('{invalid JSON')")
        check("could not be displayed" in page.locator("#message-error").inner_text(), "Malformed-message feedback stays in the light UI")
        audit("malformed-message-feedback")
        page.evaluate("window.__transport.failSend = true")
        page.locator("#message-value").fill("Retry this message")
        page.locator("#send-btn").click()
        check("could not be sent" in page.locator("#message-error").inner_text(), "Send-failure feedback visible")
        audit("send-failure-feedback")
        spacing = page.add_style_tag(content="* { line-height:1.5 !important; letter-spacing:.12em !important; word-spacing:.16em !important; } p { margin-bottom:2em !important; }")
        audit("wcag-text-spacing-and-reflow")
        spacing.evaluate("el => el.remove()")
        if screenshots:
            screenshots.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshots / (name + "-chat.png")), full_page=True)
        page.evaluate("window.__transport.fail()")
        check(page.locator("#send-btn").is_disabled(), "Disconnected send control disabled with readable colors")
        audit("connection-loss")
        page.locator("#logout").click()
        check(page.locator("#chat-room").is_hidden() and page.locator("#name-form").is_visible(), "Logout hides the whole chat view")
        check(page.locator("#message-list li").count() == 0, "Logout clears previous session messages")
        check(page.locator("#name-value").evaluate("el => el === document.activeElement"), "Logout restores name-input focus")
        audit("logout")
        page.locator("#name-value").fill("Retry reviewer")
        page.locator("#login").click()
        page.evaluate("window.__transport.fail()")
        check(page.locator("#login-error").is_visible() and page.locator("#login").is_enabled(), "Failed login connection is recoverable")
        audit("connection-failure")
        check(not errors and not dialogs, "No uncaught JavaScript errors or native dialogs")
        if screenshots:
            page.screenshot(path=str(screenshots / (name + "-login.png")), full_page=True)
        return {"configuration": name, "passed": True, "checks": len(checks), "audits": audits, "pairs": pairs}
    except Exception as error:
        return {"configuration": name, "passed": False, "checks": len(checks), "audits": audits, "error": str(error), "page_errors": errors}
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("ui-test-results.json"))
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    for filename in ["index.html", "style.css", "script1.js"]:
        assert (STATIC / filename).read_bytes() == (ROOT / "springboot_chatapp/target/classes/static" / filename).read_bytes(), "Tracked build mirror mismatch: " + filename
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(STATIC)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    results = {"transport": "mocked SockJS/STOMP; no live server or two-client broadcast tested", "wcag_text_threshold": 4.5, "wcag_control_border_threshold": 3, "configurations": []}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            results["browser"] = "Chromium " + browser.version
            for width, height in [(320, 800), (768, 1024), (1280, 900)]:
                for scheme in ["light", "dark"]:
                    result = exercise(browser, f"http://127.0.0.1:{server.server_port}/", width, height, scheme, args.screenshots)
                    results["configurations"].append(result)
                    print(result["configuration"], "PASS" if result["passed"] else "FAIL", result.get("error", ""), flush=True)
            browser.close()
    finally:
        server.shutdown()
    results["passed"] = all(item["passed"] for item in results["configurations"]) and len(results["configurations"]) == 6
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    raise SystemExit(0 if results["passed"] else 1)

if __name__ == "__main__":
    main()
