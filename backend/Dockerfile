FROM python:3.12-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    proj-bin \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG INSTALL_ML=false
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN if [ "$INSTALL_ML" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]