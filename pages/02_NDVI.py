import os
import ee
import solara
import leafmap.foliumap as leafmap

# --- 1. GEE 初始化 ---
def init_gee():
    try:
        if not ee.data._initialized:
            sa = os.environ.get("GEE_SERVICE_ACCOUNT")
            key = os.environ.get("GEE_JSON_KEY")
            if sa and key:
                ee.Initialize(ee.ServiceAccountCredentials(sa, key_data=key))
            else:
                ee.Initialize()
        return True, "✅ GEE 已就緒"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# --- 2. 八八風災核心運算 (Landsat 5) ---
def run_morakot_analysis():
    # 高雄山區受災嚴重區域 (六龜、甲仙、那瑪夏一帶)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    # 八八風災發生於 2009-08-08
    # 統一使用 Landsat 5 計算 NDVI
    def get_ndvi(start, end):
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
                .median()
        # Landsat 5 波段: B4 (NIR), B3 (Red)
        return img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')

    # 風災前：2009年上半年 | 風災後：2010年上半年
    pre_ndvi = get_ndvi('2009-01-01', '2009-07-31')
    post_ndvi = get_ndvi('2010-01-01', '2010-07-31')

    # 核心計算：後減前 (2010 - 2009)
    diff = post_ndvi.subtract(pre_ndvi)

    # --- 分類與比例統計邏輯 ---
    # 紅色 (-): 減少 | 綠色 (+): 增加 | 白色: 穩定
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

    total = stats['red'] + stats['green'] + stats['neutral']
    ratios = {
        "red": stats['red'] / total if total > 0 else 0,
        "green": stats['green'] / total if total > 0 else 0,
        "neutral": stats['neutral'] / total if total > 0 else 0
    }

    return diff, ratios, roi

# --- 3. Solara 介面組件 ---
@solara.component
def Page():
    ok, msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災植生變遷監測 (2009 vs 2010)")
        
        if ok:
            diff_img, ratios, roi = run_morakot_analysis()
            
            # 顯示比例統計卡片
            solara.Markdown("### 📊 八八風災前後區域影響比例統計")
            with solara.Row():
                with solara.Card("🔴 植生減少 (崩塌/受損)", style={"flex": "1", "border-top": "5px solid red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定區域 (無變化)", style={"flex": "1", "border-top": "5px solid gray"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加 (復甦)", style={"flex": "1", "border-top": "5px solid green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 地圖顯示
            solara.Markdown("### 🗺️ NDVI 差異分佈圖 (2010 - 2009)")
            m = leafmap.Map(center=[23.16, 120.63], zoom=12)
            
            # 設定您要求的紅、白、綠三色
            diff_vis = {
                'min': -0.5,
                'max': 0.5,
                'palette': ['red', 'white', 'green']
            }
            
            m.add_layer(diff_img, diff_vis, "八八風災 NDVI 變遷")
            
            # 加入圖例
            legend_dict = {
                '植生嚴重流失 (<-0.1)': 'red',
                '環境穩定 (-0.1~0.1)': 'white',
                '植生復甦 (>0.1)': 'green'
            }
            m.add_legend(title="變遷分類說明", legend_dict=legend_dict)
            
            solara.display(m)
        else:
            solara.Error(msg)