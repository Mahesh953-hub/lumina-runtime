FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LUMINA_OUTPUT_DIR=/data/output
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN mkdir -p /data/output && useradd -r -u 10001 lumina && chown -R lumina /data/output
USER lumina
EXPOSE 8000
CMD ["lumina", "serve", "--host", "0.0.0.0", "--port", "8000"]
