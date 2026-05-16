import re
import os
from playwright.sync_api import expect
from playwright.sync_api import sync_playwright

import argparse

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--new_code', action='store_true', help='Create new code after deleting')
parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (no UI)')
parser.add_argument('--phone', type=str, help='Specific phone number to process (e.g., 79081538274)')
args = parser.parse_args()

STATE_DIR = "states"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=args.headless)

    # Get list of files to process
    if args.phone:
        # Process only the specified phone number
        state_files = [f"{args.phone}.json"] if os.path.exists(os.path.join(STATE_DIR, f"{args.phone}.json")) else []
        if not state_files:
            print(f"File for phone {args.phone} not found")
    else:
        # Process all JSON files
        state_files = [f for f in os.listdir(STATE_DIR) if f.endswith(".json")]

    for file in state_files:
        if not file.endswith(".json"):
            continue

        state_path = os.path.join(STATE_DIR, file)

        context = browser.new_context(storage_state=state_path)
        page = context.new_page()

        if args.new_code:
            page.goto("https://key.rt.ru/main/pwa/dashboard")
            expect(page.get_by_text("Moй дом")).to_be_visible(timeout=300_000)
            input(f"Залогинься и нажми Enter...")

            # Wait for it to disappear
            page.wait_for_timeout(3000)
            # Look for any existing code's delete button
            delete_buttons = page.locator('button svg path[fill="#70F"]').count()
            # print(f"Count - > {delete_buttons}")
            # input(f"Залогинься и нажми Enter...")
            
            if delete_buttons > 0:
                # Click the first delete button
                page.locator('button svg path[fill="#70F"]').first.click()
                
                # Wait for popup
                page.wait_for_selector('text=Вы действительно хотите удалить временный код?')

                # Wait for it to disappear
                page.wait_for_timeout(3000)
                
                # Confirm deletion
                page.click('button:has-text("Удалить")', force=True)

                # Wait for it to disappear
                page.wait_for_timeout(3000)
                # print("Deleted existing code")
                page.reload()
            # input(f"Залогинься и нажми Enter...")
            # Now create new code
            page.click('button:has-text("Создать код для домофонов")')
            # print("Created new code")
            # Refresh to see updated list
            page.wait_for_timeout(3000)
            page.reload()

        page.goto("https://key.rt.ru/main/pwa/dashboard")
        locator = page.locator('[data-testid*="intercom-device-intercode"] p.MuiTypography-mediumBody1')
        locator.wait_for()

        code = locator.inner_text()

        page.goto("https://key.rt.ru/main/pwa/profile/details")
        locator = page.locator("p.MuiTypography-root.MuiTypography-regularBody3").nth(0)

        locator.wait_for()

        address = locator.inner_text()

        phone = file.replace(".json", "")

        print(f"+{phone} {address} Код: {code}")

        # input(f"Залогинься и нажми Enter...")

        context.close()

    browser.close()
