import solara
import geemap
import ee
import os

# ==========================================
# 1. GEE 驗證與初始化
# ==========================================
MY_PROJECT_ID = 'ee-julia200594714' 

try:
    ee.Initialize(project=MY_PROJECT_ID)
    print("Google Earth Engine initialized (Local).")
except Exception:
    print("Local auth failed. Checking for HF Secrets...")
    token = os.environ.get("EARTHENGINE_TOKEN")
    
    if token:
        token = token.strip()
        credential_folder = os.path.expanduser("~/.config/earthengine/")
        os.makedirs(credential_folder, exist_ok=True)
        with open(os.path.join(credential_folder, "credentials"), 'w') as f:
            f.write(token)
        ee.Initialize(project=MY_PROJECT_ID)
        print("Google Earth Engine initialized (Cloud).")
    else:
        raise Exception("GEE 驗證失敗！")

# ==========================================
# 2. 街道圖 vs 災後影像
# ==========================================
@solara.component
def Page():
    solara.Title("地圖對照：現代街道圖 vs 2009 災後現場")

    map_center = [23.161, 120.645]
    map_zoom = 13
    date_after_start  = '2009-08-15'
    date_after_end    = '2009-12-31'

    with solara.Card(title="對比：地圖上的路網 vs 實際被淹沒的區域"):
        
        # ⭐⭐⭐ 修改這裡：關閉工具列與繪圖工具 ⭐⭐⭐
        m = geemap.Map(
            center=map_center, 
            zoom=map_zoom, 
            height="600px",
            toolbar_ctrl=False, 
            draw_ctrl=False
        )

        l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        vis_params = {
            'min': 8000,
            'max': 17000,
            'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 
            'gamma': 1.3
        }

        point = ee.Geometry.Point([map_center[1], map_center[0]])
        image_after = (l5
            .filterBounds(point)
            .filterDate(date_after_start, date_after_end)
            .sort('CLOUD_COVER')
            .first()
        )
        
        right_layer = geemap.ee_tile_layer(image_after, vis_params, '2009 災後影像')

        m.split_map(left_layer='ROADMAP', right_layer=right_layer)
        solara.display(m)