# 🎯 Kanggyeonggu.store 프로젝트 전략 문서

## 📋 프로젝트 개요

**Kanggyeonggu.store**는 B2B ERP 시스템을 위한 마이크로서비스 아키텍처(MSA) 기반 플랫폼입니다.

---

## 🏗️ 아키텍처 구조

### **도메인별 역할 분리**

```
kanggyeonggu.store/
├── api.kanggyeonggu.store/      # API Gateway (Spring Cloud Gateway)
├── core.kanggyeonggu.store/      # 백엔드 코어 서비스 (Spring Boot)
├── ai.kanggyeonggu.store/       # AI 서비스 (FastAPI)
├── erp.kanggyeonggu.store/       # ERP 서비스 (FastAPI)
├── www.kanggyeonggu.store/       # 웹 프론트엔드 (Next.js)
└── app.kanggyeonggu.store/       # 모바일 앱 (Flutter, 추후)
```

---

## 🎯 도메인별 전략

### **1. api.kanggyeonggu.store (Gateway)**

**역할**: 모든 요청의 단일 진입점

**기술 스택**:
- Spring Cloud Gateway
- Java 21
- Spring Boot 3.5.7

**주요 기능**:
- ✅ 라우팅: `/auth/**`, `/api/users/**`, `/oauth2/**`, `/ai/**`
- ✅ CORS 설정
- ✅ JWT 검증 (추후)
- ✅ 로드 밸런싱

**포트**: `8080`

**라우팅 규칙**:
```yaml
/auth/**          → oauthservice:8081
/oauth2/**        → oauthservice:8081 (RewritePath)
/api/users/**     → user-service:8082
/ai/crawler/**    → crawler-service:9001
/ai/chatbot/**    → chatbot-service:9002
```

---

### **2. core.kanggyeonggu.store (백엔드 코어)**

**역할**: 인증 및 사용자 관리

#### **2.1 oauthservice**

**기능**:
- ✅ 소셜 로그인 (Kakao, Naver, Google)
- ✅ JWT 토큰 발급
- ✅ 사용자 정보 DB 저장 (Neon DB)
- ✅ 사용자 정보 Redis 캐싱 (Upstash)

**데이터 저장**:
- **Neon DB**: 사용자 프로필 영구 저장
- **Upstash Redis**: 사용자 정보 캐싱 (24시간 TTL)

**수집 데이터**:
- Provider ID (kakao/naver/google)
- Nickname
- Profile Image URL
- ❌ Email (제외)

**포트**: `8081`

#### **2.2 userservice**

**기능**:
- 사용자 정보 관리
- 사용자 프로필 CRUD

**포트**: `8082`

---

### **3. ai.kanggyeonggu.store (AI 서비스)**

**역할**: 머신러닝 및 AI 기능 제공

**기술 스택**:
- FastAPI
- Python 3.11
- Pandas, NumPy, Scikit-learn
- HuggingFace Datasets

#### **3.1 mlservice** ⭐

**기능**:
- ✅ **Customer 분석**: B2B 고객 이탈 예측, 통계 분석
- ✅ **Titanic 분석**: 타이타닉 데이터셋 분석 및 ML

**Customer API**:
- 고객 목록 조회 (간단/전체)
- 고객 상세 조회
- 필터링 (상태/업종/이탈 위험도)
- 통계 분석 (전체/업종별)
- **이탈 예측 ML** (`/customer/ml/predict/{customer_id}`)
- 모델 학습 (`/customer/ml/train`)

**Titanic API**:
- 승객 데이터 조회
- 생존율 통계
- 데이터 분석

**포트**: `9002`

**독립 실행**:
```bash
cd ai.kanggyeonggu.store/mlservice
docker compose up -d
```

**데이터**:
- `customer_data.csv`: 30개 기업 고객 데이터
- `train.csv`: 891명 타이타닉 승객 데이터
- `test.csv`: 418명 타이타닉 승객 데이터

#### **3.2 chatbotservice**

**기능**: 챗봇 서비스

**포트**: `9003`

#### **3.3 crawlerservice**

**기능**: 웹 크롤링 서비스

**포트**: `9001`

#### **3.4 authservice**

**기능**: AI 서비스 인증

---

### **4. erp.kanggyeonggu.store (ERP 서비스)**

**역할**: B2B ERP 비즈니스 로직

**서비스 목록**:
- `customerservice`: 고객 관리
- `dashboardservice`: 대시보드
- `orderservice`: 주문 관리
- `financeservice`: 재무 관리
- `reportservice`: 리포트
- `settingservice`: 설정
- `stockservice`: 재고 관리

**기술 스택**:
- FastAPI
- Python 3.11

---

### **5. www.kanggyeonggu.store (웹 프론트엔드)**

**역할**: 사용자 인터페이스

