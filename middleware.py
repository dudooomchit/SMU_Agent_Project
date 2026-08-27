import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any
from langchain.agents.middleware import before_agent, wrap_tool_call, AgentState
from langgraph.runtime import Runtime

from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver





from langchain.agents import create_agent
# TODO: 팀에서 생성한 커스텀 도구를 import 하세요
# 예시: from custom_tools import CUSTOM_TOOLS . 
from tools import outwork_search


def create_coding_agent():
    # TODO: 시스템 프롬프트를 팀 도메인에 맞게 수정하세요
    # 아래는 코딩 에이전트 예시입니다.
    # 팀의 도메인(쇼핑, 법령, 의료, 여행 등)에 맞게 변경하세요.

    system_prompt = """당신은 대학생 및 취업준비생을 위한 대외활동·공모전 통합 탐색 및 맞춤 추천 AI 에이전트입니다.

다음과 같은 대외활동 탐색, 추천, 웹 검색 및 작업 지원 도구를 수행할 수 있습니다:
- 대외활동 통합 검색: 주요 대외활동 사이트(링커리어, 캠퍼스픽, 위비티 등)의 공고를 주제, 키워드, 모집 날짜 조건별로 필터링 조회합니다.
- 원본 URL 안내: 관심 있는 대외활동의 원본 모집 페이지 상세 링크 및 접수 안내를 제공합니다.
- 사용자 맞춤 추천: 사용자의 관심 분야, 희망 직무, 선호 혜택을 바탕으로 매칭 점수가 높은 대외활동을 추천합니다.
- 인기·최신 콘텐츠 추천: 검색어와 관련된 연관 키워드를 도출하고, 조회수가 높거나 최근 작성된 합격 후기·팁 게시글을 연계 추천합니다.
- 실시간 웹 검색: 대외활동 전문 사이트 및 일반 웹 영역을 실시간 검색하여 최신 공고와 중복 여부를 파악합니다.
- 파일 및 폴더 제어: 파일 읽기/쓰기/삭제, 디렉터리 생성/목록 조회 등을 통해 지원서 초안 관리나 자료 정리를 보조합니다.
- Python 코드 실행: Python 코드를 직접 실행하여 데이터 처리, 연산, 조건 분석을 수행합니다.
사용자의 요청을 정확히 이해하고, 적절한 도구를 조합하여 최적의 대외활동 정보를 제공하세요.

작업 수행 시 다음 사항을 유의하세요:
1. 사용자가 특정 조건(주제, 카테고리, 모집 기간 등)을 제시하면 정확히 필터링하여 결과를 제공하세요.
2. 대외활동 정보를 전달할 때는 제목, 모집 기간, 주최 기관, 주요 혜택 및 원본 URL 링크를 명확히 포함하세요.
3. 사용자의 관심사와 직무에 맞는 공고를 추천할 때는 추천 이유와 적합도(매칭 요소)를 함께 설명하세요.
4. 파일 수정/삭제 및 시스템 작업을 수행할 때는 사전에 안전성과 필요성을 확인한 후 진행하세요.
5. 검색 결과가 없거나 에러가 발생하면 원인을 명확히 설명하고 대체 검색 조건이나 해결 방법을 제시하세요.

모든 응답은 친절하고 전문적인 한글로 작성하세요."""

   # 에이전트 생성
    # DAEO_AGENT_TOOLS는 이 파일 아래쪽에서 정의되지만,
    # create_coding_agent()는 그 뒤에 호출되므로 참조 시점에는 이미 존재합니다.
    agent_executor = create_agent(
        model="gpt-5.4-mini",
        tools=[outwork_search, *DAEO_AGENT_TOOLS],
        system_prompt=system_prompt,
        middleware=[
            workspace_index_middleware,      # @before_agent: workspace 파일 인덱싱
            inject_user_profile_middleware,  # @before_agent: 사용자 프로필 주입
            auto_backup_middleware,          # @wrap_tool_call: 파일 수정 전 백업
        ],
    )

    return agent_executor


# NOTE: agent 인스턴스 생성은 미들웨어 정의가 모두 끝난 아래쪽에서 수행합니다.
#       (여기서 호출하면 미들웨어가 아직 정의되지 않아 NameError)

# TODO: 팀에서 생성한 모든 도구를 리스트로 추가하세요

# CUSTOM_TOOLS = [
#     tool1,
#     tool2,
#     tool3,
# ]

# print(f"총 {len(CUSTOM_TOOLS)}개의 도구가 준비되었습니다.\n")

# for i, tool in enumerate(CUSTOM_TOOLS, 1):
#     print(f"{i}. {tool.name}")
#     print(f"   설명: {tool.description}")
#     print()
from langchain_core.tools import tool

