FROM python:3.10.4-alpine as builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY services/api/requirements_common.txt \
     services/api/requirements_worker.txt \
     ./
RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements_common.txt && \
    pip install --no-cache-dir -r requirements_worker.txt

FROM python:3.10.4-alpine
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY services/api/common ./common
COPY services/api/worker ./worker
COPY services/api/run_worker.py ./
