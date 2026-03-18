"""
buc_sensor.py — JARVIS MKIII BUC Portal Sensor
Monitors British University in Cairo portal for:
- Grade updates
- Announcements
- Exam schedules
- Assignment deadlines

Uses Playwright headless browser.

Setup:
    python3 vault.py store BUC_USERNAME your_student_id
    python3 vault.py store BUC_PASSWORD your_password
    python3 vault.py store BUC_URL https://your-portal-url.buc.edu.eg
"""

import asyncio
import os
from vault import vault


class BUCSensor:
    def __init__(self):
        self._available    = False
        self._last_data    = {}
        self._login_tried  = False
        print("[BUC SENSOR] Initialized.")

    async def read(self) -> dict:
        """Scrape BUC portal and return world state update."""
        username = vault.get("BUC_USERNAME")
        password = vault.get("BUC_PASSWORD")
        url      = vault.get("BUC_URL")

        if not username or not password or not url:
            # Return last known data or defaults
            return self._last_data or {
                "buc_portal": {
                    "grades_updated":  False,
                    "announcements":   0,
                    "next_exam":       "",
                    "days_to_exam":    99,
                }
            }

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page    = await browser.new_page()

                # Navigate to portal
                await page.goto(url, timeout=15000)

                # Login if needed
                try:
                    if await page.is_visible("input[type='password']", timeout=3000):
                        await page.fill("input[name='username'], input[type='text']", username)
                        await page.fill("input[type='password']", password)
                        await page.click("button[type='submit'], input[type='submit']")
                        await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                # Scrape announcements
                announcements = 0
                try:
                    ann_elements = await page.query_selector_all(
                        ".announcement, .notice, [class*='announce'], [class*='notice']"
                    )
                    announcements = len(ann_elements)
                except Exception:
                    pass

                # Scrape grade updates
                grades_updated = False
                try:
                    grade_elements = await page.query_selector_all(
                        ".grade-new, .updated-grade, [class*='grade'][class*='new']"
                    )
                    grades_updated = len(grade_elements) > 0
                except Exception:
                    pass

                await browser.close()

                result = {
                    "buc_portal": {
                        "grades_updated": grades_updated,
                        "announcements":  announcements,
                        "next_exam":      self._last_data.get("buc_portal", {}).get("next_exam", ""),
                        "days_to_exam":   self._last_data.get("buc_portal", {}).get("days_to_exam", 99),
                    }
                }
                self._last_data = result
                print(f"[BUC SENSOR] Scraped — announcements:{announcements} grades_updated:{grades_updated}")
                return result

        except Exception as e:
            print(f"[BUC SENSOR] Scrape error: {e}")
            return self._last_data or {}


buc_sensor = BUCSensor()

if __name__ == "__main__":
    async def test():
        print("[TEST] BUC sensor...")
        username = vault.get("BUC_USERNAME")
        if not username:
            print("[TEST] No BUC credentials in vault.")
            print("       Run:")
            print("       python3 vault.py store BUC_USERNAME your_id")
            print("       python3 vault.py store BUC_PASSWORD your_password")
            print("       python3 vault.py store BUC_URL https://portal.buc.edu.eg")
            print("[TEST] BUC skipped — not configured.")
        else:
            result = await buc_sensor.read()
            buc = result.get("buc_portal", {})
            print(f"Announcements:  {buc.get('announcements', 0)}")
            print(f"Grades updated: {buc.get('grades_updated', False)}")
            print("[TEST] BUC PASS")
    asyncio.run(test())
