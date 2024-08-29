import sys
import signal
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from datetime import datetime, timedelta
from selenium import webdriver
import time
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
from fatwoman_dir_setup import avanza_data_path, avanza_config_file
file_date_format = r"%d/%m/%Y"

class AvanzaDataScraping:
    def __init__(self, link=None):
        # Set up the driver
        options = webdriver.FirefoxOptions()
        # options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
        # options = Options()
        # options.add_argument("--headless")
        # self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        # self.link = "https://www.avanza.se/fonder/om-fonden.html/177748/amundi-fds-volatil-wld-a-usd-c"
        if link:
            self.link = link

        # def load(self):
        self.driver.get(self.link)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "highcharts-root")))
        self.instrument_name = self.driver.find_element(By.XPATH, "//h1").text
        self.data = []
        logging.info('__init__ finish')

    def get_instrument_name(self):
        logging.info('get_instrument_name')
        heading_1 = self.driver.find_element(By.XPATH, "//h1")
        print(heading_1.text)
        return heading_1.text

    def set_calendar(self, start_date, end_date):
        logging.info('set_calendar')
        cookies_bar = self.driver.find_element(By.XPATH, "/html/body/aza-app/aza-shell/div/aza-cookie-message/div/div")
        cookies_bar_height = cookies_bar.size['height']

        calendar_button = self.driver.find_element(By.XPATH, "//button[@data-timeperiod='custom']")
        self.driver.execute_script(f"window.scrollBy(0, {cookies_bar_height * 2});")
        calendar_button.click()
        time.sleep(1)

        date_buttons = self.driver.find_elements(By.XPATH, '//aza-datepicker//div[@class="desktop"]//input')
        start_date_field = date_buttons[1]
        end_date_field = date_buttons[3]

        start_date_field.clear()
        start_date_field.send_keys(start_date)
        end_date_field.clear()
        end_date_field.send_keys(end_date)
        end_date_field.send_keys(Keys.RETURN)

    # Set the graph frequency to daily
    def select_daily_data(self):
        logging.info('select_daily_data')
        print('select_daily_data')
        self.driver.execute_script("window.scrollTo(0, 0);")
        dropdown = self.driver.find_element(By.XPATH, '//button[@data-e2e="tbs-resolution-picker-button"]')
        dropdown.click()
        time.sleep(1)
        day_option_locator = (By.XPATH, "//*[@data-e2e='tbs-chart-resolution-picker']//aza-list-option-text") # not found
        day_option = self.driver.find_element(*day_option_locator)
        day_option.click()
        time.sleep(2)

    # reads graph
    def scrape_graph(self, scrape_year=None):
        logging.info('scrape_graph')
        time.sleep(2)
        graph = self.driver.find_element(By.CLASS_NAME, "highcharts-root")
        graph_width = graph.size['width']
        x_pos = -graph.size['width'] / 2
        action = ActionChains(self.driver)
        old = []
        while x_pos <= graph_width / 2:
            action.move_to_element_with_offset(graph, x_pos, 0).perform()
            x_pos = x_pos + 1
            try:
                date_price_instrument_element = self.driver.find_element(By.XPATH,
                                                                         "//div[@class='highcharts-label highcharts-tooltip highcharts-color-undefined']")
                date_price_texts = date_price_instrument_element.text.split(
                    "\n")  # Get text from webElement and split from new lines
                if old == date_price_texts:
                    continue
                old = date_price_texts
                date_price_texts = date_price_texts[:3]  # Getting rid of the fourth column
                date_price_texts.append(str(scrape_year))  # Adds the data's year
                date_price_texts.append(
                    datetime.now().strftime('%Y-%m-%d %H:%M'))  # Adds the time of scrape as a column
                # write raw data
                print(";".join(date_price_texts))
                with open(f'{avanza_instance.instrument_name}-raw.csv', 'a') as f:
                    f.write(";".join(date_price_texts))
                    f.write("\n")
                    f.flush()
                default_columns = ['day', 'quote_type', 'instrument_name_and_price', 'year', 'time_stamp', 'dummy1', 'dummy2']
                df_raw = pd.DataFrame([date_price_texts], columns=default_columns[:len(date_price_texts)])
                df_row = self.reformat_row(df_raw, scrape_year)
                filename = f'{avanza_instance.instrument_name}.csv'
                print(';'.join(df_row.iloc[0].astype(str)))
                df_row.to_csv(filename, mode='a', header=not os.path.exists(filename), sep=';', index=False)
                # # write clean data
                # with open(f'{avanza_instance.insturment_name}.csv', 'a') as file:
                #     row = ';'.join(df_row.iloc[0].astype(str))
                #     file.write(row)
                #     file.write("\n")
                #     file.flush()
                #     print(row)

            except Exception as e:
                logging.info(e)
                print(e)
                pass

        print("scrape is done")

    def reformat_row(self, input_row, scrape_year):
        # logging.info('reformat_row')
        # print('reformat_row')
        month_translation = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'maj': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'okt': '10', 'nov': '11', 'dec': '12'
        }

        # Function to convert Swedish date and time to standard format
        def convert_date(date_str, year):
            try:
                _, day, month, _ = date_str.split()
                month_num = month_translation[month.lower().replace(',', '')]
                formatted_date = f"{year}-{month_num}-{day.zfill(2)}"
                return formatted_date
            except Exception as e:
                print(e)
        input_row['Date'] = input_row.apply(lambda row: convert_date(row['day'], scrape_year), axis=1)
        input_row = input_row.drop_duplicates()  # Getting rid of duplicates
        input_row = input_row.drop(columns=['day', 'year'])  # Drops unnecessary columns

        # Move the last column to the first position
        cols = input_row.columns.tolist()  # Get a list of all column names
        cols = [cols[-1]] + cols[:-1]  # Rearrange the columns
        input_row = input_row[cols]  # Reassign reordered columns to the DataFrame
        return input_row


