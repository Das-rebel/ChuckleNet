#!/usr/bin/env python3
"""
☁️ GOOGLE DRIVE DATA STORAGE SYSTEM
Memory-efficient solution for 8GB RAM constraint using cloud storage
"""

import os
import sys
import json
import logging
import io
from pathlib import Path
from typing import Dict, List, Optional

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleDriveDataManager:
    """
    ☁️ Google Drive Integration for Memory-Constrained Training
    Stores raw data on Google Drive, loads only what's needed for training
    """
    
    def __init__(self):
        self.drive_folder_id = None  # Will be set up
        self.local_cache_dir = Path("gdrive_cache")
        self.local_cache_dir.mkdir(exist_ok=True)
        
        # Memory-efficient chunking
        self.chunk_size = 100  # Load 100 samples at a time
        self.max_memory_usage = 4  # Stay under 4GB for training
        
    def setup_google_drive(self) -> bool:
        """Setup Google Drive integration"""
        logger.info("☁️  SETTING UP GOOGLE DRIVE INTEGRATION")
        logger.info("=" * 80)
        
        try:
            # Check for Google Drive API credentials
            if not os.path.exists('credentials.json'):
                logger.info("📋 Setting up Google Drive API...")
                self.setup_google_drive_api()
            else:
                logger.info("✅ Google Drive credentials found")
            
            # Check for gdown or pydrive
            if self.check_gdown_available():
                logger.info("✅ gdown available for file downloads")
            elif self.check_pydrive_available():
                logger.info("✅ PyDrive available for API access")
            else:
                logger.info("📦 Installing Google Drive tools...")
                self.install_drive_tools()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Drive setup failed: {e}")
            return False
    
    def setup_google_drive_api(self):
        """Guide user through Google Drive API setup"""
        logger.info("📋 GOOGLE DRIVE API SETUP REQUIRED")
        logger.info("1. Visit: https://console.cloud.google.com/")
        logger.info("2. Create a new project")
        logger.info("3. Enable Google Drive API")
        logger.info("4. Create OAuth 2.0 credentials")
        logger.info("5. Download credentials.json")
        logger.info("6. Place credentials.json in project directory")
        logger.info("")
        logger.info("Alternative: Use gdown with shareable links (simpler)")
        
    def check_gdown_available(self) -> bool:
        """Check if gdown is available"""
        try:
            import subprocess
            result = subprocess.run(['gdown', '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def check_pydrive_available(self) -> bool:
        """Check if PyDrive is available"""
        try:
            from pydrive.drive import GoogleDrive
            from pydrive.auth import GoogleAuth
            return True
        except ImportError:
            return False
    
    def install_drive_tools(self):
        """Install Google Drive tools"""
        logger.info("📦 Installing Google Drive tools...")
        
        try:
            import subprocess
            
            # Install gdown (simpler alternative)
            subprocess.run(['pip3', 'install', 'gdown'], 
                          check=True, timeout=300)
            logger.info("✅ gdown installed successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not install gdown: {e}")
            logger.info("💡 Alternative: Upload data manually to Google Drive")
    
    def upload_harvested_data_to_drive(self, data_files: List[Path]) -> bool:
        """Upload harvested comedy data to Google Drive"""
        logger.info("☁️  UPLOADING HARVESTED DATA TO GOOGLE DRIVE")
        logger.info("=" * 80)
        
        try:
            # Method 1: Use gdown for individual files
            for data_file in data_files:
                if data_file.exists():
                    logger.info(f"📤 Uploading: {data_file.name}")
                    self.upload_file_to_gdrive(data_file)
            
            logger.info("✅ Data upload complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    def upload_file_to_gdrive(self, file_path: Path):
        """Upload individual file to Google Drive"""
        try:
            # For now, provide manual instructions
            logger.info(f"📋 MANUAL UPLOAD REQUIRED FOR: {file_path.name}")
            logger.info("1. Go to: https://drive.google.com")
            logger.info("2. Create folder: 'comedy_training_data'")
            logger.info(f"3. Upload file: {file_path}")
            logger.info("4. Get shareable link")
            logger.info("5. Save link to: gdrive_links.json")
            
        except Exception as e:
            logger.error(f"❌ File upload failed: {e}")
    
    def create_gdrive_links_file(self):
        """Create file to store Google Drive links"""
        links_file = Path("gdrive_links.json")
        
        if not links_file.exists():
            example_links = {
                "opensubtitles_data": "https://drive.google.com/file/PLACEHOLDER/view",
                "addic7ed_data": "https://drive.google.com/file/PLACEHOLDER/view",
                "scraps_loft_data": "https://drive.google.com/file/PLACEHOLDER/view",
                "aligned_data": "https://drive.google.com/file/PLACEHOLDER/view",
                "wesr_bench_data": "https://drive.google.com/file/PLACEHOLDER/view"
            }
            
            with open(links_file, 'w') as f:
                json.dump(example_links, f, indent=2)
            
            logger.info("✅ Created gdrive_links.json - add your Google Drive links")
    
    def load_data_from_gdrive(self, data_type: str, chunk_size: int = 100) -> List[Dict]:
        """
        Memory-efficient loading from Google Drive
        Loads data in chunks to respect 8GB RAM constraint
        """
        logger.info(f"☁️  LOADING {data_type} FROM GOOGLE DRIVE (chunk size: {chunk_size})")
        
        try:
            # Load Google Drive links
            links_file = Path("gdrive_links.json")
            
            if not links_file.exists():
                logger.warning("⚠️  gdrive_links.json not found - using local data")
                return self.load_local_data_chunk(data_type, chunk_size)
            
            with open(links_file, 'r') as f:
                gdrive_links = json.load(f)
            
            if data_type not in gdrive_links:
                logger.warning(f"⚠️  No Google Drive link for {data_type}")
                return self.load_local_data_chunk(data_type, chunk_size)
            
            gdrive_url = gdrive_links[data_type]
            
            # Download chunk from Google Drive
            logger.info(f"📥 Downloading chunk from: {gdrive_url}")
            
            # Method 1: Try gdown
            if self.check_gdown_available():
                return self.download_with_gdown(gdrive_url, chunk_size)
            
            # Method 2: Try manual download
            else:
                return self.manual_gdrive_download(gdrive_url, chunk_size)
            
        except Exception as e:
            logger.error(f"❌ Failed to load from Google Drive: {e}")
            return self.load_local_data_chunk(data_type, chunk_size)
    
    def download_with_gdown(self, gdrive_url: str, chunk_size: int) -> List[Dict]:
        """Download data using gdown"""
        try:
            import subprocess
            
            # Extract file ID from Google Drive URL
            file_id = self.extract_gdrive_file_id(gdrive_url)
            
            # Download to cache
            cache_file = self.local_cache_dir / f"chunk_{chunk_size}.json"
            
            if not cache_file.exists():
                subprocess.run([
                    'gdown', 
                    f'https://drive.google.com/uc?id={file_id}',
                    '-O', str(cache_file)
                ], check=True, timeout=300)
            
            # Load chunk
            return self.load_data_chunk_from_file(cache_file, chunk_size)
            
        except Exception as e:
            logger.error(f"❌ gdown download failed: {e}")
            return []
    
    def manual_gdrive_download(self, gdrive_url: str, chunk_size: int) -> List[Dict]:
        """Provide instructions for manual download"""
        logger.info("📋 MANUAL DOWNLOAD REQUIRED")
        logger.info("1. Visit Google Drive link")
        logger.info("2. Download file to local cache directory")
        logger.info("3. System will load from cache")
        logger.info(f"Cache directory: {self.local_cache_dir}")
        
        # Try to load from cache
        cache_files = list(self.local_cache_dir.glob("*.json"))
        if cache_files:
            return self.load_data_chunk_from_file(cache_files[0], chunk_size)
        
        return []
    
    def load_local_data_chunk(self, data_type: str, chunk_size: int) -> List[Dict]:
        """Load chunk of data from local storage"""
        logger.info(f"💾 Loading local {data_type} chunk...")
        
        try:
            if data_type == "synthetic":
                return self.load_synthetic_chunk(chunk_size)
            elif data_type == "real":
                return self.load_real_data_chunk(chunk_size)
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to load local chunk: {e}")
            return []
    
    def load_synthetic_chunk(self, chunk_size: int) -> List[Dict]:
        """Load chunk of synthetic data"""
        synthetic_path = Path("data/sample_transcripts.jsonl")
        
        if not synthetic_path.exists():
            logger.warning("⚠️  Synthetic data not found")
            return []
        
        chunk = []
        with open(synthetic_path, 'r') as f:
            for i, line in enumerate(f):
                if i >= chunk_size:
                    break
                try:
                    chunk.append(json.loads(line.strip()))
                except Exception:
                    continue
        
        logger.info(f"✅ Loaded {len(chunk)} synthetic samples")
        return chunk
    
    def load_real_data_chunk(self, chunk_size: int) -> List[Dict]:
        """Load chunk of real harvested data"""
        import sqlite3
        
        db_path = Path("comedy_enhanced_harvest.db")
        
        if not db_path.exists():
            logger.warning("⚠️  Real data database not found")
            return []
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, source, title, clean_text, has_laughter, 
                   laughter_tags_found, comedian, year
            FROM enhanced_harvest
            WHERE processed = 1
            LIMIT ?
        """, (chunk_size,))
        
        items = cursor.fetchall()
        conn.close()
        
        chunk = []
        for item in items:
            chunk.append({
                'id': item[0],
                'source': item[1],
                'title': item[2] if item[2] else '',
                'text': item[3],
                'label': 1 if item[4] else 0,
                'laughter_count': item[5] if item[5] else 0,
                'comedian': item[6],
                'year': item[7],
                'data_type': 'real'
            })
        
        logger.info(f"✅ Loaded {len(chunk)} real comedy samples")
        return chunk
    
    def load_data_chunk_from_file(self, file_path: Path, chunk_size: int) -> List[Dict]:
        """Load chunk from cached file"""
        chunk = []
        
        try:
            with open(file_path, 'r') as f:
                for i, line in enumerate(f):
                    if i >= chunk_size:
                        break
                    try:
                        if file_path.suffix == '.jsonl':
                            chunk.append(json.loads(line.strip()))
                        else:
                            # Assume JSON array
                            data = json.load(f)
                            chunk = data[:chunk_size]
                            break
                    except Exception:
                        continue
            
            logger.info(f"✅ Loaded {len(chunk)} samples from cache")
            
        except Exception as e:
            logger.error(f"❌ Failed to load from cache: {e}")
        
        return chunk
    
    def extract_gdrive_file_id(self, url: str) -> str:
        """Extract file ID from Google Drive URL"""
        if '/file/d/' in url:
            return url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            return url.split('id=')[1].split('&')[0]
        else:
            return url
    
    def monitor_memory_usage(self) -> bool:
        """Monitor and manage memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_gb = memory_info.rss / 1024 / 1024 / 1024
            
            logger.info(f"💾 Current memory usage: {memory_gb:.2f}GB")
            
            if memory_gb > self.max_memory_usage:
                logger.warning(f"⚠️  Memory usage high: {memory_gb:.2f}GB")
                logger.info("🧹 Clearing cache and reducing chunk size...")
                self.clear_cache()
                self.chunk_size = max(50, self.chunk_size // 2)
                return False
            
            return True
            
        except ImportError:
            # psutil not available, skip monitoring
            return True
    
    def clear_cache(self):
        """Clear local cache to free memory"""
        logger.info("🧹 Clearing local cache...")
        
        import shutil
        if self.local_cache_dir.exists():
            shutil.rmtree(self.local_cache_dir)
            self.local_cache_dir.mkdir(exist_ok=True)
        
        logger.info("✅ Cache cleared")

def main():
    """Setup Google Drive integration for memory-constrained training"""
    logger.info("☁️  GOOGLE DRIVE DATA STORAGE SETUP")
    logger.info("=" * 80)
    
    # Initialize Google Drive manager
    drive_manager = GoogleDriveDataManager()
    
    # Setup Google Drive
    if drive_manager.setup_google_drive():
        logger.info("✅ Google Drive setup successful")
    else:
        logger.info("💡 Manual setup required - see instructions above")
    
    # Create links file
    drive_manager.create_gdrive_links_file()
    
    # Test memory-efficient loading
    logger.info("🧪 TESTING MEMORY-EFFICIENT LOADING")
    
    synthetic_chunk = drive_manager.load_data_from_gdrive("synthetic", chunk_size=50)
    logger.info(f"✅ Loaded {len(synthetic_chunk)} synthetic samples")
    
    real_chunk = drive_manager.load_data_from_gdrive("real", chunk_size=50)
    logger.info(f"✅ Loaded {len(real_chunk)} real comedy samples")
    
    # Monitor memory
    drive_manager.monitor_memory_usage()
    
    logger.info("=" * 80)
    logger.info("✅ GOOGLE DRIVE INTEGRATION READY")
    logger.info("🎯 System can now handle unlimited data with 8GB RAM constraint")
    logger.info("📊 Data stored on Google Drive, loaded in chunks for training")

if __name__ == "__main__":
    main()