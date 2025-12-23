import os
import ee
import solara
import geemap.foliumap as geemap # 使用 geemap 核心
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
            return True, f"✅ 認證成功: {my_project_id}"
        else:
            ee.Initialize(project=my_project_id)
            return True, "✅ 本地認證成功"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# ==========================================
# 2. 核心分析函數 (回傳圖層與影像計數)
# ==========================================
def run_analysis_task():
    # 高雄山區受災中心點
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def get_ndvi(start, end):
        # 抓取 Landsat 5 影像
        col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 50))
        
        count = col.size().getInfo()
        # 使用 median 合成並計算 NDVI
        img = col.median().clip(roi)
        ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
        return ndvi, count

    # 執行運算
    pre_ndvi, pre_count = get_ndvi('2009-01-01', '2009-08-01')
    post_ndvi, post_count = get_ndvi('2010-01-01', '2010-08-01')
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

    debug_msg = f"災前影像數: {pre_count} | 災後影像數: {post_count}"
    return diff, ratios, debug_msg

# ==========================================
# 3. Solara 介面呈現
# ==========================================
@solara.component
def Page():
    ok_status, msg = solara.use_memo(init_gee, [])
    # 使用 Thread 處理運算，避免網頁卡死
    result = solara.use_thread(run_analysis_task, dependencies=[ok_status])

    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷偵測系統")

        if not ok_status:
            solara.Error(f"初始化失敗：{msg}")
            return

        if result.state == solara.ResultState.RUNNING:
            solara.Info("⏳ 正在與 Google Earth Engine 進行跨年度運算，請稍候...")
            solara.ProgressLinear(True)

        elif result.state == solara.ResultState.FINISHED:
            diff_img, ratios, debug_info = result.value
            
            solara.Info(f"📊 數據狀態：{debug_info}")

            # 顯示比例統計
            with solara.Row():
                with solara.Card("🔴 植生減少", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定區域", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 地圖顯示
            # 在 geemap.foliumap 中，Map 物件的 add_ee_layer 應改為 addLayer
            m = geemap.Map(center=[23.16, 120.63], zoom=12, height=600)
            m.add_basemap("HYBRID")
            
            diff_vis = {
                'min': -0.5, 
                'max': 0.5, 
                'palette': ['#ff0000', '#ffffff', '#00ff00']
            }
            
            # --- 關鍵修正：geemap.foliumap 應使用 addLayer ---
            m.addLayer(diff_img, diff_vis, "NDVI Difference")
            
            m.add_legend(title="變遷分類說明", legend_dict={
                '植生減少 (崩塌)': '#ff0000',
                '環境穩定': '#ffffff',
                '植生增加 (復甦)': '#00ff00'
            })
            
            # 強制 HTML 渲染確保圖層出現
            solara.HTML(m._repr_html_(), style={"height": "600px", "width": "100%"})

        elif result.state == solara.ResultState.ERROR:
            solara.Error(f"運算錯誤：{result.error}")