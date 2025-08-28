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

<details>
<summary><strong>immich</strong> - Immich utility scripts</summary>

Simple utility scripts for Immich:

- [immich/check-uploaded.py](immich/check-uploaded.py): Verify if photos are already uploaded to Immich, with optional deletion of local copies.
- [immich/upload.py](immich/upload.py): Upload photos and videos to Immich with retry functionality and album support.

<h4>Setup</h4>

Configure the required environment variables using the <code>.env.template</code> file in <code>immich/</code>:

- <code>URL</code>: The URL of your Immich instance
- <code>API_KEY</code>: Your Immich API key (available in Account Settings of the Immich web interface)

<h4>Usage</h4>

<b>check-uploaded.py</b>

```bash
python immich/check-uploaded.py <photos_folder> [-d | --delete]
```

<b>upload.py</b>

```bash
python immich/upload.py <photos_folder> [-a ALBUM_ID | --album ALBUM_ID]
```

</details>
