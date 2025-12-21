FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# ❌ 刪除這一行！不要建立 __init__.py，讓 Solara 自動掃描檔案！
# RUN touch pages/__init__.py  <-- 這行請刪掉，或者像這樣註解掉

# 建立使用者
RUN useradd -m -u 1000 user

# ✅ 權限修正 (這行一定要保留！)
RUN chown -R user:user /code

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    GRADIO_ALLOW_FLAGGING=never \
    GRADIO_NUM_PORTS=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_THEME=huggingface \
    SYSTEM=spaces \
    SOLARA_ASSETS_PROXY=False

# ✅ 指向資料夾 (這會讓側邊欄出現)
CMD ["solara", "run", "pages", "--host=0.0.0.0", "--port=7860"]