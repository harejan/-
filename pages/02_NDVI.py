@solara.component
def Page():
    solara.Title("八八風災小林村：NDVI 變遷分析")
    
    with solara.Column(style={"padding": "20px"}):
        solara.Markdown("# 🌪️ 小林村植被變遷偵測 (2008-2010)")
