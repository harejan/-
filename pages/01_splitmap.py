import solara
import geemap
import ee
import os
import json

# --- GEE 驗證與初始化 (雲端/本地 通用版) ---
try:
    # 1. 嘗試直接初始化 (適用於已驗證的本地環境)
    ee.Initialize()
    print("Google Earth Engine initialized successfully.")
except Exception:
    # 2. 如果失敗，檢查是否有環境變數 (適用於 Hugging Face)
    token = os.environ.get("EARTHENGINE_TOKEN")
    if token:
        print("Found EARTHENGINE_TOKEN, attempting to authenticate...")
        # 將 token 字串存成暫存檔案，這是最簡單讓 ee 讀取的方式
        credential_path = os.path.expanduser("~/.config/earthengine/credentials")
        os.makedirs(os.path.dirname(credential_path), exist_ok=True)
        with open(credential_path, 'w') as f:
            f.write(token)
        
        # 再次初始化
        ee.Initialize()
        print("Google Earth Engine initialized with Token.")
    else:
        # 3. 如果都沒有，就報錯
        print("Error: GEE authentication failed. Please set EARTHENGINE_TOKEN.")
        raise