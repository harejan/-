import solara

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
        import matplotlib.pyplot as plt
import pandas as pd

data = {
    'Date': ['8/6', '8/7', '8/8', '8/9', '8/10'],
    'Rainfall': [56, 762, 1165, 856, 112]
}
# 轉成 DataFrame 表格格式
df_rain = pd.DataFrame(data)

# --- 開始畫圖 ---
plt.figure(figsize=(10, 6))

# 畫出長條圖，使用深藍色代表降雨
# alpha 是透明度，0.8 比較不刺眼
bars = plt.bar(df_rain['Date'], df_rain['Rainfall'], color='#1f77b4', alpha=0.8)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 10, int(yval), 
             ha='center', va='bottom', fontsize=12, fontweight='bold')

# 設定標題與標籤
plt.title('Daily Rainfall During Typhoon Morakot (Alishan Station)', fontsize=15)
plt.xlabel('Date (Aug 2009)', fontsize=12)
plt.ylabel('Accumulated Rainfall (mm)', fontsize=12)

# 設定 Y 軸範圍
plt.ylim(0, 1400) 

# 加個虛線網格，比較好對照數值
plt.grid(axis='y', linestyle='--', alpha=0.5)

# 顯示圖表
plt.show()


        