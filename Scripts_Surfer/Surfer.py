""" Created on Sun Jul 23 13:42:59 2023 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
# from fatwoman_dir_setup import Screensaver_url_dir as url_dir
from fatwoman_dir_setup import url_configuration_1, url_configuration_2
from fatwoman_dir_setup import url_config_BBG, url_config_yahoo
from fatwoman_dir_setup import firefox_profile1, firefox_profile2
from fatwoman_dir_setup import surfer_dir_override
from fatwoman_dir_setup import Screensaver_html_dir
import logging
import os
import signal
import sys
import time
from selenium import webdriver
import pandas as pd
import socket
import argparse
import pyautogui

def signal_handler(signum, frame):
    print("Gracefully shutting down... " + time.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        # logging.info("Gracefully shutting down: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        for manager in managers:
            manager.driver.quit()
    except Exception as e:
        print(f"Error in closing drivers: {e}")
        logging.info("Error in closing drivers: %s"%e)
    finally:
        logging.info("Gracefully shutted down")
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class ScreensaverManager:
    def __init__(self, profile_path, window_position, config_path, screennumber):
        # logging.info('Creating surfer on %i - %s' %(screennumber, profile_path))
        # print('Creating surfer %i with %s' %(screennumber, profile_path))
        # Firefox Driver
        self.profile_path = profile_path
        self.window_position = window_position
        self.config_path = config_path
        self.driver = None
        self.screennumber = screennumber
        # Configurations
        self.url_configs_df = None
        self.url_config_row = None
        self.filesize = 0
        self.counter = -1
        self.URL_name = None
        self.URL = None
        self.SLEEP = None
        self.SCROLL = None

    def start_firefox_driver(self):
        # print('Loading Firefox driver with profile:', self.profile_path)
        # logging.info('Loading Firefox driver with profile:', self.profile_path)
        firefox_options = webdriver.FirefoxOptions()    
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(self.profile_path)
        self.driver = webdriver.Firefox(options=firefox_options)
        self.driver.set_window_position(*self.window_position)
        # logging.info('Loading Firefox driver done' + self.profile_path)

    def load_configs(self):
        config = pd.read_csv(self.config_path)
        config = config[config['INCLUDE_THIS_TOGGLE']]
        new_size = len(config)
        if self.filesize is None or new_size != self.filesize:
            # print(f'Loading config from {self.config_path}')
            # logging.info(f'Loading config from {self.config_path}')
            self.url_configs_df = config
            self.filesize = new_size
            # print(f'Load config done for {self.config_path}')
            # logging.info(f'Load config done for {self.config_path}')
        self.url_config_row = self.url_configs_df.iloc[self.counter, :]
        self.URL_name = self.url_config_row['Title']
        self.URL    = surfer_dir_override.get(self.URL_name, self.url_config_row['URL']) # surfer_dir_override is a dict. get url from dict, if not from config row
        self.SLEEP  = self.url_config_row['Waittime']
        self.SCROLL = self.url_config_row['ScrollAmount']

    def update_counter(self):
        self.counter = (self.counter + 1) % self.filesize

    def get_url(self):
        URL = self.URL
        self.driver.get(URL)

    # def load_saved_html(self):
    #     print(manager.counter)
    #     if manager.counter == 0: manager.get_url()
    #     self.driver.get(r'file://' + self.saved_html_url)

    # def save_html(self):
    #     self.saved_html_url = os.path.join(Screensaver_html_dir, self.URL_name + '.html')
    #     html_content = self.driver.page_source
    #     with open(self.saved_html_url, 'w', encoding='utf-8') as file:
    #         file.write(html_content)
    #     # print(f"HTML content saved to {self.saved_html_url}")

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bbg", action="store_true")
    parser.add_argument("--tenminutes", action="store_true")
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--doublescreen", action="store_true")
    return parser.parse_args()
    
def bbg_starter():
    time.sleep(30)
    print("Moving Cursor to BBG TV and clicking...")
    logging.info("Moving Cursor to BBG TV and clicking...")
    pyautogui.moveTo(642, 628, duration=1) # pyautogui.moveTo(1781, 523, duration=1)
    pyautogui.click()

if __name__ == "__main__":

    args = parse_arguments()

    print('Starting Screensaver ' + time.strftime("%Y-%m-%d %H:%M:%S"))
    # logging.info('Starting Screensaver ' + time.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info(args)

    configuration_1 = url_config_yahoo  if args.bbg else url_configuration_1
    configuration_2 = url_config_BBG    if args.bbg else url_configuration_2
    
    managers = [
        ScreensaverManager(firefox_profile2, (1300, 100),   configuration_2, 2) # right, alp
    ]

    if args.doublescreen: managers.append(ScreensaverManager(firefox_profile1, (100, 100),    configuration_1, 1)) # left, alisa

    for manager in managers:
        manager.start_firefox_driver()
        manager.driver.fullscreen_window()
        manager.load_configs()

    i = 0 # total loop counter
    try_i = 0
    while True:
        try:
            sleep_timer = 0
            for manager in managers:
                manager.update_counter()
                manager.load_configs() # Also updates URL
                # print(f"Loading screen %i: Loop %3i: Url_name: %s" %(manager.screennumber, i, manager.URL_name))
                # logging.info(f"Loading screen %i: Loop %3i: Url_name: %s" %(manager.screennumber, i, manager.URL_name))
                manager.get_url()
                # manager.save_html()
                # manager.load_saved_html()
                sleep_timer += manager.SLEEP
            if args.bbg: bbg_starter()
            if args.tenminutes: sleep_timer = 300
            if args.fast: sleep_timer = sleep_timer / 5
            # print("Sleeping %s" %sleep_timer)
            # logging.info("Sleeping %s" %sleep_timer)
            time.sleep(sleep_timer) # / len(managers)
            i += 1
        except Exception as e:
            print('Error in loop:')
            for manager in managers:
                print('Screen %s is on %s' %(manager.screennumber,manager.URL))
                # logging.info('Screen %s is on %s' %(manager.screennumber,manager.URL))
                time.sleep(1)
            print(e)
            time.sleep(5)
            if try_i <5:
                try_i += 1
                print('Looping again, try counter:%s at %s' %(try_i, time.strftime("%Y-%m-%d %H:%M:%S")))
                continue
            else:
                break

script_end_log()
