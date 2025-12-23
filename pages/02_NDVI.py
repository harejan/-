import os
import json
import ee
import solara
import geemap.foliumap as geemap
from google.oauth2 import service_account

# ==========================================
# 1. GEE 認證與初始化 (與主頁一致)
# ==========================================
MY_PROJECT_ID = 'ee-julia200594714' 

def initialize_gee():
    try:
        gee_key = os.environ.get("GEE_SERVICE_ACCOUNT")
        if gee_key:
            info = json.loads(gee_key)
            credentials = service_account.Credentials.from_service_account_info(info)
            ee.Initialize(credentials, project=MY_PROJECT_ID)
            return True, "✅ 初始化成功"
        else:
            return False, "❌ 找不到 GEE_SERVICE_ACCOUNT"
    except Exception as e:
        return False, str(e)

# ==========================================
# 2. 地理運算邏輯 (NDVI 差異分析)
# ==========================================
def get_ndvi_analysis():
    # 小林村區域
    roi = ee.Geometry.Polygon([[[120.61, 23.185], [120.61, 23.135], [120.67, 23.135], [120.67, 23.185], [120.61, 23.185]]])
    
    def addNDVI(img):
        return img.addBands(img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI'))

    # 取得 2008(災前) 與 2010(災後) 的 Landsat 5 中位數影像
    pre = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterDate('2008-01-01', '2008-12-31').filterBounds(roi).map(addNDVI).median().clip(roi)
    post = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").filterDate('2010-01-01', '2010-12-31').filterBounds(roi).map(addNDVI).median().clip(roi)

    # 計算差異: 災後 - 災前
    diff = post.select('NDVI').subtract(pre.select('NDVI'))

    # 分類統計區域
    def classify(img):
        severe = img.lt(-0.3).rename('severe')        # 嚴重崩塌
        loss = img.lt(-0.1).And(img.gte(-0.3)).rename('loss') # 一般流失
        stable = img.gte(-0.1).rename('stable')       # 穩定
        return img.addBands([severe, loss, stable])

    classified = classify(diff)
    stats = classified.reduceRegion(reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e9).getInfo()
    
    return diff, stats

# ==========================================
# 3. Solara 介面呈現
# ==========================================
@solara.component
def Page():
    # 初始化
    is_ok, msg = solara.use_memo(initialize_gee, [])
    
    # 執行地理計算
    diff_map, stats = solara.use_memo(lambda: get_ndvi_analysis() if is_ok else (None, None), [is_ok])

    with solara.Column(style={"padding": "20px"}):
        solara.Title("NDVI 變遷分析")
        solara.Markdown("# 🛰️ 八八風災前後 NDVI 變遷偵測")
        solara.Markdown("---")

        if not is_ok:
            solara.Error(f"GEE 初始化失敗：{msg}")
            return

        with solara.Row():
            # 左側：地圖顯示
            with solara.Column(md=8):
                solara.Markdown("### 🗺️ NDVI 差異圖 (2010 - 2008)")
                m = geemap.Map(center=[23.16, 120.64], zoom=14)
                m.add_basemap('HYBRID')
                
                if diff_map:
                    vis = {'min': -0.6, 'max': 0.6, 'palette': ['#800000', '#ff0000', '#ffffff', '#00ff00', '#008000']}
                    m.addLayer(diff_map, vis, 'NDVI Change')
                    m.add_legend(title="NDVI 變化圖例", legend_dict={
                        '嚴重崩塌 (<-0.3)': '#800000',
                        '植被流失 (-0.3~-0.1)': '#ff0000',
                        '無變化/恢復 (>-0.1)': '#ffffff'
                    })
                
                # ★★★ 核心修正：使用 solara.display(m) 替代 solara.FigureFolium(m) ★★★
                solara.display(m)

            # 右側：統計摘要
            with solara.Column(md=4):
                solara.Markdown("### 📊 變遷比例統計")
                if stats:
                    s = stats.get('severe', 0)
                    l = stats.get('loss', 0)
                    stb = stats.get('stable', 0)
                    total = s + l + stb
                    
                    if total > 0:
                        solara.Error(f"🔴 嚴重崩塌比例: {s/total:.1%}")
                        solara.Warning(f"🟠 植被流失比例: {l/total:.1%}")
                        solara.Success(f"⚪ 穩定與復育比例: {stb/total:.1%}")
                        solara.Markdown("---")
                        solara.Markdown(f"**受災影響總面積：{(s+l)/total:.1%}**")
                    else:
                        solara.Info("數據讀取中...")
                else:
                    solara.ProgressLinear(True)


