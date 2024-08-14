#!/bin/bash

# Check if required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <source_directory> <output_file.tar.gz>"
    exit 1
fi

SOURCE_DIR="$1"
OUTPUT_FILE="$2"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Source directory does not exist: $SOURCE_DIR"
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
tar cf - -C "$SOURCE_DIR" . | $COMPRESS_CMD > "$OUTPUT_FILE"

# Check if compression was successful
if [ $? -eq 0 ]; then
    echo "Compression completed successfully."
    echo "Output file: $OUTPUT_FILE"
    echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
else
    echo "Compression failed."
    exit 1
fi
