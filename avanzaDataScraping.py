from datetime import datetime, timedelta
from selenium import webdriver
import time
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re


class AvanzaDataScraping:
    def __init__(self, link=None):
        # Set up the driver
        options = Options()
        # options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)

        self.link = "https://www.avanza.se/borshandlade-produkter/certifikat-torg/om-certifikatet.html/943012/ava-sp500-tracker"
        if link:
            self.link = link

        self.load()
        self.data = []

    def load(self):
        # Get the link
        self.driver.get(self.link)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "highcharts-root")))

    def set_calendar(self, start_date, end_date):
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

    def select_daily_data(self):
        self.driver.execute_script("window.scrollTo(0, 0);")
        dropdown = self.driver.find_element(By.XPATH, '//button[@data-e2e="tbs-resolution-picker-button"]')
        dropdown.click()
        time.sleep(1)
        day_option_locator = (By.XPATH, "//*[@data-e2e='tbs-chart-resolution-picker']//aza-list-option-text")
        day_option = self.driver.find_element(*day_option_locator)
        day_option.click()
        time.sleep(2)

    def calculate_day_difference(self, date1, date2):
        date_format = "%Y-%m-%d"
        d1 = datetime.strptime(date1, date_format)
        d2 = datetime.strptime(date2, date_format)
        day_difference = (d1 - d2).days
        print(f"DIF_CAL: {date1} - {date2},  dif = {day_difference}")
        return day_difference

    def get_data_start_date(self):
        old_date_1 = "1900"
        old_date_2 = "1901"
        self.set_calendar(old_date_1, old_date_2)
        time.sleep(1)
        start_date = self.driver.find_element(By.XPATH,
                                              '//*[@id="instrument-period-picker"]/div[2]/div/div[1]/aza-datepicker/div[2]/div/button/span[2]')

        star_date_html = start_date.get_attribute('outerHTML')
        start_index = star_date_html.find("20")
        start_date_text = star_date_html[start_index: start_index + 10]
        return start_date_text

    def add_days_to_date(self, date, days_to_add):
        date_format = "%Y-%m-%d"
        start_date_obj = datetime.strptime(date, date_format)
        new_date_obj = start_date_obj + timedelta(days=days_to_add)
        new_date_str = new_date_obj.strftime(date_format)
        return new_date_str

    def smart_graph_scrape_over_the_years(self, start_date, end_date):
        data_start_date = self.get_data_start_date()

        print(f"SMRT: {data_start_date} - {start_date},  dif = {self.calculate_day_difference(data_start_date, start_date)}")

        if self.calculate_day_difference(data_start_date, start_date) > 0:
            start_date = data_start_date

        remaining_days = self.calculate_day_difference(start_date, end_date)
        daily_data_display_allowence = 365

        if remaining_days <= daily_data_display_allowence:
            self.set_calendar(start_date, end_date)
            self.select_daily_data()
            self.scrape_graph()
            return

        while remaining_days > daily_data_display_allowence:
            end_date = self.add_days_to_date(start_date, daily_data_display_allowence)
            self.set_calendar(start_date, end_date)
            self.select_daily_data()
            self.scrape_graph()
            start_date = end_date
            remaining_days -= daily_data_display_allowence

        self.set_calendar(start_date, self.add_days_to_date(start_date, remaining_days))
        self.select_daily_data()
        self.scrape_graph()

    def scrape_graph(self):
        time.sleep(2)
        graph = self.driver.find_element(By.CLASS_NAME, "highcharts-root")
        graph_width = graph.size['width']
        x_pos = -graph.size['width'] / 2
        action = ActionChains(self.driver)
        past_value = None

        temp, c = 0, 0

        while x_pos <= graph_width / 2:
            action.move_to_element_with_offset(graph, x_pos, 0).perform()
            x_pos = x_pos + 1

            try:
                date_price_instrument = self.driver.find_element(By.XPATH,
                                                                 "//div[@class='highcharts-label highcharts-tooltip highcharts-color-undefined']")


                print(f"\n xpos = {x_pos} out of {graph_width / 2}")

                if date_price_instrument.text != past_value:
                    past_value = date_price_instrument.text

                    print(date_price_instrument.text)
                    self.data.append(date_price_instrument.text)
                    c = temp
                else:
                    print("VAPAAOAOAOAOSDOADASDASDLASÇDKSAÖMD")
                    temp += 1
            except:
                pass

    def parse_data(self):
        parsed_data = []
        for item in self.data:
            lines = item.split('\n')
            if len(lines) >= 3:
                date_time = lines[0]
                action = lines[1]

                market_1 = ''
                price_1 = ''
                change_1 = ''
                if len(lines) >= 3:
                    market_1_details = re.search(r'(.+) (\d{1,3}\.\d{2}) \((.+?)%\)', lines[2])
                    if market_1_details:
                        market_1 = market_1_details.group(1)
                        price_1 = market_1_details.group(2)
                        change_1 = market_1_details.group(3)

                market_2 = ''
                change_2 = ''

                if len(lines) == 4:
                    market_2_details = re.search(r'(.+) (.+?)%', lines[3])
                    if market_2_details:
                        market_2 = market_2_details.group(1)
                        change_2 = market_2_details.group(2)

                date, time = date_time.split(', ')
                parsed_data.append([date, time, action, market_1, price_1, change_1, market_2, change_2])

        return parsed_data

    def save_to_dataframe(self, parsed_data):
        df = pd.DataFrame(parsed_data, columns=[
            "Date", "Time", "Action", "Market_1", "Price_1", "Change_1", "Market_2", "Change_2"
        ])
        df.to_csv("output.csv", index=False)
        df.to_excel("output.xlsx", index=False)
        print("Data saved to output.csv and output.xlsx")
        print(df)


if __name__ == "__main__":
    avanza_instance = AvanzaDataScraping()
    date_1 = "2020-03-20"
    date_2 = "2020-12-31"
    avanza_instance.smart_graph_scrape_over_the_years(date_1, date_2)

    parsed_data = avanza_instance.parse_data()
    avanza_instance.save_to_dataframe(parsed_data)