**기술 스택**:
- Next.js
- TypeScript
- React

**주요 화면**:
- 로그인 페이지
- 대시보드
- 고객 관리
- 주문 관리
- 재무 관리
- 재고 관리
- 리포트
- 설정

---

### **6. app.kanggyeonggu.store (모바일 앱)**

**역할**: 모바일 애플리케이션

**기술 스택**:
- Flutter (추후 구현)

**상태**: 준비 중

---

## 🗄️ 데이터베이스 전략

### **Neon DB (PostgreSQL)**

**용도**: 영구 데이터 저장

**저장 데이터**:
- 사용자 프로필 (users 테이블)
- 고객 정보
- 주문 정보
- 재무 정보
- 기타 비즈니스 데이터

**연결 정보**:
- Development: Preview Branch
- Production: Main Branch

### **Upstash Redis**

**용도**: 캐싱 및 세션 관리

**저장 데이터**:
- 사용자 정보 캐싱 (24시간 TTL)
- JWT 토큰
- 세션 데이터

**연결 방식**:
- SSL/TLS 지원
- REST API 지원

---

## 🔐 인증 전략

### **소셜 로그인 플로우**

```
1. 프론트엔드 → POST /auth/{provider}/login
2. Gateway → OAuth Service
3. OAuth Service → 소셜 로그인 URL 반환
4. 사용자 → 소셜 로그인 인증
5. 소셜 플랫폼 → GET /oauth2/{provider}/callback?code=xxx
6. Gateway → OAuth Service (RewritePath)
7. OAuth Service:
   - 액세스 토큰 받기
   - 사용자 정보 조회
   - Neon DB에 저장 (upsert)
   - Upstash Redis에 캐싱
   - JWT 토큰 생성
8. 프론트엔드로 리다이렉트 (JWT 포함)
```

### **지원 플랫폼**

- ✅ **Kakao**: `/auth/kakao/login`, `/oauth2/kakao/callback`
- ✅ **Naver**: `/auth/naver/login`, `/oauth2/naver/callback`
- ✅ **Google**: `/auth/google/login`, `/oauth2/google/callback`

### **JWT 토큰**

- **Secret**: 환경 변수에서 관리
- **Expiration**: 24시간 (86400000ms)
- **Payload**: `userId`, `nickname`

---

## 📊 ML 전략

### **Customer 이탈 예측**

**목표**: 고객 이탈 위험도 예측

**데이터**:
- 30개 기업 고객
- 22개 특성 (총 주문, 매출, 연체 횟수, 성장률 등)
- 라벨: `churn_risk` (0=안전, 1=위험)

**모델**:
- RandomForestClassifier
- 규칙 기반 예측 (임시)

**API**:
- `GET /customer/ml/predict/{customer_id}`: 이탈 확률 예측
- `POST /customer/ml/train`: 모델 학습

**예측 결과**:
```json
{
  "customer_id": "CUST-005",
  "churn_probability": 0.9,
  "risk_level": "high",
  "key_factors": ["마지막 주문 후 120일 경과", "연체 5회 발생"],
  "recommendations": ["🚨 즉시 담당자 미팅", "💰 특별 할인 제안"]
}
```

### **Titanic 생존 예측**

**목표**: 승객 생존 여부 예측

**데이터**:
- 891명 학습 데이터
- 418명 테스트 데이터

**상태**: 분석 및 조회 기능 구현 완료

---

## 🚀 배포 전략

### **MSA 독립 실행**

각 서비스는 독립적으로 실행 가능:

```bash
# MLService만 실행
cd ai.kanggyeonggu.store/mlservice
docker compose up -d

# AI 서비스 전체 실행
cd ai.kanggyeonggu.store
docker compose up -d

# 전체 스택 실행
docker compose up -d
```

### **Docker Compose 구조**

1. **루트 `docker-compose.yaml`**: 전체 통합 실행
2. **`ai.kanggyeonggu.store/docker-compose.yaml`**: AI 서비스만
3. **`ai.kanggyeonggu.store/mlservice/docker-compose.yaml`**: MLService만

---

## 🔄 데이터 흐름

### **소셜 로그인 데이터 흐름**

```
사용자 로그인
    ↓
OAuth Service
    ↓
[Neon DB] 사용자 저장/업데이트
    ↓
[Upstash Redis] 사용자 캐싱 (24h TTL)
    ↓
JWT 토큰 발급
    ↓
프론트엔드로 리다이렉트
```

### **ML 예측 데이터 흐름**

```
프론트엔드 요청
    ↓
Gateway (/api/ml/**)
    ↓
MLService
    ↓
CSV 데이터 로드
    ↓
모델 예측
    ↓
결과 반환 (이탈 확률, 권장 조치)
```

---

## 📁 파일 구조

