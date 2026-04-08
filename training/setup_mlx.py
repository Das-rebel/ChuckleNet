#!/usr/bin/env python3
"""
MLX Environment Setup Script
Configures Apple MLX framework for optimal performance on M2 with 8GB RAM
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_system_requirements():
    """Verify system meets minimum requirements"""
    print("🔍 Checking system requirements...")
    
    # Check if running on Apple Silicon
    machine = platform.machine()
    if machine not in ['arm64', 'arm64e']:
        print(f"❌ Not running on Apple Silicon (detected: {machine})")
        return False
    
    # Check macOS version
    mac_version = platform.mac_ver()[0]
    major_version = int(mac_version.split('.')[0]) if mac_version else 0
    if major_version < 14:
        print(f"❌ macOS 14.0+ required (detected: {mac_version})")
        return False
    
    print(f"✅ Apple Silicon detected: {machine}")
    print(f"✅ macOS version: {mac_version}")
    return True

def check_memory():
    """Check available memory"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        print(f"💾 Total RAM: {total_gb:.1f} GB")
        
        if total_gb < 8:
            print("⚠️  Warning: Less than 8GB RAM detected")
            print("   Performance may be significantly degraded")
        elif total_gb >= 8:
            print("✅ Sufficient memory for target hardware")
        
        return total_gb
    except ImportError:
        print("⚠️  psutil not installed, skipping memory check")
        return 8.0

def install_mlx():
    """Install Apple MLX framework"""
    print("\n📦 Installing Apple MLX framework...")
    
    try:
        # Check if MLX is already installed
        import mlx
        print(f"✅ MLX already installed: {mlx.__version__}")
        return True
    except ImportError:
        pass
    
    # Install MLX
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "mlx", "mlx-lm", "--upgrade", "--quiet"
        ], check=True)
        print("✅ MLX installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install MLX: {e}")
        return False

def create_mlx_config():
    """Create MLX configuration for memory optimization"""
    print("\n⚙️  Creating MLX configuration...")
    
    config_dir = Path.home() / ".config" / "mlx"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / "config.yaml"
    
    config_content = """
# MLX Configuration for Autonomous Laughter Prediction
# Optimized for Apple M2 8GB RAM

# Memory Settings
memory:
  limit: 5GB
  enable_memory_mapping: true
  cache_size: 2GB
  
# Quantization Settings
quantization:
  enabled: true
  bits: 4
  calibration_size: 512
  
# Neural Engine Settings
neural_engine:
  enabled: true
  fallback_to_cpu: true
  
# Logging
logging:
  level: INFO
  file: ~/mlx.log
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content.strip())
    
    print(f"✅ MLX config created: {config_file}")

def setup_environment_variables():
    """Set up environment variables for MLX optimization"""
    print("\n🔧 Setting up environment variables...")
    
    env_vars = {
        'MLX_MEMORY_LIMIT': '5GB',
        'MLX_ENABLE_NE': '1',
        'MLX_QUANTIZATION_BITS': '4',
        'MLX_CACHE_SIZE': '2GB',
        'PYTORCH_ENABLE_MPS_FALLBACK': '1',
    }
    
    for key, value in env_vars.items():
        # Set for current session
        os.environ[key] = value
        print(f"   {key}={value}")
    
    print("✅ Environment variables configured")

def verify_installation():
    """Verify MLX installation"""
    print("\n🧪 Verifying MLX installation...")
    
    try:
        import mlx
        import mlx.nn as nn
        import mlx.core as mx
        
        print(f"✅ MLX version: {mlx.__version__}")
        
        # Test basic functionality
        x = mx.array([1.0, 2.0, 3.0])
        y = mx.array([4.0, 5.0, 6.0])
        z = x + y
        
        print(f"✅ Basic operations working: {z.tolist()}")
        
        # Test memory allocation
        large_array = mx.zeros((1000, 1000))
        print(f"✅ Memory allocation test passed")
        
        return True
    except Exception as e:
        print(f"❌ MLX verification failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Apple MLX Environment Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met. Exiting.")
        return False
    
    # Check memory
    total_memory = check_memory()
    
    # Install MLX
    if not install_mlx():
        print("\n❌ MLX installation failed. Exiting.")
        return False
    
    # Create configuration
    create_mlx_config()
    
    # Setup environment
    setup_environment_variables()
    
    # Verify installation
    if not verify_installation():
        print("\n❌ MLX verification failed. Exiting.")
        return False
    
    print("\n" + "=" * 50)
    print("✅ MLX environment setup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Configure .env file: cp .env.example .env")
    print("   3. Run initialization: python scripts/init_data_pipeline.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)