def gen_date_pairs(start_date):
    logging.info('gen_date_pairs')
    # Convert start date string to a datetime object
    start = datetime.strptime(start_date, file_date_format) #"%Y-%m-%d")
    current_date = datetime.now()
    pairs = []
    current_year = start.year
    while True:
        # Calculate end of the current year
        end_of_year = datetime(current_year, 12, 31)
        if end_of_year > current_date:
            end_of_year = current_date  # Adjust if the end of year is beyond the current date
        pairs.append((start.strftime(file_date_format), end_of_year.strftime(file_date_format)))
        if end_of_year == current_date:
            break  # Exit the loop if we reach the current date
        # Update start date to the beginning of the next year
        start = datetime(current_year + 1, 1, 1)
        current_year += 1
    return pairs


if __name__ == "__main__":
    instrument_name = ""

    # Read link csv
    df_link_date = pd.read_csv(avanza_config_file, encoding='ISO-8859-1', delimiter=',')
    df_link_date = df_link_date[df_link_date['Include']] # df_link_date['Start date'] = pd.to_datetime(df_link_date['Start date'], format='%d/%m/%Y')
    os.chdir(avanza_data_path)

    for index, [link, date] in df_link_date[['Link','Start date']].iterrows():
        print(f"Scraping {link} from {date}")
        logging.info(f"Scraping {link} from {date}")
        try:
            time.sleep(1)
            date_pairs = gen_date_pairs(date)
            avanza_instance = AvanzaDataScraping(link)
            instrument_name = avanza_instance.get_instrument_name()
            for start_date, end_date in date_pairs:
                start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%d/%m/%Y").strftime("%Y-%m-%d")
                avanza_instance.set_calendar(start_date, end_date)
                try :
                    avanza_instance.select_daily_data()
                except Exception as e:
                    print('select daily data failed')
                try:
                    time.sleep(1)
                    date_year = datetime.strptime(start_date, "%Y-%m-%d").year # 15/02/2021
                    avanza_instance.scrape_graph(date_year)
                except Exception as e:
                    avanza_instance.driver.quit()
                    logging.error(e)
                    print(e)
        
        except Exception as e:
            avanza_instance.driver.quit()
            logging.error(e)
            print(e)

    avanza_instance.driver.quit()
    script_end_log()




    # """
    #     if date_price_text != past_value:
    #         past_value = date_price_text
    #         # print(f"\n xpos = {x_pos} out of {graph_width / 2}")
            

    #         with open(f'{insturment_name}.txt', 'a') as file:
    #             print("file opened")
    #             for i, text in enumerate(date_price_texts):
    #                 print("anything")
    #                 if i < len(date_price_texts) - 1:
    #                     to_append = text + ';'
    #                 else:
    #                     to_append = text + f';{scrape_year}'

    #                 print(to_append)
    #                 file.write(to_append)
    #                 # self.data.append(date_price_text)  # todo
    #             c = temp
    #             file.write('\n')

    #     else:
    #         # print("VAPAAOAOAOAOSDOADASDASDLASÇDKSAÖMD")  # debugging todo
    #         temp += 1"""
    # def get_data_start_date(self):
    #     old_date_1 = "1900"
    #     old_date_2 = "1901"
    #     self.set_calendar(old_date_1, old_date_2)
    #     time.sleep(1)
    #     start_date = self.driver.find_element(By.XPATH,
    #                                           '//*[@id="instrument-period-picker"]/div[2]/div/div[1]/aza-datepicker/div[2]/div/button/span[2]')

    #     star_date_html = start_date.get_attribute('outerHTML')
    #     start_index = star_date_html.find("20")
    #     start_date_text = star_date_html[start_index: start_index + 10]
    #     return start_date_text

    # # Does not work yet

    # def calculate_day_difference(self, date1, date2):
    #     date_format = "%Y-%m-%d"
    #     d1 = datetime.strptime(date1, date_format)
    #     d2 = datetime.strptime(date2, date_format)
    #     day_difference = (d1 - d2).days
    #     # print(f"DIF_CAL: {date1} - {date2},  dif = {day_difference}")
    #     return day_difference

    # def add_days_to_date(self, date, days_to_add):
    #     date_format = "%Y-%m-%d"
    #     start_date_obj = datetime.strptime(date, date_format)
    #     new_date_obj = start_date_obj + timedelta(days=days_to_add)
    #     new_date_str = new_date_obj.strftime(date_format)
    #     return new_date_str
    # def smart_graph_scrape_over_the_years(self, start_date, end_date):
    #     data_start_date = self.get_data_start_date()

    #     print(f"SMRT: {data_start_date} - {start_date},  dif = {self.calculate_day_difference(data_start_date, start_date)}")

    #     if self.calculate_day_difference(data_start_date, start_date) > 0:
    #         start_date = data_start_date

    #     remaining_days = self.calculate_day_difference(start_date, end_date)
    #     daily_data_display_allowence = 365

    #     if remaining_days <= daily_data_display_allowence:
    #         self.set_calendar(start_date, end_date)
    #         self.select_daily_data()
    #         self.scrape_graph()
    #         return

    #     while remaining_days > daily_data_display_allowence:
    #         end_date = self.add_days_to_date(start_date, daily_data_display_allowence)
    #         self.set_calendar(start_date, end_date)
    #         self.select_daily_data()
    #         self.scrape_graph()
    #         start_date = end_date
    #         remaining_days -= daily_data_display_allowence

    #     self.set_calendar(start_date, self.add_days_to_date(start_date, remaining_days))
    #     self.select_daily_data()
    #     self.scrape_graph(),

    # def parse_data(self):
    # parsed_data = []
    # for item in self.data:
    #     lines = item.split('\n')
    #     if len(lines) >= 3:
    #         date_time = lines[0]
    #         action = lines[1]

    #         market_1 = ''
    #         price_1 = ''
    #         change_1 = ''
    #         if len(lines) >= 3:
    #             market_1_details = re.search(r'(.+) (\d{1,3}\.\d{2}) \((.+?)%\)', lines[2])
    #             if market_1_details:
    #                 market_1 = market_1_details.group(1)
    #                 price_1 = market_1_details.group(2)
    #                 change_1 = market_1_details.group(3)

    #         market_2 = ''
    #         change_2 = ''

    #         if len(lines) == 4:
    #             market_2_details = re.search(r'(.+) (.+?)%', lines[3])
    #             if market_2_details:
    #                 market_2 = market_2_details.group(1)
    #                 change_2 = market_2_details.group(2)

    #         date, time = date_time.split(', ')
    #         parsed_data.append([date, time, action, market_1, price_1, change_1, market_2, change_2])

    # return parsed_data

