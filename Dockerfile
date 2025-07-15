FROM python:3.12.11-slim-bookworm

RUN apt-get update; apt-get install -y nano vim htop \
    && pip install uv \
    && mkdir /app

COPY requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r /app/requirements.txt

ENV PYTHONPATH /app
COPY src /app/src
COPY tests /app/tests
RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8000
WORKDIR /app/src
CMD ["uvicorn", "src.api:app", "--proxy-headers", "--host", "0.0.0.0"]