# 대외활동 주요 플랫폼 사이트 리스트
DAEO_SITES = [
    "allforyoung.com",
    "gokams.or.kr",
    "youth.seoul.go.kr",
    "univ20.com",
    "wevity.com",
    "satisfy.kr",
    "jobaba.net",
    "contestkorea.com",
    "linkareer.com",
    "campuspick.com",
]

from langchain_tavily import TavilySearch
# 레시피 전문 검색 도구
outwork_search = TavilySearch(
    max_results=5,
    include_domains=[
        "allforyoung.com",
        "gokams.or.kr",
        "youth.seoul.go.kr",
        "univ20.com",
        "wevity.com",
        "satisfy.kr",
        "jobaba.net",
        "contestkorea.com",
        "linkareer.com",
        "campuspick.com",
    ],
)


# Tavily가 돌려주는 본문 요약의 최대 길이(자).
# Tavily는 건당 1,200~1,500자를 반환하는데, 그대로 쓰면 검색 한 번에
# 도구 출력이 7,000자를 넘어 LLM 컨텍스트를 크게 잡아먹습니다.
SUMMARY_MAX_CHARS = 300


def _tavily_search(
    query: str,
    max_results: int,
    site_filter: str | None = None,
    summary_max_chars: int = SUMMARY_MAX_CHARS,
) -> list[dict]:
    """Tavily로 검색을 수행하고 {'title', 'link', 'summary'} 목록으로 반환하는 헬퍼.

    site_filter를 지정하면 해당 도메인으로만 한정해 검색합니다.
    summary_max_chars를 0 이하로 주면 요약을 자르지 않고 전문을 반환합니다.
    (기존 BeautifulSoup 기반 _search_google을 Tavily로 대체한 함수입니다.)
    """
    search = TavilySearch(
        max_results=max_results,
        include_domains=[site_filter] if site_filter else None,
    )
    response = search.invoke({"query": query})

    # TavilySearch는 {"results": [...]} 형태의 dict를 반환합니다.
    raw_results = response.get("results", []) if isinstance(response, dict) else (response or [])

    results = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        link = item.get("url", "")
        if not link:
            continue

        summary = " ".join((item.get("content") or "").split())
        if 0 < summary_max_chars < len(summary):
            summary = summary[:summary_max_chars].rstrip() + "…"

        results.append({
            "title": item.get("title", ""),
            "link": link,
            "summary": summary,
        })
        if len(results) >= max_results:
            break
    return results


