import os
import ee
import solara
import geemap.foliumap as geemap # 改用 geemap 核心增加穩定性
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
            return True
        else:
            ee.Initialize(project=my_project_id)
            return True
    except:
        return False

# ==========================================
# 2. 核心分析函數 (回傳圖層與除錯資訊)
# ==========================================
def run_analysis_task():
    # 高雄山區受災中心 (八八風災)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def process_year(start, end):
        # 抓取影像集合
        col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 50)) # 稍微放寬雲量限制確保有圖
        
        count = col.size().getInfo() # 檢查抓到幾張圖
        img = col.median().clip(roi)
        ndvi = img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
        return ndvi, count

    # 災前與災後
    pre_ndvi, pre_count = process_year('2009-01-01', '2009-08-01')
    post_ndvi, post_count = process_year('2010-01-01', '2010-08-01')
    
    # 差值計算
    diff = post_ndvi.subtract(pre_ndvi)

    # 統計比例
    red_mask = diff.lt(-0.1).rename('red')
    green_mask = diff.gt(0.1).rename('green')
    neutral_mask = diff.gte(-0.1).And(diff.lte(0.1)).rename('neutral')
    
    stats = diff.addBands([red_mask, green_mask, neutral_mask]).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e9
    ).getInfo()

    r, g, n = stats.get('red', 0) or 0, stats.get('green', 0) or 0, stats.get('neutral', 0) or 0
    total = r + g + n
    ratios = {"red": r/total, "green": g/total, "neutral": n/total} if total > 0 else {"red":0,"green":0,"neutral":0}

    # 回傳結果與除錯訊息
    debug_msg = f"災前影像數: {pre_count}, 災後影像數: {post_count}"
    return diff, ratios, debug_msg

# ==========================================
# 3. Solara 介面
# ==========================================
@solara.component
def Page():
    is_authenticated = solara.use_memo(init_gee, [])
    result = solara.use_thread(run_analysis_task, dependencies=[is_authenticated])

    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災 NDVI 變遷監測 (影像偵錯版)")

        if not is_authenticated:
            solara.Error("GEE 認證失敗")
            return

        if result.state == solara.ResultState.RUNNING:
            solara.Info("⏳ 正在計算中... 請稍候 10-20 秒")
            solara.ProgressLinear(True)

        elif result.state == solara.ResultState.FINISHED:
            diff_img, ratios, debug_info = result.value
            
            # 顯示除錯資訊 (這很重要，如果數字是 0，代表沒抓到影像)
            solara.Info(f"📊 數據偵錯：{debug_info}")

            # 比例卡片
            with solara.Row():
                with solara.Card("🔴 植生減少", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 增加", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 地圖部分
            m = geemap.Map(center=[23.16, 120.63], zoom=12)
            m.add_basemap("HYBRID")
            
            # 設定視覺化
            diff_vis = {'min': -0.5, 'max': 0.5, 'palette': ['red', 'white', 'green']}
            
            # 這裡一定要用 add_ee_layer
            m.add_ee_layer(diff_img, diff_vis, "NDVI Difference")
            
            m.add_legend(title="變遷分類", legend_dict={'減少': 'red', '穩定': 'white', '增加': 'green'})
            
            # 強制使用 HTML 渲染確保圖層出現
            solara.HTML(m._repr_html_(), style={"height": "600px", "width": "100%"})

        elif result.state == solara.ResultState.ERROR:
            solara.Error(f"錯誤: {result.error}")