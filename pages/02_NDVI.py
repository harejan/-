import os
import ee
import solara
import leafmap.foliumap as leafmap

# --- 1. GEE 初始化邏輯 (解決環境變數報錯) ---
def init_gee():
    try:
        if not ee.data._initialized:
            # 優先讀取雲端 Secrets
            sa = os.environ.get("GEE_SERVICE_ACCOUNT")
            key = os.environ.get("GEE_JSON_KEY")
            
            if sa and key:
                # 雲端部署認證
                credentials = ee.ServiceAccountCredentials(sa, key_data=key)
                ee.Initialize(credentials)
            else:
                # 本地開發認證
                ee.Initialize()
        return True, "✅ GEE 初始化成功"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# --- 2. 衛星影像處理邏輯 (計算 NDVI 與變遷) ---
def run_ndvi_analysis():
    # 設定高雄山區中心點 (八八風災受災區)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(10000).bounds()

    # 選取 Landsat 5 影像 (2009年適用)
    def get_ndvi(start, end):
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
                .median()
        # Landsat 5: B4 為 NIR, B3 為 RED
        return img.normalizedDifference(['SR_B4', 'SR_B3'])

    # 風災前 (2009) 與 風災後 (2010)
    pre_ndvi = get_ndvi('2009-01-01', '2009-07-30')
    post_ndvi = get_ndvi('2010-01-01', '2010-07-30')

    # 計算差異：負值越大代表植被消失越嚴重
    diff = post_ndvi.subtract(pre_ndvi)
    
    return pre_ndvi, post_ndvi, diff

# --- 3. Solara 介面組件 ---
@solara.component
def Page():
    # 使用 use_memo 確保初始化只跑一次
    is_ok, status_msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷偵測")

        if is_ok:
            # 建立地圖
            m = leafmap.Map(center=[23.16, 120.63], zoom=12)
            
            # 執行運算
            pre, post, diff = run_ndvi_analysis()

            # 設定 NDVI 顏色
            ndvi_vis = {'min': 0, 'max': 0.8, 'palette': ['white', '#99cc99', '#006600']}
            
            # 設定變遷視覺化 (這是你要求的核心圖層)
            # 紅色代表植被大幅減少 (崩塌地)
            diff_params = {
                'min': -0.5, 
                'max': 0, 
                'palette': ['#ff0000', '#ffa500', '#ffffff']
            }
           
            m.add_layer(diff, diff_params, "植被減少區域 (變遷)")
            
            # 在 Solara 中顯示地圖
            solara.display(m)
            
        else:
            solara.Error("請檢查您的 GEE 認證設定。")
