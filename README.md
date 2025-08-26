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
<summary><strong>mp4-to-DHxHD.sh</strong> - Convert MP4 to DNxHD format</summary>

Converts MP4 files to DaVinci Resolve-compatible DNxHD format (MP4 files import as audio-only in DaVinci).

```bash
./mp4-to-DHxHD.sh <directory>
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

**Requirements:** `gpxpy`

</details>