@tool(parse_docstring=True)
def search_platform_activities(
    platform: str | None = None,
    keyword: str | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """대외활동 정보를 플랫폼, 제목/키워드, 주제(카테고리), 모집 날짜(시작일/마감일) 조건별로 통합 검색합니다.

    Args:
        platform: 검색할 플랫폼 명칭 ('링커리어', '캠퍼스픽', '위비티', '콘테스트코리아' 등). 지정하지 않을 경우 전체 대상으로 검색합니다.
        keyword: 검색할 제목 및 상세 내용 키워드 (예: '마케팅', 'AI', '서포터즈').
        category: 대외활동 주제/카테고리 (예: '서포터즈', '공모전', '봉사활동', '기자단', '동아리').
        start_date: 모집 시작일 필터 기준 날짜 (YYYY-MM-DD 형식).
        end_date: 모집 마감일 필터 기준 날짜 (YYYY-MM-DD 형식).

    Returns:
        검색 조건에 맞는 대외활동 정보 목록을 담은 JSON 문자열 또는 실패 메시지.
    """
    import json
    from datetime import datetime

    try:
        activities_db = [
            {
                "id": "LINK-2026-001",
                "platform": "링커리어",
                "title": "2026 상명 AI 에이전트 서포터즈 1기",
                "category": "서포터즈",
                "organizer": "상명대학교",
                "start_date": "2026-03-01",
                "end_date": "2026-03-15",
                "url": "https://linkareer.com/activity/20260301",
                "description": "AI 챗봇 개발 및 서비스 홍보 활동",
            },
            {
                "id": "CAMPUS-2026-012",
                "platform": "캠퍼스픽",
                "title": "천안시 대학생 소상공인 마케팅 공모전",
                "category": "공모전",
                "organizer": "천안시청",
                "start_date": "2026-03-05",
                "end_date": "2026-03-25",
                "url": "https://www.campuspick.com/activity/view?id=20260305",
                "description": "착한가격업소 및 전통시장 상권 활성화 아이디어",
            },
            {
                "id": "WEVITY-2026-103",
                "platform": "위비티",
                "title": "전국 대학생 IT/개발 연합 동아리 신입 모집",
                "category": "동아리",
                "organizer": "전국대학생IT연합",
                "start_date": "2026-02-20",
                "end_date": "2026-03-10",
                "url": "https://www.wevity.com/?c=find&s=1&gbn=view&ix=103",
                "description": "웹/앱 개발 프로젝트 수행 및 오픈소스 스터디",
            },
            {
                "id": "CONTEST-2026-404",
                "platform": "콘테스트코리아",
                "title": "소외계층 디지털 배움터 대학생 봉사단",
                "category": "봉사활동",
                "organizer": "한국지능정보사회진흥원",
                "start_date": "2026-03-10",
                "end_date": "2026-03-31",
                "url": "https://www.contestkorea.com/sub/view.php?txtNo=404",
                "description": "고령층 대상 스마트폰 및 디지털 키오스크 활용 교육 봉사",
            },
            {
                "id": "LINK-2026-005",
                "platform": "링커리어",
                "title": "2026 20대 트렌드 리포터 기자단 5기",
                "category": "기자단",
                "organizer": "대학내일",
                "start_date": "2026-03-15",
                "end_date": "2026-04-05",
                "url": "https://linkareer.com/activity/20260315",
                "description": "대학생 트렌드 취재 및 매거진 기사 작성",
            },
        ]

        filtered = activities_db

        if platform:
            filtered = [a for a in filtered if platform.strip().lower() in a["platform"].lower()]

        if keyword:
            kw = keyword.strip().lower()
            filtered = [a for a in filtered if kw in a["title"].lower() or kw in a["description"].lower()]

        if category:
            filtered = [a for a in filtered if category.strip().lower() in a["category"].lower()]

        if start_date:
            try:
                target_start = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
                filtered = [a for a in filtered if datetime.strptime(a["start_date"], "%Y-%m-%d").date() >= target_start]
            except ValueError:
                return "실패: start_date는 YYYY-MM-DD 형식이어야 합니다."

        if end_date:
            try:
                target_end = datetime.strptime(end_date.strip(), "%Y-%m-%d").date()
                filtered = [a for a in filtered if datetime.strptime(a["end_date"], "%Y-%m-%d").date() <= target_end]
            except ValueError:
                return "실패: end_date는 YYYY-MM-DD 형식이어야 합니다."

        if not filtered:
            return "성공: 조건에 일치하는 대외활동 공고가 없습니다."

        return json.dumps(filtered, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"실패: {str(e)}"


@tool(parse_docstring=True)
def get_activity_url(activity_id: str | None = None, title: str | None = None) -> str:
    """특정 대외활동 공고의 원본 상세 페이지 URL 주소 및 바로가기 링크를 제공합니다.

    Args:
        activity_id: 대외활동 고유 ID (예: 'LINK-2026-001')
        title: 대외활동 제목 (activity_id가 없을 경우 사용)

    Returns:
        해당 대외활동의 원본 웹사이트 URL 주소 및 안내 메시지.
    """
    import json

    try:
        url_db = {
            "LINK-2026-001": {"title": "2026 상명 AI 에이전트 서포터즈 1기", "url": "https://linkareer.com/activity/20260301"},
            "CAMPUS-2026-012": {"title": "천안시 대학생 소상공인 마케팅 공모전", "url": "https://www.campuspick.com/activity/view?id=20260305"},
            "WEVITY-2026-103": {"title": "전국 대학생 IT/개발 연합 동아리 신입 모집", "url": "https://www.wevity.com/?c=find&s=1&gbn=view&ix=103"},
            "CONTEST-2026-404": {"title": "소외계층 디지털 배움터 대학생 봉사단", "url": "https://www.contestkorea.com/sub/view.php?txtNo=404"},
            "LINK-2026-005": {"title": "2026 20대 트렌드 리포터 기자단 5기", "url": "https://linkareer.com/activity/20260315"},
        }

        if activity_id and activity_id in url_db:
            info = url_db[activity_id]
            return f"공고명: {info['title']}\n원본 URL: {info['url']}"

        if title:
            for item in url_db.values():
                if title.strip().lower() in item["title"].lower():
                    return f"공고명: {item['title']}\n원본 URL: {item['url']}"

        return "실패: 해당 대외활동의 URL 주소를 찾을 수 없습니다."

    except Exception as e:
        return f"실패: {str(e)}"


@tool(parse_docstring=True)
def recommend_by_user_preference(
    user_interests: str,
    target_job: str | None = None,
    preferred_benefit: str | None = None,
) -> str:
    """사용자의 관심 분야, 희망 직무, 선호 혜택을 바탕으로 가장 적합한 대외활동을 맞춤 추천합니다.

    Args:
        user_interests: 사용자의 관심 카테고리/키워드 (예: '마케팅', 'AI', 'IT', '기획')
        target_job: 희망 직무 (예: '서비스 기획자', '데이터 분석가', '마케터')
        preferred_benefit: 선호하는 혜택 (예: '활동비', '상금', '서류면제', '수료증')

    Returns:
        사용자 매칭 점수 기반 맞춤 대외활동 목록(JSON) 또는 오류 메시지.
    """
    import json

    try:
        activities_pool = [
            {
                "id": "LINK-2026-001",
                "title": "2026 상명 AI 에이전트 서포터즈 1기",
                "category": "서포터즈/IT",
                "benefit": "활동비, 수료증",
                "match_score": 95,
                "url": "https://linkareer.com/activity/20260301",
            },
            {
                "id": "CAMPUS-2026-012",
                "title": "천안시 대학생 소상공인 마케팅 공모전",
                "category": "공모전/마케팅",
                "benefit": "상금, 시장상",
                "match_score": 88,
                "url": "https://www.campuspick.com/activity/view?id=20260305",
            },
            {
                "id": "WEVITY-2026-103",
                "title": "전국 대학생 IT/개발 연합 동아리 신입 모집",
                "category": "동아리/IT",
                "benefit": "프로젝트 구축, 네트워크",
                "match_score": 82,
                "url": "https://www.wevity.com/?c=find&s=1&gbn=view&ix=103",
            },
        ]

        recommendations = []
        interests_lower = user_interests.lower()

        for act in activities_pool:
            score = 70
            if any(k in act["category"].lower() or k in act["title"].lower() for k in interests_lower.split()):
                score += 15
            if preferred_benefit and preferred_benefit.lower() in act["benefit"].lower():
                score += 10
            act["computed_match_score"] = min(score, 100)
            recommendations.append(act)

        recommendations.sort(key=lambda x: x["computed_match_score"], reverse=True)
        return json.dumps(recommendations, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"실패: {str(e)}"


@tool(parse_docstring=True)
def recommend_related_trending(query: str, sort_by: str = "views") -> str:
    """검색한 대외활동 키워드와 관련된 연관 검색어, 최신 인기 게시글, 조회수 높은 후기를 추천합니다.

    Args:
        query: 기준 검색어/키워드 (예: '마케팅 서포터즈', '공모전')
        sort_by: 정렬 기준 ('views': 조회수 높은 순, 'recent': 최신 순)

    Returns:
        연관 검색어 리스트 및 추천 게시글/후기 데이터(JSON) 또는 오류 메시지.
    """
    import json

    try:
        trending_data = {
            "query": query,
            "related_keywords": [f"{query} 합격후기", f"{query} 자소서 팁", f"{query} 2026 모집", f"{query} 면접 질문"],
            "recommended_posts": [
                {
                    "title": f"🔥 [조회수 Top] {query} 1차 서포터즈 합격자 자소서 공개",
                    "views": 15200,
                    "date": "2026-02-24",
                    "link": "https://linkareer.com/community/post/101",
                },
                {
                    "title": f"✨ [최신글] {query} 지원 시 꼭 피해야 할 3가지 실수",
                    "views": 8400,
                    "date": "2026-02-26",
                    "link": "https://www.campuspick.com/community/view?id=202",
                },
                {
                    "title": f"💡 {query} 우수 수료자가 알려주는 카드뉴스 제작 템플릿",
                    "views": 12100,
                    "date": "2026-02-22",
                    "link": "https://univ20.com/content/303",
                },
            ],
        }

        if sort_by == "views":
            trending_data["recommended_posts"].sort(key=lambda x: x["views"], reverse=True)
        elif sort_by == "recent":
            trending_data["recommended_posts"].sort(key=lambda x: x["date"], reverse=True)

        return json.dumps(trending_data, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"실패: {str(e)}"


@tool(parse_docstring=True)
def search_daeo_activities_websites(query: str, max_results: int = 5) -> str:
    """대외활동 웹사이트 전용으로 실시간 웹검색을 수행합니다.

    Args:
        query: 검색할 키워드
        max_results: 반환할 최대 결과 수

    Returns:
        검색 결과 또는 오류 메시지
    """
    try:
        results = []
        seen_links = set()

        for site in DAEO_SITES:
            site_results = _tavily_search(query, max_results, site)
            for item in site_results:
                if item["link"] in seen_links:
                    continue
                seen_links.add(item["link"])
                results.append({
                    "title": item["title"],
                    "site": site,
                    "link": item["link"],
                    "summary": item["summary"] or "(요약 없음)",
                })
                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        if not results:
            return f"대외활동 사이트 전용 검색 결과가 없습니다: {query}"

        lines = [f"검색어: {query}", "대외활동 사이트 전용 검색 결과:", ""]
        for idx, item in enumerate(results, start=1):
            lines.append(
                f"[{idx}] 제목: {item['title']}\n사이트: {item['site']}\n링크: {item['link']}\n요약: {item['summary']}"
            )
            lines.append("-" * 60)

        return "\n".join(lines).rstrip("-\n")
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def search_web(query: str, max_results: int = 5) -> str:
    """일반 웹에서 실시간 검색을 수행합니다.

    Args:
        query: 검색할 키워드
        max_results: 반환할 최대 결과 수

    Returns:
        검색 결과 또는 오류 메시지
    """
    try:
        results = _tavily_search(query, max_results)
        if not results:
            return f"검색 결과가 없습니다: {query}"

        duplicate_results = []
        normal_results = []
        for item in results:
            is_duplicate_daeo = any(site in item["link"] for site in DAEO_SITES)
            item["duplicate_text"] = "중복된 대외활동" if is_duplicate_daeo else ""
            item["summary"] = item["summary"] or "(요약 없음)"
            if is_duplicate_daeo:
                duplicate_results.append(item)
            else:
                normal_results.append(item)

        lines = [f"검색어: {query}", "일반 웹검색 결과:", ""]

        if duplicate_results:
            lines.append("[대외활동과 중복된 결과]")
            for idx, item in enumerate(duplicate_results, start=1):
                lines.append(
                    f"[{idx}] 제목: {item['title']} / {item['duplicate_text']}\n링크: {item['link']}\n요약: {item['summary']}"
                )
                lines.append("-" * 60)
            lines.append("")

        if normal_results:
            lines.append("[일반 웹 결과]")
            for idx, item in enumerate(normal_results, start=1):
                lines.append(
                    f"[{idx}] 제목: {item['title']}\n링크: {item['link']}\n요약: {item['summary']}"
                )
                lines.append("-" * 60)

        return "\n".join(lines).rstrip("-\n")
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def read_file(file_path: str) -> str:
    """파일의 내용을 읽어서 반환합니다.

    Args:
        file_path: 읽을 파일의 경로 (상대 경로 또는 절대 경로)

    Returns:
        파일 내용 또는 오류 메시지
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        line_count = len(content.split("\n"))
        return f"파일: {file_path}\n총 {line_count}줄\n\n{content}"
    except FileNotFoundError:
        return f"오류: 파일을 찾을 수 없습니다: {file_path}"
    except PermissionError:
        return f"오류: 파일에 대한 읽기 권한이 없습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def write_file(file_path: str, content: str) -> str:
    """파일에 내용을 작성합니다. 파일이 없으면 생성하고, 있으면 덮어씁니다.

    Args:
        file_path: 작성할 파일의 경로
        content: 파일에 쓸 내용

    Returns:
        성공 메시지 또는 오류 메시지
    """
    import os

    try:
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        line_count = len(content.split("\n"))
        return f"성공: 파일이 작성되었습니다: {file_path} (총 {line_count}줄)"
    except PermissionError:
        return f"오류: 파일에 대한 쓰기 권한이 없습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def delete_file(file_path: str) -> str:
    """파일을 삭제합니다.

    Args:
        file_path: 삭제할 파일의 경로

    Returns:
        성공 메시지 또는 오류 메시지
    """
    import os

    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            return f"성공: 파일이 삭제되었습니다: {file_path}"
        else:
            return f"오류: 파일을 찾을 수 없습니다: {file_path}"
    except PermissionError:
        return f"오류: 파일에 대한 삭제 권한이 없습니다: {file_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def create_directory(dir_path: str) -> str:
    """새로운 디렉터리를 생성합니다.

    Args:
        dir_path: 생성할 디렉터리의 경로

    Returns:
        성공 메시지 또는 오류 메시지
    """
    import os

    try:
        os.makedirs(dir_path, exist_ok=True)
        return f"성공: 디렉터리가 생성되었습니다: {dir_path}"
    except PermissionError:
        return f"오류: 디렉터리 생성 권한이 없습니다: {dir_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def list_directory(dir_path: str = ".") -> str:
    """디렉터리의 파일과 폴더 목록을 반환합니다.

    Args:
        dir_path: 조회할 디렉터리 경로 (기본값: 현재 디렉터리)

    Returns:
        파일 및 폴더 목록 또는 오류 메시지
    """
    import os

    try:
        if not os.path.exists(dir_path):
            return f"오류: 디렉터리를 찾을 수 없습니다: {dir_path}"
        if not os.path.isdir(dir_path):
            return f"오류: {dir_path}는 디렉터리가 아닙니다"
        items = os.listdir(dir_path)
        if not items:
            return f"디렉터리가 비어있습니다: {dir_path}"
        folders, files = [], []
        for item in sorted(items):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                folders.append(f"[폴더] {item}/")
            else:
                size = os.path.getsize(item_path)
                files.append(f"[파일] {item} ({size} bytes)")
        result = f"디렉터리: {dir_path}\n\n"
        if folders:
            result += "폴더:\n" + "\n".join(folders) + "\n\n"
        if files:
            result += "파일:\n" + "\n".join(files)
        return result
    except PermissionError:
        return f"오류: 디렉터리에 대한 읽기 권한이 없습니다: {dir_path}"
    except Exception as e:
        return f"오류: {str(e)}"


@tool(parse_docstring=True)
def execute_python_code(code: str) -> str:
    """Python 코드를 실행하고 결과를 반환합니다.

    Args:
        code: 실행할 Python 코드 문자열

    Returns:
        코드 실행 결과 또는 오류 메시지
    """
    import os
    import subprocess
    import sys

    try:
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10, cwd=os.getcwd())
        output_parts = []
        if result.stdout:
            output_parts.append(f"출력:\n{result.stdout.strip()}")
        if result.stderr:
            output_parts.append(f"오류:\n{result.stderr.strip()}")
        if result.returncode == 0:
            return "실행 성공\n\n" + "\n\n".join(output_parts) if output_parts else "실행 성공 (출력 없음)"
        return f"실행 실패 (종료 코드: {result.returncode})\n\n" + "\n\n".join(output_parts)
    except subprocess.TimeoutExpired:
        return "오류: 코드 실행 시간이 10초를 초과했습니다."
    except Exception as e:
        return f"오류: {str(e)}"


# Agent 바인딩용 도구 리스트
DAEO_AGENT_TOOLS = [
    search_platform_activities,
    get_activity_url,
    recommend_by_user_preference,
    recommend_related_trending,
    search_daeo_activities_websites,
    search_web,
    read_file,
    write_file,
    delete_file,
    create_directory,
    list_directory,
    execute_python_code,
]


@before_agent
def workspace_index_middleware(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Workspace Index Middleware

    에이전트 시작 시 workspace의 문서 파일들을 스캔하여
    파일 목록을 state에 저장합니다.

    이를 통해 LLM은 매번 list_directory를 호출하지 않고도
    workspace의 파일 구조를 즉시 파악할 수 있습니다.
    """
    print("\n[Workspace Index] 파일 인덱싱 시작...")

    cwd = os.getcwd()
    file_list = []

    # 지원하는 확장자 (MD, CSV, TXT)
    extensions = {'.md', '.csv', '.txt'}

    # workspace 스캔 (최대 3단계 깊이)
    for root, dirs, files in os.walk(cwd):
        # 제외할 디렉터리
        dirs[:] = [d for d in dirs if not d.startswith('.')
                   and d not in ['__pycache__', 'node_modules', 'venv', '.cache', 'backup']]

        level = root.replace(cwd, '').count(os.sep)
        if level > 3:
            continue

        for file in files:
            if file.startswith('.'):
                continue

            file_ext = os.path.splitext(file)[1].lower()

            if file_ext in extensions:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, cwd)
                file_list.append(f"  • {rel_path}")

    # 인덱스 요약
    index_info = [
        f"📁 Workspace: {cwd}",
        f"📊 총 {len(file_list)}개 파일 발견\n",
        "📋 파일 목록:"
    ]
    index_info.extend(file_list)

    print(f"[Workspace Index] ✅ {len(file_list)}개 파일 인덱싱 완료")

    # 시스템 메시지로 인덱스 정보 추가
    system_message = SystemMessage(
        content=f"[Workspace Index]\n{chr(10).join(index_info)}\n\n사용자가 요청하는 문서를 이 목록에서 찾아 처리하세요."
    )

    return {"messages": [system_message]}


# 기존 파일을 덮어쓰거나 삭제하는 도구 = 백업이 필요한 도구
# (edit_file은 아직 없지만, 나중에 추가되어도 자동으로 백업되도록 함께 넣어둡니다)
BACKUP_TARGET_TOOLS = {"write_file", "delete_file", "edit_file"}


@wrap_tool_call
async def auto_backup_middleware(request, handler):
    """Auto Backup Middleware

    파일을 덮어쓰거나 삭제하는 도구(BACKUP_TARGET_TOOLS)를 실행하기 전에
    자동으로 백업을 생성합니다.
    백업 파일은 backup/ 디렉터리에 "파일명_YYYYMMDD_HHMMSS.확장자" 형식으로 저장됩니다.

    예시:
    - meeting.md 수정 시 → backup/meeting_20260730_143022.md 생성
    """
    tool_name = request.tool_call["name"]
    tool_args = request.tool_call.get("args", {})

    # 파일을 변경하는 도구만 백업
    if tool_name not in BACKUP_TARGET_TOOLS:
        return await handler(request)

    file_path = tool_args.get("file_path")
    if not file_path or not os.path.exists(file_path):
        # 파일이 없으면 백업 없이 진행
        return await handler(request)

    try:
        # backup 디렉터리 생성
        backup_dir = Path("backup")
        backup_dir.mkdir(exist_ok=True)

        # 파일명과 확장자 분리
        file_name = os.path.basename(file_path)
        name_without_ext, ext = os.path.splitext(file_name)

        # 현재 시각으로 백업 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{name_without_ext}_{timestamp}{ext}"

        # 타임스탬프가 초 단위라 같은 초에 두 번 수정하면 앞선 백업을 덮어씁니다.
        # 이미 있으면 -2, -3 … 을 붙여 충돌을 피합니다.
        seq = 2
        while backup_path.exists():
            backup_path = backup_dir / f"{name_without_ext}_{timestamp}-{seq}{ext}"
            seq += 1

        # 파일 복사
        shutil.copy2(file_path, backup_path)
        print(f"\n[Auto Backup] 💾 백업 생성: {backup_path}")

    except Exception as e:
        print(f"[Auto Backup] ⚠️ 백업 실패: {e}")
        # 백업 실패해도 원본 작업은 진행

    # 원본 도구 실행
    return await handler(request)


@before_agent
def inject_user_profile_middleware(state, runtime):
    # 예시: 세션이나 저장소에서 유저 프로필 추출
    user_profile = (
        "[사용자 개인화 프로필]\n"
        "- 전공/학년: 경영학과 3학년\n"
        "- 관심 분야: 마케팅, AI/IT, 콘텐츠 제작\n"
        "- 선호 지역: 서울/수도권, 충남/천안, 비대면\n"
        "- 희망 혜택: 활동비 지급, 수료증\n"
    )
    return {"messages": [SystemMessage(content=user_profile)]}


# LangGraph Studio에서 사용할 에이전트 내보내기
# 위 미들웨어 3개가 모두 정의된 뒤에 호출해야 하므로 여기에 위치합니다.
# (아래쪽에서 inject_user_profile_middleware가 일반 함수로 재정의되기 때문에
#  이 줄을 파일 맨 끝으로 옮기면 미들웨어가 아닌 엉뚱한 함수가 바인딩됩니다.)
agent = create_coding_agent()


# ==================================================================
# 사용자 프로필 온보딩 그래프
#
# 원래 이 아래에 State/미들웨어/그래프 정의가 3벌 중복되어 있었고,
# 같은 이름(ActivityAgentState, inject_user_profile_middleware,
# builder, memory, app)이 서로를 덮어써서 앞의 정의가 모두 사라졌습니다.
# 세 버전의 기능을 합쳐 하나로 통합한 것이 아래 코드입니다.
# ==================================================================

# ------------------------------------------------------------------
# [1] State 정의 (3개 버전의 필드를 모두 합친 단일 정의)
# ------------------------------------------------------------------
class ActivityAgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]  # 대화 히스토리
    user_id: str                                          # 사용자 식별 ID
    user_profile: dict                                    # 주입된 사용자 프로필 정보
    is_onboarding: bool                                   # 온보딩(정보 수집) 진행 중 여부
    preferred_category: str                               # 선호 카테고리 (예: 마케팅, IT)
    preferred_region: str                                 # 선호 지역 (예: 서울, 경기)


# ------------------------------------------------------------------
# [Mock DB] 실제 환경에서는 PostgreSQL, MongoDB 등의 DB 조회 로직으로 대체
#           (기존의 mock_db와 USER_DB를 하나로 합쳤습니다)
# ------------------------------------------------------------------
USER_DB: dict[str, dict] = {
    "user_123": {
        "name": "김스무",
        "major": "컴퓨터공학과",
        "grade": "3학년",
        "interests": ["IT/SW", "AI", "빅데이터"],
        "region": "서울",
    }
}


def get_user_profile_from_db(user_id: str) -> dict:
    """user_id로 프로필을 조회합니다. 없으면 빈 dict를 반환합니다."""
    return USER_DB.get(user_id, {})


# ------------------------------------------------------------------
# [2] 프로필 미들웨어 노드
#     - DB에 프로필이 있으면 State에 자동 주입
#     - 없으면 수집 질문을 던지고, 답변이 오면 DB에 저장
# ------------------------------------------------------------------
def profile_onboarding_middleware(state: ActivityAgentState):
    """사용자 프로필을 조회·주입하거나, 없으면 온보딩으로 수집·저장하는 미들웨어"""
    user_id = state.get("user_id")
    last_message = state["messages"][-1].content if state.get("messages") else ""

    # 이미 State에 프로필이 있으면 DB 조회를 건너뛰어 성능 최적화
    profile = state.get("user_profile") or (get_user_profile_from_db(user_id) if user_id else {})

    # CASE A: 프로필이 있는 경우 -> 주입 후 통과
    if profile:
        return {"user_profile": profile, "is_onboarding": False}

    # CASE B: 이전 턴의 수집 질문에 대한 답변이 온 경우 -> DB에 저장
    if state.get("is_onboarding") and last_message:
        # 실제 서비스에서는 LLM/Pydantic으로 정교하게 파싱
        new_profile = {"raw_info": last_message, "status": "configured"}
        if user_id:
            USER_DB[user_id] = new_profile
        return {
            "user_profile": new_profile,
            "is_onboarding": False,
            "messages": [AIMessage(content="프로필 정보가 성공적으로 등록되었습니다! 원하시는 대외활동이나 공모전을 물어보세요.")],
        }

    # CASE C: 프로필도 없고 온보딩도 시작되지 않은 최초 상태 -> 수집 질문
    return {
        "is_onboarding": True,
        "messages": [AIMessage(content="맞춤형 추천을 위해 간단한 정보가 필요해요. **전공과 학년, 관심 분야**를 입력해 주세요!")],
    }

# ------------------------------------------------------------------
# [3] 프로필 정보를 활용하는 LLM 추천 노드
#     (하드코딩 문자열을 돌려주던 main_recommend_agent 대신
#      실제 LLM을 호출하는 이 노드 하나로 통일했습니다)
# ------------------------------------------------------------------
def call_agent_llm(state: ActivityAgentState):
    profile = state.get("user_profile", {})

    # 프로필 정보를 바탕으로 시스템 프롬프트(System Prompt) 동적 구성
    if profile.get("raw_info"):
        # 온보딩으로 방금 수집한 원문 프로필
        profile_context = (
            f"사용자가 입력한 정보: {profile['raw_info']}\n\n"
            f"위 정보를 참고하여 대외활동/공모전을 맞춤 추천해 주세요."
        )
    elif profile:
        # DB에 저장되어 있던 구조화된 프로필
        profile_context = (
            f"사용자 정보:\n"
            f"- 이름: {profile.get('name', '미지정')}\n"
            f"- 전공/학년: {profile.get('major', '미지정')} / {profile.get('grade', '미지정')}\n"
            f"- 관심 분야: {', '.join(profile.get('interests', []))}\n"
            f"- 거주 지역: {profile.get('region', '미지정')}\n\n"
            f"위 사용자 스펙과 관심사를 참고하여 대외활동/공모전을 맞춤 추천해 주세요."
        )
    else:
        profile_context = "사용자 프로필 정보가 없습니다. 일반적인 안내를 제공해 주세요."

    system_message = SystemMessage(
        content=f"당신은 대학생 대외활동 맞춤 추천 AI 에이전트입니다.\n\n{profile_context}"
    )

    # LLM 호출 (시스템 메시지 + 이전 대화 기록)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    response = llm.invoke([system_message] + state["messages"])

    return {"messages": [response]}


# ------------------------------------------------------------------
# [4] 조건부 라우팅 (미들웨어 판단 결과에 따른 분기)
# ------------------------------------------------------------------
def route_after_middleware(state: ActivityAgentState):
    # 온보딩 질문이 나갔거나 프로필이 아직 없으면 여기서 종료
    if state.get("is_onboarding") or not state.get("user_profile"):
        return END
    return "recommend_agent"


# ------------------------------------------------------------------
# [5] 그래프 파이프라인 구성 (단일 정의)
# ------------------------------------------------------------------
builder = StateGraph(ActivityAgentState)

# 미들웨어 노드와 추천 노드 추가
builder.add_node("profile_middleware", profile_onboarding_middleware)
builder.add_node("recommend_agent", call_agent_llm)

# 흐름 연결: 시작 -> 프로필 미들웨어 -> (분기) -> 추천 노드 -> 종료
builder.add_edge(START, "profile_middleware")
builder.add_conditional_edges("profile_middleware", route_after_middleware)
builder.add_edge("recommend_agent", END)

# Checkpointer(메모리)를 통해 thread_id별로 대화 맥락 유지
memory = MemorySaver()
app = builder.compile(checkpointer=memory)
