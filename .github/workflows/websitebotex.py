import psutil
import os
import sys
os.system("pkill -9 chrome")
def kill_chrome():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "chrome" in process.info["name"].lower():
            try:
                p = psutil.Process(process.info["pid"])
                p.terminate()
            except psutil.NoSuchProcess:
                pass

kill_chrome()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

options = Options()
USER_DATA_DIR = "/tmp/seedloaf-session"
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument("--profile-directory=Default")

options.binary_location = "/opt/chrome/chrome"
options.add_argument("--headless=new")
options.add_argument("window-size=1920x1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36 "
    "OPR/133.0.0.0 (Edition std-2)"
)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--enable-javascript")
options.add_argument("--disable-web-security")
service = Service("/usr/local/bin/chromedriver")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-features=IsolateOrigins,site-per-process")
options.add_argument("--disable-extensions")

driver = webdriver.Chrome(options=options, service=service)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(window, 'opr', { get: () => ({}) });"},
)
driver.execute_cdp_cmd(
    "Network.setUserAgentOverride",
    {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 OPR/133.0.0.0 (Edition std-2)",
        "platform": "Windows",
    },
)
driver.get("https://accounts.seedloaf.com/sign-in")

WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

# --- Cloudflare challenge detection ---
# "Just a moment..." is Cloudflare's known challenge-page title. If we see
# it, the automated browser got blocked before ever reaching the real page.
if "Just a moment" in driver.title:
    print("STATUS: cloudflare_blocked")
    print(f"Blocked by Cloudflare challenge. Page title: {driver.title}")
    driver.quit()
    sys.exit(1)

driver.save_screenshot("screenshot_after_load.png")
with open("page_source_after_load.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print(f"Screenshot saved. Current URL: {driver.current_url}")
print(f"Page title: {driver.title}")


def run_loginflow(usernamesec, passwordsec):
    try:
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "identifier-field"))
        )
        print("After waiting for username:\n" + driver.current_url)

        driver.execute_script("arguments[0].scrollIntoView(true);", username)
        driver.execute_script("arguments[0].click();", username)
        username.send_keys(usernamesec)
        username.send_keys(Keys.RETURN)

        time.sleep(5)
        print("entered username")
        ran_loginflow = 1
    except Exception as e:
        print(f"Error occurred(username): {e}")
        print("After waiting for username:\n" + driver.current_url)
        # DIAGNOSTIC: capture the failure moment
        driver.save_screenshot("screenshot_username_fail.png")
        with open("page_source_username_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    try:
        try:
            wait = WebDriverWait(driver, 5)
            error_elem = wait.until(EC.visibility_of_element_located((By.ID, "error-identifier")))
            if error_elem:
                print("Username is incorrect")
                driver.quit()
                sys.exit()
        except Exception as e:
            pass

        wait = WebDriverWait(driver, 15)
        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password-field"))
        )
        print("After waiting for password:\n" + driver.current_url)

        old_url = driver.current_url
        driver.execute_script("arguments[0].scrollIntoView(true);", password)
        driver.execute_script("arguments[0].click();", password)
        password.send_keys(passwordsec)
        password.send_keys(Keys.RETURN)
        time.sleep(8)
        print("entered password")
    except Exception as e:
        print(f"Error occurred(password): {e}")
        print("After waiting for password:\n" + driver.current_url)
        driver.save_screenshot("screenshot_password_fail.png")
    ran_loginflow = 2

def open_shared_tab():
    """Click the 'Shared With You' tab so the server list loads."""
    try:
        label = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//span[contains(translate(normalize-space(.), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shared with you')]"
            ))
        )
        try:
            target = label.find_element(
                By.XPATH,
                "./ancestor::*[self::button or self::a or @role='tab'][1]"
            )
        except Exception:
            target = label

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
        driver.execute_script("arguments[0].click();", target)
        print("Clicked 'Shared With You'")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"'Shared With You' tab not found: {e}")
        driver.save_screenshot("screenshot_shared_fail.png")
        with open("page_source_shared_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return False

MARKER_FILE = "/tmp/seedloaf-session/.valid_session"
try:
    os.remove(MARKER_FILE)
except FileNotFoundError:
    pass

if "Just a moment" in driver.title:
    print("STATUS: cloudflare_blocked")
    print(f"Blocked by Cloudflare mid-flow. Page title: {driver.title}")
    driver.quit()
    sys.exit(1)

try:
    WebDriverWait(driver, 10).until(lambda d: "dashboard" in d.current_url)
    print("✅ Already logged in, at dashboard")
except:
    print("🔐 Not logged in — need to re-run login flow:\n" + driver.current_url)
    try:
        ran_loginflow = 0
        usernamesec = os.getenv("USERNAME")
        passwordsec = os.getenv("PASSWORD")
        run_loginflow(usernamesec, passwordsec)
    except Exception as e:
        print("something wrong with secrets")
    with open(MARKER_FILE, "w") as f:
        f.write("session valid")
open_shared_tab()
try:
    try:
        wait = WebDriverWait(driver, 20)
        startworld = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary")))
        print("After waiting for start:\n" + driver.current_url)
    except:
        driver.save_screenshot("screenshot_final_fail.png")
        with open("page_source_final_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        try:
            if ran_loginflow and driver.current_url == old_url:
                error_elem = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "error-password")))
                if error_elem:
                    print("Password is incorrect")
                    driver.quit()
                    sys.exit()
            else:
                try:
                    stopworld = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'btn-error')]"))
                    )
                    print("Stop button found — world already running.")
                    driver.quit()
                    sys.exit()
                except Exception as e:
                    print(f"Neither Start nor Stop button found. Something might be wrong: {e}")
                    driver.quit()
                    exit()
        except Exception as inner_exc:
            print(f"Unexpected error during start/stop button checks: {inner_exc}")
            print("After waiting for start/stop:\n" + driver.current_url)
            driver.quit()
            sys.exit()
    driver.execute_script("arguments[0].scrollIntoView(true);", startworld)

    # Retry loop: click Start, check for "servers full" toast, retry every
    # second for up to 3 minutes if servers are full.
    MAX_RETRY_SECONDS = 180
    RETRY_INTERVAL = 1
    attempt = 0
    started_successfully = False

    while attempt * RETRY_INTERVAL < MAX_RETRY_SECONDS:
        driver.execute_script("arguments[0].click();", startworld)
        attempt += 1
        print(f"STATUS: server_full_retrying {attempt}")

        # Give the toast a brief moment to appear if it's going to.
        time.sleep(1)

        try:
            full_toast = driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'All servers are currently full')]"
            )
            if full_toast.is_displayed():
                print(f"Servers full, attempt {attempt}. Retrying in {RETRY_INTERVAL}s...")
                time.sleep(RETRY_INTERVAL)
                continue
        except Exception:
            # No "servers full" toast found - assume the click worked.
            started_successfully = True
            break

    if started_successfully:
        print("STATUS: started")
        print("Clicked start - server starting.")
    else:
        print("STATUS: failed_servers_full")
        print(f"Gave up after {attempt} attempts over {MAX_RETRY_SECONDS} seconds - servers still full.")

    time.sleep(2)

except Exception as e:
    print(f"Error occurred(start): {e}")

driver.quit()
