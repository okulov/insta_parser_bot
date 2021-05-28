from time import sleep


def scroll_page(browser):
    SCROLL_PAUSE_TIME = 3
    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")
    # Scroll down to bottom
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # Wait to load page
    sleep(SCROLL_PAUSE_TIME)
    # Calculate new scroll height and compare with last scroll height
    new_height = browser.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        return True
    # last_height = new_height