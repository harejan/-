import solara
import geemap
import ee
import os

# ==========================================
# 1. GEE 驗證與初始化
# ==========================================
try:
    ee.Initialize()
    print("Google Earth Engine initialized (Local).")
except Exception:
    print("Local auth failed. Checking for HF Secrets...")
    token = os.environ.get("EARTHENGINE_TOKEN")
    if token:
        credential_folder = os.path.expanduser("~/.config/earthengine/")
        os.makedirs(credential_folder, exist_ok=True)
        with open(os.path.join(credential_folder, "credentials"), 'w') as f:
            f.write(token)
        ee.Initialize()
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
    # 這是八八風災受創最嚴重的區域之一
    map_center = [23.161, 120.645] 
    map_zoom = 13  # Landsat 解析度較低，Zoom 13 大概是極限

    # --- 設定時間範圍 ---
    # 災前：2009年初 (找雲最少的一張)
    date_before_start = '2008-01-01'
    date_before_end   = '2009-08-01'

    # 災後：2009年底 (風災過後，天氣放晴時)
    date_after_start  = '2009-08-15'
    date_after_end    = '2009-12-31'
    # ----------------------------------------------------

    with solara.Card(title="2009 八八風災 - 小林村崩塌與土石流"):
        
        m = geemap.Map(center=map_center, zoom=map_zoom, height="600px")

        # 1. 定義 Landsat 5 資料集 (當年唯一的歷史資料)
        l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")

        # 2. 定義視覺化參數 (真彩色 RGB: Band 3, 2, 1)
        # Landsat Collection 2 的數值範圍大約在 7000~15000 之間代表可見光
        vis_params = {
            'min': 8000,
            'max': 17000,
            'bands': ['SR_B3', 'SR_B2', 'SR_B1'], # 紅、綠、藍
            'gamma': 1.2 #稍微調亮一點
        }

        # 3. 獲取影像的函式
        def get_best_image(start, end, point):
            return (l5
                .filterBounds(point)
                .filterDate(start, end)
                .sort('CLOUD_COVER') # 雲量越少越好
                .first()
            )

        # 建立篩選點
        point = ee.Geometry.Point([map_center[1], map_center[0]])

        # 取得影像
        image_before = get_best_image(date_before_start, date_before_end, point)
        image_after = get_best_image(date_after_start, date_after_end, point)

        # 建立圖層
        # 災前：綠意盎然的山谷
        left_layer = geemap.ee_tile_layer(image_before, vis_params, '災前 (2009上半年)')
        # 災後：可以看到大面積的灰色土石流痕跡
        right_layer = geemap.ee_tile_layer(image_after, vis_params, '災後 (2009下半年)')

        # 執行捲簾
        m.split_map(left_layer, right_layer)


Page()