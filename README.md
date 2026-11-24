# chaektarae-books

책타래 앱이 읽어 가는 파일.

- `books.json` — 유저와 책 (`{"users":[...],"books":[...]}`). 조금씩 들어오는 책은 `"more":true`, `"total":전체 조각 수`를 갖는다.
- `posts.json` — 유저 트윗 (`{"posts":[{"id","u","x","ts"}]}`)
- `catalog.json` — 서점 목록. 저작권 끝난 책의 제목·작가·소개·원문 주소(`src`). 못 만드는 책은 `"no":"이유"`.
- `src/<id>.json` — 책 전체를 미리 잘라 둔 원문 조각. 앱은 안 읽는다. 다음 부분을 이어 붙일 때 쓴다.
- `tools/` — 원문 뽑기(`ptext.py`), 조각 나누기(`chunk.py`), 검사(`check.py`), 올리기(`put.py`).

책 신청은 이 저장소 이슈로 들어온다. 제목 `신청 <id>`는 새 책, `이어서 <id>`는 다음 부분.
