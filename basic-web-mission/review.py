import os
import json

print("Checking web mission...")
if os.path.exists("submissions/index.html"):
    print("✅ index.html found")
else:
    print("❌ index.html missing")

if os.path.exists("submissions/style.css"):
    print("✅ style.css found")
else:
    print("❌ style.css missing")
