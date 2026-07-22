#!/usr/bin/env python3
"""
네이버 블로그 SELECTORS 캡처 도구 — 읽기 전용 진단 도구

사람이 이미 로그인해둔 세션(session/naver_state.json)으로 실제 글쓰기 페이지를
열고, 제목 입력란/본문 에디터/임시저장 버튼을 순서대로 클릭하면 클릭한 요소의
CSS 셀렉터를 계산해서 터미널에 출력해준다.

⚠️ 이 스크립트는 아무 것도 자동으로 입력/클릭/제출하지 않는다.
   오직 사람의 클릭을 관찰해서 셀렉터 정보만 출력하는 1회성 보조 도구다.
⚠️ 로그인도 여전히 사람이 capture_session.py로 미리 해둔 세션을 재사용할 뿐,
   이 스크립트가 로그인을 대신하지 않는다.

사용법:
    python capture_selectors.py <blog_id>
    (또는 .env 에 NAVER_BLOG_ID 를 설정해두면 인자 없이 실행 가능)
"""
import json
import os
import sys

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from auto_publish import SESSION_FILE, WRITE_PAGE_URL_TEMPLATE

# ── 브라우저에 주입할 클릭 감지 스크립트 ─────────────────────
# page.add_init_script() 로 등록하면 메인 페이지뿐 아니라 새로 생성/탐색되는
# 모든 iframe 문서에도 스크립트 실행 전 시점에 안정적으로 주입된다.
# 클릭이 발생하면 셀렉터를 계산해서 window.reportSelector() 로 Python에 전달한다.
# 아무 것도 preventDefault/stopPropagation 하지 않으므로 실제 클릭 동작에는
# 영향을 주지 않는다(순수 관찰용).
CLICK_LISTENER_SCRIPT = """
(function () {
  function cssPath(el) {
    if (!el || el.nodeType !== 1) return '(알 수 없음)';
    if (el.id) return '#' + el.id;

    if (el.classList && el.classList.length) {
      var classes = Array.from(el.classList).slice(0, 2).join('.');
      if (classes) return el.tagName.toLowerCase() + '.' + classes;
    }

    // id/class가 없으면 태그명 + nth-of-type 체인으로 부모까지 최대 3단계
    var parts = [];
    var node = el;
    for (var i = 0; i < 3 && node && node.nodeType === 1; i++) {
      var tag = node.tagName.toLowerCase();
      var parent = node.parentElement;
      var idx = 1;
      if (parent) {
        var siblings = Array.from(parent.children).filter(function (c) {
          return c.tagName === node.tagName;
        });
        idx = siblings.indexOf(node) + 1;
      }
      parts.unshift(tag + ':nth-of-type(' + idx + ')');
      node = parent;
    }
    return parts.join(' > ');
  }

  function frameInfo() {
    if (window === window.top) return '메인 페이지';
    try {
      var fe = window.frameElement;
      if (fe) {
        return 'iframe (src=' + fe.getAttribute('src') + ', name=' + (fe.getAttribute('name') || '(없음)') + ')';
      }
      return 'iframe (cross-origin이라 src/name 확인 불가, location=' + location.href + ')';
    } catch (err) {
      return 'iframe (프레임 정보 확인 중 오류: ' + err + ')';
    }
  }

  document.addEventListener(
    'click',
    function (e) {
      var el = e.target;
      var payload = {
        frame: frameInfo(),
        selector: cssPath(el),
        tag: el && el.outerHTML ? el.outerHTML.slice(0, 200) : '(알 수 없음)',
      };
      if (window.reportSelector) {
        window.reportSelector(JSON.stringify(payload));
      }
    },
    true
  );
})();
"""


# ── Python 쪽 출력 ────────────────────────────────────────
def handle_report(payload_json: str) -> None:
    """JS에서 window.reportSelector() 로 전달한 클릭 정보를 콘솔에 보기 좋게 출력한다."""
    data = json.loads(payload_json)
    print(f"[클릭 감지] 프레임: {data['frame']}")
    print(f"추정 셀렉터: {data['selector']}")
    print(f"태그: {data['tag']}")
    print("---")


# ── blog_id 확인 ──────────────────────────────────────────
def resolve_blog_id(argv: list[str]) -> str:
    if len(argv) >= 2:
        return argv[1]

    blog_id = os.environ.get("NAVER_BLOG_ID")
    if blog_id:
        return blog_id

    print("사용법: python capture_selectors.py <blog_id>")
    print("(또는 .env 에 NAVER_BLOG_ID 를 설정해두면 인자 없이 실행 가능)")
    sys.exit(1)


def main() -> int:
    load_dotenv()
    blog_id = resolve_blog_id(sys.argv)

    if not SESSION_FILE.exists():
        print(f"[오류] 세션 파일이 없습니다: {SESSION_FILE}\n먼저 capture_session.py 를 실행하세요.")
        return 1

    write_url = WRITE_PAGE_URL_TEMPLATE.format(blog_id=blog_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()

        # expose_function 은 이 page에 속한 모든 프레임(메인 + iframe)의
        # window 객체에 함수를 등록해준다 — 클릭 시점에만 호출되므로
        # iframe 로드 타이밍을 따로 신경 쓸 필요가 없다.
        page.expose_function("reportSelector", handle_report)
        page.add_init_script(CLICK_LISTENER_SCRIPT)

        print(f"글쓰기 페이지로 이동: {write_url}")
        page.goto(write_url)

        print()
        print("=" * 60)
        print("브라우저에서 순서대로 클릭하세요:")
        print("  1) 제목 입력란")
        print("  2) 본문 에디터 영역")
        print("  3) 임시저장 버튼")
        print("각 클릭마다 셀렉터가 여기 출력됩니다. 끝나면 Ctrl+C로 종료하세요.")
        print("=" * 60)
        print()

        try:
            while True:
                page.wait_for_timeout(1_000)
        except KeyboardInterrupt:
            print()
            print("종료합니다. 위에 출력된 셀렉터를 auto_publish.py의 SELECTORS 딕셔너리에 붙여넣으세요.")
        finally:
            browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
