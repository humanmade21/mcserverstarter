import psutil
import os
import sys
os.system("pkill -9 opera")  # Forcefully kill all Opera processes
def kill_opera():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "opera" in process.info["name"].lower():
            try:
                p = psutil.Process(process.info["pid"])
                p.terminate()
            except psutil.NoSuchProcess:
                pass

kill_opera()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

OPERA_GX_PATH = os.getenv("OPERA_GX_PATH", "/usr/bin/opera-gx")

# Opera GX bundles its own libffmpeg.so in its install directory rather than
# a standard system location, so the dynamic linker needs to be told where
# to find it explicitly, or the browser process crashes immediately on launch.
opera_lib_dir = os.path.dirname(os.path.realpath(OPERA_GX_PATH))
os.environ["LD_LIBRARY_PATH"] = opera_lib_dir + ":" + os.environ.get("LD_LIBRARY_PATH", "")

options = Options()
USER_DATA_DIR = "/tmp/seedloaf-session"
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument("--profile-directory=Default")

options.binary_location = OPERA_GX_PATH
options.add_argument("--headless=new")
options.add_argument("window-size=1920x1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--enable-javascript")
options.add_argument("--disable-web-security")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-features=IsolateOrigins,site-per-process")
options.add_argument("--disable-extensions")

service = Service("/usr/local/bin/chromedriver")

driver = webdriver.Chrome(options=options, service=service)
driver.get("https://accounts.seedloaf.com/sign-in")

WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

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

        global old_url
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
    ran_loginflow = 2


MARKER_FILE = "/tmp/seedloaf-session/.valid_session"
SESSION_DIR = "/tmp/seedloaf-session"
try:
    os.remove(MARKER_FILE)
except FileNotFoundError:
    pass

try:
    WebDriverWait(driver, 10).until(
        lambda d: "dashboard" in d.current_url
    )
    print("✅ Already logged in, at dashboard")
    ran_loginflow = 0
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

try:
    try:
        wait = WebDriverWait(driver, 20)
        stopworld = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, "//button[contains(@class, 'btn-error')]"))
        )
        print("After waiting for stop:\n" + driver.current_url)
    except:
        try:
            if ran_loginflow and driver.current_url == old_url:
                error_elem = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "error-password")))
                if error_elem:
                    print("Password is incorrect")
                    driver.quit()
                    sys.exit()
            else:
                try:
                    startworld = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary")))
                    print("Start button found — world already stopped.")
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
    driver.execute_script("arguments[0].scrollIntoView(true);", stopworld)
    driver.execute_script("arguments[0].click();", stopworld)
    print("Clicked stop")
    time.sleep(2)

except Exception as e:
    print(f"Error occurred(start): {e}")

driver.quit()
