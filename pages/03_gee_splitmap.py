import solara
import ee
import geemap
import os

# --- GEE 初始化設定 ---
# 嘗試初始化 GEE。如果使用者尚未在終端機執行過 `earthengine authenticate`，這裡會失敗。
try:
    # 使用預設專案或是從環境變數讀取 (如果有的話)
    try:
        ee.Initialize()
    except Exception as e:
        # 如果初始化失敗，嘗試使用高權限模式 (有時候在某些環境需要)
        ee.Authenticate()
        ee.Initialize()
    GEE_READY = True
except Exception as e:
    GEE_READY = False
    GEE_ERROR = str(e)

def create_gee_split_map():
    if not GEE_READY:
        # 如果 GEE 沒準備好，回傳一個空地圖避免崩潰
        return geemap.Map()

    # --- 1. 定義研究區域與時間 ---
    # 小林村座標點
    xiaolin_point = ee.Geometry.Point([120.645, 23.159])
    # 建立一個以小林村為中心，半徑 6 公里的緩衝區作為研究範圍 (AOI)
    aoi = xiaolin_point.buffer(6000)

    # 莫拉克風災日期：2009年8月8日
    # 災前時間範圍 (取災前一年半到災前一個月，確保有足夠無雲影像合成)
    pre_start = '2008-01-01'
    pre_end = '2009-07-01'

    # 災後時間範圍 (取災後一年內)
    post_start = '2009-09-01'
    post_end = '2010-12-31'

    # --- 2. 選擇衛星資料集 (Landsat 7) ---
    # 使用 Landsat 7 Collection 2 Surface Reflectance
    # 當時 Landsat 8 還沒發射，Landsat 7 是最好的選擇
    l7 = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")

    # --- 3. 定義去雲與影像處理函式 ---
    def preprocess_l7(image):
        # 選擇品質波段
        qa_mask = image.select('QA_PIXEL')
        # 位元運算：遮蔽雲(bit 3)與雲影(bit 4)
        mask = qa_mask.bitwiseAnd(1 << 3).eq(0).And(qa_mask.bitwiseAnd(1 << 4).eq(0))
        
        # 應用遮罩並將數值縮放到 0-1 之間 (光學波段有縮放因子)
        # Landsat Collection 2 的縮放公式: DN * 0.0000275 - 0.2
        opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        
        return image.addBands(opticalBands, None, True).updateMask(mask).clip(aoi)

    # --- 4. 建立災前與災後合成影像 (Composite) ---
    # 篩選地點、時間，應用去雲處理，然後取中位數 (Median) 合成最清晰的影像
    pre_image = l7.filterBounds(aoi).filterDate(pre_start, pre_end).map(preprocess_l7).median()
    post_image = l7.filterBounds(aoi).filterDate(post_start, post_end).map(preprocess_l7).median()

    # --- 5. 設定視覺化參數 (假彩色) ---
    # 使用「假彩色」組合 (Near Infrared, Red, Green) = (B4, B3, B2)
    # 在假彩色中，健康的植被會顯示為「鮮紅色」，裸露地或崩塌地會顯示為「土色/青灰色」
    # 這種配色最適合觀察植被流失和崩塌地。
    vis_params = {
        'bands': ['SR_B4', 'SR_B3', 'SR_B2'],
        'min': 0.0,
        'max': 0.4,
        'gamma': 1.2
    }

    # --- 6. 建立 geemap 捲簾地圖 ---
    m = geemap.Map(center=[23.159, 120.645], zoom=13, height="650px")
    
    # 建立左右圖層
    left_layer = geemap.ee_tile_layer(pre_image, vis_params, name='災前 (Pre-Disaster)')
    right_layer = geemap.ee_tile_layer(post_image, vis_params, name='災後 (Post-Disaster)')
    
    # 啟用捲簾模式
    m.split_map(left_layer, right_layer)
    
    # 加入圖例 (選用)
    # m.add_legend(title="Legend", builtin_legend='NLCD') # 這裡先不加複雜圖例，保持畫面乾淨

    return m

@solara.component
def Page():
    with solara.Column(style={"height": "100vh", "padding": "0px"}):
        
        # --- 標題與說明 ---
        with solara.Card(style={"padding": "15px", "margin": "10px", "max-width": "900px"}):
            solara.Markdown("## 🛰️ Google Earth Engine 衛星變遷對比")
            solara.Markdown("### 小林村與獻肚山崩塌前後 (Landsat 7)")
            
            if not GEE_READY:
                 solara.Error(f"⚠️ GEE 尚未認證或是初始化失敗。請先在終端機執行 `earthengine authenticate`。")
                 solara.Text(f"錯誤訊息: {GEE_ERROR}", style={"font-size": "12px", "color": "gray"})
            else:
                solara.Info("請拖動中間的分隔線。左側為災前 (2008-2009中)，右側為災後 (2009末-2010)。")
                solara.Markdown("""
                **影像說明 (假彩色)：**
                此地圖使用 Landsat 7 衛星影像的近紅外光波段組合。
                * 🟥 **鮮紅色**：代表健康的森林與植被。
                * 🟫/⬜ **土色/灰白色**：代表裸露地、崩塌地或河床。
                
                觀察災後圖像，獻肚山區域出現大片非紅色區域，即為大規模崩塌發生處。
                """)

        # --- 顯示地圖 ---
        if GEE_READY:
            # 使用 use_memo 確保地圖只會被建立一次，不會一直重整
            m = solara.use_memo(create_gee_split_map, dependencies=[GEE_READY])
            # geemap.Map 可以直接在 Solara 中顯示
            solara.display(m)