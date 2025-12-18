# 使用輕量級的 Python 3.10 映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的系統工具
# libgl1-mesa-glx 是為了支援一些圖形處理 (有時候 map libraries 會需要)
# git 是為了以防需要從 GitHub 安裝特定的套件
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 套件
# 先做這一步是為了利用 Docker Cache，加速之後的建置過程
COPY requirements.txt .

# 升級 pip 並安裝套件
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製其餘的專案程式碼到容器內
COPY . .

# 設定環境變數 (讓 Solara 知道這是在生產環境)
ENV SOLARA_MODE=production

# 開放 Solara 的預設埠號
EXPOSE 8765

# 啟動指令：執行 Solara
# --host=0.0.0.0 讓外部可以連線
# --port=8765 指定埠號
CMD ["solara", "run", "app.py", "--host=0.0.0.0", "--port=8765"]