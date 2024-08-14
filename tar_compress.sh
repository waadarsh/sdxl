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

# Compress the directory
echo "Compressing $SOURCE_DIR to $OUTPUT_FILE..."
tar czf "$OUTPUT_FILE" -C "$SOURCE_DIR" .

# Check if compression was successful
if [ $? -eq 0 ]; then
    echo "Compression completed successfully."
    echo "Output file: $OUTPUT_FILE"
    echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
else
    echo "Compression failed."
    exit 1
fi
