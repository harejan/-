import solara
import geemap
import ee
import os

# 🔹 請在這裡填入您的專案 ID
MY_PROJECT_ID = '您的專案ID'  # <--- 請貼在這裡

try:
    ee.Initialize(project='ee-julia200594714')
except Exception:
    token = os.environ.get("EARTHENGINE_TOKEN")
    if token:
        credential_folder = os.path.expanduser("~/.config/earthengine/")
        os.makedirs(credential_folder, exist_ok=True)
        with open(os.path.join(credential_folder, "credentials"), 'w') as f:
            f.write(token)
        
        # 這裡也要加 project
        ee.Initialize(project=MY_PROJECT_ID)
    else:
        raise Exception("GEE 驗證失敗！")

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
        # 或者可以用 'HYBRID' (衛星+路網)
        m.split_map(left_layer='ROADMAP', right_layer=right_layer)

        # 顯示
        solara.display(m)
        
        solara.Info("左側為現代街道圖 (Current Map)，右側為 2009 年災後影像。您可以觀察原本規劃的道路在災後影像中是否已被土石掩埋。")
