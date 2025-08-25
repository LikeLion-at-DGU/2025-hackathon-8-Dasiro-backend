# 다시로 Dasiro 🕳️🚶‍♀️

> 싱크홀 위험을 예측하고 안전한 경로를 제공하는 도시 안전 서비스

2025 동국대학교 멋쟁이사자처럼 중앙해커톤 '땅속추적단' 백엔드 레포지토리입니다.

## 📋 서비스 개요

다시로는 **싱크홀 위험 예측 및 안전 경로 안내 서비스**입니다. AI를 활용한 위험도 분석과 실시간 사고 정보를 통해 시민들에게 안전한 이동 경로를 제공하며, 시민 제보 시스템을 통해 지속적으로 안전 정보를 업데이트합니다.

<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/66494d48-a151-4557-b1b5-59a04ab446cd" />

### 주요 가치
- 🛡️ **예방적 안전**: 사고 발생 전 위험 구역 회피
- 📍 **실시간 정보**: 최신 사고 정보와 복구 현황 제공  
- 🤝 **시민 참여**: 시민 제보를 통한 집단 지성 활용
- 🎯 **개인화**: 개인별 이동 패턴과 선호에 맞춤화된 서비스

## 🔧 주요 기술 스택

| 분야 | 기술 스택 |
|------|----------|
| **Backend** | Python 3.x, Django 5.2.4, Django REST Framework |
| **Database** | SQLite3 (개발용), PostgreSQL (운영 고려) |
| **Storage** | AWS S3 (파일 업로드) |
| **External APIs** | Kakao Map API, OpenRouteService, OpenAI GPT API |
| **Deploy & Infrastructure** | AWS EC2, Gunicorn, Nginx |
| **CI/CD** | GitHub Actions |
| **기타** | django-cors-headers, django-storages, requests |

## 🚀 주요 기능

### 1. 지역별 위험도 분석 (`/api/v1/districts/`)
- **동별 위험도 등급**: G1(매우 위험) ~ G5(안전) 5단계 분류
- **세부 위험 요소**: 지반안정성, 지하수영향, 지하구조물밀집도, 노후건물분포, 사고이력
- **구별 통합 위험도**: 시군구 단위 위험도 집계
- **AI 기반 분석**: GPT를 활용한 지역별 위험도 해석

### 2. 싱크홀 사고 관리 (`/api/v1/incidents/`)
- **실시간 사고 정보**: 발생 위치, 원인, 복구 상태 관리
- **복구 현황 추적**: 복구중/임시복구/복구완료 상태별 관리
- **지도 기반 시각화**: 위경도 좌표 기반 사고 위치 표시
- **사고 이미지 관리**: AWS S3 연동 이미지 업로드

### 3. 안전 경로 안내 (`/api/v1/proxy/`)
- **다중 경로 옵션**: 최단거리, 안전우선, 대중교통 등
- **위험구역 회피**: 사고 발생지와 고위험 구역 우회
- **실시간 경로 업데이트**: 새로운 사고 정보 반영

### 4. 시민 제보 시스템 (`/api/v1/reports/`)
- **다중 이미지 업로드**: AWS S3 기반 이미지 저장
- **AI 위험도 평가**: 제보 내용 기반 0-100점 위험점수 산출
- **챗봇 인터페이스**: GPT 연동 대화형 제보 처리
- **제보 상태 관리**: 접수됨/분석중/분석완료

### 5. 주변 편의시설 (`/api/v1/places/`)
- **카테고리별 검색**: 음식점/카페/편의점
- **Kakao API 연동**: 실시간 장소 정보 동기화
- **안전경로 연계**: 목적지까지 안전한 경로 제공

### 6. 리워드 시스템 (`/api/v1/coupons/`)
- **제보 인센티브**: 유효한 제보에 대한 쿠폰 지급
- **쿠폰 관리**: 발급/사용/만료 상태 관리

## 🏗️ 시스템 아키텍처

