"""
Upload photos and videos from a folder to Immich instance.
The script retries failed uploads and provides detailed progress information.

Usage:
    python upload.py <photos_folder> [-a ALBUM_ID | --album ALBUM_ID]

Environment variables (can be set in .env file):
    URL - Immich server URL (e.g., https://immich.example.com)
    API_KEY - Immich API key

CLI arguments:
    photos_folder - Path to the folder containing images/videos to upload
    -a, --album   - Album UUID to upload files to (optional)
"""

import os
import time
from common import setup_args, make_request, validate_directory, get_all_files, SUPPORTED_EXTENSIONS

ARGS = setup_args("Upload files to Immich",
                 ("photos_folder", {"help": "Path to the folder containing photos to upload"}),
                 ("-a", "--album", {"help": "Album UUID to upload photos to", "default": None}))

DIRECTORY = ARGS.photos_folder
ALBUM_ID = ARGS.album

MAX_RETRIES = 10
RETRY_DELAY = 2 # seconds

def is_supported_file(filepath):
    _, ext = os.path.splitext(filepath)
    return ext.lower() in SUPPORTED_EXTENSIONS

def upload_file(filepath):
    endpoint = "/api/assets"

    with open(filepath, 'rb') as f:
        files = {
            'assetData': (os.path.basename(filepath), f, 'application/octet-stream')
        }
        data = {
            'deviceAssetId': os.path.basename(filepath),
            'deviceId': 'upload-script',
            'fileCreatedAt': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(os.path.getctime(filepath))),
            'fileModifiedAt': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(os.path.getmtime(filepath)))
        }

        response = make_request("POST", endpoint, data, files=files)
        return response.json()

def upload_with_retry(filepath, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        time.sleep(RETRY_DELAY * attempt) # exponential backoff
        try:
            result = upload_file(filepath)
            return True, result
        except Exception as e:
            continue
    return False, str(e)

def add_asset_to_album(album_id, asset_id):
    endpoint = f"/api/albums/{album_id}/assets"
    payload = {"ids": [asset_id]}
    response = make_request("PUT", endpoint, payload)
    return response.json()

def main():
    validate_directory(DIRECTORY)

    files = [f for f in get_all_files(DIRECTORY) if is_supported_file(f)]

    total_files = len(files)
    uploaded_files = []
    warning_album_files = []
    failed_files = []

    album_text = f" to album {ALBUM_ID}" if ALBUM_ID else ""
    print(f"📤 Uploading {total_files} files from {DIRECTORY} (recursive){album_text}")
    print("=" * 80)

    for i, filepath in enumerate(files):
        relative_path = os.path.relpath(filepath, DIRECTORY)
        progress = f"[{i+1:>{len(str(total_files))}}/{total_files}]"

        print(f"{progress} {relative_path:<40} ", end="", flush=True)

        success, result = upload_with_retry(filepath)

        if success:
            if ALBUM_ID and 'id' in result:
                try:
                    add_asset_to_album(ALBUM_ID, result['id'])
                    print("✅ Uploaded and added to album")
                    uploaded_files.append(relative_path)
                except Exception as e:
                    print("⚠️ Uploaded but failed to add to album")
                    warning_album_files.append(relative_path)
            else:
                print("✅ Uploaded successfully")
                uploaded_files.append(relative_path)
        else:
            print(f"❌ Failed after {MAX_RETRIES} attempts: {result}")
            failed_files.append((relative_path, result))

    print("=" * 80)

    if uploaded_files:
        print(f"✅ Successfully uploaded {len(uploaded_files)} files:")
        for filename in uploaded_files:
            print(f"   • {filename}")

    if warning_album_files:
        print(f"⚠️  Uploaded but failed to add to album {len(warning_album_files)} files:")
        for filename in warning_album_files:
            print(f"   • {filename}")

    if failed_files:
        print(f"\n❌ Failed to upload {len(failed_files)} files:")
        for filename, error in failed_files:
            print(f"   • {filename}: {error}")

    if not uploaded_files and not failed_files:
        print("ℹ️  No supported files found to upload")

    print(f"📊 Summary: {len(uploaded_files)} files uploaded, {len(failed_files)} files failed")

if __name__ == "__main__":
    main()
