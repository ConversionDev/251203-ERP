FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 공통 모듈 복사 (빌드 컨텍스트가 ai.kanggyeonggu.store인 경우)
COPY common ./common

# requirements.txt 복사 및 설치
COPY mlservice/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 한글 폰트 설치 (나눔고딕) 및 Java JDK 설치 (KoNLPy용)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-nanum \
    fontconfig \
    default-jdk \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# 앱 복사 (train.csv 포함)
COPY mlservice/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9002"]

