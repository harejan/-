import os
import ee
import solara
import leafmap.foliumap as leafmap
import json

# ==========================================
# 1. 初始化 GEE
# ==========================================
def init_gee():
    try:
        # 強制使用您的 Project ID
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
# 2. 核心分析邏輯 (Landsat 5)
# ==========================================
def run_morakot_analysis():
    # 高雄山區受災中心點
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def get_ndvi_layer(start, end):
        # 抓取 Landsat 5 影像並計算 NDVI
        # 擴大一點日期範圍確保有影像存在
        dataset = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                    .filterBounds(roi) \
                    .filterDate(start, end) \
                    .median()
        
        ndvi = dataset.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
        return ndvi.clip(roi)

    # 災前 (2009) 與 災後 (2010)
    pre_ndvi = get_ndvi_layer('2009-01-01', '2009-08-01')
    post_ndvi = get_ndvi_layer('2010-01-01', '2010-08-01')

    # 計算差值 (2010 - 2009)
    diff = post_ndvi.subtract(pre_ndvi)

    # 比例統計 (紅、白、綠)
    red_mask = diff.lt(-0.1).rename('red')
    green_mask = diff.gt(0.1).rename('green')
    neutral_mask = diff.gte(-0.1).And(diff.lte(0.1)).rename('neutral')
    
    stats = diff.addBands([red_mask, green_mask, neutral_mask]).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e9
    ).getInfo()

    r = stats.get('red', 0) or 0
    g = stats.get('green', 0) or 0
    n = stats.get('neutral', 0) or 0
    total = r + g + n
    ratios = {"red": r/total, "green": g/total, "neutral": n/total} if total > 0 else {"red":0,"green":0,"neutral":0}

    return diff, ratios

# ==========================================
# 3. Solara 介面呈現
# ==========================================
@solara.component
def Page():
    ok, msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測系統")
        
        if ok:
            diff_img, ratios = run_morakot_analysis()
            
            # A. 比例卡片
            with solara.Row():
                with solara.Card("🔴 植生減少", style={"flex": "1", "color": "#d32f2f"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 環境穩定", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加", style={"flex": "1", "color": "#388e3c"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # B. 地圖區域
            # 使用 HYBRID 底圖更能看出地形
            m = leafmap.Map(center=[23.16, 120.63], zoom=12, height=600)
            m.add_basemap("HYBRID") 

            # 設定差異視覺化
            diff_vis = {
                'min': -0.5, 
                'max': 0.5, 
                'palette': ['#ff0000', '#ffffff', '#00ff00']
            }
            
            # 加入 GEE 圖層
            m.add_ee_layer(diff_img, diff_vis, "NDVI 變遷層")
            
            # 加入圖例
            m.add_legend(title="變遷分類", legend_dict={
                '植生減少 (崩塌)': '#ff0000',
                '環境穩定': '#ffffff',
                '植生增加 (復甦)': '#00ff00'
            })
            
            # --- 關鍵修正：強制將 Folium 物件轉為 HTML 渲染 ---
            map_html = m._repr_html_()
            solara.HTML(map_html, style={"height": "600px", "width": "100%"})
            
        else:
            solara.Error(f"GEE 初始化失敗: {msg}")