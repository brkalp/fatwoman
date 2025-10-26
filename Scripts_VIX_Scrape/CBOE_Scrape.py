# """Created on 07-21-2024 23:07:40 @author: DenizYalimYilmaz"""

from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import CBOE_Scrape_Data_File, CBOE_Scrape_timestamp_format

import logging
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import pandas as pd

TIMESTAMP_FORMAT = CBOE_Scrape_timestamp_format
HOUR_FORMAT = "%H:%M"
MAX_ATTEMPTS = 1
LINK = "https://www.cboe.com/tradable_products/vix/vix_futures/"


def _clean_table_and_save_to_csv(table_2d):
    logging.info("Atttempting to manip the table scrapped at csv_manip")
    # Clean data
    columns = ["Maturity", "Last", "Change", "High", "Low", "Settlement", "Volume"]
    df_futures = pd.DataFrame(table_2d[1:], columns=columns)
    df_futures.iloc[0, 0] = "VIX"
    df_futures["Volume"].replace(",", "", regex=True, inplace=True)
    df_futures["Volume"] = pd.to_numeric(df_futures["Volume"], errors="coerce")
    df_futures["Settlement"].replace("-", "", regex=True, inplace=True)
    df_futures["Settlement"] = pd.to_numeric(df_futures["Settlement"], errors="coerce")
    df_futures["Timestamp"] = dt.now().strftime(TIMESTAMP_FORMAT)
    df_futures["Hour"] = dt.now().strftime(HOUR_FORMAT)
    # data includes vix itself so maturity formatting is not valid
    # df_futures["Maturity"] = dt.now().strftime(HOUR_FORMAT)
    # df_futures['Maturity'] = pd.to_datetime(df_futures['Maturity'], format='%m/%d/%Y') #CBOE_RAW_timestamp_format = '%m/%d/%Y'

    # Write file Add header if file does not exist
    try:
        file_exists = os.path.exists(CBOE_Scrape_Data_File)
        df_futures.to_csv(
            CBOE_Scrape_Data_File,
            mode="a",
            sep=",",
            header=not file_exists,
            index=False,
        ) 
    except Exception as e:
        msg = f"error while writing to csv: \n {e}"
        logging.error(msg)
        print(msg)
        return False
    print(f"Successfully cleaned data gathered and saved to {CBOE_Scrape_Data_File}")
    return True


def main():
    logging.info("Starting CBOE Data Scrape " + time.strftime("%Y-%m-%d %H:%M:%S"))

    for _attempt in range(MAX_ATTEMPTS):
        logging.info("Setting up the driver")
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        success = False
        with webdriver.Firefox(options=options) as driver:

            driver.get(LINK)
            logging.info("Driver get done; Driver setup complete, initiating scraping")

            try:
                table_2d = []
                table_element = driver.find_element(By.TAG_NAME, "table")
                for row in table_element.find_elements(By.TAG_NAME, "tr"):
                    values = [col.text for col in row.find_elements(By.TAG_NAME, "td")]
                    table_2d.append(values)

                # drop first column of each row
                for row in table_2d:
                    if row:
                        row.pop(0)

                if _clean_table_and_save_to_csv(
                    table_2d=table_2d
                ):  # clean data and save to csv
                    success = True

            except ValueError as ve:
                msg = (
                    f"Attempt {_attempt + 1} failed with ValueError: {ve}. Retrying..."
                )
                logging.error(msg)
                print(msg)
                time.sleep(5)

            except Exception as e:
                msg = f"Attempt {_attempt + 1} failed with error: {e}. Retrying..."
                logging.error(msg)
                print(msg)

                time.sleep(5)

        if success:
            break

if __name__ == "__main__":
    main()

    # TODO: script_end_log()

    # options.add_argument("-profile")
    # options.add_argument(firefox_profile1)

# import ace_tools as tools; tools.display_dataframe_to_user(name="Stock Data", dataframe=df)


# options = Options()  #webdriver.ChromeOptions()
# # options.add_argument("--headless")
# driver = webdriver.Chrome(options=options)
# driver.get('https://www.cboe.com/tradable_products/vix/vix_futures/')
# source = driver.page_source


# df_temp = df0['timestamp'][:5391]
# df_temp = pd.to_datetime(df_temp, format='%d/%m/%Y %H:%M').dt.strftime(timestamp_format)
# df0['timestamp'][:5391] = df_temp.copy()

# """

