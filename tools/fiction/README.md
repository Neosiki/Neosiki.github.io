# 문명 연작 게시 파이프라인 (한국어 / English)

전 12편 예정. 편이 늘어도 HTML을 손으로 만들지 않는다.
`series.json`(메타데이터) + `_manuscripts/*.md`(본문) + `assets/fiction/<slug>/`(이미지)를 넣고
빌더를 한 번 돌리면 **한국어판과 영문판이 함께** 다시 생성된다.

```
tools/fiction/
  series.json          ← 단일 진실 원천. 편별 메타데이터와 en 블록
  build_fiction.py     ← 빌더
fiction/
  _manuscripts/<slug>.md      ← 한국어 본문
  _manuscripts/<slug>.en.md   ← 영문 본문
  <slug>.html                 ← 생성물. 직접 고치지 말 것
fiction.html                  ← 생성물 (한국어 허브)
en/fiction.html               ← 생성물 (영문 허브)
en/fiction/<slug>.html        ← 생성물 (영문 편별)
assets/fiction/<slug>/        ← 1600px JPEG. 한·영 공용
```

두 언어는 `<link rel="alternate" hreflang>`과 `canonical`로 상호 연결된다.
검색·AI 인용에서 언어별 URL이 각자의 주제 신호를 갖도록 하기 위한 구조이므로,
한 페이지에 두 언어를 넣는 방식으로 되돌리지 않는다.

## 새 편 추가 (예: 제5편)

1. **이미지** — `assets/fiction/05-<slug>/`에 1600px JPEG로 넣는다.
   장면 이미지는 읽을 수 있는 문자가 없어 한·영이 공용한다. 표지·엔딩만 언어별로 둔다
   (영문은 `00-en-cover.jpg`, `99-en-ending.jpg` 같은 이름을 쓰고 `-en-` 이 들어가면 갤러리에서 제외된다).
   ```bash
   python3 -c "
   from PIL import Image; import glob,os
   for f in glob.glob('원본폴더/*.png'):
       im=Image.open(f).convert('RGB')
       if im.width>1600: im=im.resize((1600,round(im.height*1600/im.width)),Image.LANCZOS)
       im.save('assets/fiction/05-<slug>/'+os.path.basename(f)[:-4]+'.jpg','JPEG',quality=82,optimize=True,progressive=True)"
   ```
   표지는 **16:9로 준비한다.** 2:3 세로 포스터는 카드와 히어로에서 제목이 잘린다.
2. **본문** — `fiction/_manuscripts/05-<slug>.md`(한국어), `05-<slug>.en.md`(영문).
   앞머리(표지 이미지·제목·소개·영상 링크)와 끝의 제작 크레딧·엔딩 이미지는 넣지 않는다.
   `## 一. …` 또는 `## I. …`처럼 본문 첫 절부터 시작한다.
   본문 이미지는 `![설명](./assets/파일명)` 형태면 되고, 빌더가 언어별 상대경로로 자동 교체한다.
3. **메타데이터** — `series.json`의 `works` 배열에 항목을 추가한다.
   공통 키(제목·러닝타임·표지·영상)를 쓰고, 영문에서 달라지는 값만 `en` 블록에 넣으면 된다.
   `en`에 없는 키는 공통값으로 되돌아간다.
4. **빌드**
   ```bash
   python3 tools/fiction/build_fiction.py
   ```
5. **메인 페이지** — `index.html`의 `id="fiction"` 섹션에 카드 한 장을 추가한다. 이 부분만 수동이다.

## 영상 링크

영상 파일은 저장소에 넣지 않는다. GitHub는 파일 하나가 100MB를 넘으면 푸시를 거부하고,
Pages 사이트 권장 한도는 1GB다. 1~4편 한국어 최종본만 합쳐 899MB다.

영상은 네이버에 올리고 주소를 `series.json`의 `video.naverUrl`(한국어),
`en.video.naverUrl`(영문)에 넣은 뒤 다시 빌드한다. 비어 있으면 버튼이 `링크 준비 중`으로 비활성 표시된다.
소설 원문을 올린 네이버 블로그 주소는 `blogUrl`에 넣으면 별도 버튼이 생긴다.

## 본문이 아직 없을 때

`manuscriptKo` 또는 `manuscriptEn`을 `null`로 두면 본문 자리에 안내 문구가 들어가고,
영상·시놉시스·스틸 갤러리는 정상 표시된다. 본문에 이미지가 있으면 갤러리는 중복이므로 자동 생략된다.

## 의존성

`markdown` (`pip install markdown`), 이미지 변환에는 `Pillow`.
