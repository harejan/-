import os
import json
import ee
import solara
import geemap.foliumap as geemap
from google.oauth2 import service_account

# ==========================================
# 1. Google Earth Engine 初始化設定
# ==========================================
# 請確保你的 Hugging Face Secret 名稱為 GEE_SERVICE_ACCOUNT
PROJECT_ID = 'ee-julia200594714'  

def initialize_gee():
    try:
        gee_key = os.environ.get("GEE_SERVICE_ACCOUNT")
        if not gee_key:
            return False, "找不到環境變數 GEE_SERVICE_ACCOUNT"
        
        info = json.loads(gee_key)
        credentials = service_account.Credentials.from_service_account_info(info)
        ee.Initialize(credentials, project=PROJECT_ID)
        return True, "GEE 初始化成功"
    except Exception as e:
        return False, str(e)

# ==========================================
# 2. 地理空間運算邏輯 (八八風災小林村案例)
# ==========================================
# 定義小林村 ROI
roi = ee.Geometry.Polygon([[[120.61, 23.185], [120.61, 23.135], [120.67, 23.135], [120.67, 23.185], [120.61, 23.185]]])

def get_landslide_analysis():
    # 計算 NDVI 的函數
    def addNDVI(img):
        return img.addBands(img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI'))

    # 1. 取得災前 (2008) 與 災後 (2010) Landsat 5 影像
    pre_img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
        .filterDate('2008-01-01', '2008-12-31') \
        .filterBounds(roi) \
        .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
        .map(addNDVI).median().clip(roi)

    post_img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
        .filterDate('2010-01-01', '2010-12-31') \
        .filterBounds(roi) \
        .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
        .map(addNDVI).median().clip(roi)

    # 2. 計算差異圖 (Post - Pre)
    diff = post_img.select('NDVI').subtract(pre_img.select('NDVI'))

    # 3. 統計分類面積 (像素數)
    def classify(img):
        severe = img.lt(-0.3).rename('severe')        # 嚴重崩塌
        loss = img.lt(-0.1).And(img.gte(-0.3)).rename('loss') # 一般流失
        stable = img.gte(-0.1).And(img.lte(0.1)).rename('stable') # 穩定
        return img.addBands([severe, loss, stable])

    classified = classify(diff)
    stats = classified.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    return diff, stats

# ==========================================
# 3. Solara 介面組件
# ==========================================
@solara.component
def Page():
    # 初始化 GEE 並暫存狀態
    is_ok, msg = solara.use_memo(initialize_gee, [])
    
    # 執行地理運算 (只有在初始化成功後才執行)
    diff_map, stats_data = solara.use_memo(lambda: get_landslide_analysis() if is_ok else (None, None), [is_ok])

    with solara.Column(style={"padding": "30px", "font-family": "sans-serif"}):
        solara.Markdown("# 🌪️ 八八風災小林村：植被變遷視覺化分析")
        solara.Markdown("### 地理資訊系統 (GIS) 專案報告")
        solara.Divider()

        if not is_ok:
            solara.Error(f"⚠️ 系統錯誤：{msg}")
            solara.Info("請檢查 Hugging Face Space 的 Secrets 設定是否包含完整的 GEE JSON 金鑰。")
            return

        with solara.Row():
            # 左側：地圖展示
            with solara.Column(md=8):
                solara.Markdown("#### 🗺️ NDVI 差異偵測圖 (Difference Map)")
                
                # 地圖視覺化設定
                m = geemap.Map(center=[23.16, 120.64], zoom=14)
                m.add_basemap('HYBRID')
                
                if diff_map:
                    vis_params = {
                        'min': -0.6, 'max': 0.6,
                        'palette': ['#800000', '#ff0000', '#ffffff', '#00ff00', '#008000']
                    }
                    m.addLayer(diff_map, vis_params, 'NDVI Change')
                    m.add_legend(title="變遷類別", legend_dict={
                        '嚴重崩塌 (Severe)': '#800000',
                        '植被流失 (Loss)': '#ff0000',
                        '無明顯變化 (Stable)': '#ffffff',
                        '植被復育 (Growth)': '#00ff00'
                    })
                
                solara.FigureFolium(m)

            # 右側：統計數據
            with solara.Column(md=4):
                solara.Markdown("#### 📊 區域變遷統計")
                
                if stats_data:
                    s = stats_data.get('severe', 0)
                    l = stats_data.get('loss', 0)
                    stb = stats_data.get('stable', 0)
                    total = s + l + stb
                    
                    if total > 0:
                        solara.Markdown(f"**分析範圍總像素：** `{int(total)}` (Landsat 5, 30m)")
                        
                        # 顯示比例與卡片
                        with solara.Card("災害影響評估"):
                            solara.Markdown(f"🔴 **嚴重崩塌比例：** `{s/total:.1%}`")
                            solara.Markdown(f"🟠 **一般植被流失：** `{l/total:.1%}`")
                            solara.Markdown(f"⚪ **地表穩定比例：** `{stb/total:.1%}`")
                            solara.Divider()
                            solara.Error(f"總受災比例：{(s+l)/total:.1%}")
                        
                        solara.Markdown("""
                        **數據解讀：**
                        深紅色區域表示 NDVI 值下降超過 0.3，與 2009 年獻肚山大規模崩塌及土石流堆積區高度吻合。
                        """)
                    else:
                        solara.Warning("統計數據讀取中...")
                else:
                    solara.ProgressLinear(True)

        solara.Divider()
        solara.Markdown("資料來源：NASA/USGS Landsat 5 衛星影像 | 處理平台：Google Earth Engine")

# 啟動頁面
Page()