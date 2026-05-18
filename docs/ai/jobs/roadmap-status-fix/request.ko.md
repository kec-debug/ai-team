# 작업 ID
roadmap-status-fix

# 작업명
마스터 로드맵 기준으로 작업 상태 재정렬

지금까지 mvp 번호가 너무 많이 늘어났고, 같은 작업을 반복하고 있다.

앞으로는 새 mvp 번호를 계속 만들지 말고, `docs/ai/MASTER_TRADING_ROADMAP.md` 기준으로 현재 상태를 정리한다.

## 목표

1. 지금까지 진행한 mvp-001 ~ mvp-023 작업을 마스터 로드맵 기준으로 재분류.
2. 완료 / 진행 중 / BLOCKED / 중복을 명확히 구분.
3. 앞으로 새 mvp 번호를 만들지 말고 기존 Phase 안에서 진행.
4. Codex 구현 지시를 만들기 전에 해당 작업이 이미 완료됐는지 먼저 확인.

## mvp-023 상태 재분류

- 상태: `BLOCKED-BY-DOCS`
- 이유: KIS 시세 endpoint / TR ID / request fields / response fields 공식값 부족
- 다음 조치: 공식 KIS 시세 문서값을 채운 뒤 같은 mvp-023 범위에서 재개

## 진행 원칙

- KIS 공식 문서값 없는 상태에서 KIS HTTP 구현 작업 재생산 금지.
- 공식값 없으면 새 mvp 번호로 넘기지 말고 BLOCKED 표시.
- mock/synthetic feed 작업은 "KIS 실제 HTTP 대체"가 아니라 "로컬 검증용"으로 별도 표시.
- 동일 작업을 새 번호로 반복 금지.
- 새 mvp 생성 전 반드시 `MASTER_TRADING_ROADMAP.md`와 기존 jobs 확인.

## 산출물

1. `docs/ai/ROADMAP_STATUS.md` — 전체 진행 현황 + 다음 단 하나의 작업.
2. `docs/ai/MASTER_TRADING_ROADMAP.md` 업데이트 — mvp-023 BLOCKED 표시 + 중복 방지 규칙.
3. `docs/ai/jobs/roadmap-status-fix/plan.md` — 정리 내용.

## Codex 구현 지시는 만들지 않는다

이번 작업은 코드 구현이 아니다. Claude가 로드맵과 상태만 정리.
