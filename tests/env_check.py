import sys
print(f"Python executable: {sys.executable}")

try:
    import duckduckgo_search
    print("✅ duckduckgo_search imported")
except ImportError as e:
    print(f"❌ duckduckgo_search import failed: {e}")

try:
    import zhipuai
    print("✅ zhipuai imported")
except ImportError as e:
    print(f"❌ zhipuai import failed: {e}")

try:
    import requests
    print("✅ requests imported")
except ImportError as e:
    print(f"❌ requests import failed: {e}")

try:
    import sqlite3
    print("✅ sqlite3 imported")
except ImportError as e:
    print(f"❌ sqlite3 import failed: {e}")