### **MLService 구조**

```
mlservice/
├── docker-compose.yaml          # 독립 실행용
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py                  # FastAPI 앱
    ├── config.py
    ├── customer/
    │   ├── customer_data.csv    # 고객 데이터
    │   ├── customer_model.py    # Pydantic 모델 + ML 래퍼
    │   ├── customer_service.py  # 비즈니스 로직
    │   └── router.py            # API 라우터
    └── titanic/
        ├── train.csv            # 학습 데이터
        ├── test.csv             # 테스트 데이터
        ├── titanic_model.py     # Pydantic 모델 + ML 래퍼
        ├── titanic_service.py  # 비즈니스 로직
        └── router.py            # API 라우터
```

---

## 🎯 현재 구현 상태

### **✅ 완료**

- [x] 소셜 로그인 (Kakao, Naver, Google)
- [x] Neon DB 연동
- [x] Upstash Redis 연동
- [x] JWT 토큰 발급
- [x] Gateway 라우팅
- [x] MLService 독립 실행
- [x] Customer 분석 API
- [x] Titanic 분석 API
- [x] 이탈 예측 ML (규칙 기반)
- [x] MSA 구조 정리

### **🚧 진행 중**

- [ ] 실제 ML 모델 학습 및 배포
- [ ] Gateway JWT 검증 미들웨어
- [ ] Frontend API 연동

### **📋 예정**

- [ ] Neon DB에서 실시간 데이터 수집
- [ ] ML 모델 성능 개선
- [ ] ERP 서비스 구현
- [ ] Flutter 모바일 앱 개발

---

## 🔧 환경 변수

### **필수 환경 변수 (.env)**

```env
# Neon DB
NEON_DEV_HOST=ep-delicate-mouse-ad4q7fh3-pooler.c-2.us-east-1.aws.neon.tech
NEON_DEV_PORT=5432
NEON_DEV_DATABASE=neondb
NEON_DEV_USER=neondb_owner
NEON_DEV_PASSWORD=***
NEON_DEV_SSL_MODE=require

# Upstash Redis
UPSTASH_REDIS_HOST=emerging-whippet-43982.upstash.io
UPSTASH_REDIS_PORT=6379
UPSTASH_REDIS_PASSWORD=***
UPSTASH_REDIS_REST_URL=https://emerging-whippet-43982.upstash.io

# OAuth
KAKAO_REST_API_KEY=***
KAKAO_CLIENT_SECRET=***
NAVER_CLIENT_ID=***
NAVER_CLIENT_SECRET=***
GOOGLE_CLIENT_ID=***
GOOGLE_CLIENT_SECRET=***

# JWT
JWT_SECRET=***
JWT_EXPIRATION=86400000
```

---

## 🌐 API 엔드포인트

### **인증**

```
POST   /auth/kakao/login
GET    /oauth2/kakao/callback
POST   /auth/naver/login
GET    /oauth2/naver/callback
POST   /auth/google/login
GET    /oauth2/google/callback
```

### **ML Service (포트 9002)**

```
# Customer
GET    /customer/customers/simple
GET    /customer/customers
GET    /customer/customers/{customer_id}
GET    /customer/statistics/overview
GET    /customer/statistics/industry
GET    /customer/ml/predict/{customer_id}
POST   /customer/ml/train

# Titanic
GET    /titanic/passengers/top10/simple
GET    /titanic/passengers/top10
GET    /titanic/statistics/survival-rate
```

### **문서**

```
GET    /docs              # Swagger UI
GET    /redoc             # ReDoc
GET    /openapi.json      # OpenAPI Spec
```

---

## 🎯 다음 단계

1. **Gateway ML 라우팅 추가**
   ```yaml
   - id: ml-service
     uri: http://mlservice:9002
     predicates:
       - Path=/api/ml/**
     filters:
       - RewritePath=/api/ml/(?<segment>.*), /${segment}
   ```

2. **Frontend 연동**
   - Customer 관리 화면에 ML 예측 결과 표시
   - 이탈 위험 고객 자동 하이라이트

3. **실제 데이터 연동**
   - Neon DB에서 고객 데이터 실시간 수집
   - 주기적으로 CSV 생성 및 모델 재학습

4. **모델 개선**
   - 더 많은 데이터로 학습
   - XGBoost, LightGBM 등 고급 모델 적용
   - 하이퍼파라미터 튜닝

---

## 📝 참고 사항

- 모든 서비스는 독립적으로 실행 가능 (MSA 원칙)
- 각 서비스는 자체 `docker-compose.yaml` 보유
- 환경 변수는 루트 `.env` 파일에서 중앙 관리
- 프로젝트 이름: `kanggyeonggu.store` (Labzang → 변경 완료)

---

**최종 업데이트**: 2025-12-05