# link_date_dict = {
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1063549/ishares--treasury-bond-20yr-ucits-etf-usd-dist": "2020-03-17",
#     # iShares $ Treasury Bond 20+yr UCITS ETF USD (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1064244/amundi-us-treasury-bond-long-dated-ucits-etf-dist": "2020-03-18",
#     # Amundi US Treasury Bond Long Dated UCITS ETF Dist
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1233042/spdr-bloomberg-10-year-u-s--treasury-bond-ucits-etf-dist": "2021-06-02",
#     # SPDR Bloomberg 10+ Year U.S. Treasury Bond UCITS ETF (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/384764/ishares--treasury-bond-7-10yr-ucits-etf-usd-dist": "2020-03-17",
#     # iShares $ Treasury Bond 7-10yr UCITS ETF USD (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1182073/invesco-us-treasury-bond-7-10-year-ucits-etf-dist": "2021-02-15",
#     # Invesco US Treasury Bond 7-10 Year UCITS ETF Dist
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1063519/ishares--treasury-bond-7-10yr-ucits-etf-eur-hedged-dist": "2020-03-21",
#     # iShares $ Treasury Bond 7-10yr UCITS ETF EUR Hedged (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1064095/ishares--treasury-bond-3-7yr-ucits-etf-eur-hedged-dist": "2020-04-02",
#     # iShares $ Treasury Bond 3-7yr UCITS ETF EUR Hedged (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1182083/invesco-us-treasury-bond-1-3-year-ucits-etf-dist": "2021-04-02",
#     # Invesco US Treasury Bond 1-3 Year UCITS ETF Dist
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/384740/ishares--treasury-bond-1-3yr-ucits-etf-usd-dist": "2020-11-14",
#     # iShares $ Treasury Bond 1-3yr UCITS ETF USD (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1233135/invesco-us-treasury-bond-0-1-year-ucits-etf-dist": "2021-10-15",
#     # Invesco US Treasury Bond 0-1 Year UCITS ETF Dist
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/479484/xtrackers-ii-usd-overnight-rate-swap-ucits-etf-1c": "2020-03-17",
#     # Xtrackers II USD Overnight Rate Swap UCITS ETF 1C
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/636979/xact-obligation": "2016-02-25",
#     # XACT Obligation
#     "https://www.avanza.se/fonder/om-fonden.html/536695/lannebo-high-yield": "2015-01-30",  # Lannebo High Yield
#     "https://www.avanza.se/fonder/om-fonden.html/2069/lannebo-rantefond-kort": "2001-11-13",  # Lannebo Räntefond Kort
#     "https://www.avanza.se/fonder/om-fonden.html/1131558/lannebo-sustainable-corporate-bond-a-sek": "2020-02-19",
#     # Lannebo Sustainable Corporate Bond A SEK
#     "https://www.avanza.se/fonder/om-fonden.html/94867/spiltan-rantefond-sverige": "2007-09-17",
#     # Spiltan Räntefond Sverige
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/384683/ishares-govt-bond-15-30yr-ucits-etf-eur-dist": "2020-03-17",
#     # iShares Govt Bond 15-30yr UCITS ETF EUR (Dist)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/479457/xtrackers-ii-eurozone-government-bond-25-ucits-etf-1c": "2020-03-17",
#     # Xtrackers II Eurozone Government Bond 25+ UCITS ETF 1C
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1063593/ishares-govt-bond-3-7yr-ucits-etf-eur-acc": "2020-03-25",
#     # iShares Govt Bond 3-7yr UCITS ETF EUR (Acc)
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/479446/xtrackers-ii-eur-overnight-rate-swap-ucits-etf-1c": "2021-06-02",
#     # Xtrackers II EUR Overnight Rate Swap UCITS ETF 1C
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1063610/xtrackers-ii-eur-overnight-rate-swap-ucits-etf-1d": "2020-03-21",
#     # Xtrackers II EUR Overnight Rate Swap UCITS ETF 1D
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1064006/amundi-eur-overnight-return-ucits-etf-acc": "2020-03-19",
#     # Amundi EUR Overnight Return UCITS ETF Acc
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1063629/xtrackers-ii-gbp-overnight-rate-swap-ucits-etf-1d": "2020-03-20",
#     # Xtrackers II GBP Overnight Rate Swap UCITS ETF 1D
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/384766/ishares-emerging-asia-local-govt-bond-ucits-etf-usd-dist": "2020-03-16",
#     # iShares Emerging Asia Local Govt Bond UCITS ETF USD (Dist)
#     "https://www.avanza.se/borshandlade-produkter/certifikat-torg/om-certifikatet.html/943012/ava-sp500-tracker": "2019-05-21",
#     # AVA SP500 TRACKER
#     "https://www.avanza.se/fonder/om-fonden.html/1025150/avanza-usa": "2019-12-17",  # Avanza USA
#     "https://www.avanza.se/fonder/om-fonden.html/878733/avanza-global": "2018-08-21",  # Avanza Global
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/365296/vanguard-s-p-500-ucits-etf---usd-dist": "2020-03-16",
#     # Vanguard S&P 500 UCITS ETF - (USD) Dist
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1063851/ishares-core-s-p-500-ucits-etf-usd-acc": "2020-03-16",
#     # iShares Core S&P 500 UCITS ETF USD (Acc)
#     "https://www.avanza.se/aktier/om-aktien.html/5246/investor-a": "1982-01-07",  # Investor A
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/5649/xact-sverige": "2004-05-11",
#     # XACT Sverige
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/159464/xact-norden": "2009-01-15",
#     # XACT Norden
#     "https://www.avanza.se/borshandlade-produkter/etf-torg/om-fonden.html/1064252/amundi-msci-usa-minimum-volatility-factor-ucits-etf-c": "2020-03-16"
#     # Amundi MSCI USA Minimum Volatility Factor UCITS ETF (C)
# }
# new_df = pd.DataFrame([link_date_dict]).T.reset_index()
# new_df.columns = ['Link','Start date']
# new_df.to_csv('New_df.csv', sep=';', index=False)