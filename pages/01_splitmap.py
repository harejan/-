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
        # 如果是服務帳戶金鑰 (JSON) 方式
        gee_key = os.environ.get("GEE_SERVICE_ACCOUNT")
        if gee_key:
            import json
            from google.oauth2 import service_account
            info = json.loads(gee_key)
            credentials = service_account.Credentials.from_service_account_info(info)
            ee.Initialize(credentials, project=MY_PROJECT_ID)
            print("Google Earth Engine initialized (Service Account).")
        else:
            raise Exception("GEE 驗證失敗！")

# ==========================================
# 2. 災前影像 vs 街道圖 (Solara Component)
# ==========================================
@solara.component
def Page():
    solara.Title("地圖對照：災前影像 vs 街道圖")

    map_center = [23.161, 120.645]
    map_zoom = 14
    
    # 調整日期範圍：使用 2008 全年到 2009 風災前，以獲取最清晰的影像
    date_pre_start = '2008-01-01'
    date_pre_end   = '2009-08-01'

    with solara.Card(title="對比：災害前影像(左) vs 路網街道圖(右)"):
        
        m = geemap.Map(
            center=map_center, 
            zoom=map_zoom, 
            height="600px",
            toolbar_ctrl=False, 
            draw_ctrl=False
        )

        # 讀取 Landsat 5
        l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        
        # 視覺化參數設定 (True Color: B3, B2, B1)
        vis_params = {
            'min': 7000,
            'max': 16000,
            'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 
            'gamma': 1.4
        }

        # --- 優化去雲：使用 Median 中位數合成 ---
        # 透過中位數合成，可以篩選掉不同時間點的雲朵，留下乾淨的地表
        image_pre = (l5
            .filterBounds(ee.Geometry.Point([map_center[1], map_center[0]]))
            .filterDate(date_pre_start, date_pre_end)
            .filter(ee.Filter.lt('CLOUD_COVER', 20)) # 先過濾掉雲量太高的原始片
            .median() # 取中位數合成
            .clip(ee.Geometry.Point([map_center[1], map_center[0]]).buffer(5000).bounds())
        )
        
        # 建立左側影像圖層
        left_layer = geemap.ee_tile_layer(image_pre, vis_params, '災前清晰影像')

        # 執行 Split Map: 左邊放影像圖層，右邊放街道圖
        m.split_map(left_layer=left_layer, right_layer='ROADMAP')
        
        solara.display(m)

    solara.Markdown("""
    ### 💡 分析說明
    * **左側 (災前影像)**：使用了 Landsat 5 在 2008 年至 2009 年期間的 **中位數合成 (Median Composite)** 技術。這能有效過濾掉山區常見的雲霧，呈現最真實的地形原貌。
    * **右側 (街道圖)**：目前的 OpenStreetMap 路網，可對照小林村原本的聚落位置與聯外道路（如台29線）。
    """)

# 啟動
Page()