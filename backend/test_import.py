#!/usr/bin/env python3
"""Quick import test for FastAPI application"""

import sys
from pathlib import Path

print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")
print(f"Working dir: {Path.cwd()}")
print()

try:
    print("Testing imports...")
    from app.main import app
    print("✅ FastAPI OK")
    print(f"✅ App title: {app.title}")
    
    from app.converter import get_converter
    converter = get_converter()
    print(f"✅ Converter OK (CUDA: {converter.cuda_available})")
    
    print("\n🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"\nMake sure you're in your activated venv:")
    print(f"  cd backend")
    print(f"  source venv/bin/activate  # or 'source .venv/bin/activate'")
    print(f"  pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
