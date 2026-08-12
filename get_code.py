import argparse
import os
import sys
import time

from playwright.sync_api import expect, sync_playwright


STATE_DIR = "states"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--new_code", action="store_true", help="Create new code after deleting"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode (no UI)"
    )
    parser.add_argument(
        "--phone", type=str, help="Specific phone number to process (e.g., 79081538274)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Number of retries with a fresh browser after an error (default: 1)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=30,
        help="Cooldown in seconds before retrying a throttled request (default: 30)",
    )
    args = parser.parse_args()
    if args.retries < 0:
        parser.error("--retries must be zero or greater")
    if args.retry_delay < 0:
        parser.error("--retry-delay must be zero or greater")
    return args


def get_state_files(phone):
    state_files = sorted(
        filename
        for filename in os.listdir(STATE_DIR)
        if filename.endswith(".json")
    )

    if phone:
        matches = [
            filename
            for filename in state_files
            if filename == f"{phone}.json" or filename.endswith(f"-{phone}.json")
        ]
        if matches:
            return matches

        print(f"File for phone {phone} not found")
        return []

    return state_files


def get_phone_from_filename(filename):
    return filename.removesuffix(".json").split("-", 1)[-1]


def process_phone(browser, filename, create_new_code):
    phone = get_phone_from_filename(filename)
    state_path = os.path.join(STATE_DIR, filename)
    context = browser.new_context(storage_state=state_path)

    try:
        page = context.new_page()

        if create_new_code:
            page.goto("https://key.rt.ru/main/pwa/dashboard")
            expect(page.get_by_text("Moй дом")).to_be_visible(timeout=300_000)
            page.wait_for_timeout(3000)

            delete_buttons = page.locator('button svg path[fill="#70F"]').count()
            if delete_buttons > 0:
                page.locator('button svg path[fill="#70F"]').first.click()
                page.wait_for_selector(
                    "text=Вы действительно хотите удалить временный код?"
                )
                page.wait_for_timeout(3000)
                page.click('button:has-text("Удалить")', force=True)
                page.wait_for_timeout(3000)
                page.reload()

            page.click('button:has-text("Создать код")')
            page.wait_for_timeout(3000)
            page.reload()

        page.goto("https://key.rt.ru/main/pwa/dashboard")
        code_locator = page.locator(
            '[data-testid*="intercom-device-intercode"] p.MuiTypography-mediumBody1'
        )
        code_locator.wait_for()
        code = code_locator.inner_text()

        page.goto("https://key.rt.ru/main/pwa/profile/details")
        address_locator = page.locator(
            "p.MuiTypography-root.MuiTypography-regularBody3"
        ).nth(0)
        address_locator.wait_for()
        address = address_locator.inner_text()

        return f"{address} Код: {code}"
    finally:
        try:
            context.close()
        except Exception:
            # Do not let cleanup hide the request error that triggered it.
            pass


def close_browser(browser):
    if browser is None:
        return

    try:
        browser.close()
    except Exception:
        # The browser process may already have crashed or disconnected.
        pass


def main():
    args = parse_args()
    state_files = get_state_files(args.phone)

    try:
        with sync_playwright() as playwright:
            browser = None

            try:
                for filename in state_files:
                    phone = get_phone_from_filename(filename)
                    last_error = None

                    for attempt in range(args.retries + 1):
                        try:
                            if browser is None or not browser.is_connected():
                                close_browser(browser)
                                browser = playwright.chromium.launch(
                                    headless=args.headless
                                )

                            result = process_phone(
                                browser, filename, args.new_code
                            )
                            print(result, flush=True)
                            last_error = None
                            break
                        except Exception as error:
                            last_error = error
                            close_browser(browser)
                            browser = None

                            if attempt < args.retries:
                                error_message = str(error).splitlines()[0]
                                print(
                                    f"[{phone}] {type(error).__name__}: "
                                    f"{error_message}; restarting Chromium in "
                                    f"{args.retry_delay:g}s",
                                    file=sys.stderr,
                                )
                                if args.retry_delay:
                                    time.sleep(args.retry_delay)

                    if last_error is not None:
                        error_message = str(last_error).splitlines()[0]
                        print(f"+{phone} : Ошибка", flush=True)
                        print(
                            f"[{phone}] {type(last_error).__name__}: {error_message}",
                            file=sys.stderr,
                        )
            finally:
                close_browser(browser)
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
