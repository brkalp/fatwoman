# #!/bin/bash

# echo "Starting Log Archive"
# TODAYS_DATE=$(date +%Y%m%d)
# LLM_LOG_DIR = $FATBOY_DIR/Scripts_LLM_trader
# ARCHIVE_PATH="$LLM_LOG_DIR/archive/$TODAYS_DATE"

# mkdir -p "$ARCHIVE_PATH"

# EXCLUDE_LIST=("archive_here.sh" "archive")

# for FILE_FULL_PATH in $LLM_LOG_DIR/*; do
#     FILENAME=$(basename "$FILE_FULL_PATH")
#     if [[ ! " ${EXCLUDE_LIST[@]} " =~ " ${FILENAME} " ]]; then
#         cat "$FILE_FULL_PATH" >> "$ARCHIVE_PATH/$FILENAME"
#         rm "$FILE_FULL_PATH"
#         echo "Appended and removed $FILE_FULL_PATH to $ARCHIVE_PATH/$FILENAME"
#     fi
# done

# echo "Archive Finished $TODAYS_DATE"
