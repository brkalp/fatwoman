""" Created on Sun Jul 23 13:42:59 2023 @author: DenizYalimYilmaz """
# import fatwoman_log_setup
# from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import CBOE_Scrape_Data_File
import logging
from datetime import datetime as dt
# import selenium
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import re
import pandas as pd

print("Starting CBOE Data Scrape")

def getLines(very_long_string, starter, ender):
    testString = starter + '(.*?)' + ender
    matches = re.findall(testString, very_long_string)
    return matches

attempt = 0
max_attempts = 10
while attempt < max_attempts:
    try:
        # Driver setup
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        driver.get('https://www.cboe.com/tradable_products/vix/vix_futures/')
        print('Attempting to wait for rows')
        WebDriverWait(driver, 50).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'tr[role="row"]')))
        time.sleep(10)
        source = driver.page_source
        print('len of string is %s'%len(source))

        # Get Data and parsing
        allRowsHtml = []
        allRowsHtml = getLines(source, 'tr role="row"', "</tr>")
        print('len of rows are %s'%len(allRowsHtml))
        table_2d = []
        for row in allRowsHtml:
            table_2d.append(getLines(row, 'fOvMUL">', "</div>"))

        # Clean data
        columns = ["Maturity", "Last", "Change", "High", "Low", "Settlement", "Volume"]
        df_futures = pd.DataFrame(table_2d[1:], columns=columns)
        df_futures.iloc[0,0] = 'VIX'
        df_futures['timestamp'] = dt.now().strftime('%Y-%m-%d %H:%M')

        # Add header if file does not exist
        file_exists = os.path.exists(CBOE_Scrape_Data_File)
        # Write file
        df_futures.to_csv(CBOE_Scrape_Data_File, mode='a', sep=',', header=not file_exists, index=False)

        driver.quit()
        print("Script finished successfully")
        break

    except ValueError as ve:
        print(f"Attempt {attempt + 1} failed with ValueError: {ve}. Retrying...")
        driver.quit()
        attempt += 1
        time.sleep(5)

    except Exception as e:
        print(f"Attempt {attempt + 1} failed with error: {e}. Retrying...")
        driver.quit()
        attempt += 1
        time.sleep(5)

else:
    print("Failed to scrape data after several attempts")
    driver.quit()


# script_end_log()

        # options.add_argument("-profile")
        # options.add_argument(firefox_profile1)

# import ace_tools as tools; tools.display_dataframe_to_user(name="Stock Data", dataframe=df)


        # options = Options()  #webdriver.ChromeOptions()
        # # options.add_argument("--headless")
        # driver = webdriver.Chrome(options=options)
        # driver.get('https://www.cboe.com/tradable_products/vix/vix_futures/')
        # source = driver.page_source