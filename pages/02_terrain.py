import solara
import leafmap.maplibregl as leafmap
import os

MAPTILER_KEY = os.environ.get("MAPTILER_API_KEY", "")

def create_3d_map():
    # 2. 檢查 Key 是否存在
    if not MAPTILER_KEY:
        # 如果沒有 Key，回傳基礎地圖並定位在小林村
        m = leafmap.Map(
            center=[120.645, 23.159],
            zoom=12,
            style="https://demotiles.maplibre.org/style.json",
        )
        return m

    # 3. 設定 MapTiler 衛星影像樣式
    style_url = f"https://api.maptiler.com/maps/hybrid/style.json?key={MAPTILER_KEY}"
    
    m = leafmap.Map(
        style=style_url,
        center=[120.645, 23.159], # ✅ 修改中心：小林村與獻肚山
        zoom=14,                  # ✅ 放大：更清楚看到崩塌地細節
        pitch=80,                 # 傾斜角度：模擬低空飛越
        bearing=90,               # ✅ 視角：面向正東方 (面對獻肚山崩塌面)
    )
    
    # 步驟 A: 加入地形資料源 (Source)
    m.add_source("maptiler-terrain", {
        "type": "raster-dem",
        "url": f"https://api.maptiler.com/tiles/terrain-rgb/tiles.json?key={MAPTILER_KEY}",
        "tileSize": 512,
        "maxzoom": 14
    })
    
    # 步驟 B: 啟用該地形 (Set Terrain)
    # ✅ Exaggeration 設為 2.0：增強山勢陡峭感，突顯順向坡結構
    m.set_terrain({"source": "maptiler-terrain", "exaggeration": 2.0})
    
    # 加入導航控制項
    m.add_control("navigation", position="top-right")
    
    return m

@solara.component
def Page():
    with solara.Column(style={"height": "100vh", "padding": "0px"}):
        
        # 浮動資訊卡片
        with solara.Card(style={"position": "absolute", "top": "10px", "left": "10px", "z-index": "1000", "width": "320px"}):
            solara.Markdown("## ⛰️ 小林村與獻肚山 3D 地形")
            if not MAPTILER_KEY:
                solara.Error("⚠️ 請設定 MapTiler API Key 以檢視 3D 地形。")
            else:
                solara.Markdown("視角正對**獻肚山**崩塌面。")
                solara.Markdown("按住 **滑鼠右鍵** 拖曳可旋轉視角觀察順向坡結構。")

        # 顯示地圖
        m = create_3d_map()
        solara.display(m)

