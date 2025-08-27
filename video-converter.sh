#!/bin/bash

# Unified video conversion script for DaVinci Resolve workflows
# Supports both MP4->DNxHD and MOV->Mobile MP4 conversions

show_usage() {
    echo "Usage: $0 <mode> <directory>"
    echo ""
    echo "Modes:"
    echo "  to-dnxhd    Convert MP4 files to DaVinci Resolve-friendly DNxHD format"
    echo "  to-mobile   Convert MOV files to mobile-optimized MP4 format"
    echo ""
    echo "Examples:"
    echo "  $0 to-dnxhd /path/to/mp4/files"
    echo "  $0 to-mobile /path/to/mov/files"
}

# Check arguments
if [ $# -ne 2 ]; then
    show_usage
    exit 1
fi

MODE="$1"
TARGET_DIR="$2"

# Validate directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist"
    exit 1
fi

# Change to target directory
cd "$TARGET_DIR" || exit 1

case "$MODE" in
    "to-dnxhd")
        SOURCE_EXT="mp4"
        TARGET_EXT="mov"
        DESCRIPTION="DNxHD format"
        FFMPEG_OPTS="-c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p -c:a pcm_s16le"
        ;;
    "to-mobile")
        SOURCE_EXT="mov"
        TARGET_EXT="mp4"
        DESCRIPTION="mobile-optimized MP4 format"
        FFMPEG_OPTS="-c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 128k -vf \"scale=1080:1920,setsar=1\" -movflags +faststart"
        ;;
    *)
        echo "Error: Invalid mode '$MODE'"
        show_usage
        exit 1
        ;;
esac

echo "Converting $SOURCE_EXT files to $DESCRIPTION in: $(pwd)"
echo ""

# Check if any source files exist
file_count=$(ls -1 *.$SOURCE_EXT 2>/dev/null | wc -l)
if [ "$file_count" -eq 0 ]; then
    echo "No $SOURCE_EXT files found in the directory"
    exit 0
fi

for file in *.$SOURCE_EXT; do
    if [ -f "$file" ]; then
        output="${file%.*}.$TARGET_EXT"

        echo "Converting '$file' to '$output'..."

        eval "ffmpeg -i \"$file\" $FFMPEG_OPTS \"$output\" -y > /dev/null 2>&1"

        if [ $? -eq 0 ]; then
            echo "Successfully converted '$file'."
        else
            echo "Error converting '$file'."
        fi
        echo ""
    fi
done

echo "Conversion complete!"
