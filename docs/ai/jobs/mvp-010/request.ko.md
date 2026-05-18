# 작업 ID
mvp-010-cleanup

# 작업명
워크트리 GUI dirty 정리 및 커밋 단위 분리

현재 워크트리에 여러 작업 변경사항이 섞여 있다.

특히 아래 파일들이 이전 GUI 작업에서 생긴 dirty 변경으로 보인다.

- web/server.js
- web/public/app.js
- web/public/index.html
- web/public/style.css

지금 KIS / paper-trading 작업을 계속하기 전에,
먼저 현재 변경사항을 정리하고 어떤 파일을 어떤 커밋 단위로 묶어야 하는지 분리해줘.

## 목표

1. 현재 git status를 확인한다.
2. GUI 관련 변경과 paper-trading 관련 변경을 분리한다.
3. docs/ai/jobs 관련 작업 산출물을 분리한다.
4. 어떤 파일을 지금 커밋해도 되는지 목록화한다.
5. 어떤 파일은 아직 커밋하면 안 되는지 목록화한다.
6. 불필요한 변경을 임의로 삭제하지 말고 먼저 분석한다.
7. git add -A는 하지 않는다.
8. commit, push, merge는 하지 않는다.

## 확인할 파일

- web/server.js
- web/public/app.js
- web/public/index.html
- web/public/style.css
- docs/ai/jobs/*
- projects/paper-trading/*
- .gitignore
- README.md

## 결과로 원하는 것

patch.md에 아래를 정리해줘.

1. 현재 변경사항 전체 요약
2. GUI 변경 파일 목록
3. paper-trading 변경 파일 목록
4. docs/jobs 변경 파일 목록
5. 지금 커밋 가능한 파일 목록
6. 커밋하면 안 되는 파일 목록
7. 권장 커밋 순서
8. 다음 작업으로 A/B/C/D 중 무엇을 하면 좋은지

## 금지

- git add -A 하지 마
- commit 하지 마
- push 하지 마
- merge 하지 마
- 파일을 임의로 삭제하지 마
- secrets, .env, auth, payment, production infra, database migrations 건드리지 마

## 추가 조건

- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 분석을 시작해.
- 필요한 경우에만 최소한의 질문을 해.