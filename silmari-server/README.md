# 북실북실 같이 읽기 서버 쪽

- `social.src.js` → `npx esbuild social.src.js --bundle --minify --format=iife --target=es2019 --outfile=../silmari/social.js` (firebase@12 필요)
- `firestore.rules` → Firebase 콘솔 Firestore 규칙에 그대로 붙여 넣기
- `rules.test.mjs` → 에뮬레이터 켜고 `node rules.test.mjs` 로 규칙 시험

운영: 글 지우기는 Firestore 콘솔 `posts`에서, 글쓰기 막기는 `bans/{uid}` 문서 하나 만들기.