```
Frontend (React) ← CORS → Backend (Django)
                              ↓
                         [Django Apps]
                         ├── districts (위험도 분석)
                         ├── incidents (사고 관리) 
                         ├── routes (경로 안내)
                         ├── reports (시민 제보)
                         ├── places (편의시설)
                         └── coupons (리워드)
                              ↓
                         [External APIs]
                         ├── Kakao Map API
                         ├── OpenRouteService
                         ├── OpenAI GPT API
                         └── AWS S3
```

## 💡 구현 특징

### 1. 모듈화된 Django 앱 구조
각 기능을 독립적인 앱으로 분리하여 유지보수성과 확장성을 확보했습니다.

### 2. 외부 API 통합
- **Kakao Map API**: 장소 검색 및 좌표 변환
- **OpenRouteService**: 도보 경로 최적화
- **OpenAI GPT**: 제보 분석 및 위험도 해석

### 3. 파일 업로드 최적화
AWS S3를 활용하여 이미지 업로드 성능을 최적화하고 서버 부하를 분산했습니다.

### 4. 데이터 모델링
- 지역(District) - 위험도(DistrictMetric) 관계 설계
- 사고(RecoveryIncident) - 지역(District) 연관 관계
- 제보(CitizenReport) - 이미지(CitizenReportImage) 1:N 관계

## 🛠️ 로컬 실행 방법

### 1. 저장소 클론
```bash
git clone https://github.com/LikeLion-at-DGU/2025-hackathon-8-Dasiro-backend.git
cd 2025-hackathon-8-Dasiro-backend
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일을 생성하고 다음 키들을 설정하세요:
```bash
SECRET_KEY=your_django_secret_key
DEBUG=True
KAKAO_REST_KEY=your_kakao_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_s3_bucket_name
OPENAI_API_KEY=your_openai_api_key
ORS_API_KEY=your_openrouteservice_key
EMAIL_HOST_USER=your_gmail_address
EMAIL_HOST_PASSWORD=your_app_password
AI_API_KEY=your_additional_ai_key
```

### 5. 데이터베이스 마이그레이션
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 관리자 계정 생성
```bash
python manage.py createsuperuser
```

### 7. 개발 서버 실행
```bash
python manage.py runserver
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 8. 초기 데이터 로드 (선택사항)
```bash
# 지역 데이터 로드
python manage.py import_districts

# 사고 데이터 로드  
python manage.py load_incidents

# 장소 데이터 동기화
python manage.py sync_places
```

## 📁 프로젝트 구조

```
📦 2025-hackathon-8-Dasiro-backend
├── 📂 districts/          # 지역별 위험도 분석
├── 📂 incidents/          # 싱크홀 사고 관리
├── 📂 routes/             # 경로 안내 프록시
├── 📂 reports/            # 시민 제보 시스템
├── 📂 places/             # 주변 편의시설
├── 📂 coupons/            # 리워드 관리
├── 📂 project/            # Django 프로젝트 설정
├── 📂 data/               # 초기 데이터 파일
├── 📂 static/             # 정적 파일
├── 📄 requirements.txt    # Python 의존성
└── 📄 manage.py          # Django 관리 스크립트
```

## 📄 API 문서

개발 서버 실행 후 다음 엔드포인트에서 API를 테스트할 수 있습니다:

- **지역 위험도**: `GET /api/v1/districts/`
- **사고 정보**: `GET /api/v1/incidents/`  
- **경로 안내**: `POST /api/v1/proxy/`
- **시민 제보**: `POST /api/v1/reports/`
- **편의시설**: `GET /api/v1/places/`
- **쿠폰 관리**: `GET /api/v1/coupons/`

## 🔒 보안 고려사항

- 환경변수를 통한 민감 정보 관리
- CORS 설정으로 허용된 도메인만 접근 가능
- AWS S3 ACL 비활성화로 보안 강화
- Django의 기본 보안 미들웨어 활용

---

> 지속가능한 백엔드 구조와 사용자 경험, 실용적인 배포 흐름을 고려하여 개발된 프로젝트입니다.
