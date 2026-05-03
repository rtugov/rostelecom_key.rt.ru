import argparse

import re
import os
from playwright.sync_api import expect
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num", type=int, default=1,
                        help="Количество браузеров (по умолчанию 1)")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://key.rt.ru/main/auth/b2c/otp_code")

        expect(page.get_by_text("Временный код")).to_be_visible(timeout=300_000)

        page.goto("https://key.rt.ru/main/pwa/profile/details")
        locator = page.locator("p.MuiTypography-root.MuiTypography-regularBody3").nth(1)

        locator.wait_for()
      
        phone = re.sub(r'\D', '', locator.inner_text())

        # input(f"Залогинься и нажми Enter...")

        state_file = f"{phone}.json"
        context.storage_state(path=f"states/{state_file}")

        print(f"Сессия сохранена в {state_file}")

if __name__ == "__main__":
    main()
