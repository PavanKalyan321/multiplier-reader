#!/usr/bin/env python3
"""
Test script for cashout button interaction
Helps debug the cashout action with detailed output
"""

import asyncio
import sys
from playwright.async_api import async_playwright, Page
from playwright_config import PlaywrightConfig
from playwright_game_actions import PlaywrightGameActions


async def test_cashout_visibility():
    """Test if cashout button is visible"""
    config = PlaywrightConfig().load()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Go to game
        await page.goto(config.get('game_url'), wait_until='load')
        print("[INFO] Loaded game page")
        await asyncio.sleep(2)

        # Test selector
        selector = config.get_selector('cashout_button_1')
        print(f"[INFO] Testing selector: {selector}")

        locator = page.locator(selector)
        count = await locator.count()
        print(f"[INFO] Elements found: {count}")

        if count > 0:
            # Get element details
            try:
                is_visible = await locator.is_visible()
                is_enabled = await locator.is_enabled()
                text = await locator.text_content()

                print(f"[INFO] Is visible: {is_visible}")
                print(f"[INFO] Is enabled: {is_enabled}")
                print(f"[INFO] Text content: {text}")

                # Get bounding box
                box = await locator.bounding_box()
                print(f"[INFO] Bounding box: {box}")

                # Check classes
                classes = await locator.get_attribute('class')
                print(f"[INFO] Classes: {classes}")

                # Check data attributes
                test_id = await locator.get_attribute('data-testid')
                print(f"[INFO] data-testid: {test_id}")

            except Exception as e:
                print(f"[ERROR] Failed to get element details: {e}")
        else:
            print("[WARN] Cashout button not found!")

            # Try to find any buttons
            print("\n[DEBUG] Searching for all buttons...")
            buttons = await page.query_selector_all('div[role="button"]')
            print(f"[DEBUG] Found {len(buttons)} buttons with role='button'")

            for i, btn in enumerate(buttons[:5]):
                text = await page.evaluate('el => el.textContent', btn)
                testid = await page.evaluate('el => el.getAttribute("data-testid")', btn)
                print(f"  Button {i}: data-testid={testid}, text={text}")

        # Wait for manual inspection
        print("\n[INFO] Browser will stay open for 10 seconds for inspection...")
        await asyncio.sleep(10)

        await browser.close()


async def test_cashout_click():
    """Test actual cashout button click"""
    config = PlaywrightConfig().load()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Go to game
        await page.goto(config.get('game_url'), wait_until='load')
        print("[INFO] Loaded game page")
        await asyncio.sleep(2)

        # Initialize actions
        actions = PlaywrightGameActions(page, config)

        # Wait for a cashout button to appear (simulate game running)
        print("[INFO] Waiting for cashout button to appear...")
        print("[INFO] Place a bet to activate the cashout button, then test will proceed...")

        selector = config.get_selector('cashout_button_1')
        locator = page.locator(selector)

        # Wait max 30 seconds for button
        try:
            await locator.wait_for(state='visible', timeout=30000)
            print("[OK] Cashout button appeared!")

            # Now test click
            print("[INFO] Testing click methods...")
            result = await actions.click_cashout_button(panel=1, retries=1)

            if result:
                print("[OK] CASHOUT SUCCESSFUL!")
            else:
                print("[ERROR] Cashout click failed")

        except Exception as e:
            print(f"[WARN] Cashout button did not appear: {e}")
            print("[INFO] Make sure to place a bet to activate cashout button")

        # Keep browser open for inspection
        print("\n[INFO] Browser will stay open for 10 seconds...")
        await asyncio.sleep(10)

        await browser.close()


async def test_js_cashout():
    """Test JavaScript-based cashout"""
    config = PlaywrightConfig().load()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Go to game
        await page.goto(config.get('game_url'), wait_until='load')
        print("[INFO] Loaded game page")
        await asyncio.sleep(2)

        selector = config.get_selector('cashout_button_1')
        print(f"[INFO] Using selector: {selector}")

        print("[INFO] Waiting 30 seconds for cashout button to appear...")
        print("[INFO] (Place a bet to activate it)")

        locator = page.locator(selector)

        try:
            await locator.wait_for(state='visible', timeout=30000)
            print("[OK] Cashout button found!")

            # Test JavaScript click
            print("[INFO] Attempting JavaScript click...")
            await page.evaluate(f"""
                const btn = document.querySelector('{selector}');
                console.log('Button found:', btn);
                console.log('Button classes:', btn?.className);
                console.log('Button visible:', btn?.offsetParent !== null);

                if (btn) {{
                    console.log('Clicking button via JavaScript...');
                    btn.click();
                    console.log('Click dispatched');
                }}
            """)

            print("[OK] JavaScript click executed")
            await asyncio.sleep(2)

        except Exception as e:
            print(f"[ERROR] {e}")

        await asyncio.sleep(10)
        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_cashout.py [visibility|click|js]")
        print("  visibility - Test if button is visible")
        print("  click      - Test actual click action")
        print("  js         - Test JavaScript click")
        sys.exit(1)

    test_type = sys.argv[1]

    if test_type == 'visibility':
        asyncio.run(test_cashout_visibility())
    elif test_type == 'click':
        asyncio.run(test_cashout_click())
    elif test_type == 'js':
        asyncio.run(test_js_cashout())
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)
