FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 시스템 패키지 설치 (Selenium용)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 공통 모듈 복사
COPY common ./common

# requirements.txt 복사 및 설치
COPY crawlerservice/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY crawlerservice/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9001"]
