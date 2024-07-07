""" Created on Sun Jul 23 13:42:59 2023 @author: DenizYalimYilmaz """
#import fatwoman_log_setup
#from fatwoman_log_setup import script_end_log
import logging
from fatwoman_dir_setup import VIX_C_Scrape_Data_File, Data_Feed_folder, is_platform_pc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import glob # concat libs
import os
import pandas as pd
import time
from datetime import datetime as dt


attempt = 0
max_attempts = 5
fail = False
while attempt < max_attempts:
    try:
        # setting virtual display
        if not is_platform_pc:
            print('Starting virtual display')
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1200, 900))
            display.start()
            # xrandr --query
            # ps aux | grep Xvfb
            # pkill -f 'Xvfb.*1200x900'

            print(f'Display started with PID: {display.pid}')


        print('Starting Drivers')
        # Driver Setup and get webpage
        options = webdriver.FirefoxOptions()
        # options.add_argument("--headless")
        # Set Firefox Preferences to manage downloads
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", Data_Feed_folder)
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
        driver = webdriver.Firefox(options=options)
        driver.get('http://vixcentral.com/')
        # time.sleep(2)

        # Find dropdown menu and click
        print('Clicking for download')
        xpath = "//*[contains(@transform, 'translate(762,10)')]"
        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        actions.click(element).perform()
        print('Menu is OK, clicking on DL')
        xpath = "//li[@class='highcharts-menu-item' and text()='Download CSV']"
        menu_item = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
        actions.move_to_element(menu_item).click().perform()
        print('DL is ok')
        break

    except ValueError as ve:
        print(f"Attempt {attempt + 1} failed with ValueError: {ve}")
        print(f"Retrying...")
        driver.quit()
        if not is_platform_pc: display.stop()
        attempt += 1
        time.sleep(2)

    except Exception as e:
        print(f"Attempt {attempt + 1} failed with error: {e}")
        print(f"Retrying...")
        driver.quit()
        if not is_platform_pc: display.stop()
        attempt += 1
        time.sleep(2)

else:
    print("Failed to scrape data after several attempts")
    fail = True

if not fail:
    print('Download succeeded, concat to %s' %VIX_C_Scrape_Data_File)
    time.sleep(1) # so last download would finish
    csv_files = glob.glob(os.path.join(Data_Feed_folder, '*vix-futures-term*.csv'))
    if len(csv_files) > 2: print('Have multiple files!')
    latest_file = max(csv_files, key=os.path.getmtime) #os.path.getmtime(csv_files[0])
    print('Reading %s' %latest_file)
    df = pd.read_csv(latest_file) # df is new data
    vix_row = pd.DataFrame({'Future Month':'VIX', 'Last': df['VIX Index'][0]}, index = [0])
    df = pd.concat([df, vix_row], ignore_index=True)
    df = df.drop('VIX Index', axis = 1).assign(Timestamp=dt.now().strftime('%Y-%m-%d %H:%M'))
    file_exists = os.path.exists(VIX_C_Scrape_Data_File)
    df.to_csv(VIX_C_Scrape_Data_File, mode='a', sep=',', header=not file_exists, index=False)
    
    print('Cleaning %s'%csv_files)
    for dl_file in csv_files:
        os.remove(dl_file)

    driver.quit()
    if not is_platform_pc: display.stop()
    print('Stops succeeded')

if not is_platform_pc:
    import subprocess  # To run shell commands
    result = subprocess.run(["pgrep", "-a", "Xvfb"], capture_output=True, text=True)
    print("Running Xvfb processes after stopping PyVirtualDisplay:")
    print(result.stdout)


# # Driver setup
# options = webdriver.FirefoxOptions()
# # options.add_argument("--headless")
# driver = webdriver.Firefox(options=options)
# driver.get('http://vixcentral.com/')


        # element = driver.find_element(By.XPATH, "//*[contains(@transform, 'translate(762,10)')]")
        # driver.execute_script("arguments[0].scrollIntoView();", element)

# profile.set_preference("browser.download.folderList", 2)  # 0 means to download to the desktop, 1 means to download to the default download folder, 2 means to use the directory specified for the most recent download


# context_button = WebDriverWait(driver, 2).until(
# EC.element_to_be_clickable((By.XPATH, "//g[contains(@class, 'highcharts-button')][contains(@class, 'highcharts-contextbutton')]")))
# menu_button.click()
# button.click()
# element = driver.find_element(By.XPATH, "//g[contains(@g class, 'a')]")
# element = driver.find_element(By.ID, "a") 
# element = driver.find_element(By.XPATH, "//*[contains(@title, 'Chart context menu')]")
# element = driver.find_element(By.XPATH, "//*[contains(@class, 'highcharts-no-tooltip') and contains(@class, 'highcharts-button') and contains(@class, 'highcharts-contextbutton') and contains(@class, 'highcharts-button-normal')]")


#menu_item = driver.find_element(By.XPATH, "//li[@class='highcharts-menu-item' and text()='Download CSV']") # It's safer to use WebDriverWait