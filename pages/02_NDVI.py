import os
import json
import ee
import solara
import geemap.foliumap as geemap
from google.oauth2 import service_account

# ==========================================
# 1. GEE 認證與初始化 (Hugging Face 專屬版本)
# ==========================================
MY_PROJECT_ID = 'ee-julia200594714' 

def initialize_gee():
    try:
        # 從環境變數讀取 JSON 金鑰
        gee_key = os.environ.get("GEE_SERVICE_ACCOUNT")
        
        if gee_key:
            info = json.loads(gee_key)
            credentials = service_account.Credentials.from_service_account_info(info)
            ee.Initialize(credentials, project=MY_PROJECT_ID)
            return True, "✅ 服務帳戶認證成功"
        else:
            # 本地測試時使用
            ee.Initialize(project=MY_PROJECT_ID)
            return True, "✅ 本地初始化成功"
    except Exception as e:
        return False, str(e)

# ==========================================
# 2. 地理運算邏輯 (小林村區域)
# ==========================================
def get_satellite_layer(map_center):
    # 擴大範圍，使用 2008-2009 年的中位數合成以達到無雲效果
    date_pre_start = '2008-01-01'
    date_pre_end   = '2009-08-01'
    
    # 讀取 Landsat 5
    l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
    
    # True Color 視覺參數
    vis_params = {
        'min': 7000,
        'max': 16000,
        'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 
        'gamma': 1.4
    }

    # 中位數合成，過濾雲量大於 20% 的片子
    image_pre = (l5
        .filterBounds(ee.Geometry.Point([map_center[1], map_center[0]]))
        .filterDate(date_pre_start, date_pre_end)
        .filter(ee.Filter.lt('CLOUD_COVER', 20))
        .median()
    )
    
    return geemap.ee_tile_layer(image_pre, vis_params, '災前清晰影像')

# ==========================================
# 3. Solara UI 組件 (修正 Divider 錯誤)
# ==========================================
@solara.component
def Page():
    # 呼叫初始化
    is_ok, msg = solara.use_memo(initialize_gee, [])
    
    # 設定地圖中心與層級
    map_center = [23.161, 120.645] # 小林村獻肚山周邊
    map_zoom = 14

    solara.Title("八八風災：災前影像 vs 街道圖對照")

    with solara.Column(style={"padding": "20px"}):
        solara.Markdown("# 🌪️ 八八風災小林村：空間環境回顧")
        
        # 使用 Markdown 代替會報錯的 solara.Divider()
        solara.Markdown("---")

        if not is_ok:
            solara.Error(f"⚠️ GEE 初始化失敗：{msg}")
            solara.Markdown("請檢查 Hugging Face Secrets 是否已正確設定 `GEE_SERVICE_ACCOUNT`。")
            return

        with solara.Card(title="影像對照：災前衛星(左) vs 目前街道(右)"):
            with solara.Column():
                # 建立地圖物件
                m = geemap.Map(
                    center=map_center, 
                    zoom=map_zoom, 
                    height="600px"
                )

                # 取得無雲影像圖層
                satellite_layer = get_satellite_layer(map_center)

                # 執行 Split Map：左邊影像，右邊街道圖
                m.split_map(left_layer=satellite_layer, right_layer='ROADMAP')
                
                # 顯示地圖
                solara.FigureFolium(m)

        solara.Markdown("---")
        solara.Markdown("""
        ### 🔍 技術說明
        1. **左側圖層 (災前衛星)**：採用 **Landsat 5 TM** 影像，透過 2008-2009 年之 **Median Composite (中位數合成)** 技術排除雲霧。
        2. **右側圖層 (街道圖)**：使用目前 OpenStreetMap 道路圖，可用於對照災前河谷聚落與今日交通線的相對位置。
        """)
        
        # 使用 Vuetify 的分隔線 (另一種方案)
        solara.v.Divider()
        solara.Caption("地理系專案報告 | 資料來源：NASA/USGS & Google Earth Engine")

# 啟動頁面
Page()
