#!/bin/bash

# Set the source and output
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/model"
OUTPUT_FILE="model.tar.gz"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: 'model' directory does not exist in the script's directory."
    exit 1
fi

# Check if pigz is installed, if not use gzip
COMPRESS_CMD="gzip"
if command -v pigz &> /dev/null; then
    COMPRESS_CMD="pigz"
else
    echo "Warning: pigz not found. Using gzip instead. Install pigz for faster compression."
fi

# Compress the directory
echo "Compressing $SOURCE_DIR to $OUTPUT_FILE using $COMPRESS_CMD..."
tar cf - -C "$SCRIPT_DIR" model | $COMPRESS_CMD > "$OUTPUT_FILE"

# Check if compression was successful
if [ $? -eq 0 ]; then
    echo "Compression completed successfully."
    echo "Output file: $OUTPUT_FILE"
    echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
else
    echo "Compression failed."
    exit 1
fi
