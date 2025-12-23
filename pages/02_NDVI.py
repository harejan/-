import os
import ee
import solara
import leafmap.ee_planner as leafmap
import json

# ==========================================
# 1. GEE 認證與初始化 (解決您之前的報錯)
# ==========================================
def initialize_gee():
    try:
        # 優先尋找環境變數中的 Service Account
        service_account = os.environ.get("GEE_SERVICE_ACCOUNT")
        json_key = os.environ.get("GEE_JSON_KEY")

        if service_account and json_key:
            # 雲端部署模式
            credentials = ee.ServiceAccountCredentials(service_account, key_data=json_key)
            ee.Initialize(credentials)
            return True, "✅ 雲端服務帳戶認證成功"
        else:
            # 本地開發模式 (需先執行 earthengine authenticate)
            ee.Initialize()
            return True, "✅ 本地帳戶認證成功"
    except Exception as e:
        return False, f"❌ 初始化失敗: {e}"

# ==========================================
# 2. NDVI 與變遷偵測邏輯
# ==========================================
def run_ndvi_analysis():
    # 設定高雄山區感興趣區域 (ROI)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(10000).bounds()

    # 選用 Landsat 5 影像 (2009年最穩定的資料源)
    def get_ndvi(start_date, end_date):
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
                .median()
        # Landsat 5: B4 為 NIR, B3 為 Red
        return img.normalizedDifference(['SR_B4', 'SR_B3'])

    # 風災前 (2009 上半年) 與 風災後 (2010 上半年，待植被復甦期觀察受損)
    pre_ndvi = get_ndvi('2009-01-01', '2009-07-30')
    post_ndvi = get_ndvi('2010-01-01', '2010-07-30')

    # 計算差異 (變遷)：後 - 前
    # 負值越大的地方，代表植被消失越嚴重（崩塌地）
    diff = post_ndvi.subtract(pre_ndvi)

    return pre_ndvi, post_ndvi, diff, roi

# ==========================================
# 3. Solara 介面組件
# ==========================================
@solara.component
def Page():
    # 使用 use_memo 確保初始化只執行一次
    is_ok, status_msg = solara.use_memo(initialize_gee, [])
    
    with solara.Column(style={"padding": "30px", "background-color": "#f0f2f6"}):
        solara.Title("🛰️ 八八風災植被變遷偵測")
        solara.Markdown(f"**系統狀態：** {status_msg}")

        if is_ok:
            with solara.Card("高雄山區 NDVI 變遷地圖"):
                # 初始化地圖
                m = leafmap.Map(center=[23.16, 120.63], zoom=12)
                
                # 執行運算
                pre, post, diff, roi = run_ndvi_analysis()

                # 設定視覺化參數
                ndvi_vis = {'min': 0, 'max': 0.8, 'palette': ['#ece7f2', '#a6bddb', '#2b8cbe', '#00441b']}
                
                # 您要求的核心變遷圖層參數
                diff_params = {
                    'min': -0.5, 
                    'max': 0, 
                    'palette': ['#ff0000', '#ffa500', '#ffffff'] # 紅色表示嚴重減少，白色表示無變化
                }

                # 加入圖層
                m.add_layer(pre, ndvi_vis, "2009 風災前植被 (NDVI)")
                m.add_layer(post, ndvi_vis, "2010 風災後植被 (NDVI)")
                
                # --- 這行是您指定的完整內容核心 ---
                m.add_layer(diff, diff_params, "植被減少區域 (變遷)")

                # 顯示地圖
                solara.FigureLeaflet(m)
        else:
            solara.Error("無法載入地圖，請檢查 GEE 權限設定。")




