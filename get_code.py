import re
import os
from playwright.sync_api import expect
from playwright.sync_api import sync_playwright


STATE_DIR = "states"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for file in os.listdir(STATE_DIR):
        if not file.endswith(".json"):
            continue

        state_path = os.path.join(STATE_DIR, file)

        context = browser.new_context(storage_state=state_path)
        page = context.new_page()

        page.goto("https://key.rt.ru/main/pwa/dashboard")
        
        locator = page.locator('[data-testid*="intercom-device-intercode"] p.MuiTypography-mediumBody1')
        locator.wait_for()

        code = locator.inner_text()

        page.goto("https://key.rt.ru/main/pwa/profile/details")
        locator = page.locator("p.MuiTypography-root.MuiTypography-regularBody3").nth(0)

        locator.wait_for()

        address = locator.inner_text()
      
        print(f"{file} {address} Код: {code}")

        # input(f"Залогинься и нажми Enter...")

        context.close()

    browser.close()
