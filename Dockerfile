# 使用輕量級的 Python 3.10 映像檔
FROM python:3.10-slim

WORKDIR /app

# 安裝必要的系統工具
# libgl1 是修正後的正確套件名稱
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 升級 pip 並安裝套件
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製其餘的專案程式碼到容器內的 /app 目錄
COPY . .

# 設定環境變數
ENV SOLARA_MODE=production

# 開放埠號
EXPOSE 8765

CMD ["solara", "run", "00_home.py", "--host=0.0.0.0", "--port=8765"]