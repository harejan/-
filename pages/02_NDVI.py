import os
import ee
import solara
import geemap.foliumap as geemap
import json

# ==========================================
# 1. 初始化 GEE
# ==========================================
def init_gee():
    try:
        my_project_id = "ee-julia200594714" 
        sa = os.environ.get("GEE_SERVICE_ACCOUNT")
        key = os.environ.get("GEE_JSON_KEY")
        if sa and key:
            credentials = ee.ServiceAccountCredentials(sa, key_data=key)
            ee.Initialize(credentials, project=my_project_id)
            return True, f"OK: {my_project_id}"
        else:
            ee.Initialize(project=my_project_id)
            return True, "Local OK"
    except Exception as e:
        return False, str(e)

# ==========================================
# 2. 核心分析：鎖定災區座標與運算
# ==========================================
def run_analysis_task():
    # 鎖定八八風災中心：小林村/甲仙一帶
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(12000).bounds()

    def get_ndvi(start, end):
        # 抓取 Landsat 5 影像集合
        col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 50))
        
        count = col.size().getInfo()
        # 使用中位數合成 (Median Composite)
        img = col.median().clip(roi)
        # Landsat 5 NDVI 公式: (B4-B3)/(B4+B3)
        ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
        return ndvi, count

    # 執行災前(2009)與災後(2010)運算
    pre_ndvi, pre_count = get_ndvi('2009-01-01', '2009-08-01')
    post_ndvi, post_count = get_ndvi('2010-01-01', '2010-08-01')
    
    # 核心：變遷圖 (2010 - 2009)
    diff = post_ndvi.subtract(pre_ndvi)

    # 執行區域統計 (reduceRegion)
    stats = diff.addBands([
        diff.lt(-0.1).rename('red'),
        diff.gt(0.1).rename('green'),
        diff.gte(-0.1).And(diff.lte(0.1)).rename('neutral')
    ]).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    r = stats.get('red', 0) or 0
    g = stats.get('green', 0) or 0
    n = stats.get('neutral', 0) or 0
    total = r + g + n
    ratios = {"red": r/total, "green": g/total, "neutral": n/total} if total > 0 else {"red":0,"green":0,"neutral":0}

    return diff, pre_ndvi, post_ndvi, ratios, f"災前:{pre_count} | 災後:{post_count}"

# ==========================================
# 3. Solara 介面渲染
# ==========================================
@solara.component
def Page():
    ok_status, msg = solara.use_memo(init_gee, [])
    result = solara.use_thread(run_analysis_task, dependencies=[ok_status])

    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災 NDVI 變遷分佈 (紅色為崩塌受災區)")

        if result.state == solara.ResultState.FINISHED:
            diff_img, pre_ndvi, post_ndvi, ratios, debug_info = result.value
            
            solara.Info(f"📊 數據統計狀態：{debug_info}")

            # 顯示比例卡片
            with solara.Row():
                with solara.Card("🔴 植生流失 (災區)", style={"flex": "1", "color": "red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 環境穩定", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生復甦", style={"flex": "1", "color": "green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 地圖設置
            m = geemap.Map(center=[23.16, 120.63], zoom=13, height=600)
            m.add_basemap("HYBRID") # 使用衛星底圖更易對照地形
            
            # 視覺化參數：NDVI 差異層 (紅-白-綠)
            diff_params = {'min': -0.4, 'max': 0.4, 'palette': ['#FF0000', '#FFFFFF', '#00FF00']}
            
            # 加入圖層
            m.addLayer(pre_ndvi, {'min': 0, 'max': 0.8, 'palette': ['white', 'green']}, "2009 災前 NDVI", False)
            m.addLayer(diff_img, diff_params, "NDVI 變遷 (紅色代表受災)")
            
            # 加入圖例
            m.add_legend(title="變遷分類", legend_dict={
                '植生流失 (崩塌地)': '#FF0000',
                '環境穩定': '#FFFFFF',
                '植生復甦': '#00FF00'
            })
            
            solara.display(m)

        elif result.state == solara.ResultState.RUNNING:
            solara.Info("⏳ 請稍候...")
            solara.ProgressLinear(True)