import os
import ee
import solara
import leafmap.foliumap as leafmap
import json

# ==========================================
# 1. 初始化 GEE (確保 Project ID 正確)
# ==========================================
def init_gee():
    try:
        # 請確保這裡的 ID 與您的 Google Cloud 專案一致
        my_project_id = "ee-julia200594714" 
        sa = os.environ.get("GEE_SERVICE_ACCOUNT")
        key = os.environ.get("GEE_JSON_KEY")
        
        if sa and key:
            credentials = ee.ServiceAccountCredentials(sa, key_data=key)
            ee.Initialize(credentials, project=my_project_id)
            return True, f"✅ 認證成功: {my_project_id}"
        else:
            ee.Initialize(project=my_project_id)
            return True, "✅ 本地認證成功"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# ==========================================
# 2. 核心運算：明確載入兩年度影像
# ==========================================
def run_morakot_analysis():
    # 高雄山區受災中心 (六龜/甲仙區域)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def get_ndvi_data(start, end):
        # 載入 Landsat 5
        dataset = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                    .filterBounds(roi) \
                    .filterDate(start, end) \
                    .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
                    .median()
        # 計算 NDVI (Landsat 5: B4=NIR, B3=Red)
        ndvi = dataset.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
        return dataset.clip(roi), ndvi.clip(roi)

    # 災前 (2009) 與 災後 (2010)
    pre_img, pre_ndvi = get_ndvi_data('2009-01-01', '2009-07-30')
    post_img, post_ndvi = get_ndvi_data('2010-01-01', '2010-07-30')

    # 計算差異 (2010 - 2009)
    diff = post_ndvi.subtract(pre_ndvi)

    # 比例統計
    red_mask = diff.lt(-0.1).rename('red')
    green_mask = diff.gt(0.1).rename('green')
    neutral_mask = diff.gte(-0.1).And(diff.lte(0.1)).rename('neutral')
    
    stats = diff.addBands([red_mask, green_mask, neutral_mask]).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e9
    ).getInfo()

    r, g, n = stats.get('red', 0) or 0, stats.get('green', 0) or 0, stats.get('neutral', 0) or 0
    total = r + g + n
    ratios = {"red": r/total, "green": g/total, "neutral": n/total} if total > 0 else {"red":0,"green":0,"neutral":0}

    return pre_img, post_img, diff, ratios

# ==========================================
# 3. Solara 介面渲染
# ==========================================
@solara.component
def Page():
    # 執行初始化
    ok, msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測 (2009-2010)")
        
        if ok:
            # 取得運算結果
            pre_img, post_img, diff_img, ratios = run_morakot_analysis()
            
            # --- 顯示統計卡片 ---
            with solara.Row():
                with solara.Card("🔴 植生減少 (崩塌)", style={"flex": "1", "color": "#d32f2f", "border-top": "5px solid red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定區域", style={"flex": "1", "border-top": "5px solid gray"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加 (復甦)", style={"flex": "1", "color": "#388e3c", "border-top": "5px solid green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # --- 地圖呈現 ---
            m = leafmap.Map(center=[23.16, 120.63], zoom=12, height=600)
            
            # 視覺化參數修正 (採用最標準的 positional arguments)
            rgb_vis = {'bands': ['SR_B3', 'SR_B2', 'SR_B1'], 'min': 7000, 'max': 15000}
            diff_vis = {'min': -0.5, 'max': 0.5, 'palette': ['#ff0000', '#ffffff', '#00ff00']}

            # 修正 add_ee_layer 呼叫方式，確保顯示

            m.add_ee_layer(diff_img, diff_vis, "NDVI 變遷圖 (2010-2009)")
            
            # 圖例
            m.add_legend(title="變遷分類說明", legend_dict={
                '植生減少 (崩塌地)': '#ff0000',
                '環境穩定': '#ffffff',
                '植生增加 (復甦)': '#00ff00'
            })
            
            # 改用 FigureFolium 強制渲染
            solara.FigureFolium(m)
            
        else:
            solara.Error(f"初始化失敗：{msg}")