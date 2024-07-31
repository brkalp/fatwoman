from datetime import datetime, timedelta

from selenium import webdriver
import time

from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AvanzaDataScraping:
    def __init__(self, link = None):
        # Set up the driver
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)

        # 'https://www.avanza.se/borshandlade-produkter/certifikat-torg/om-certifikatet.html/1395805/bear-vix-x4-von3'
        # link = "https://www.avanza.se/fonder/om-fonden.html/878733/avanza-global"
        self.link = "https://www.avanza.se/borshandlade-produkter/certifikat-torg/om-certifikatet.html/943012/ava-sp500-tracker"

        if link:
            self.link = link

        self.load()


    def load(self):
        # Get the link
        self.driver.get(self.link)

        # It takes a bit for Avanza to load, so a buffer like time.sleep(5) is healthy, feel free to increase it 8 or 10 secs if internet speed is not up to par
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "highcharts-root")))
    def set_calendar(self, start_date, end_date):
        # Now we will set up the date, to click the calendar button we might have to go behind the cookies button
        cookies_bar = self.driver.find_element(By.XPATH, "/html/body/aza-app/aza-shell/div/aza-cookie-message/div/div")
        cookies_bar_height = cookies_bar.size['height']

        # Find the calendar_button
        calendar_button = self.driver.find_element(By.XPATH, "//button[@data-timeperiod='custom']")

        # Scroll down for calendar_button to be in view
        self.driver.execute_script(f"window.scrollBy(0, {cookies_bar_height * 2});")

        # Click the calendar button to open start_date and end_date fields
        calendar_button.click()

        # Wait for fields to open
        time.sleep(1)

        # Get the buttons related to start and end date
        date_buttons = self.driver.find_elements(By.XPATH, '//aza-datepicker//div[@class="desktop"]//input')
        # 1. Indexed webElement is the start_date_field while 3. indexed is the end_date_field
        start_date_field = date_buttons[1]
        end_date_field = date_buttons[3]

        # Clear start date field and send desired start_date
        start_date_field.clear()
        start_date_field.send_keys(start_date)

        # Clear end date field and send desired end_date
        end_date_field.clear()
        end_date_field.send_keys(end_date)

        # Presses Enter to send changes
        end_date_field.send_keys(Keys.RETURN)

    # Selects the 'daily' option from the data display settigns menu
    def select_daily_data(self):

        self.driver.execute_script("window.scrollTo(0, 0);")

        dropdown = self.driver.find_element(By.XPATH, '//button[@data-e2e="tbs-resolution-picker-button"]')
        dropdown.click()
        time.sleep(1)

        """print("IT IS HAPPENING")
        time.sleep(5)
        """

        # day_option_locator = (By.XPATH, "//*[@data-e2e='tbs-chart-resolution-picker']//aza-list-option-psuedo-input")
        day_option_locator = (By.XPATH, "//*[@data-e2e='tbs-chart-resolution-picker']//aza-list-option-text")

        day_option = self.driver.find_element(*day_option_locator)
        day_option.click()

        time.sleep(2)


    def calculate_day_difference(self, date1, date2):
        date_format = "%Y-%m-%d"
        d1 = datetime.strptime(date1, date_format)
        d2 = datetime.strptime(date2, date_format)
        day_difference = abs((d2 - d1).days)

        return day_difference

    # This method relies on site autocorrecting start-date to the date of the first actual data
    def get_data_start_date(self):
        old_date_1 = "1900"
        old_date_2 = "1901"

        self.set_calendar(old_date_1, old_date_2)

        time.sleep(2)  # todo write better wait

        # Presses Enter to send changes

        # Get the buttons related to start and end date
        start_date = self.driver.find_element(By.XPATH,
                                              '//*[@id="instrument-period-picker"]/div[2]/div/div[1]/aza-datepicker/div[2]/div/button/span[2]')  # '//*[@class="text"]'

        time.sleep(2)

        # print(f"GOTTEN DATE: {start_date.text},    {start_date}")

        # Get the outer HTML of the element
        star_date_html = start_date.get_attribute('outerHTML')

        # Print the element's HTML source
        # print("Element's HTML Source:", star_date_html)

        start_index = star_date_html.find("20")

        start_date_text = star_date_html[start_index: start_index + 10]
        # print(F"GET_DATA_STRT_DTE: {start_date_text}") # Debugging

        return start_date_text

    def add_days_to_date(self, date, days_to_add):
        date_format = "%Y-%m-%d"
        start_date_obj = datetime.strptime(date, date_format)
        new_date_obj = start_date_obj + timedelta(days=days_to_add)
        new_date_str = new_date_obj.strftime(date_format)
        return new_date_str

    def smart_graph_scrape_over_the_years(self, start_date, end_date):
        data_start_date = self.get_data_start_date()

        print(f"SMRT_GRPH: cur_start = {start_date}, actual = {data_start_date}, calculation = {self.calculate_day_difference(data_start_date, start_date)}")
        # Set start date to the date where first data is logged if start date is before date of the first logged data
        if self.calculate_day_difference(data_start_date, start_date) > 0:
            start_date = data_start_date

        print(f"SMRT_GRPH: AFTER IF-> cur_start{start_date}, actual = {data_start_date} \n \n")


        # Get remaining_days between start_date and end_date
        remaining_days = self.calculate_day_difference(start_date, end_date)

        daily_data_display_allowence = 365  #  I can probably set this up high as 519, the value where Avanza refuses to give daily info


        # We want daily data, avanza displays daily data if remaining_days between start and end is less than 520 days
        if remaining_days <= daily_data_display_allowence:
            self.set_calendar(start_date, end_date)
            self.select_daily_data()
            return

        # Selects daily option. Site changes to weekly display if remaining_days between start and end date is over 520
        # self.select_daily_data()

        while (remaining_days > daily_data_display_allowence):
            """print(f"SMRTGRPH: start_date = {start_date}  || old = {end_date}", end=' ')  # Debugging
            end_date = self.add_days_to_date(start_date, daily_data_display_allowence)

            print(f"SMRTGRPH: new = {end_date}")  # Debugging"""

            # Set calendar
            self.set_calendar(start_date, end_date)
            self.select_daily_data() # Select daily value display

            # Scrape graph
            self.scrape_graph()

            start_date = end_date  # It might be healthy to + 1 to not get the same days twice
            remaining_days -= daily_data_display_allowence

        # After all '365 day cycles' are over, we have to get the remaining data
        self.set_calendar(start_date, self.add_days_to_date(start_date, remaining_days))
        self.select_daily_data()

        self.scrape_graph()

    def scrape_graph(self):
        # i = 0
        time.sleep(2)

        # Find the graph element from the page, this graph is quite complicated, and data output is given from mouse inputs
        graph = self.driver.find_element(By.CLASS_NAME, "highcharts-root")

        # Since we will move from left corner of the graph to the right corner, graph's size is important
        graph_width = graph.size['width']

        # We will simulate mouse movements, y_pos is unimportant as graph only changes from mouse's x pos
        x_pos = -graph.size['width'] / 2

        # Sets up the mouse hover
        action = ActionChains(self.driver)

        # Past value to not print redundant data
        past_value = None  # todo: This is a way to not print redundant data, but still slow as x_pos still increases by 1.

        # Graph doesn't start to give output from -graph.size['width']/2 but rather seems to from about -graph.size['width']/2 + 30, feel free to change it a bit
        while (x_pos <= graph_width/2):

            # Hover at point
            action.move_to_element_with_offset(graph, x_pos, 0).perform()

            # Reads every minute when set to +1, feel free to make it read almost every hour with +60 or every half hour with +30 etc.
            x_pos = x_pos + 1  # 769

            try:
                # Get Date, Price, Instrument etc.
                date_price_instrument = self.driver.find_element(By.XPATH,
                                                                 "//div[@class='highcharts-label highcharts-tooltip highcharts-color-undefined']")

                if date_price_instrument.text != past_value:
                    # Print to the console
                    print("hover_position: %i of %i" % (x_pos, graph_width/2))
                    print(f"{date_price_instrument.text} \n")

                    # Set past_value to current price and date
                    past_value = date_price_instrument.text
            except:
                # date_price_instrument won't be found when hover first starts, this is expected
                pass


if __name__ == "__main__":
    # AvanzaDataScarping instance
    avanza_instance = AvanzaDataScraping()

    # Start and end dates of the Graph we want to scrape
    # start_date = "2008-05-20"
    start_date = "2020-08-20"
    end_date = "2020-12-21"

    date_1 = "2010-07-31"
    date_2 = "2020-12-31"

    # Inside another method of the class
    # print(avanza_instance.calculate_day_difference(date_1, date_2))


    avanza_instance.smart_graph_scrape_over_the_years(date_1, date_2)
