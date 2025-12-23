import os
import ee
import solara
import leafmap.foliumap as leafmap
import json

# --- 1. 修正後的 GEE 初始化邏輯 ---
def init_gee():
    try:
        # 取得環境變數
        sa = os.environ.get("GEE_SERVICE_ACCOUNT")
        json_key = os.environ.get("GEE_JSON_KEY")
        
        if sa and json_key:
            # 雲端模式：使用 Service Account
            # 這裡不檢查 _initialized，直接嘗試初始化
            credentials = ee.ServiceAccountCredentials(sa, key_data=json_key)
            ee.Initialize(credentials)
        else:
            # 本地模式
            ee.Initialize()
        return True, "✅ GEE 初始化成功"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# --- 2. 八八風災核心運算 (Landsat 5) ---
def run_morakot_analysis():
    # 設定高雄受災山區座標 (六龜、甲仙中心點)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def get_ndvi(start, end):
        # 使用 Landsat 5
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
                .median()
        return img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')

    # 風災前 (2009) 與 風災後 (2010)
    pre_ndvi = get_ndvi('2009-01-01', '2009-07-31')
    post_ndvi = get_ndvi('2010-01-01', '2010-07-31')

    # 核心計算：變遷 (2010 - 2009)
    diff = post_ndvi.subtract(pre_ndvi)

    # 分類統計比例
    red_mask = diff.lt(-0.1).rename('red')
    green_mask = diff.gt(0.1).rename('green')
    neutral_mask = diff.gte(-0.1).And(diff.lte(0.1)).rename('neutral')
    
    combined = diff.addBands([red_mask, green_mask, neutral_mask])
    
    stats = combined.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    # 安全地計算比例 (防止除以 0)
    total = (stats.get('red', 0) or 0) + (stats.get('green', 0) or 0) + (stats.get('neutral', 0) or 0)
    if total > 0:
        ratios = {
            "red": stats.get('red', 0) / total,
            "green": stats.get('green', 0) / total,
            "neutral": stats.get('neutral', 0) / total
        }
    else:
        ratios = {"red": 0, "green": 0, "neutral": 0}

    return diff, ratios

# --- 3. Solara UI 介面 ---
@solara.component
def Page():
    # 使用 use_memo 確保初始化在頁面載入時執行
    ok, msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測 (2009-2010)")
        
        if ok:
            diff_img, ratios = run_morakot_analysis()
            
            # 統計卡片
            with solara.Row():
                with solara.Card("🔴 植生減少 (崩塌)", style={"flex": "1", "color": "red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定區域", style={"flex": "1"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加 (復甦)", style={"flex": "1", "color": "green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 地圖顯示
            m = leafmap.Map(center=[23.16, 120.63], zoom=12)
            
            # 設定紅、白、綠三色
            diff_vis = {
                'min': -0.5,
                'max': 0.5,
                'palette': ['#ff0000', '#ffffff', '#00ff00']
            }
            
            m.add_layer(diff_img, diff_vis, "NDVI 變遷 (2010 - 2009)")
            
            # 加入圖例
            legend_dict = {
                '植生減少 (崩塌地)': '#ff0000',
                '環境穩定': '#ffffff',
                '植生增加 (復甦)': '#00ff00'
            }
            m.add_legend(title="變遷分類說明", legend_dict=legend_dict)
            
            solara.display(m)
        else:
            solara.Error(f"初始化失敗：{msg}")