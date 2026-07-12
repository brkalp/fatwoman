#!/bin/bash

echo "Starting Log Archive"
TODAYS_DATE=$(date +%Y%m%d)
ARCHIVE_PATH="$LOG_DIR/archive/$TODAYS_DATE"

mkdir -p "$ARCHIVE_PATH"

EXCLUDE_LIST=("archive_here.sh" "archive")

for FILE_FULL_PATH in "$LOG_DIR"/*; do
    FILENAME=$(basename "$FILE_FULL_PATH")
    if [[ ! " ${EXCLUDE_LIST[@]} " =~ " ${FILENAME} " ]]; then
        [ -f "$FILE_FULL_PATH" ] || continue
        # append, carry the original mtime over to the archived copy,
        # and only delete the source once both steps succeeded
        cat "$FILE_FULL_PATH" >> "$ARCHIVE_PATH/$FILENAME" \
            && touch -r "$FILE_FULL_PATH" "$ARCHIVE_PATH/$FILENAME" \
            && rm "$FILE_FULL_PATH" \
            && echo "Appended and removed $FILE_FULL_PATH to $ARCHIVE_PATH/$FILENAME"
    fi
done

echo "Archive Finished $TODAYS_DATE"
