import os
import ee
import solara
import geemap.foliumap as geemap
import json

# ==========================================
# 1. 初始化 GEE (強制指定 Project ID)
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
# 2. 核心分析：八八風災 NDVI 變遷運算
# ==========================================
def run_analysis_task():
    try:
        # 鎖定受災中心點
        roi = ee.Geometry.Point([120.63, 23.16]).buffer(12000).bounds()

        def get_ndvi(start, end):
            col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                    .filterBounds(roi) \
                    .filterDate(start, end) \
                    .filter(ee.Filter.lt('CLOUD_COVER', 50))
            
            img = col.median().clip(roi)
            # Landsat 5: B4=NIR, B3=Red
            ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
            return ndvi

        # 執行計算
        pre_ndvi = get_ndvi('2009-01-01', '2009-08-01')
        post_ndvi = get_ndvi('2010-01-01', '2010-08-01')
        diff = post_ndvi.subtract(pre_ndvi)

        # 區域統計 (紅、白、綠)
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

        return diff, pre_ndvi, ratios
    
    except Exception as e:
        raise Exception(f"GEE 運算失敗: {str(e)}")

# ==========================================
# 3. Solara 介面渲染 (已移除數據狀態提示)
# ==========================================
@solara.component
def Page():
    ok_status, _ = solara.use_memo(init_gee, [])
    result = solara.use_thread(run_analysis_task, dependencies=[ok_status])

    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測系統")

        if result.state == solara.ResultState.RUNNING:
            with solara.Card():
                solara.Info("⏳ 正在計算中... 請稍候")
                solara.ProgressLinear(True)

        elif result.state == solara.ResultState.ERROR:
            solara.Error(f"❌ 運算發生錯誤：{result.error}")

        elif result.state == solara.ResultState.FINISHED and result.value:
            diff_img, pre_ndvi, ratios = result.value
            
            # 1. 顯示比例卡片
            with solara.Row():
                with solara.Card("🔴 植生流失", style={"flex": "1", "color": "red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 環境穩定", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生復甦", style={"flex": "1", "color": "green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 2. 地圖設置
            m = geemap.Map(center=[23.16, 120.63], zoom=13, height=600)
            m.add_basemap("HYBRID")
            
            # 視覺化參數
            diff_params = {'min': -0.4, 'max': 0.4, 'palette': ['#FF0000', '#FFFFFF', '#00FF00']}
            
            # 加入圖層
            m.addLayer(pre_ndvi, {'min': 0, 'max': 0.8, 'palette': ['white', 'green']}, "2009 災前 NDVI", False)
            m.addLayer(diff_img, diff_params, "NDVI 變遷 (紅色為受災區)")
            
            m.add_legend(title="變遷分類", legend_dict={
                '植生流失 (崩塌地)': '#FF0000',
                '環境穩定': '#FFFFFF',
                '植生復甦': '#00FF00'
            })
            
            solara.display(m)