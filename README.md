# Utility Scripts

Collection of various utility scripts _(probably vibe coded)_.

## Scripts

<details>
<summary><strong>restic-backup.sh</strong> - Backup using Restic</summary>

Automated backup script using Restic with validation and cleanup functionality.

```bash
sudo ./restic-backup.sh <BACKUP_DIR> <RESTIC_REPO>
```

**Requirements:** `restic`

</details>

<details>
<summary><strong>video-converter.sh</strong> - Video format converter</summary>

Converts between video formats for DaVinci Resolve workflows.

```bash
# Convert MP4 to DNxHD (for DaVinci import)
./video-converter.sh to-dnxhd <directory>

# Convert MOV to mobile MP4 (for DaVinci export)
./video-converter.sh to-mobile <directory>
```

**Requirements:** `ffmpeg`

</details>

<details>
<summary><strong>gpx-editor.py</strong> - Standardize GPX files</summary>

Standardizes GPX files exported from various GPS recorders by removing unnecessary metadata.
Enforces consistent file naming to match internal track names.

```bash
python gpx-editor.py [OPTIONS] [DIRECTORY]

# Options:
-r    # recursive search
-v    # verbose output
-f    # fix files
-c    # count points
```

**Requirements:** `pip gpxpy`

</details>
