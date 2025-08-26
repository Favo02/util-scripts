#!/bin/bash

# A simple script to batch convert MP4 files to a DaVinci Resolve-friendly
# DNxHD format using FFmpeg.

# Check if directory argument is provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 <directory>"
  echo "Convert all MP4 files in the specified directory to DNxHD format"
  exit 1
fi

TARGET_DIR="$1"

# Validate directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' does not exist"
  exit 1
fi

# Change to target directory
cd "$TARGET_DIR" || exit 1

echo "Converting MP4 files in: $(pwd)"
echo ""

# Check if any MP4 files exist
mp4_count=$(ls -1 *.mp4 2>/dev/null | wc -l)
if [ "$mp4_count" -eq 0 ]; then
  echo "No MP4 files found in the directory"
  exit 0
fi

for file in *.mp4; do
  if [ -f "$file" ]; then
    output="${file%.*}.mov"

    echo "Converting '$file' to '$output'..."

    ffmpeg -i "$file" -c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p -c:a pcm_s16le "$output" -y > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "Successfully converted '$file'."
    else
        echo "Error converting '$file'."
    fi
    echo ""
  fi
done

echo "Conversion complete!"
