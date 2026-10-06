import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        # 1. Homepage
        await page.goto("http://localhost:8000")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="shot_01_homepage.png", full_page=False)
        print("Screenshot 1: homepage")

        # 2. Cerca un indirizzo reale con molte transazioni
        addr = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        await page.fill("#addr-input", addr)
        await page.screenshot(path="shot_02_input_filled.png")
        print("Screenshot 2: indirizzo inserito")

        # 3. Clicca Analizza e aspetta i risultati
        await page.click("button:has-text('Analizza')")
        try:
            await page.wait_for_selector("#stats-section", state="visible", timeout=20000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path="shot_03_stats_loaded.png")
            print("Screenshot 3: stats caricate")

            # 4. Tab Transazioni
            await page.click("button:has-text('Transazioni')")
            await page.wait_for_timeout(500)
            await page.screenshot(path="shot_04_transactions.png")
            print("Screenshot 4: tabella transazioni")

            # 5. Tab Grafo
            await page.click("button:has-text('Grafo Connessioni')")
            await page.wait_for_timeout(1500)
            await page.screenshot(path="shot_05_graph.png")
            print("Screenshot 5: grafo connessioni")

        except Exception as e:
            print(f"Timeout o errore durante la ricerca: {e}")
            await page.screenshot(path="shot_error.png")

        # 6. Test indirizzo non valido
        await page.fill("#addr-input", "indirizzoInvalido123")
        await page.click("button:has-text('Analizza')")
        await page.wait_for_timeout(500)
        await page.screenshot(path="shot_06_invalid_address.png")
        print("Screenshot 6: errore indirizzo non valido")

        await browser.close()

asyncio.run(run())
