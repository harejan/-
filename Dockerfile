FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# 1. 建立 init 檔案 (這是我們上一招，繼續保留)
RUN touch pages/__init__.py

# 2. 建立使用者
RUN useradd -m -u 1000 user

# ⭐⭐⭐ 關鍵修改在這裡！⭐⭐⭐
# 把 /code 資料夾的所有權限，從 root 轉移給 user
# 這樣 user 才能寫入臨時檔，不會因為權限不足而崩潰
RUN chown -R user:user /code

# 切換身分
USER user

# 設定環境變數
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    GRADIO_ALLOW_FLAGGING=never \
    GRADIO_NUM_PORTS=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_THEME=huggingface \
    SYSTEM=spaces \
    # 關閉 Log 裡的 assets proxy 警告
    SOLARA_ASSETS_PROXY=False

# 啟動指令 (指向 pages 資料夾)
CMD ["solara", "run", "pages", "--host=0.0.0.0", "--port=7860"]