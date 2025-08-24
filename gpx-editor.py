import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import re
from datetime import datetime
import gpxpy
import gpxpy.gpx


class GPXAnalyzer:
    """A class to analyze GPX files and extract key information."""

    def __init__(self, verbose: bool = False, fix_files: bool = False, count_points: bool = False):
        self.verbose = verbose
        self.fix_files = fix_files
        self.count_points = count_points

    def analyze_file(self, file_path: Path) -> Optional[dict]:
        """
        Parses a single GPX file and extracts key information.

        Args:
            file_path (Path): The path to the GPX file.

        Returns:
            dict: Dictionary containing file information, or None if parsing failed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)

            filename = file_path.name
            creator = self._get_creator(gpx)
            track_name = self._get_track_name(gpx)
            date = self._get_date(gpx)

            file_info = {
                'filename': filename,
                'track_name': track_name,
                'date': date,
                'creator': creator,
                'file_path': file_path
            }

            if self.count_points:
                counts = self._count_features(gpx)
                file_info.update(counts)

            return file_info

        except gpxpy.gpx.GPXXMLSyntaxException:
            if self.verbose:
                print(f"!!! Error: {file_path.name} appears to be corrupted or invalid GPX format.")
            return None
        except Exception as e:
            if self.verbose:
                print(f"!!! Unexpected error with {file_path.name}: {e}")
            return None

    def _check_filename_format(self, file_info: dict) -> list[str]:
        """Check if filename follows the YYYY-MM-DD NAME format and validate consistency."""
        filename = file_info['filename']
        warnings = []

        # Remove .gpx extension for checking
        filename_no_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename

        # YYYY-MM-DD NAME
        pattern = r'^(\d{4}-\d{2}-\d{2})\s+(.+)$'
        match = re.match(pattern, filename_no_ext)

        if not match:
            warnings.append("📝 Invalid filename format")
            return warnings

        filename_date_str = match.group(1)
        filename_name = match.group(2)

        track_date = file_info['date']
        if track_date != "No date found" and track_date != filename_date_str:
            warnings.append("📅 Date mismatch")

        track_name = file_info['track_name']
        if track_name != "No track name found" and track_name != filename_name:
            warnings.append("🏷️ Track name mismatch")

        return warnings

    def _get_creator(self, gpx: gpxpy.gpx.GPX) -> str:
        """Extract creator information from GPX file."""
        if gpx.creator:
            return gpx.creator
        elif gpx.metadata and gpx.metadata.author_name:
            return gpx.metadata.author_name
        return "Not specified"

    def _get_track_name(self, gpx: gpxpy.gpx.GPX) -> str:
        """Extract track name from GPX file."""
        if gpx.tracks and gpx.tracks[0].name:
            return gpx.tracks[0].name
        elif gpx.routes and gpx.routes[0].name:
            return gpx.routes[0].name
        return "No track name found"

    def _get_date(self, gpx: gpxpy.gpx.GPX) -> str:
        """Extract date from GPX file."""
        time_bounds = gpx.get_time_bounds()
        if time_bounds and time_bounds.start_time:
            return time_bounds.start_time.strftime('%Y-%m-%d')
        elif gpx.time:
            return gpx.time.strftime('%Y-%m-%d')
        return "No date found"

    def _count_features(self, gpx: gpxpy.gpx.GPX) -> dict:
        """Count various features in the GPX file."""
        track_points = 0
        waypoints = len(gpx.waypoints)
        route_points = 0

        for track in gpx.tracks:
            for segment in track.segments:
                track_points += len(segment.points)

        for route in gpx.routes:
            route_points += len(route.points)

        return {
            'track_points': track_points,
            'waypoints': waypoints,
            'route_points': route_points
        }

    def print_file_info(self, file_info: dict, warnings: list[str] = None) -> None:
        """Print formatted information about a GPX file."""
        filename = file_info['filename']

        status = "✅" if not warnings else "⚠️ "
        line = f"{status} {filename}"

        if self.count_points:
            track_pts = file_info.get('track_points', 0)
            waypts = file_info.get('waypoints', 0)
            route_pts = file_info.get('route_points', 0)
            line += f" (📍 {track_pts} track pts, 🎯 {waypts} waypts, 🛤️  {route_pts} route pts)"

        print(line)

        if warnings:
            for warning in warnings:
                print(f"  {warning}")

    def fix_gpx_file(self, file_path: Path) -> bool:
        """
        Fix a GPX file to keep only essential information and update track name from filename.

        Args:
            file_path (Path): The path to the GPX file.

        Returns:
            bool: True if fixing was successful, False otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)

            # Extract NAME from filename
            filename_no_ext = file_path.stem
            pattern = r'^(\d{4}-\d{2}-\d{2})\s+(.+)$'
            match = re.match(pattern, filename_no_ext)

            track_name = None
            if match:
                track_name = match.group(2)

            new_gpx = gpxpy.gpx.GPX()

            if gpx.time:
                new_gpx.time = gpx.time

            for track in gpx.tracks:
                new_track = gpxpy.gpx.GPXTrack()
                if track_name:
                    new_track.name = track_name
                elif track.name:
                    new_track.name = track.name

                for segment in track.segments:
                    new_segment = gpxpy.gpx.GPXTrackSegment()

                    for point in segment.points:
                        new_point = gpxpy.gpx.GPXTrackPoint(
                            latitude=point.latitude,
                            longitude=point.longitude,
                            elevation=point.elevation,
                            time=point.time
                        )
                        new_segment.points.append(new_point)

                    new_track.segments.append(new_segment)

                new_gpx.tracks.append(new_track)

            for route in gpx.routes:
                new_route = gpxpy.gpx.GPXRoute()
                if track_name:
                    new_route.name = track_name
                elif route.name:
                    new_route.name = route.name

                for point in route.points:
                    new_point = gpxpy.gpx.GPXRoutePoint(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        elevation=point.elevation
                    )
                    new_route.points.append(new_point)

                new_gpx.routes.append(new_route)

            with open(file_path, 'w', encoding='utf-8') as gpx_file:
                gpx_file.write(new_gpx.to_xml())

            return True

        except Exception as e:
            if self.verbose:
                print(f"!!! Error fixing {file_path.name}: {e}")
            return False


