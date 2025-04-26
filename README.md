# QcctvKor - 대한민국 교통 CCTV 뷰어

![QcctvKor](QcctvKor/resources/icon.png)

QGIS용 대한민국 교통 CCTV 실시간 스트리밍 플러그인

## 소개

QcctvKor는 QGIS에서 대한민국 도로의 교통 CCTV를 실시간으로 모니터링할 수 있는 플러그인입니다. ITS 국가교통정보센터의 API를 활용하여 전국 주요 도로의 CCTV 영상을 QGIS 환경에서 쉽게 확인할 수 있습니다.

주요 특징:
- 전국 교통 CCTV 위치 표시
- 실시간 CCTV 영상 스트리밍
- 다양한 필터링 옵션
- 화면 캡처 기능
- 데이터 내보내기 및 보고서 생성

## 설치 방법

### 요구사항
- QGIS 3.36 이상
- OpenCV (영상 처리)
- PyQt5 (GUI 컴포넌트)
- ITS API 키 (http://openapi.its.go.kr 에서 발급)

### 설치 과정
1. QGIS 플러그인 관리자에서 "QcctvKor" 검색
2. 플러그인 설치
3. QGIS 재시작
4. 플러그인 메뉴에서 "QcctvKor > ITS API 키 설정"을 통해 API 키 입력

## 사용 방법

### API 키 설정
1. QGIS 메뉴에서 "플러그인 > QcctvKor > ITS API 키 설정" 클릭
2. 발급받은 API 키 입력
3. "저장" 버튼 클릭

### CCTV 표시
1. QGIS 메뉴에서 "플러그인 > QcctvKor > QcctvKor" 클릭
2. 지도에 CCTV 위치가 표시됨
3. CCTV 포인트를 클릭하면 실시간 영상 표시

### 필터링
- 지역별 필터 (서울, 경기, 인천, 부산 등)
- 도로 유형별 필터 (고속도로, 국도, 시도)
- CCTV 이름 검색 기능

### 영상 캡처
1. CCTV 영상 시청 화면에서 "캡처" 버튼 클릭
2. 저장 위치 선택
3. 현재 프레임이 이미지 파일로 저장됨

## 주요 기능

### 자동 필터
사용자가 정의한 기준에 따라 주기적으로 자동 필터링이 가능합니다.

### 필터 조합
여러 필터 조건을 조합하여 복잡한 검색 조건을 생성할 수 있습니다.

### 필터 추천
사용 패턴을 분석하여 사용자에게 최적화된 필터를 추천합니다.

### 데이터 내보내기
- CSV 파일로 저장
- Shapefile 형식으로 내보내기
- CCTV 데이터 보고서 생성

## 디렉토리 구조

```
QcctvKor/
├── controller/       # 컨트롤러 (MVC 패턴)
│   └── cctv_controller.py
├── model/            # 데이터 모델 (MVC 패턴)
│   ├── cctv_model.py
│   ├── filter_auto.py
│   ├── filter_combine.py
│   ├── filter_recommend.py
│   ├── filter_settings.py
│   └── filter_share.py
├── view/             # 뷰 컴포넌트 (MVC 패턴)
│   ├── api_key_dialog.py
│   ├── auto_filter_dialog.py
│   ├── cctv_dialog.py
│   ├── combine_filter_dialog.py
│   ├── error_dialog.py
│   ├── filter_dialog.py
│   ├── help_dialog.py
│   ├── recommend_dialog.py
│   └── settings_dialog.py
├── utils/            # 유틸리티 함수
│   ├── config_manager.py
│   ├── exceptions.py
│   └── logger.py
├── resources/        # 리소스 파일
│   ├── cctv_icon.svg
│   └── manual.html
├── __init__.py       # 플러그인 초기화
└── metadata.txt      # 플러그인 메타데이터
```

## 개발 정보

- **언어**: Python
- **프레임워크**: QGIS Python API, PyQt5
- **아키텍처**: MVC (Model-View-Controller) 패턴
- **라이선스**: MIT

## 문제 해결

### 자주 발생하는 문제

1. **영상이 표시되지 않는 경우**
   - 네트워크 연결 확인
   - API 키 유효성 확인
   - CCTV 정비/점검 여부 확인

2. **필터링이 작동하지 않는 경우**
   - 검색어 철자 확인
   - 플러그인 재시작 시도

3. **API 키 오류 발생 시**
   - API 키가 올바르게 입력되었는지 확인
   - ITS 오픈 API 사이트에서 키의 유효성 확인

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 브랜치를 생성합니다: `git checkout -b my-feature-branch`
3. 변경 사항을 커밋합니다: `git commit -am 'Add a new feature'`
4. 브랜치를 푸시합니다: `git push origin my-feature-branch`
5. Pull Request를 제출합니다.

## 연락처

- **개발자**: Jordan Moon (GISPE)
- **GitHub**: https://github.com/kekero1004/QcctvKor
- **이메일**: 저장소에서 확인 
