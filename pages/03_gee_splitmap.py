import solara
import geemap
import ee
import os

# ==========================================
# 1. GEE 驗證與初始化 (已修正專案 ID)
# ==========================================

# 🔹 這是您剛剛查到的專案 ID
MY_PROJECT_ID = 'ee-julia200594714'

try:
    # 嘗試直接連線 (加入 project 參數)
    ee.Initialize(project=MY_PROJECT_ID)
    print("Google Earth Engine initialized (Local).")
except Exception:
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
        
        # 再次初始化 (這裡也要加 project 參數)
        ee.Initialize(project=MY_PROJECT_ID)
        print("Google Earth Engine initialized (Cloud).")
    else:
        raise Exception("GEE 驗證失敗！請確認已在 Hugging Face Settings 加入 EARTHENGINE_TOKEN")

# ==========================================
# 2. 建立地圖組件 (八八風災 - 小林村)
# ==========================================
@solara.component
def Page():
    solara.Title("八八風災前後對比 (Landsat 5 歷史影像)")

    # --- 🛠️ 設定區域：高雄 小林村 (Xiaolin Village) ---
    map_center = [23.161, 120.645] 
    map_zoom = 13  

    # --- 設定時間範圍 ---
    date_before_start = '2008-01-01'
    date_before_end   = '2009-08-01'

    date_after_start  = '2009-08-15'
    date_after_end    = '2009-12-31'
    # ----------------------------------------------------

    with solara.Card(title="2009 八八風災 - 小林村崩塌與土石流"):
        
        m = geemap.Map(center=map_center, zoom=map_zoom, height="600px")

        # 1. 定義 Landsat 5 資料集
        l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")

        # 2. 定義視覺化參數
        vis_params = {
            'min': 8000,
            'max': 17000,
            'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 
            'gamma': 1.2
        }

        # 3. 獲取影像的函式
        def get_best_image(start, end, point):
            return (l5
                .filterBounds(point)
                .filterDate(start, end)
                .sort('CLOUD_COVER')
                .first()
            )

        # 建立篩選點
        point = ee.Geometry.Point([map_center[1], map_center[0]])

        # 取得影像
        image_before = get_best_image(date_before_start, date_before_end, point)
        image_after = get_best_image(date_after_start, date_after_end, point)

        # 建立圖層
        left_layer = geemap.ee_tile_layer(image_before, vis_params, '災前 (2009上半年)')
        right_layer = geemap.ee_tile_layer(image_after, vis_params, '災後 (2009下半年)')

        # 執行捲簾
        m.split_map(left_layer, right_layer)

        solara.display(m)

# 執行頁面
Page()