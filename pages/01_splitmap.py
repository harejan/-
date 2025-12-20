import solara
import geemap
import ee
import os

# ==========================================
# 1. GEE 驗證與初始化 (已修正：解決 gcloud 錯誤)
# ==========================================
try:
    # 嘗試直接連線 (本機環境)
    ee.Initialize()
    print("Google Earth Engine initialized (Local).")
except Exception:
    # 如果失敗，改用 Hugging Face Secret 連線
    print("Local auth failed. Checking for HF Secrets...")
    token = os.environ.get("EARTHENGINE_TOKEN")
    
    if token:
        # 建立驗證檔路徑
        credential_folder = os.path.expanduser("~/.config/earthengine/")
        os.makedirs(credential_folder, exist_ok=True)
        credential_path = os.path.join(credential_folder, "credentials")
        
        # 寫入 Token
        with open(credential_path, 'w') as f:
            f.write(token)
        
        # 再次初始化
        ee.Initialize()
        print("Google Earth Engine initialized (Cloud).")
    else:
        raise Exception("GEE 驗證失敗！請確認已在 Hugging Face Settings 加入