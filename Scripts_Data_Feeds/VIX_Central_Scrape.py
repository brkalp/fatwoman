""" Created on Sun Jul 23 13:42:59 2023 @author: DenizYalimYilmaz """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

options = Options()
# options.headless = True
# driver = webdriver.Firefox(options=options)
options.headless = True
driver = webdriver.Firefox()
driver.get('http://vixcentral.com/')
element = driver.find_element(By.XPATH, "//*[contains(@transform, 'translate(762,10)')]")
# driver.execute_script("arguments[0].scrollIntoView(true);", element)

actions = ActionChains(driver)
actions.move_to_element(element).perform()  # Hover over the element
actions.click(element).perform()

# context_button = WebDriverWait(driver, 2).until(
# EC.element_to_be_clickable((By.XPATH, "//g[contains(@class, 'highcharts-button')][contains(@class, 'highcharts-contextbutton')]")))
# menu_button.click()
# button.click()
# element = driver.find_element(By.XPATH, "//g[contains(@g class, 'a')]")
# element = driver.find_element(By.ID, "a") 
# element = driver.find_element(By.XPATH, "//*[contains(@title, 'Chart context menu')]")
# element = driver.find_element(By.XPATH, "//*[contains(@class, 'highcharts-no-tooltip') and contains(@class, 'highcharts-button') and contains(@class, 'highcharts-contextbutton') and contains(@class, 'highcharts-button-normal')]")

