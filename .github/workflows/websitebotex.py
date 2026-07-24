import psutil
import os
import sys
os.system("pkill -9 chrome")  # Forcefully kill all Chrome processes
def kill_chrome():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "chrome" in process.info["name"].lower():
            try:
                p = psutil.Process(process.info["pid"])
                p.terminate()  # Terminate gracefully
            except psutil.NoSuchProcess:
                pass  # Process already closed

kill_chrome()

#requiredlib = [selenium,time]
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.firefox.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
#import tempfile
#import uuid

'''
os.environ["MOZ_LOG"] = "debug"  # Enable verbose logging
# Initialize WebDriver
options = Options()
service = Service(excecutable_path="/usr/local/bin/geckodriver")
options.binary_location = '/usr/bin/firefox'
options.add_argument("--headless")
driver = webdriver.Firefox(options=options, service=service)
'''
# Chrome Options
options = Options()
# Use persistent user profile
USER_DATA_DIR = "/tmp/seedloaf-session"
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument("--profile-directory=Default")  # Optional

options.binary_location = "/opt/chrome/chrome"
options.add_argument("--headless=new")  # Use new headless mode
options.add_argument("window-size=1920x1080")  # Ensure full viewport
options.add_argument("--disable-gpu")  # Fix rendering issues in headless
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
#temp_dir = f"/tmp/chrome-user-data-{uuid.uuid4()}"
#options.add_argument(f"--user-data-dir={temp_dir}")

# Bypass detection
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--enable-javascript")
options.add_argument("--disable-web-security")
service = Service("/usr/local/bin/chromedriver")  # Path to ChromeDriver
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-features=IsolateOrigins,site-per-process")
options.add_argument("--disable-extensions")

# Initialize WebDriver
driver = webdriver.Chrome(options=options,service=service) 
driver.get("https://accounts.seedloaf.com/sign-in")
#driver.maximize_window()

# Wait for page to fully load
WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

# Login flow function
def run_loginflow(usernamesec,passwordsec):
#---------------------------
    try:
        # Wait for the username field to be visible
        username = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "identifier-field"))
        )
        print("After waiting for username:\n"+driver.current_url)
        
        driver.execute_script("arguments[0].scrollIntoView(true);", username)
        driver.execute_script("arguments[0].click();", username)
        username.send_keys(usernamesec)
        username.send_keys(Keys.RETURN)
        
        # Optional: Wait to observe behavior (debugging)
        time.sleep(5)
        print("entered username")
        ran_loginflow = 1
    except Exception as e:
        print(f"Error occurred(username): {e}")
        print("After waiting for username:\n"+driver.current_url)
        
    #---------------------------
    
    try:
        try: # Check if username is incorrect
            wait = WebDriverWait(driver, 5)
            error_elem = wait.until(EC.visibility_of_element_located((By.ID, "error-identifier")))
            if error_elem:
                print("Username is incorrect")
                driver.quit()
                sys.exit()  
        except Exception as e:
            pass
            
        # Wait for the password field to be visible
        wait = WebDriverWait(driver, 15)
        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password-field"))
        )
        print("After waiting for password:\n"+driver.current_url)
        
        # Now enter password  
        old_url = driver.current_url
        driver.execute_script("arguments[0].scrollIntoView(true);", password)
        driver.execute_script("arguments[0].click();", password)
        password.send_keys(passwordsec)
        password.send_keys(Keys.RETURN)
        # Optional: Wait to observe behavior (debugging)
        time.sleep(8)
        print("entered password")
    except Exception as e:
        print(f"Error occurred(password): {e}")
        print("After waiting for password:\n"+driver.current_url)
    ran_loginflow = 2



# Cleanup old marker
MARKER_FILE = "/tmp/seedloaf-session/.valid_session"
SESSION_DIR = "/tmp/seedloaf-session"
try:
    os.remove(MARKER_FILE)
except FileNotFoundError:
    pass
    
# Check dashboard
try:
    WebDriverWait(driver, 10).until(
        lambda d: "dashboard" in d.current_url
    )
    print("✅ Already logged in, at dashboard")
except:
    print("🔐 Not logged in — need to re-run login flow:\n"+driver.current_url)
    try: 
        ran_loginflow = 0
        usernamesec = os.getenv("USERNAME")
        passwordsec = os.getenv("PASSWORD")
        run_loginflow(usernamesec,passwordsec)
    except Exception as e:
        print("something wrong with secrets")
    # Write that Llogin flow has occured
    with open(MARKER_FILE, "w") as f:
        f.write("session valid")
    

#---------------------------
try:
    # Wait for the start button to be visible
    try:
        wait = WebDriverWait(driver, 20)
        startworld = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary")))
        print("After waiting for start:\n"+driver.current_url)
    except:
        try: # Check if password is incorrect or stop button is already present
            if  ran_loginflow and driver.current_url == old_url:
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
            print("After waiting for start/stop:\n"+driver.current_url)
            driver.quit()
            sys.exit()
    # Now ensure it’s clickable
    driver.execute_script("arguments[0].scrollIntoView(true);", startworld)
    driver.execute_script("arguments[0].click();", startworld)
    print("Clicked start")
    time.sleep(2)

except Exception as e:
    print(f"Error occurred(start): {e}")



#---------------------------
''' #--- Jasper removed this feature now (only the start success alert maybe)
    #--- Uncomment to view any error alert if ur workflow doesnt work
try:
    # Wait for the alert div to appear
    alert_div = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[@role='alert']/div[2]"))
    )
    
    # Extract the text
    alert_text = alert_div.text
    print(f"{alert_text}")

except Exception as e:
    print(f"Error while fetching alert text: {e}")

#---------------------------
# Handle alert if present
try:
    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert_text = alert.text
    print(f"Alert text: {alert_text}")
    alert.accept()  # Accept the alert
except Exception:
    print("No alert found.")
    
# Check browser logs to see if any errors are happening
for entry in driver.get_log('browser'):
    print(entry)
'''
driver.quit()
