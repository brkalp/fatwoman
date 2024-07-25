from selenium import webdriver
import time

from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AvanzaDataScraping:
    def __init__(self):
        # Set up the driver
        options = Options()
        # options.add_argument("--headless") # ActionChain doesn't work with headless display, so visual display should be added for some devices
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(800, 800)

        # 'https://www.avanza.se/borshandlade-produkter/certifikat-torg/om-certifikatet.html/1395805/bear-vix-x4-von3'
        link = "https://www.avanza.se/fonder/om-fonden.html/878733/avanza-global"

        # Get the link
        self.driver.get(link)

        # It takes a bit for Avanza to load, so a buffer like time.sleep(5) is healthy, feel free to increase it 8 or 10 secs if internet speed is not up to par
        WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.CLASS_NAME, "highcharts-root")))
        time.sleep(1)


    def set_calendar(self, start_date, end_date):
        # Now we will set up the date, to click the calendar button we might have to go behind the cookies button
        cookies_bar = self.driver.find_element(By.XPATH, "/html/body/aza-app/aza-shell/div/aza-cookie-message/div/div")
        cookies_bar_height = cookies_bar.size['height']

        calendar_button = self.driver.find_element(By.XPATH, "/html/body/aza-app/aza-shell/div/div[2]/main/div/aza-fund-guide/aza-subpage/div/div/div/div[2]/div[1]/mint-card[1]/div[4]/aza-area-chart/div/aza-period-picker/div/aza-period-button[8]/button")


        actions = ActionChains(self.driver)

        # I genuinely can't find a better way to scroll down. If you have any suggestions that actually work my discord: #denami1
        actions.scroll_by_amount(0, cookies_bar_height*2).perform()
        calendar_button.click()

        time.sleep(1)

        date_buttons = self.driver.find_elements(By.XPATH, '//aza-datepicker//div[@class="desktop"]//input')
        date_buttons[1].click()
        date_buttons[1].clear()
        date_buttons[1].send_keys(start_date)

        date_buttons[3].click()
        date_buttons[3].clear()
        date_buttons[3].send_keys(end_date)


    def scrape_graph(self):
        time.sleep(2)

        # Find the graph element from the page, this graph is quite complicated, and data output is given from mouse inputs
        graph = self.driver.find_element(By.CLASS_NAME, "highcharts-root")

        # Since we will move from left corner of the graph to the right corner, graph's size is important
        graph_width = graph.size['width']

        # We will simulate mouse movements, y_pos is unimportant as graph only changes from mouse's x pos
        x_pos = -graph.size['width']/2

        # Graph doesn't start to give output from -graph.size['width']/2 but rather seems to from about -graph.size['width']/2 + 30, feel free to change it a bit
        while(x_pos <= graph_width):

            # Sets up the mouse hover
            action = ActionChains(self.driver)
            action.move_to_element_with_offset(graph, x_pos, 0).perform()

            # Reads every minute when set to +1, feel free to make it read almost every hour with +60 or every half hour with +30 etc.
            x_pos = x_pos + 1

            try:
                # Get Date, Price, Instrument etc.
                date_price_instrument = self.driver.find_element(By.XPATH, "//div[@class='highcharts-label highcharts-tooltip highcharts-color-undefined']")

                # Print to the console
                print(f"{date_price_instrument.text} \n")

            except:
                # No exceptions
                pass


# AvanzaDataScarping instance
avanza_instance = AvanzaDataScraping()

# Start and end dates of the Graph we want to scrape
start_date = "2008-05-20"
end_date = "2009-05-21"

avanza_instance.set_calendar(start_date, end_date) # Setting the calendar is optional, if unset, site will give daily graph

# Scarpe graph
avanza_instance.scrape_graph()