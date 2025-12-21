# 使用輕量級的 Python 3.10 映像檔
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的系統工具 (GIS 套件需要)
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

# 複製所有檔案
COPY . .

# 設定環境變數
ENV SOLARA_MODE=production


EXPOSE 7860
CMD ["solara", "run", "./pages", "--host=0.0.0.0", "--port=7860"]