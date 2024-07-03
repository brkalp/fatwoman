""" Created on Sun Jul 23 13:42:59 2023 @author: DenizYalimYilmaz """
#import fatwoman_log_setup
#from fatwoman_log_setup import script_end_log
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

options = Options()
options.headless = True
driver = webdriver.Firefox()
driver.get('http://vixcentral.com/')

element = driver.find_element(By.XPATH, "//*[contains(@transform, 'translate(762,10)')]")

# Download path isn't sent until we click to the dropdown menu, so we have to click it first
actions = ActionChains(driver)
actions.move_to_element(element).perform()  # Hover over the element
actions.click(element).perform()


#menu_item = driver.find_element(By.XPATH, "//li[@class='highcharts-menu-item' and text()='Download CSV']") # It's safer to use WebDriverWait

wait = WebDriverWait(driver, 10)
menu_item = wait.until(EC.presence_of_element_located((By.XPATH, "//li[@class='highcharts-menu-item' and text()='Download CSV']")))
actions.move_to_element(menu_item).click().perform()

# Optional: Wait for some time to observe the result, Alp don't forget to delete this later
import time
time.sleep(10)

driver.close()
