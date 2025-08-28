"""
Check if some photos (contained in the IMAGES folder) are already uploaded to Immich,
without actually uploading them, but searching for the hash.
If the photo IS uploaded and -d/--delete flag is specified, it is deleted from the local directory.

Usage:
    python check-uploaded.py <photos_folder> [-d | --delete]

Environment variables (can be set in .env file):
    URL - Immich server URL (e.g., https://immich.example.com)
    API_KEY - Immich API key

CLI arguments:
    photos_folder - Path to the folder containing images to check
    -d, --delete  - Delete files that are already uploaded (optional)
"""

import hashlib
import os
from common import setup_args, make_request, validate_directory, get_all_files, SUPPORTED_EXTENSIONS

ARGS = setup_args("Check if files are uploaded to Immich",
                 ("photos_folder", {"help": "Path to the folder containing photos to check"}),
                 ("-d", "--delete", {"help": "Delete files that are already uploaded", "action": "store_true"}))

DIRECTORY = ARGS.photos_folder
DELETE_FILES = ARGS.delete

def is_supported_file(filepath):
    _, ext = os.path.splitext(filepath)
    return ext.lower() in SUPPORTED_EXTENSIONS

def sha1(filepath):
    hash_sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()

def search(checksum):
    endpoint = "/api/search/metadata"
    payload = {"checksum": checksum}
    try:
        response = make_request("POST", endpoint, payload)
        data = response.json() or {}
        assets = data.get("assets", {})
        return {
            "count": assets.get("count", 0),
            "items": assets.get("items", []),
        }
    except Exception as e:
        print(f"Search API error: {e}")
        return {"count": 0, "items": []}

def albums(id):
    endpoint = f"/api/albums?assetId={id}"
    try:
        response = make_request("GET", endpoint)
        return response.json()
    except Exception as e:
        print(f"Albums API error: {e}")
        return []

def main():
    validate_directory(DIRECTORY)

    files = [f for f in get_all_files(DIRECTORY) if is_supported_file(f)]
    deleted_files = []
    found_files = []

    total_files = len(files)

    delete_text = " (will delete duplicates)" if DELETE_FILES else " (check only)"
    print(f"🔍 Checking {total_files} files in {DIRECTORY} (recursive){delete_text}")
    print("=" * 80)

    for i, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        relative_path = os.path.relpath(filepath, DIRECTORY)
        progress = f"[{i+1:>{len(str(total_files))}}/{total_files}]"

        print(f"{progress} {relative_path:<40} ", end="", flush=True)

        result = search(sha1(filepath))

        if result["count"] == 0:
            print("❌ Not found - keeping file")
            continue
        elif result["count"] > 1:
            print("⚠️ Multiple results found - keeping file")
            continue

        asset = result["items"][0] if result["items"] else {}
        asset_id = asset.get("id")
        if not asset_id:
            print("⚠️ Result missing asset id - keeping file")
            continue

        item_albums = [al["albumName"] for al in albums(asset_id)]
        albums_str = ", ".join(item_albums) if item_albums else "No albums"

        if DELETE_FILES:
            try:
                print(f"✅ Found in [{albums_str}] - deleting")
                os.remove(filepath)
                deleted_files.append(relative_path)
            except Exception as e:
                print(f"⚠️ Failed to delete: {e}")
        else:
            print(f"✅ Found in [{albums_str}] - would delete")
            found_files.append(relative_path)

    print("=" * 80)
    if DELETE_FILES:
        if deleted_files:
            print(f"🗑️  Deleted {len(deleted_files)} files that were already uploaded:")
            for filename in deleted_files:
                print(f"   • {filename}")
        else:
            print("ℹ️  No files were deleted - all files are unique or not found")

        kept_files = total_files - len(deleted_files)
        print(f"📊 Summary: {kept_files} files kept, {len(deleted_files)} files deleted")
    else:
        if found_files:
            print(f"📋 Found {len(found_files)} files that are already uploaded:")
            for filename in found_files:
                print(f"   • {filename}")
        else:
            print("ℹ️  No duplicate files found")

        would_keep = total_files - len(found_files)
        print(f"📊 Summary: {would_keep} files would be kept, {len(found_files)} files would be deleted")

if __name__ == "__main__":
    main()
