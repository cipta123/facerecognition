"""
Batch Encoder untuk process semua foto dan generate embeddings
Support: sample mode, custom file list, resume capability
"""
import os
import sys
import random
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
import argparse

from face_recognition.config import PHOTOS_DIR, SUPPORTED_FORMATS
from face_recognition.encoder import ArcFaceEncoder
from face_recognition.database import FaceDatabase


class BatchEncoder:
    """Batch encoder untuk process multiple photos."""
    
    def __init__(self):
        """Initialize encoder dan database."""
        print("Initializing ArcFace encoder...")
        self.encoder = ArcFaceEncoder()
        self.db = FaceDatabase()
        print("Initialization complete!")
    
    def extract_nim_from_filename(self, filename: str) -> str:
        """
        Extract NIM atau identifier dari filename.
        Format: {nim}.jpg, {nim}.png, atau {identifier}.{ext}
        
        Args:
            filename: Filename (dengan atau tanpa path)
            
        Returns:
            NIM atau identifier
        """
        # Get basename tanpa extension
        name = Path(filename).stem
        return name
    
    def get_photo_files(self, photos_dir: Path) -> List[Path]:
        """
        Get semua photo files dari directory.
        
        Args:
            photos_dir: Directory berisi foto
            
        Returns:
            List of photo file paths
        """
        photo_files = []
        for ext in SUPPORTED_FORMATS:
            photo_files.extend(photos_dir.glob(f"*{ext}"))
        return sorted(photo_files)
    
    def process_file(self, photo_path: Path, force: bool = False) -> tuple:
        """
        Process single photo file.
        
        Args:
            photo_path: Path ke photo file
            force: Jika True, regenerate embedding meskipun sudah ada di database
            
        Returns:
            (success: bool, nim: str, error: str or None)
        """
        try:
            # Extract NIM dari filename
            nim = self.extract_nim_from_filename(photo_path.name)
            
            # Check if already exists in database
            if not force:
                existing = self.db.get_embedding(nim)
                if existing is not None:
                    return (True, nim, "Already processed (use --force to regenerate)")
            
            # Generate embedding
            embedding = self.encoder.encode_from_path(str(photo_path))
            
            if embedding is None:
                return (False, nim, "Gagal generate embedding (no face detected atau error)")
            
            # Save to database (will overwrite if exists)
            success = self.db.save_embedding(nim, embedding, str(photo_path))
            
            if success:
                return (True, nim, None)
            else:
                return (False, nim, "Gagal save ke database")
                
        except Exception as e:
            nim = self.extract_nim_from_filename(photo_path.name)
            return (False, nim, str(e))
    
    def process_files(self, photo_files: List[Path], desc: str = "Processing", force: bool = False) -> dict:
        """
        Process multiple photo files.
        
        Args:
            photo_files: List of photo file paths
            desc: Progress bar description
            force: Jika True, regenerate embedding meskipun sudah ada di database
            
        Returns:
            Statistics dict
        """
        stats = {
            'total': len(photo_files),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        with tqdm(total=len(photo_files), desc=desc) as pbar:
            for photo_path in photo_files:
                success, nim, error = self.process_file(photo_path, force=force)
                
                if success:
                    if error is None or "Regenerated" in str(error):
                        stats['success'] += 1
                    else:
                        stats['skipped'] += 1  # Already exists (and not forced)
                else:
                    stats['failed'] += 1
                    stats['errors'].append({
                        'nim': nim,
                        'file': str(photo_path),
                        'error': error
                    })
                
                pbar.update(1)
                pbar.set_postfix({
                    'success': stats['success'],
                    'failed': stats['failed'],
                    'skipped': stats['skipped']
                })
        
        return stats
    
    def process_sample(self, n: int = 100, force: bool = False) -> dict:
        """
        Process random sample of photos.
        
        Args:
            n: Number of samples
            force: Jika True, regenerate embedding meskipun sudah ada di database
            
        Returns:
            Statistics dict
        """
        photo_files = self.get_photo_files(PHOTOS_DIR)
        
        if len(photo_files) == 0:
            print(f"Tidak ada foto ditemukan di {PHOTOS_DIR}")
            return {}
        
        # Random sample
        if n > len(photo_files):
            n = len(photo_files)
        
        sample_files = random.sample(photo_files, n)
        print(f"Processing {n} random samples dari {len(photo_files)} total files...")
        
        return self.process_files(sample_files, desc="Processing samples", force=force)
    
    def process_custom_files(self, file_list: List[str], force: bool = False) -> dict:
        """
        Process custom file list.
        
        Args:
            file_list: List of filenames atau paths
            force: Jika True, regenerate embedding meskipun sudah ada di database
            
        Returns:
            Statistics dict
        """
        photo_files = []
        for file_path in file_list:
            # Try as absolute path first
            path = Path(file_path)
            if not path.is_absolute():
                # Try relative to photos directory
                path = PHOTOS_DIR / file_path
            
            if path.exists():
                photo_files.append(path)
            else:
                print(f"Warning: File tidak ditemukan: {file_path}")
        
        if len(photo_files) == 0:
            print("Tidak ada file valid untuk diproses")
            return {}
        
        print(f"Processing {len(photo_files)} custom files...")
        return self.process_files(photo_files, desc="Processing custom files", force=force)
    
    def process_nims(self, nim_list: List[str], force: bool = False) -> dict:
        """
        Process specific NIMs dari database.
        Mencari file foto berdasarkan NIM di photos directory.
        
        Args:
            nim_list: List of NIMs atau identifiers
            force: Jika True, regenerate embedding meskipun sudah ada di database
            
        Returns:
            Statistics dict
        """
        photo_files = []
        for nim in nim_list:
            # Cari file dengan nama NIM (dengan berbagai extension)
            found = False
            for ext in SUPPORTED_FORMATS:
                photo_path = PHOTOS_DIR / f"{nim}{ext}"
                if photo_path.exists():
                    photo_files.append(photo_path)
                    found = True
                    break
            
            if not found:
                print(f"Warning: Foto tidak ditemukan untuk NIM: {nim}")
        
        if len(photo_files) == 0:
            print("Tidak ada foto ditemukan untuk NIM yang diminta")
            return {}
        
        print(f"Processing {len(photo_files)} files untuk {len(nim_list)} NIMs...")
        return self.process_files(photo_files, desc="Processing NIMs", force=force)
    
    def process_all(self, force: bool = False) -> dict:
        """
        Process semua foto dari photos directory.
        
        Args:
            force: Jika True, regenerate embedding meskipun sudah ada di database
            
        Returns:
            Statistics dict
        """
        photo_files = self.get_photo_files(PHOTOS_DIR)
        
        if len(photo_files) == 0:
            print(f"Tidak ada foto ditemukan di {PHOTOS_DIR}")
            return {}
        
        print(f"Processing {len(photo_files)} files...")
        return self.process_files(photo_files, desc="Processing all files", force=force)
    
    def print_stats(self, stats: dict):
        """Print processing statistics."""
        print("\n" + "="*60)
        print("PROCESSING STATISTICS")
        print("="*60)
        print(f"Total files    : {stats.get('total', 0)}")
        print(f"Success        : {stats.get('success', 0)}")
        print(f"Failed         : {stats.get('failed', 0)}")
        print(f"Skipped        : {stats.get('skipped', 0)}")
        
        if stats.get('errors'):
            print(f"\nErrors ({len(stats['errors'])}):")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error['nim']}: {error['error']}")
            if len(stats['errors']) > 10:
                print(f"  ... dan {len(stats['errors']) - 10} error lainnya")
        print("="*60)


