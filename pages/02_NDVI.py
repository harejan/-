import os
import ee
import solara
import leafmap.foliumap as leafmap
import json

# ==========================================
# 1. 修正版初始化 (強制指定您的專案 ID)
# ==========================================
def init_gee():
    try:
        # 1. 直接指定您的專案 ID (不再依賴環境變數自動抓取)
        my_project_id = "ee-julia200594714" 
        
        # 2. 取得 Secrets 環境變數
        sa = os.environ.get("GEE_SERVICE_ACCOUNT")
        key = os.environ.get("GEE_JSON_KEY")
        
        if sa and key:
            # 雲端認證模式
            credentials = ee.ServiceAccountCredentials(sa, key_data=key)
            # 關鍵點：在這裡強制傳入 my_project_id
            ee.Initialize(credentials, project=my_project_id)
            return True, f"✅ 雲端認證成功 (專案: {my_project_id})"
        else:
            # 本地開發模式 (如果本地端已有登入，也會使用此專案)
            ee.Initialize(project=my_project_id)
            return True, f"✅ 本地開發認證成功 (專案: {my_project_id})"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# ==========================================
# 2. 八八風災變遷運算邏輯 (Landsat 5)
# ==========================================
def run_morakot_analysis():
    # 高雄山區受災中心點 (六龜/甲仙)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    def get_ndvi(start, end):
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
                .median()
        return img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')

    # 風災前 (2009) 與 風災後 (2010)
    pre_ndvi = get_ndvi('2009-01-01', '2009-07-31')
    post_ndvi = get_ndvi('2010-01-01', '2010-07-31')

    # 核心計算：變遷圖 (後減前)
    diff = post_ndvi.subtract(pre_ndvi)

    # 比例統計分類
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

    r_val = stats.get('red', 0) or 0
    g_val = stats.get('green', 0) or 0
    n_val = stats.get('neutral', 0) or 0
    total = r_val + g_val + n_val
    
    if total > 0:
        ratios = {"red": r_val/total, "green": g_val/total, "neutral": n_val/total}
    else:
        ratios = {"red": 0, "green": 0, "neutral": 0}

    return diff, ratios

# ==========================================
# 3. Solara 介面渲染
# ==========================================
@solara.component
def Page():
    ok, msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測 (2009-2010)")
        
        if ok:
            diff_img, ratios = run_morakot_analysis()
            
            # 📊 比例統計卡片
            solara.Markdown("### 📊 區域影響比例統計 (2010 vs 2009)")
            with solara.Row():
                with solara.Card("🔴 植生減少 (受災)", style={"flex": "1", "color": "#d32f2f", "border-top": "5px solid red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定/不變", style={"flex": "1", "border-top": "5px solid gray"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加 (復甦)", style={"flex": "1", "color": "#388e3c", "border-top": "5px solid green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # 🗺️ 地圖顯示
            m = leafmap.Map(center=[23.16, 120.63], zoom=12)
            diff_vis = {'min': -0.5, 'max': 0.5, 'palette': ['#ff0000', '#ffffff', '#00ff00']}
            
            # 使用正確的 EE 圖層加入方式
            m.add_ee_layer(diff_img, diff_vis, "八八風災 NDVI 變遷")
            
            m.add_legend(title="變遷分類說明", legend_dict={
                '植生減少 (崩塌地)': '#ff0000',
                '環境穩定': '#ffffff',
                '植生增加 (復甦)': '#00ff00'
            })
            test_img=ee.Image(0.1).clip(ee.Geometry.Point([23.16, 120.63]).buffer(100000))
            m.add_ee_layer(test_img,{'min':0,'msx':1,'palette':['red']},"test")
            solara.display(m)
        else:
            solara.Error(f"初始化失敗：{msg}")
            solara.Markdown(f"### 💡 排除障礙建議：")
            solara.Markdown("1. 請確認您的 Secret `GEE_JSON_KEY` 內容包含完整的大括號 `{ }`。")
            solara.Markdown(f"2. 目前程式強制使用的專案 ID 為: `ee-julia200594714`。")