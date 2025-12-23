import os
import ee
import solara
import leafmap  # 修改這裡，直接引用 leafmap

# GEE 初始化邏輯 (你已經成功的部分保留)
# ... 略 ...

@solara.component
def Page():
    # ... 略 ...
    
    # 建立地圖時直接使用 leafmap.Map
    m = leafmap.Map(center=[23.16, 120.63], zoom=12)
    
    # 這裡加入你之前的 NDVI 運算與圖層
    # m.add_layer(diff, diff_params, "植被減少區域 (變遷)")
    
    solara.display(m)