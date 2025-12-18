"""
Utility functions for SRS5G Photo Scraper
"""
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any

from config import PROGRESS_FILE, ERROR_FILE, PHOTOS_DIR, OUTPUT_DIR


def ensure_directories():
    """Create output directories if they don't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    PHOTOS_DIR.mkdir(exist_ok=True)


def load_nim_from_csv(csv_path: str) -> List[str]:
    """
    Load NIM list from CSV file.
    Expects CSV with column 'nim' or first column as NIM.
    """
    nim_list = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        
        # Try to find 'nim' column (case-insensitive)
        nim_column = None
        for field in fieldnames:
            if field.lower() == 'nim':
                nim_column = field
                break
        
        # If no 'nim' column, use first column
        if nim_column is None and fieldnames:
            nim_column = fieldnames[0]
        
        if nim_column is None:
            raise ValueError("CSV file must have at least one column")
        
        for row in reader:
            nim = str(row[nim_column]).strip()
            if nim:
                nim_list.append(nim)
    
    return nim_list


def load_progress() -> Dict[str, Any]:
    """Load progress from JSON file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "completed": [],
        "failed": [],
        "last_updated": None
    }


def save_progress(progress: Dict[str, Any]):
    """Save progress to JSON file."""
    progress["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def add_completed(nim: str, progress: Dict[str, Any]):
    """Mark NIM as completed and save progress."""
    if nim not in progress["completed"]:
        progress["completed"].append(nim)
        save_progress(progress)


def add_failed(nim: str, reason: str, progress: Dict[str, Any]):
    """Mark NIM as failed, log error, and save progress."""
    # Add to failed list if not already there
    failed_entry = {"nim": nim, "reason": reason, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    # Check if already in failed list
    existing = [f for f in progress["failed"] if f.get("nim") == nim]
    if not existing:
        progress["failed"].append(failed_entry)
        save_progress(progress)
    
    # Log to error file
    log_error(nim, reason)


def log_error(nim: str, reason: str):
    """Append error to error.txt file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] NIM: {nim} - Error: {reason}\n")


def photo_exists(nim: str) -> bool:
    """Check if photo file already exists."""
    photo_path = PHOTOS_DIR / f"{nim}.jpg"
    return photo_path.exists()


def get_photo_path(nim: str) -> Path:
    """Get the path where photo should be saved."""
    return PHOTOS_DIR / f"{nim}.jpg"


def save_photo(nim: str, image_bytes: bytes) -> bool:
    """Save image bytes to file."""
    try:
        photo_path = get_photo_path(nim)
        with open(photo_path, 'wb') as f:
            f.write(image_bytes)
        return True
    except Exception as e:
        log_error(nim, f"Failed to save photo: {str(e)}")
        return False


def get_pending_nims(all_nims: List[str], progress: Dict[str, Any]) -> List[str]:
    """
    Get list of NIMs that still need to be processed.
    Filters out completed NIMs and NIMs with existing photo files.
    """
    completed_set = set(progress["completed"])
    pending = []
    
    for nim in all_nims:
        # Skip if already completed
        if nim in completed_set:
            continue
        
        # Skip if photo already exists (add to completed)
        if photo_exists(nim):
            add_completed(nim, progress)
            continue
        
        pending.append(nim)
    
    return pending


def print_summary(progress: Dict[str, Any], total_nims: int):
    """Print summary of scraping progress."""
    completed = len(progress["completed"])
    failed = len(progress["failed"])
    remaining = total_nims - completed
    
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    print(f"Total NIM      : {total_nims}")
    print(f"Completed      : {completed}")
    print(f"Failed         : {failed}")
    print(f"Remaining      : {remaining}")
    print(f"Success Rate   : {(completed/total_nims*100):.1f}%" if total_nims > 0 else "N/A")
    print("="*50)

