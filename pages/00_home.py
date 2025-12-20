import solara

@solara.component
def Page(): 
    with solara.Column(style={"max-width": "800px", "margin": "0 auto"}):
        solara.Markdown("# 八八風災與小林村")
        
        solara.Markdown("### 🌪️ 關於八八風災 (Typhoon Morakot)")
        solara.Markdown("""
        2009 年 8 月 8 日，莫拉克颱風襲台。雖然它是中度颱風，但其引進的西南氣流在短短三天內為南台灣帶來了超過 **2,500 毫米** 的驚人雨量，相當於台灣一整年的平均降雨量。這場50 年一遇的水患造成全台 681 人死亡，是近代台灣最嚴重的氣象災害。
        """)
        
        solara.Markdown("### ⛰️ 小林村 (Xiaolin Village)")
        solara.Markdown("""
        位於高雄甲仙區的小林村，是這場災難中受創最深的地方。
        
        在連續暴雨的沖刷下，村落東北方的 **獻肚山 (Mt. Xiandu)** 發生大規模 **深層崩塌 (Deep-seated Landslide)**。超過 3,000 萬立方公尺的土石瞬間傾洩而下，將小林村第 9 至 18 鄰完全掩埋。隨後，土石阻斷旗山溪形成堰塞湖，潰決後的洪水造成了毀滅性的二次災害。
        """)

Page()
        