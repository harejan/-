import os
import ee
import solara
import leafmap.foliumap as leafmap
import json

# ==========================================
# 1. GEE 初始化 (解決 Project ID 與認證問題)
# ==========================================
def init_gee():
    try:
        # 取得環境變數
        sa = os.environ.get("GEE_SERVICE_ACCOUNT")
        key = os.environ.get("GEE_JSON_KEY")
        # 修正：讀取變數名稱 GEE_PROJECT，若沒設則嘗試從金鑰中自動抓取
        project = os.environ.get("GEE_PROJECT") 
        
        if sa and key:
            key_dict = json.loads(key)
            if not project:
                project = key_dict.get("project_id")
            
            # 若自動抓取也失敗，請在此手動補上您的 ID，例如 "ee-julia200594714"
            if not project:
                project = "ee-julia200594714"

            credentials = ee.ServiceAccountCredentials(sa, key_data=key)
            ee.Initialize(credentials, project=project)
            return True, f"✅ 雲端認證成功 (專案: {project})"
        else:
            # 本地開發模式
            ee.Initialize(project=project)
            return True, "✅ 本地開發認證成功"
    except Exception as e:
        return False, f"❌ 初始化失敗: {str(e)}"

# ==========================================
# 2. 八八風災變遷運算邏輯 (Landsat 5)
# ==========================================
def run_morakot_analysis():
    # 高雄山區受災中心點 (六龜/甲仙)
    roi = ee.Geometry.Point([120.63, 23.16]).buffer(15000).bounds()

    # NDVI 計算函數 (Landsat 5: B4 為 NIR, B3 為 Red)
    def get_ndvi(start, end):
        img = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start, end) \
                .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
                .median()
        # 計算 NDVI 並命名為 'NDVI'
        return img.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')

    # 風災前 (2009) 與 風災後 (2010)
    pre_ndvi = get_ndvi('2009-01-01', '2009-07-31')
    post_ndvi = get_ndvi('2010-01-01', '2010-07-31')

    # 核心計算：變遷圖 (後減前: 2010 - 2009)
    # 負值代表植生減少，正值代表植生增加
    diff = post_ndvi.subtract(pre_ndvi)

    # --- 比例統計邏輯 ---
    # 分類門檻：減少 (< -0.1), 增加 (> 0.1), 穩定 (-0.1 ~ 0.1)
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

    # 安全計算百分比，防止 None 或 0 導致報錯
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
    # 執行初始化 (使用 use_memo 確保只執行一次)
    ok, msg = solara.use_memo(init_gee, [])
    
    with solara.Column(style={"padding": "20px"}):
        solara.Title("🛰️ 八八風災前後 NDVI 變遷監測 (2009-2010)")
        
        if ok:
            # 取得運算結果
            diff_img, ratios = run_morakot_analysis()
            
            # A. 比例統計卡片 (顯示三色比例)
            solara.Markdown("### 📊 區域影響比例統計 (2010年 vs 2009年)")
            with solara.Row():
                with solara.Card("🔴 植生減少 (受災)", style={"flex": "1", "color": "#d32f2f", "border-top": "5px solid red"}):
                    solara.Markdown(f"## {ratios['red']:.2%}")
                with solara.Card("⚪ 穩定/不變", style={"flex": "1", "border-top": "5px solid gray"}):
                    solara.Markdown(f"## {ratios['neutral']:.2%}")
                with solara.Card("🟢 植生增加 (復甦)", style={"flex": "1", "color": "#388e3c", "border-top": "5px solid green"}):
                    solara.Markdown(f"## {ratios['green']:.2%}")

            # B. 地圖顯示
            solara.Markdown("### 🗺️ NDVI 變遷分佈圖 (後減前)")
            m = leafmap.Map(center=[23.16, 120.63], zoom=12)
            
            # 設定視覺化參數 (紅, 白, 綠)
            diff_vis = {
                'min': -0.5,
                'max': 0.5,
                'palette': ['#ff0000', '#ffffff', '#00ff00']
            }
            
            # --- 關鍵修正：針對 EE 物件必須使用 add_ee_layer ---
            m.add_ee_layer(diff_img, diff_vis, "八八風災 NDVI 變遷")
            
            # 加入圖例
            legend_dict = {
                '植生減少 (崩塌地)': '#ff0000',
                '環境穩定': '#ffffff',
                '植生增加 (復甦)': '#00ff00'
            }
            m.add_legend(title="變遷分類說明", legend_dict=legend_dict)
            
            # 顯示地圖
            solara.display(m)
            
        else:
            # 顯示錯誤引導
            solara.Error(f"初始化失敗：{msg}")
            solara.Markdown("#### 🛠️ 請檢查您的環境變數設定：")
            solara.Markdown("1. **GEE_PROJECT**: 必須填寫您的 Google Cloud Project ID (例如: `ee-julia200594714`)")
            solara.Markdown("2. **GEE_SERVICE_ACCOUNT**: 服務帳戶 Email")
            solara.Markdown("3. **GEE_JSON_KEY**: 完整的 JSON 金鑰字串")