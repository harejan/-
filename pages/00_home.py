import solara
import matplotlib.pyplot as plt
import pandas as pd

# 1. 準備數據 (放在函數外或內皆可，建議放在內或使用 memo)
data = {
    'Date': ['8/6', '8/7', '8/8', '8/9', '8/10'],
    'Rainfall': [56, 762, 1165, 856, 112]
}
df_rain = pd.DataFrame(data)

@solara.component
def Page(): 
    with solara.Column(style={"max-width": "800px", "margin": "0 auto"}):
        solara.Markdown("# 八八風災")
        
        solara.Markdown("### 🌪️ 關於八八風災 (Typhoon Morakot)")
        solara.Markdown("""
        2009 年 8 月 8 日，莫拉克颱風襲台。雖然它是中度颱風，但其引進的西南氣流在短短三天內為南台灣帶來了超過 **2,500 毫米** 的驚人雨量，相當於台灣一整年的平均降雨量。這場50 年一遇的水患造成全台 681 人死亡，是近代台灣最嚴重的氣象災害。
        """)
        
        solara.Markdown("### ⛰️ 小林村")
        solara.Markdown("""
        位於高雄甲仙區的小林村，是這場災難中受創最深的地方。
        
        在連續暴雨的沖刷下，村落東北方的獻肚山發生大規模深層崩塌。超過 3,000 萬立方公尺的土石瞬間傾洩而下，將小林村第 9 至 18 鄰完全掩埋。隨後，土石阻斷旗山溪形成堰塞湖，潰決後的洪水造成了毀滅性的二次災害。
        """)

        solara.Markdown("### 📊 降雨量統計圖")

        # --- 開始繪圖邏輯 ---
        # 在 Solara 中，我們需要建立一個 figure 物件
        fig, ax = plt.subplots(figsize=(10, 6))

        # 畫出長條圖
        bars = ax.bar(df_rain['Date'], df_rain['Rainfall'], color='#1f77b4', alpha=0.8)

        # 加上數值標籤
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 10, int(yval), 
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

        # 設定標題與標籤
        ax.set_title('Daily Rainfall During Typhoon Morakot (Alishan Station)', fontsize=15)
        ax.set_xlabel('Date (Aug 2009)', fontsize=12)
        ax.set_ylabel('Accumulated Rainfall (mm)', fontsize=12)
        ax.set_ylim(0, 1400) 
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # 使用 Solara 專用組件顯示 Matplotlib 圖表
        solara.FigureMatplotlib(fig)


        