def find_gpx_files(directory: Path, recursive: bool = False) -> list[Path]:
    """
    Find all GPX files in the specified directory.

    Args:
        directory (Path): Directory to search in.
        recursive (bool): Whether to search recursively in subdirectories.

    Returns:
        list[Path]: List of GPX file paths.
    """
    if recursive:
        return list(directory.rglob("*.gpx")) + list(directory.rglob("*.GPX"))
    else:
        return [f for f in directory.iterdir() if f.suffix.lower() == '.gpx']


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze GPX files and check filename format consistency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Check GPX files in current directory
  %(prog)s /path/to/gpx/files       # Check GPX files in specified directory
  %(prog)s -r /path/to/gpx/files    # Recursively search subdirectories
  %(prog)s -v /path/to/gpx/files    # Verbose output with error details
  %(prog)s --fix /path/to/gpx/files # Fix files to remove extra metadata and update track names
  %(prog)s -c /path/to/gpx/files    # Count and display points per file
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan for GPX files (default: current directory)'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively search subdirectories for GPX files'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output with detailed error messages'
    )

    parser.add_argument(
        '-f', '--fix',
        action='store_true',
        help='Fix GPX files to remove extra metadata and update track names from filename (YYYY-MM-DD NAME format)'
    )

    parser.add_argument(
        '-c', '--count-points',
        action='store_true',
        help='Count and display track points, waypoints, and route points per file'
    )

    return parser.parse_args()


def main() -> None:
    """Main function to scan a directory for GPX files and process them."""
    args = parse_arguments()

    target_directory = Path(args.directory).resolve()

    if not target_directory.is_dir():
        print(f"❌ Error: Directory not found at '{target_directory}'")
        sys.exit(1)

    print(f"🔍 Scanning for GPX files in: {target_directory}")
    if args.recursive:
        print("📁 (including subdirectories)")
    if args.fix:
        print("🔧 Fix mode enabled - files will be simplified and track names updated")
    else:
        print("✅ Format checking enabled")
    if args.count_points:
        print("📊 Point counting enabled")
    print()

    gpx_files = find_gpx_files(target_directory, args.recursive)

    if not gpx_files:
        print("🚫 No GPX files found in the specified directory.")
        return

    analyzer = GPXAnalyzer(verbose=args.verbose, fix_files=args.fix, count_points=args.count_points)
    successful_analyses = 0
    fixed_files = 0

    for gpx_file in sorted(gpx_files):
        file_info = analyzer.analyze_file(gpx_file)
        if file_info:
            if args.fix:
                if analyzer.fix_gpx_file(gpx_file):
                    print(f"🔧 {gpx_file.name}")
                    fixed_files += 1
                else:
                    print(f"❌ {gpx_file.name}")
            else:
                warnings = analyzer._check_filename_format(file_info)
                analyzer.print_file_info(file_info, warnings)
            successful_analyses += 1

    total_files = len(gpx_files)
    failed_files = total_files - successful_analyses

    if args.fix:
        print(f"\n📊 Summary: Successfully fixed {fixed_files}/{successful_analyses} GPX files.")
    else:
        print(f"\n📊 Summary: Analyzed {successful_analyses}/{total_files} GPX files successfully.")

    if failed_files > 0:
        print(f"⚠️ Failed to parse {failed_files} file(s). Use -v for details.")

if __name__ == "__main__":
    main()
