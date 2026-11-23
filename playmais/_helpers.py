import functools
import logging
from time import sleep
from playwright.sync_api import Error as PlaywrightError

log = logging.getLogger(__name__)

def retry_on_playwright_error(retries=8, minutes_to_sleep=3, sleep_exponent=1.2):
    """Automatically restart when encountering Playwright-errors"""
    def decorator(f):
        @functools.wraps(f) # this retains docstrings
        def wrapper(self, *args, **kwargs):
            for attempt in range(1, retries+1):
                try:
                    return f(self, *args, **kwargs)
                except PlaywrightError as e:
                    increment_delay = attempt**sleep_exponent
                    retry_after_mins = minutes_to_sleep * increment_delay
                    log.warning(f"Playwright-error tijdens {f.__name__}:\n\t{str(e).rstrip()}")

                    if attempt == retries:
                        log.error(f"Teveel Playwright-errors tijdens {f.__name__}; operatie geannuleerd")
                        exit(-1)

                    log.info(f"{f.__name__} wordt over {int(retry_after_mins)} minuten opnieuw aangeroepn")
                    sleep(60 * retry_after_mins)
                    # login again, to be safe
                    if f.__name__ != "login": # when decorating login, let `try: f(...)` handle retries
                        self.login() 
        return wrapper
    return decorator
