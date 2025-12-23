import os
import json
import ee
import solara
import geemap.foliumap as geemap
from google.oauth2 import service_account

# ==========================================
# 1. GEE 認證與初始化
# ==========================================
def geene_init():
    try:
        # Hugging Face 的 Secrets 會存在環境變數中
        gee_key = os.environ.get("GEE_SERVICE_ACCOUNT")
        if gee_key:
            info = json.loads(gee_key)
            credentials = service_account.Credentials.from_service_account_info(info)
            ee.Initialize(credentials)
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

initialized = geene_init()

# ==========================================
# 2. 定義地理運算邏輯
# ==========================================
roi = ee.Geometry.Polygon([[[120.61, 23.185], [120.61, 23.135], [120.67, 23.135], [120.67, 23.185], [120.61, 23.185]]])

def get_ndvi_data():
    if not initialized: return None, None
    
    # 影像集合與 NDVI
    def addNDVI(img): return img.addBands(img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI'))
    
    pre = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterDate('2008-01-01', '2008-12-31').filterBounds(roi).map(addNDVI).median().clip(roi)
    post = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterDate('2010-01-01', '2010-12-31').filterBounds(roi).map(addNDVI).median().clip(roi)
    
    diff = post.select('NDVI').subtract(pre.select('NDVI'))
    
    # 統計計算
    stats = diff.lt(-0.3).rename('severe').addBands(diff.lt(-0.1).And(diff.gte(-0.3)).rename('loss')).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e9
    ).getInfo()
    
    return diff, stats

# ==========================================
# 3. Solara 使用者介面組件
# ==========================================
@solara.component
def Page():
    # 獲取數據
    diff_map, stats = solara.use_memo(get_ndvi_data, [])

    with solara.Column(style={"padding": "20px", "background-color": "#f0f2f6"}):
        solara.Title("八八風災小林村：植被變遷偵測分析 (Solara)")
        solara.Markdown("# 🌪️ 小林村 NDVI 差異分析")
        
        if not initialized:
            solara.Error("GEE 未初始化，請檢查 Secrets 設定。")
            return

        with solara.Row():
            # 左側地圖
            with solara.Column(md=8):
                solara.Markdown("### 🗺️ NDVI 差異圖 (2010 - 2008)")
                # 差異圖視覺化
                diff_vis = {'min': -0.6, 'max': 0.6, 'palette': ['#800000', '#ff0000', '#ffffff', '#00ff00', '#008000']}
                
                # 在 Solara 中建立 Map
                m = geemap.Map(center=[23.16, 120.64], zoom=14)
                m.add_basemap('HYBRID')
                if diff_map:
                    m.addLayer(diff_map, diff_vis, 'NDVI Change')
                    m.add_legend(title="Vegetation Change", legend_dict={'Severe Loss': '#800000', 'Loss': '#ff0000', 'Stable': '#ffffff', 'Growth': '#00ff00'})
                
                solara.FigureFolium(m)

            # 右側統計數據
            with solara.Column(md=4):
                solara.Markdown("### 📊 統計摘要")
                if stats:
                    # 假設總像素估算 (簡化邏輯)
                    s_val = stats.get('severe', 0)
                    l_val = stats.get('loss', 0)
                    total_impact = s_val + l_val
                    
                    with solara.Card("災害影響"):
                        solara.Markdown(f"**🔴 嚴重崩塌區域**: `{s_val}` 像素")
                        solara.Markdown(f"**🟠 一般植被流失**: `{l_val}` 像素")
                        solara.Divider()
                        solara.Info(f"地圖中深紅色塊代表 NDVI 下降 > 0.3 的區域，即為本次研究識別出的土石流主要路徑。")
                else:
                    solara.ProgressLinear(True)

# 啟動頁面
Page()