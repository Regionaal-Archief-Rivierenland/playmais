import re
from playwright.sync_api import Playwright, sync_playwright, expect
from time import sleep
from datetime import datetime, timedelta

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://rar.maisflexis.com/ords/f?p=200102:LOGIN_DESKTOP::::::")
    page.get_by_role("textbox", name="Inlognaam").fill("RAR_60")
    page.get_by_role("textbox", name="Inlognaam").press("Tab")
    page.get_by_role("textbox", name="Wachtwoord").fill(password)
    page.get_by_role("textbox", name="Wachtwoord").press("Enter")
    page.get_by_role("treeitem", name="Beheren").click()
    page.get_by_role("treeitem", name="Toegangen", exact=True).click()
    files = ["/home/ludo/1764_1_102_flexis.txt"]
    for file in files:
        def importeren():
            page.get_by_role("button", name="Importeren").click()
            frame = page.locator("iframe[title=\"Importeren\"]").content_frame
            sleep(4)
            frame.locator("input[type='file']").set_input_files(file)
            if frame.get_by_text(file.split("/")[-1]).is_visible():
                print("File is uploaded successfully.")
            else:
                print("File upload failed.")
                sleep(5)
                frame.get_by_role("button", name="Annuleren").click()
                importeren()
        importeren()
        page.locator("iframe[title=\"Importeren\"]").content_frame.get_by_role("button", name="Ok").click()
        page.wait_for_function(
            "document.querySelector('.js')?.textContent?.includes('Wacht op beoordeling')",
            timeout=0
        )
        expect(page.locator("iframe[title=\"Logging\"]").content_frame.get_by_label("Logging / Voortgang")).to_contain_text("Bezig...")
        text = page.locator("iframe[title=\"Logging\"]").content_frame.get_by_label("Logging / Voortgang").inner_text()
        print(text)

password = getpass.getpass()
with sync_playwright() as playwright:
    run(playwright)

