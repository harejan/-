FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

RUN useradd -m -u 1000 user

# ✅ 權限這行一定要有
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

# ✅ 指向資料夾
CMD ["solara", "run", "pages", "--host=0.0.0.0", "--port=7860"]