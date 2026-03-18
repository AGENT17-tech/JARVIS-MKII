"""
buc_sensor.py — JARVIS MKIII BUC Portal Sensor
Microsoft Office 365 SSO login for buc.melimu.com
"""

import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vault import vault


class BUCSensor:
    def __init__(self):
        self._last_data   = {}
        self._login_tried = False
        print("[BUC SENSOR] Initialized.")

    async def read(self) -> dict:
        username = vault.get("BUC_USERNAME")
        password = vault.get("BUC_PASSWORD")
        url      = vault.get("BUC_URL")

        if not username or not password or not url:
            return self._last_data or self._default()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page    = await context.new_page()

                print("[BUC SENSOR] Navigating to portal...")
                await page.goto(url, timeout=20000)
                await page.wait_for_load_state("networkidle", timeout=10000)

                # Step 1: Click Microsoft login
                try:
                    await page.click(
                        "a[href*='microsoft'], a[href*='oauth'], "
                        "a:has-text('Microsoft'), a:has-text('Office')",
                        timeout=5000
                    )
                    print("[BUC SENSOR] Clicked Microsoft button.")
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    print("[BUC SENSOR] No Microsoft button — already on MS page.")

                # Step 2: Email
                try:
                    await page.wait_for_selector(
                        "input[type='email'], input[name='loginfmt']",
                        timeout=8000)
                    await page.fill(
                        "input[type='email'], input[name='loginfmt']", username)
                    await page.click("input[type='submit'], button[type='submit'], #idSIButton9")
                    await page.wait_for_load_state("networkidle", timeout=8000)
                    print("[BUC SENSOR] Email submitted.")
                except Exception as e:
                    print(f"[BUC SENSOR] Email error: {e}")
                    await browser.close()
                    return self._last_data or self._default()

                # Step 3: Password
                try:
                    await page.wait_for_selector(
                        "input[type='password'], input[name='passwd']",
                        timeout=8000)
                    await page.fill(
                        "input[type='password'], input[name='passwd']", password)
                    await page.click("input[type='submit'], button[type='submit'], #idSIButton9")
                    print("[BUC SENSOR] Password submitted — waiting for redirect...")
                    # Wait for redirect back to melimu
                    await page.wait_for_load_state("networkidle", timeout=20000)
                except Exception as e:
                    print(f"[BUC SENSOR] Password error: {e}")
                    await browser.close()
                    return self._last_data or self._default()

                # Step 4: Stay signed in prompt
                try:
                    await page.click("#idBtn_Back, input[value='No']", timeout=4000)
                    await page.wait_for_load_state("networkidle", timeout=8000)
                    print("[BUC SENSOR] Dismissed stay signed in.")
                except Exception:
                    pass

                # Wait extra for final redirect
                await asyncio.sleep(3)
                current_url = page.url
                print(f"[BUC SENSOR] Final URL: {current_url[:70]}")

                # Step 5: Scrape
                announcements  = 0
                grades_updated = False
                assignments    = []

                try:
                    ann = await page.query_selector_all(
                        ".activity, .section, [data-region], .course-section")
                    announcements = max(0, len(ann) - 5)
                except Exception:
                    pass

                try:
                    grade_els = await page.query_selector_all(
                        ".graded, .newgrade, [class*='grade']")
                    grades_updated = len(grade_els) > 0
                except Exception:
                    pass

                try:
                    assign_els = await page.query_selector_all(
                        ".activity.assign .instancename, "
                        "[data-activityname]")
                    for el in assign_els[:5]:
                        text = await el.inner_text()
                        if text.strip():
                            assignments.append(text.strip()[:60])
                except Exception:
                    pass

                await browser.close()

                landed_on_portal = "melimu.com" in current_url

                result = {
                    "buc_portal": {
                        "grades_updated": grades_updated,
                        "announcements":  announcements,
                        "assignments":    assignments,
                        "next_exam":      "",
                        "days_to_exam":   99,
                        "logged_in":      landed_on_portal,
                    }
                }
                self._last_data = result
                print(f"[BUC SENSOR] Done — logged_in:{landed_on_portal} "
                      f"announcements:{announcements} assignments:{len(assignments)}")
                return result

        except Exception as e:
            print(f"[BUC SENSOR] Error: {e}")
            return self._last_data or self._default()

    def _default(self):
        return {"buc_portal": {
            "grades_updated": False, "announcements": 0,
            "assignments": [], "next_exam": "",
            "days_to_exam": 99, "logged_in": False}}


buc_sensor = BUCSensor()

if __name__ == "__main__":
    async def test():
        result = await buc_sensor.read()
        buc = result.get("buc_portal", {})
        print(f"Logged in:     {buc.get('logged_in')}")
        print(f"Announcements: {buc.get('announcements')}")
        print(f"Assignments:   {buc.get('assignments')}")
    asyncio.run(test())
