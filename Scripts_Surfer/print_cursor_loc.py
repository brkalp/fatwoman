""" Created on 02-26-2024 19:55:44 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_dir_setup import ModelDownload_Output_Folder
import pandas as pd
import time
import os
import pyautogui

# Get the current mouse cursor's X and Y positions
x, y = pyautogui.position()

print(f"Cursor Location: X={x}, Y={y}")
