import os
import ee
import solara
import leafmap.ee_planner as leafmap

# --- 1. 強健的初始化邏輯 ---
def robust_ee_init():
    try:
        service_account = os.environ.get("GEE_SERVICE_ACCOUNT")
        if service_account:
            # 如果有環境變數，使用服務帳戶
            ee.Initialize(ee.ServiceAccountCredentials(service_account, os.environ.get("GEE_JSON_KEY")))
            return "✅ 使用 Service Account"
        else:
            # 沒有的話，嘗試本地初始化
            ee.Initialize()
            return "✅ 使用本地帳戶"
    except Exception as e:
        return f"❌ 初始化失敗: {str(e)}"

# --- 2. 變遷偵測運算 ---
def calculate_morakot_change():
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(10000).bounds()
    
    # Landsat 5 影像
    pre_img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterBounds(roi).filterDate('2009-01-01', '2009-07-30').median()
    post_img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterBounds(roi).filterDate('2010-01-01', '2010-07-30').median()
    
    pre_ndvi = pre_img.normalizedDifference(['SR_B4', 'SR_B3'])
    post_ndvi = post_img.normalizedDifference(['SR_B4', 'SR_B3'])
    
    # 核心：計算變遷
    diff = post_ndvi.subtract(pre_ndvi)
    return pre_ndvi, post_ndvi, diff

@solara.component
def Page():
    status = solara.use_memo(robust_ee_init, [])

    with solara.Column():
        solara.Title("八八風災 NDVI 變遷")
        solara.Markdown(f"**認證狀態：** {status}")

        if "✅" in status:
            m = leafmap.Map(center=[23.16, 120.63], zoom=12)
            pre, post, diff = calculate_morakot_change()

            # 設定變遷視覺化：-0.5 到 0 代表植被流失
            diff_params = {'min': -0.5, 'max': 0, 'palette': ['#ff0000', '#ffa500', '#ffffff']}
            
            m.add_layer(pre, {'min': 0, 'max': 0.8, 'palette': ['white', 'green']}, "風災前")
            m.add_layer(diff, diff_params, "植被減少區域 (變遷)")
            
            solara.FigureLeaflet(m)





