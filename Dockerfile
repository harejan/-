FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# ⭐⭐⭐ 關鍵修改 1：強迫系統幫我們產生 __init__.py ⭐⭐⭐
# 這樣就算 Git 沒有上傳這個檔案，Docker 也會自己做一個出來！
RUN touch pages/__init__.py

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

ENV PYTHONUNBUFFERED=1 \
    GRADIO_ALLOW_FLAGGING=never \
    GRADIO_NUM_PORTS=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_THEME=huggingface \
    SYSTEM=spaces

CMD ["solara", "run", "pages", "--host=0.0.0.0", "--port=7860"]