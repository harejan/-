import solara
import geemap
import ee
import os

# ==========================================
# 1. GEE 驗證與初始化 
# ==========================================
MY_PROJECT_ID = 'ee-julia200594714' 

try:
    # 嘗試直接連線
    ee.Initialize(project=MY_PROJECT_ID)
    print("Google Earth Engine initialized (Local).")
except Exception:
    print("Local auth failed. Checking for HF Secrets...")
    token = os.environ.get("EARTHENGINE_TOKEN")
    
    if token:
        # ⭐⭐⭐ 關鍵修改：強制清潔 Token，刪除隱藏符號 ⭐⭐⭐
        token = token.strip()
        
        credential_folder = os.path.expanduser("~/.config/earthengine/")
        os.makedirs(credential_folder, exist_ok=True)
        with open(os.path.join(credential_folder, "credentials"), 'w') as f:
            f.write(token)
        
        # 再次初始化 (加入 project 參數)
        ee.Initialize(project=MY_PROJECT_ID)
        print("Google Earth Engine initialized (Cloud).")
    else:
        raise Exception("GEE 驗證失敗！請確認 EARTHENGINE_TOKEN")

# ==========================================
# 2. 街道圖 vs 災後影像
# ==========================================
@solara.component
def Page():
    solara.Title("地圖對照：現代街道圖 vs 2009 災後現場")

    # 設定：高雄小林村
    map_center = [23.161, 120.645]
    map_zoom = 13

    # 設定災後時間 (八八風災後，天氣放晴時)
    date_after_start  = '2009-08-15'
    date_after_end    = '2009-12-31'

    with solara.Card(title="對比：地圖上的路網 vs 實際被淹沒的區域"):
        
        # 建立地圖
        m = geemap.Map(center=map_center, zoom=map_zoom, height="600px")

        # --- 右邊圖層：2009 災後 Landsat 5 影像 ---
        l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        
        # 為了突顯土石流，我們用一點特殊的配色
        # 真彩色 (3,2,1)
        vis_params = {
            'min': 8000,
            'max': 17000,
            'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 
            'gamma': 1.3
        }

        # 取得災後影像
        point = ee.Geometry.Point([map_center[1], map_center[0]])
        image_after = (l5
            .filterBounds(point)
            .filterDate(date_after_start, date_after_end)
            .sort('CLOUD_COVER')
            .first()
        )
        
        right_layer = geemap.ee_tile_layer(image_after, vis_params, '2009 災後影像')

        # --- 執行捲簾 ---
        # left_layer='ROADMAP' 代表使用 Google 的標準街道圖 (現在年份)
        m.split_map(left_layer='ROADMAP', right_layer=right_layer)

        # 顯示
        solara.display(m)