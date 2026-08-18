# syntax=docker/dockerfile:1
# ---- Backend: FastAPI served by uvicorn ----
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Dependencies first, so this layer is cached until requirements.txt changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 2) Application code, config and data. Paths are resolved from the package
#    root (app/settings.py), not the CWD, so this layout is what matters.
COPY app/ ./app/
COPY config/ ./config/
COPY data/ ./data/
COPY docs/decision-trees/ ./docs/decision-trees/

RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=40s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# Single worker on purpose: app/api/sessions.py is an in-process dict, so
# multiple workers would split sessions. See DEPLOYMENT.md "Scaling".
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
