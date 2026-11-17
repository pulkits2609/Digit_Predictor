"""Live Chromium/Edge smoke test. Start the frontend and trained API first."""
import json
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:5173/")
        expect(page.get_by_text("Model ready", exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_role("heading", name="No prediction yet")).to_be_visible()
        assert page.get_by_role("link", name="How it works").count() == 0
        assert page.get_by_role("link", name="Model insights").count() == 0
        assert page.locator("#model-insights").count() == 0
        button = page.get_by_role("button", name="Recognize digit", exact=True)
        expect(button).to_be_disabled()
        canvas = page.locator("canvas")
        bounds = canvas.bounding_box()
        assert bounds
        x, y, size = bounds["x"], bounds["y"], bounds["width"]
        page.mouse.move(x + size * .28, y + size * .25)
        page.mouse.down()
        page.mouse.move(x + size * .73, y + size * .25, steps=15)
        page.mouse.move(x + size * .42, y + size * .78, steps=20)
        page.mouse.up()
        expect(button).to_be_enabled()
        page.get_by_role("button", name="Undo", exact=True).click()
        expect(button).to_be_disabled()
        page.get_by_role("button", name="Redo", exact=True).click()
        expect(button).to_be_enabled()
        with page.expect_response(lambda response: response.url.endswith("/api/v1/predict")) as pending:
            button.click()
        drawing_response = pending.value
        assert drawing_response.status == 200
        draw = drawing_response.json()
        expect(page.locator(".predicted-digit")).to_have_text(str(draw["prediction"]))
        expect(page.locator(".prediction-explanation")).to_contain_text(f"gave {draw['prediction']} the highest score")
        expect(page.locator(".probability-chart > div")).to_have_count(10)
        expect(page.get_by_alt_text("Actual preprocessed 28 by 28 grayscale CNN input")).to_be_visible()
        page.get_by_role("button", name="Clear canvas").click()
        expect(button).to_be_disabled()
        page.get_by_role("tab", name="Upload an image").click()
        page.locator("input[type=file]").set_input_files(str(ROOT / "backend/models/samples/digit-7.png"))
        with page.expect_response(lambda response: response.url.endswith("/api/v1/predict")) as pending:
            button.click()
        upload_response = pending.value
        assert upload_response.status == 200
        upload = upload_response.json()
        expect(page.locator(".predicted-digit")).to_have_text(str(upload["prediction"]))
        with page.expect_response(lambda response: response.url.endswith("/api/v1/visualize")) as pending:
            page.get_by_text("How the model sees your digit", exact=True).click()
        assert pending.value.status == 200
        expect(page.get_by_alt_text("conv1 activation channel 1", exact=True)).to_be_visible()
        page.route("**/api/v1/predict", lambda route: route.abort("connectionrefused"))
        button.click()
        expect(page.get_by_role("alert")).to_contain_text("Cannot reach")
        page.unroute("**/api/v1/predict")
        page.get_by_role("button", name="Try again", exact=True).click()
        expect(page.locator(".predicted-digit")).to_be_visible(timeout=20000)
        page.goto("http://127.0.0.1:5173/#model-insights")
        expect(page.get_by_text("99.24", exact=False).first).to_be_visible()
        page.route("http://127.0.0.1:8000/**", lambda route: route.abort("connectionrefused"))
        page.reload()
        expect(page.get_by_text("99.24", exact=False).first).to_be_visible()
        page.get_by_role("link", name="Workspace", exact=True).click()
        expect(page.get_by_role("heading", name="No prediction yet")).to_be_visible()
        expect(page.get_by_text("Server unavailable", exact=True)).to_be_visible()
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            page.wait_for_timeout(150)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Horizontal overflow at {width}px"
        assert not errors, errors
        touch_page = browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
        touch_page.goto("http://127.0.0.1:5173/")
        touch_canvas = touch_page.locator("canvas")
        touch_canvas.scroll_into_view_if_needed()
        touch_bounds = touch_canvas.bounding_box()
        assert touch_bounds
        session = touch_page.context.new_cdp_session(touch_page)
        points = [(.25, .25), (.4, .25), (.6, .25), (.75, .25), (.65, .4), (.55, .6), (.4, .8)]
        for index, (px, py) in enumerate(points):
            session.send("Input.dispatchTouchEvent", {"type": "touchStart" if index == 0 else "touchMove",
                         "touchPoints": [{"x": touch_bounds["x"] + px * touch_bounds["width"],
                                          "y": touch_bounds["y"] + py * touch_bounds["height"]}]})
        session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        touch_button = touch_page.get_by_role("button", name="Recognize digit", exact=True)
        expect(touch_button).to_be_enabled()
        touch_button.click()
        expect(touch_page.locator(".predicted-digit")).to_be_visible(timeout=20000)
        browser.close()
        print(json.dumps({"status": "passed", "draw_prediction": draw["prediction"],
                          "upload_prediction": upload["prediction"], "browser_errors": errors,
                          "viewports": [320, 390, 768, 1440],
                          "checks": ["draw", "undo", "redo", "clear", "upload", "genuine API",
                                     "ten classes", "preview", "failure", "recovery", "offline artifacts",
                                     "Chromium emulated touch drawing", "real convolution feature maps",
                                     "minimal workspace", "result explanation", "preserved insights location"]}, indent=2))


if __name__ == "__main__":
    main()
