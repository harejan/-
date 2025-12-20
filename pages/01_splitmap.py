import solara
import ipyleaflet

def create_split_map():
    m = ipyleaflet.Map(
        center=[23.158, 120.640], 
        zoom=14, # 稍微放大一點，比較適合觀察村落範圍
        scroll_wheel_zoom=True,
        height="600px"
    )
    
    # 2. 定義左右兩張圖層
    # 左邊：衛星影像 (Esri World Imagery)
    left_layer = ipyleaflet.TileLayer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="衛星影像"
    )
    
    # 右邊：街道地圖 (OpenStreetMap)
    right_layer = ipyleaflet.TileLayer(
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="街道地圖"
    )

    # 3. 建立捲簾控制器 (SplitMapControl)
    split_control = ipyleaflet.SplitMapControl(
        left_layer=left_layer, 
        right_layer=right_layer
    )
    
    # 4. 把控制器加到地圖上
    m.add_control(split_control)
    
    # 加入比例尺 (選用，讓地圖更專業)
    m.add_control(ipyleaflet.ScaleControl(position='bottomleft'))
    
    return m

@solara.component
def Page():
    # 使用 use_memo 鎖定地圖狀態，避免重整時閃爍
    m = solara.use_memo(create_split_map, dependencies=[])
    
    with solara.Column(style={"padding": "20px", "max-width": "1200px", "margin": "0 auto"}):
        solara.Markdown("## 🗺️ 小林村 (Xiaolin Village) 衛星/地圖比對")
        
        # 顯示地圖
        solara.display(m)