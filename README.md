# rostelecom_key.rt.ru
Rostelecom Scraper for getting door key

```bash
python get_code.py --headless
```

The batch runner retries a failed account in a fresh Chromium process after a
30-second cooldown. Use `--retries 0` to disable retries or `--retry-delay N`
to change the cooldown.
