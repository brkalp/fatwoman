#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
import logging
import fatwoman_log_setup
from fatwoman_dir_setup import LLM_data_path
from fatwoman_log_setup import script_end_log
import logging
import fatwoman_log_setup

print("Starting Log Archive")
todays_date = datetime.now().strftime("%Y%m%d")
archive_path = os.path.join(LLM_data_path, "archive", todays_date)
os.makedirs(archive_path, exist_ok=True)

# Files to exclude
exclude_list = {"Archive_tester", "Archive"}

# Iterate through files
for filename in os.listdir(LLM_data_path):
    if not filename in exclude_list:

        file_full_path = os.path.join(LLM_data_path, filename)

        if os.path.isfile(file_full_path):
            dest_file = os.path.join(archive_path, filename)

            # Append contents to archive file
            with open(dest_file, "a") as df, open(file_full_path, "r") as sf:
                shutil.copyfileobj(sf, df)

            # Remove original file
            os.remove(file_full_path)
            print(f"Appended and removed {file_full_path} -> {dest_file}")

# print(f"Archive Finished {todays_date}")
script_end_log()
