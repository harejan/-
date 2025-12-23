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
        token = token.strip() # 清潔 Token
        credential_folder = os.path.expanduser("~/.config/earthengine/")
        os.makedirs(credential_folder, exist_ok=True)
        with open(os.path.join(credential_folder, "credentials"), 'w') as f:
            f.write(token)
        
        ee.Initialize(project=MY_PROJECT_ID)
        print("Google Earth Engine initialized (Cloud).")
    else:
        raise Exception("GEE 驗證失敗！")

# ==========================================
# 2. 建立地圖組件
# ==========================================
@solara.component
def Page():
    solara.Title("八八風災前後對比")

    map_center = [23.161, 120.645] 
    map_zoom = 13  

    date_before_start = '2008-01-01'
    date_before_end   = '2009-08-01'
    date_after_start  = '2009-08-15'
    date_after_end    = '2009-12-31'

    with solara.Card(title="2009 八八風災"):
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
            'gamma': 1.2
        }

        def get_best_image(start, end, point):
            return (l5
                .filterBounds(point)
                .filterDate(start, end)
                .sort('CLOUD_COVER')
                .first()
            )

        point = ee.Geometry.Point([map_center[1], map_center[0]])
        image_before = get_best_image(date_before_start, date_before_end, point)
        image_after = get_best_image(date_after_start, date_after_end, point)

        left_layer = geemap.ee_tile_layer(image_before, vis_params, '災前')
        right_layer = geemap.ee_tile_layer(image_after, vis_params, '災後')

        m.split_map(left_layer, right_layer)
        solara.display(m)