# from fatwoman_log_setup import script_end_log
# from fatwoman_dir_setup import CBOE_Scrape_Data_File, CBOE_Scrape_timestamp_format
# import logging
# from datetime import datetime as dt
# # import selenium
# from selenium import webdriver
# # from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import os
# import time
# import re
# import pandas as pd

# print("Starting CBOE Data Scrape "+ time.strftime("%Y-%m-%d %H:%M:%S"))

# def getLines(very_long_string, starter, ender):
#     testString = starter + '(.*?)' + ender
#     matches = re.findall(testString, very_long_string)
#     return matches

# timestamp_format = CBOE_Scrape_timestamp_format
# hour_format = '%H:%M'
# attempt = 0
# max_attempts = 5
# while attempt < max_attempts:
#     try:
#         # Driver setup
#         options = webdriver.FirefoxOptions()
#         options.add_argument("--headless")
#         driver = webdriver.Firefox(options=options)
#         driver.get('https://www.cboe.com/tradable_products/vix/vix_futures/'); print('Driver get done')
#         WebDriverWait(driver, 100).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'tr[role="row"]')))
#         print('Table is visible: %s' %'tr[role="row"]')
#         time.sleep(10)
#         source = driver.page_source #;print('len of string is %s'%len(source))

#         # Get Data and parsing
#         allRowsHtml = []
#         allRowsHtml = getLines(source, 'tr role="row"', "</tr>"); print('len of rows are %s'%len(allRowsHtml))
#         table_2d = []
#         for row in allRowsHtml:
#             table_2d.append(getLines(row, 'fOvMUL">', "</div>"))

#         # Clean data
#         columns = ["Maturity", "Last", "Change", "High", "Low", "Settlement", "Volume"]
#         df_futures = pd.DataFrame(table_2d[1:], columns=columns)
#         df_futures.iloc[0,0] = 'VIX'
#         df_futures['Volume'].replace(',','', regex=True, inplace=True)
#         df_futures['Volume'] = pd.to_numeric(df_futures['Volume'], errors='coerce')
#         df_futures['Settlement'].replace('-','', regex=True, inplace=True)
#         df_futures['Settlement'] = pd.to_numeric(df_futures['Settlement'], errors='coerce')
#         df_futures['Timestamp'] = dt.now().strftime(timestamp_format)
#         df_futures['Hour']      = dt.now().strftime(hour_format)
#         # data includes vix itself so maturity formatting is not valid
#         # df_futures['Maturity']      = dt.now().strftime(hour_format)
#         # df_futures['Maturity'] = pd.to_datetime(df_futures['Maturity'], format='%m/%d/%Y') #CBOE_RAW_timestamp_format = '%m/%d/%Y'

#         # Write file Add header if file does not exist
#         file_exists = os.path.exists(CBOE_Scrape_Data_File)
#         df_futures.to_csv(CBOE_Scrape_Data_File, mode='a', sep=',', header=not file_exists, index=False)

#         driver.quit()
#         #print("Script finished successfully")
#         break

#     except ValueError as ve:
#         print(f"Attempt {attempt + 1} failed with ValueError: {ve}. Retrying...")
#         logging.error(f"Attempt {attempt + 1} failed with ValueError: {ve}. Retrying...")
#         driver.quit()
#         attempt += 1
#         time.sleep(5)

#     except Exception as e:
#         print(f"Attempt {attempt + 1} failed with error: {e}. Retrying...")
#         logging.error(f"Attempt {attempt + 1} failed with     error: {e}. Retrying...")
#         driver.quit()
#         attempt += 1
#         time.sleep(5)

# else:
#     print("CBOE: Failed to scrape data after several attempts")
#     logging.critical("CBOE: Failed to scrape data after several attempts")
#     driver.quit()


# script_end_log()

#         # options.add_argument("-profile")
#         # options.add_argument(firefox_profile1)

# # import ace_tools as tools; tools.display_dataframe_to_user(name="Stock Data", dataframe=df)


#         # options = Options()  #webdriver.ChromeOptions()
#         # # options.add_argument("--headless")
#         # driver = webdriver.Chrome(options=options)
#         # driver.get('https://www.cboe.com/tradable_products/vix/vix_futures/')
#         # source = driver.page_source


# # df_temp = df0['timestamp'][:5391]
# # df_temp = pd.to_datetime(df_temp, format='%d/%m/%Y %H:%M').dt.strftime(timestamp_format)
# # df0['timestamp'][:5391] = df_temp.copy()


# """
