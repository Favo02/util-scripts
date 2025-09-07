import os
import sys
import platform
import subprocess
import tempfile
import math
import argparse
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageEnhance

# --- Configuration ---
DEFAULT_OUTPUT_FOLDER = "TOPRINT"
ENHANCEMENT_FACTOR = 1.2
DPI = 300
# 4x6 inch dimensions
OUTPUT_WIDTH_PX = 6 * DPI
OUTPUT_HEIGHT_PX = 4 * DPI


class PhotoProcessor:
    """A class to process photos for printing, creating 2x2 and 1x2 photo grids."""

    def __init__(self, verbose: bool = False, print_files: bool = False):
        self.verbose = verbose
        self.print_files = print_files

    def get_image_files(self, folder_path: Path) -> Optional[List[Path]]:
        """Returns a sorted list of valid image files from a folder."""
        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
        try:
            files = [
                folder_path / f for f in folder_path.iterdir()
                if f.suffix.lower() in supported_formats and f.is_file()
            ]
            return sorted(files)
        except FileNotFoundError:
            return None

    def apply_enhancements(self, img: Image.Image, factor: float) -> Image.Image:
        """Applies a color and brightness boost to a PIL Image."""
        # 1. Enhance Color (Saturation)
        enhancer_color = ImageEnhance.Color(img)
        img = enhancer_color.enhance(factor)
        # 2. Enhance Brightness (using a gentler boost)
        brightness_factor = 1.0 + (factor - 1.0) / 2.0
        enhancer_brightness = ImageEnhance.Brightness(img)
        img = enhancer_brightness.enhance(brightness_factor)
        return img

    def fit_image_to_quad(self, img: Image.Image, quad_width: int, quad_height: int) -> Image.Image:
        """
        Resize and rotate image to best fit in the quadrant.
        Returns the resized (and possibly rotated) image.
        """
        img_w, img_h = img.size
        # Try both orientations: original and rotated
        scale_normal = min(quad_width / img_w, quad_height / img_h)
        scale_rotated = min(quad_width / img_h, quad_height / img_w)

        # Choose the orientation that gives the largest image
        if (img_w * scale_normal) * (img_h * scale_normal) >= (img_h * scale_rotated) * (img_w * scale_rotated):
            # No rotation
            new_w, new_h = int(img_w * scale_normal), int(img_h * scale_normal)
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            # Rotate 90 degrees
            img_rotated = img.rotate(90, expand=True)
            img_w, img_h = img_rotated.size
            scale = min(quad_width / img_w, quad_height / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            img_resized = img_rotated.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return img_resized

    def create_2x2_sheet(self, image_paths: List[Path], output_path: Path) -> bool:
        """Creates a 2x2 photo grid on a 4x6 sheet, optimally fitting each image."""
        if self.verbose:
            print(f"🖼️  Creating 2x2 photo sheet: '{output_path.name}'")

        try:
            # Create a blank white canvas
            sheet = Image.new('RGB', (OUTPUT_WIDTH_PX, OUTPUT_HEIGHT_PX), 'white')

            # Define the dimensions and positions for the 2x2 grid
            quad_width = OUTPUT_WIDTH_PX // 2
            quad_height = OUTPUT_HEIGHT_PX // 2
            positions = [
                (0, 0),                    # Top-left
                (quad_width, 0),           # Top-right
                (0, quad_height),          # Bottom-left
                (quad_width, quad_height)  # Bottom-right
            ]

            for i, img_path in enumerate(image_paths):
                if i >= 4:  # Only process up to 4 images for 2x2 grid
                    break

                try:
                    img = Image.open(img_path).convert('RGB')
                except Exception as e:
                    if self.verbose:
                        print(f"❌ Error opening '{img_path.name}': {e}")
                    continue

                # Apply enhancements
                img = self.apply_enhancements(img, ENHANCEMENT_FACTOR)

                # Fit image to quadrant, possibly rotating
                img_resized = self.fit_image_to_quad(img, quad_width, quad_height)
                new_w, new_h = img_resized.size

                # Centering logic
                quad_x, quad_y = positions[i]
                paste_x = quad_x + (quad_width - new_w) // 2
                paste_y = quad_y + (quad_height - new_h) // 2

                sheet.paste(img_resized, (paste_x, paste_y))
                if self.verbose:
                    print(f"✅ Processed '{img_path.name}' with enhancement factor {ENHANCEMENT_FACTOR}")

            # Save with DPI information
            sheet.save(output_path, dpi=(DPI, DPI), quality=95)
            print(f"📄 Created 2x2 sheet: '{output_path.name}'")
            return True

        except Exception as e:
            if self.verbose:
                print(f"❌ Error creating 2x2 sheet '{output_path.name}': {e}")
            return False

    def create_1x2_sheet(self, image_paths: List[Path], output_path: Path) -> bool:
        """Creates an optimized photo grid on a 4x6 sheet, choosing between 2x1 or 1x2 layout for best space usage."""
        if self.verbose:
            print(f"🖼️  Creating optimized photo sheet: '{output_path.name}'")

        try:
            # Load and process images first
            processed_images = []
            for img_path in image_paths[:2]:  # Only process up to 2 images
                try:
                    img = Image.open(img_path).convert('RGB')
                    img = self.apply_enhancements(img, ENHANCEMENT_FACTOR)
                    processed_images.append((img, img_path))
                except Exception as e:
                    if self.verbose:
                        print(f"❌ Error opening '{img_path.name}': {e}")
                    continue

            if not processed_images:
                return False

            # If only one image, use full sheet
            if len(processed_images) == 1:
                img, img_path = processed_images[0]
                sheet = Image.new('RGB', (OUTPUT_WIDTH_PX, OUTPUT_HEIGHT_PX), 'white')

                # Fit to full sheet
                img_resized = self.fit_image_to_quad(img, OUTPUT_WIDTH_PX, OUTPUT_HEIGHT_PX)
                new_w, new_h = img_resized.size
                paste_x = (OUTPUT_WIDTH_PX - new_w) // 2
                paste_y = (OUTPUT_HEIGHT_PX - new_h) // 2

                sheet.paste(img_resized, (paste_x, paste_y))
                if self.verbose:
                    print(f"✅ Processed '{img_path.name}' (full sheet)")
            else:
                # Try both layouts: 2x1 (horizontal) and 1x2 (vertical)
                layout_1x2 = self._calculate_layout_area(processed_images, "1x2")
                layout_2x1 = self._calculate_layout_area(processed_images, "2x1")

                # Choose layout with larger total area
                if layout_2x1['total_area'] > layout_1x2['total_area']:
                    layout = "2x1"
                    quad_width = OUTPUT_WIDTH_PX // 2
                    quad_height = OUTPUT_HEIGHT_PX
                    positions = [(0, 0), (quad_width, 0)]
                    if self.verbose:
                        print(f"📐 Using 2x1 layout (total area: {layout_2x1['total_area']:,} px²)")
                else:
                    layout = "1x2"
                    quad_width = OUTPUT_WIDTH_PX
                    quad_height = OUTPUT_HEIGHT_PX // 2
                    positions = [(0, 0), (0, quad_height)]
                    if self.verbose:
                        print(f"📐 Using 1x2 layout (total area: {layout_1x2['total_area']:,} px²)")

                # Create the sheet with chosen layout
                sheet = Image.new('RGB', (OUTPUT_WIDTH_PX, OUTPUT_HEIGHT_PX), 'white')

                for i, (img, img_path) in enumerate(processed_images):
                    if i >= 2:
                        break

                    # Fit image to quadrant
                    img_resized = self.fit_image_to_quad(img, quad_width, quad_height)
                    new_w, new_h = img_resized.size

                    # Centering logic
                    quad_x, quad_y = positions[i]
                    paste_x = quad_x + (quad_width - new_w) // 2
                    paste_y = quad_y + (quad_height - new_h) // 2

                    sheet.paste(img_resized, (paste_x, paste_y))
                    if self.verbose:
                        print(f"✅ Processed '{img_path.name}' with enhancement factor {ENHANCEMENT_FACTOR}")

            # Save with DPI information
            sheet.save(output_path, dpi=(DPI, DPI), quality=95)
            print(f"📄 Created optimized sheet: '{output_path.name}'")
            return True

        except Exception as e:
            if self.verbose:
                print(f"❌ Error creating optimized sheet '{output_path.name}': {e}")
            return False

    def _calculate_layout_area(self, processed_images: List[tuple], layout: str) -> dict:
        """Calculate the total image area for a given layout."""
        if layout == "1x2":
            quad_width = OUTPUT_WIDTH_PX
            quad_height = OUTPUT_HEIGHT_PX // 2
        else:  # 2x1
            quad_width = OUTPUT_WIDTH_PX // 2
            quad_height = OUTPUT_HEIGHT_PX

        total_area = 0
        for img, _ in processed_images[:2]:
            img_w, img_h = img.size

            # Calculate area for both orientations
            scale_normal = min(quad_width / img_w, quad_height / img_h)
            scale_rotated = min(quad_width / img_h, quad_height / img_w)

            area_normal = (img_w * scale_normal) * (img_h * scale_normal)
            area_rotated = (img_h * scale_rotated) * (img_w * scale_rotated)

            # Use the larger area
            total_area += max(area_normal, area_rotated)

        return {'total_area': int(total_area), 'layout': layout}

    def print_photos(self, folder: Path) -> int:
        """Print all images in the folder using the lp command."""
        if not self.print_files:
            return 0

        image_files = self.get_image_files(folder)
        if not image_files:
            print(f"🚫 No images to print in '{folder}'.")
            return 0

        printed_count = 0
        for img_path in image_files:
            cmd = ["lp", str(img_path)]

            try:
                subprocess.run(cmd, check=True)
                print(f"🖨️ Printed '{img_path.name}'")
                printed_count += 1
            except Exception as e:
                if self.verbose:
                    print(f"❌ Failed to print '{img_path.name}': {e}")

        return printed_count

    def process_folders(self, big_folder: Path, small_folder: Path, output_folder: Path) -> tuple[int, int]:
        """Process both BIG and SMALL folders and create photo sheets."""
        # Create output directory
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created '{output_folder}' directory")

        big_sheets = 0
        small_sheets = 0

        # 1. Process BIG folder - group into 1x2 sheets
        print(f"\n## Processing {big_folder.name} Folder... ##")
        big_files = self.get_image_files(big_folder)
        if big_files is None:
            print(f"⚠️ Folder '{big_folder}' not found. Skipping.")
        elif not big_files:
            print("🚫 No images found in BIG folder.")
        else:
            # Group images into chunks of 2 for each 1x2 sheet
            chunk_size = 2
            num_sheets = math.ceil(len(big_files) / chunk_size)
            for i in range(num_sheets):
                start_index = i * chunk_size
                end_index = start_index + chunk_size
                chunk = big_files[start_index:end_index]

                sheet_path = output_folder / f"big_sheet_{i+1:03d}.jpg"
                if self.create_1x2_sheet(chunk, sheet_path):
                    big_sheets += 1

        # 2. Process SMALL folder - group into 2x2 sheets
        print(f"\n## Processing {small_folder.name} Folder... ##")
        small_files = self.get_image_files(small_folder)
        if small_files is None:
            print(f"⚠️ Folder '{small_folder}' not found. Skipping.")
        elif not small_files:
            print("🚫 No images found in SMALL folder.")
        else:
            # Group images into chunks of 4 for each 2x2 sheet
            chunk_size = 4
            num_sheets = math.ceil(len(small_files) / chunk_size)
            for i in range(num_sheets):
                start_index = i * chunk_size
                end_index = start_index + chunk_size
                chunk = small_files[start_index:end_index]

                sheet_path = output_folder / f"small_sheet_{i+1:03d}.jpg"
                if self.create_2x2_sheet(chunk, sheet_path):
                    small_sheets += 1

        return big_sheets, small_sheets


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process photos into printable 4x6 sheets with optimal layout",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s Photos/Large Photos/Small         # Use custom input folders, output to TOPRINT/
  %(prog)s /Large /Small -o ./PrintReady           # Use custom output folder
  %(prog)s /Large /Small -p                      # Process and print automatically
  %(prog)s /Large /Small -v                      # Verbose output with processing details
        """
    )

    parser.add_argument(
        'big_folder',
        type=str,
        help='Folder containing large photos for optimized sheets'
    )

    parser.add_argument(
        'small_folder',
        type=str,
        help='Folder containing small photos for 2x2 sheets'
    )

    parser.add_argument(
        '-o', '--output-folder',
        type=str,
        default=DEFAULT_OUTPUT_FOLDER,
        help=f'Output folder for processed sheets (default: {DEFAULT_OUTPUT_FOLDER})'
    )

    parser.add_argument(
        '-p', '--print',
        action='store_true',
        help='Print the processed sheets automatically'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output with detailed processing information'
    )

    return parser.parse_args()


def main() -> None:
    """Main function to process photos and optionally print them."""
    args = parse_arguments()

    # Convert string paths to Path objects
    big_folder = Path(args.big_folder).resolve()
    small_folder = Path(args.small_folder).resolve()
    output_folder = Path(args.output_folder).resolve()

    print("--- Starting Photo Processing Job ---")
    print(f"📁 Big photos folder: {big_folder}")
    print(f"📁 Small photos folder: {small_folder}")
    print(f"📁 Output folder: {output_folder}")

    if args.print:
        print(f"🖨️ Print mode enabled (default printer)")
    else:
        print("📄 Process only mode (use -p to print)")

    if args.verbose:
        print("🔍 Verbose mode enabled")
    print()

    # Create processor instance
    processor = PhotoProcessor(
        verbose=args.verbose,
        print_files=args.print
    )

    # Process folders
    big_sheets, small_sheets = processor.process_folders(big_folder, small_folder, output_folder)

    print(f"\n--- Photo Processing Finished ---")
    print(f"📊 Created {big_sheets} big sheets and {small_sheets} small sheets")
    print(f"📁 All processed files are in the '{output_folder}' directory")

    # Print if requested
    if args.print:
        printed_count = processor.print_photos(output_folder)
        print(f"🖨️ Sent {printed_count} sheets to printer")
    else:
        print("💡 Use -p/--print flag to send sheets to printer automatically")


if __name__ == '__main__':
    main()
