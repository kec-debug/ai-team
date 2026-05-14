# 작업 요청

GUI 서버 재시작 버튼이 현재 GUI를 꺼버리기만 하고 새로 켜지지 않는 문제를 수정한다.

## 현재 문제

컨트롤센터의 "GUI 서버 재시작" 버튼을 누르면 실제로는 현재 Node 서버가 종료되고, ai-gui tmux 세션에서 새 GUI 서버가 안정적으로 다시 올라오지 않는 것 같다.

증상:
- 버튼 클릭 후 GUI 접속이 끊긴다.
- http://10.10.0.104:3100 접속이 안 된다.
- 결국 SSH/PuTTY에서 수동으로 npm start를 다시 해야 한다.
- 사용자는 GUI에서 재시작 버튼을 눌렀는데 "재시작"이 아니라 "종료"처럼 느낀다.

## 목표

GUI 서버 재시작 버튼을 안정적으로 수정한다.

원하는 동작:
1. 사용자가 GUI에서 "GUI 서버 재시작" 버튼 클릭
2. 서버가 즉시 JSON 응답을 반환
3. GUI는 "GUI 서버를 재시작합니다. 3~5초 뒤 새로고침하세요."라고 표시
4. 서버는 별도 detached shell 또는 tmux 명령으로 재시작 작업을 예약
5. 기존 3100 포트의 node 프로세스를 종료
6. 기존 ai-gui tmux 세션을 정리
7. 새 ai-gui tmux 세션을 생성
8. /root/ai-dev-center/projects/ai-team/web 에서 HOST=0.0.0.0 PORT=3100 npm start 실행
9. 3100 포트가 다시 열린다

## 요구사항

1. server.js의 POST /api/service/restart-gui 를 안정화한다.

현재 Node 프로세스가 자기 자신을 죽이기 전에 반드시 HTTP 응답을 반환해야 한다.
재시작은 detached shell에서 수행해야 한다.

2. 재시작 명령은 안전하게 고정한다.

허용되는 동작:
- tmux kill-session -t ai-gui
- fuser -k 3100/tcp 또는 lsof 기반 3100 포트 정리
- tmux new-session -d -s ai-gui -c /root/ai-dev-center/projects/ai-team/web
- HOST=0.0.0.0 PORT=3100 npm start

금지:
- 임의 shell command 입력
- 사용자 입력으로 실행 명령 만들기
- rm -rf
- sudo
- git push
- gh pr merge
- 배포 자동화
- .env, token, secret, API key 읽기/출력

3. 재시작 로그를 남긴다.

로그 파일:
- /tmp/ai-team-gui-restart.log

로그에는 다음을 남긴다:
- restart requested time
- killed old process result
- tmux session creation result
- npm start output

4. GUI 프론트엔드 수정

"GUI 서버 재시작" 버튼 클릭 후:
- 즉시 안내 메시지 표시
- "재시작 요청 완료. 3~5초 뒤 브라우저를 새로고침하세요." 표시
- 자동으로 5초 뒤 /api/status를 재시도
- 실패하면 "아직 서버가 올라오지 않았습니다. 잠시 후 새로고침하거나 수동 복구 명령을 실행하세요." 표시

5. README.md 업데이트

GUI 서버 수동 복구 명령을 추가한다.

수동 복구 명령:
fuser -k 3100/tcp 2>/dev/null || true
tmux kill-session -t ai-gui 2>/dev/null || true
tmux new-session -d -s ai-gui -c /root/ai-dev-center/projects/ai-team/web "env HOST=0.0.0.0 PORT=3100 npm start"

6. 완료 기준

- GUI 서버 재시작 버튼 클릭 시 현재 요청은 JSON으로 정상 응답한다.
- 몇 초 뒤 http://10.10.0.104:3100 접속이 다시 가능하다.
- ai-gui tmux 세션이 존재한다.
- 3100 포트가 node 프로세스로 LISTEN 상태다.
- /api/status가 정상 JSON을 반환한다.
- 재시작 로그가 /tmp/ai-team-gui-restart.log에 남는다.
- 자동 commit, push, merge는 하지 않는다.
