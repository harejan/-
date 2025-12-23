import os
import ee
import solara
import leafmap.foliumap as leafmap
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
            return True
        else:
            ee.Initialize(project=my_project_id)
            return True
    except:
        return False

# ==========================================
# 2. 核心分析函數 (背景執行用)
# ==========================================
def run_analysis_task():
    # 高雄山區受災中心
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def get_ndvi(start, end):
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi).filterDate(start, end).median()
        return img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI').clip(roi)

    pre = get_ndvi('2009-01-01', '2009-08-01')
    post = get_ndvi('2010-01-01', '2010-08-01')
    diff = post.subtract(pre)

    # 執行統計 (這是最耗時的部分)
    red_mask = diff.lt(-0.1).rename('red')
    green_mask = diff.gt(0.1).rename('green')
    neutral_mask = diff.gte(-0.1).And(diff.lte(0.1)).rename('neutral')
    
    stats = diff.addBands([red_mask, green_mask, neutral_mask]).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e9
    ).getInfo()

    r, g, n = stats.get('red', 0) or 0, stats.get('green', 0) or 0, stats.get('neutral', 0) or 0
    total = r + g + n
    ratios = {"red": r/total, "green": g/total, "neutral": n/total} if total > 0 else {"red":0,"green":0,"neutral":0}

    return diff, ratios

# ==========================================
# 3. Solara 介面 (加入多執行緒處理)
# ==========================================
@solara.component
def Page():
    # 1. 認證狀態
    is_authenticated = solara.use_memo(init_gee, [])
    
    # 2. 使用執行緒處理 GEE 運算 (避免網頁卡死)
    result = solara.use_thread(run_analysis_task, dependencies=[is_authenticated])

    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測系統")

        if not is_authenticated:
            solara.Error("GEE 認證失敗，請檢查專案 ID 與 Secrets 設定。")
            return

        # 3. 根據運算狀態顯示 UI
        if result.state == solara.ResultState.RUNNING:
            with solara.Card():
                solara.Markdown("### ⏳ 正在與 Google Earth Engine 連線...")
                solara.ProgressLinear(True)
                solara.Markdown("系統正在計算 2009-2010 年間的植生變遷比例，請稍候約 10-20 秒。")

        elif result.state == solara.ResultState.ERROR:
            solara.Error(f"運算過程出錯: {result.error}")

        elif result.state == solara.ResultState.FINISHED:
            diff_img, ratios = result.value
            
            # 顯示比例卡片
            with solara.Row():
                with solara.Card("🔴 植生減少", style={"flex": "1", "color": "red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 環境穩定", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加", style={"flex": "1", "color": "green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 地圖顯示
            m = leafmap.Map(center=[23.16, 120.63], zoom=11, height=600)
            m.add_basemap("HYBRID")
            
            diff_vis = {'min': -0.5, 'max': 0.5, 'palette': ['red', 'white', 'green']}
            m.add_ee_layer(diff_img, diff_vis, "NDVI 變遷層")
            
            m.add_legend(title="變遷分類", legend_dict={'減少': 'red', '穩定': 'white', '增加': 'green'})
            
            # 在 Solara 中渲染 Folium 地圖
            solara.display(m)