def main():
    """Entry point untuk batch encoder."""
    parser = argparse.ArgumentParser(description="Batch encoder untuk face recognition")
    parser.add_argument(
        "--sample", 
        type=int, 
        default=None,
        help="Process N random samples"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Process custom file list (e.g., --files cipta_anugrah.png 857264993.jpg)"
    )
    parser.add_argument(
        "--nims",
        nargs="+",
        help="Process specific NIMs (e.g., --nims 857264993 857267523 cipta_anugrah)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process semua foto"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regenerate embeddings meskipun sudah ada di database"
    )
    
    args = parser.parse_args()
    
    # Initialize batch encoder
    batch_encoder = BatchEncoder()
    
    # Process based on arguments
    if args.nims:
        # Process specific NIMs
        stats = batch_encoder.process_nims(args.nims, force=args.force)
    elif args.files:
        # Custom file list
        stats = batch_encoder.process_custom_files(args.files, force=args.force)
    elif args.sample:
        # Random sample
        stats = batch_encoder.process_sample(args.sample, force=args.force)
    elif args.all:
        # All files
        stats = batch_encoder.process_all(force=args.force)
    else:
        # Default: process sample dengan cipta_anugrah.png
        print("No mode specified. Processing sample dengan cipta_anugrah.png...")
        default_files = ["cipta_anugrah.png"]
        # Add some JPG files if available
        photo_files = batch_encoder.get_photo_files(PHOTOS_DIR)
        jpg_files = [f.name for f in photo_files if f.suffix.lower() in ['.jpg', '.jpeg']]
        if jpg_files:
            default_files.extend(jpg_files[:5])  # Add first 5 JPG files
        
        stats = batch_encoder.process_custom_files(default_files, force=args.force)
    
    # Print statistics
    batch_encoder.print_stats(stats)
    
    # Close database
    batch_encoder.db.close()


if __name__ == "__main__":
    main()

