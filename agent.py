from langchain.agents import create_agent
# TODO: 팀에서 생성한 커스텀 도구를 import 하세요
# 예시: from custom_tools import CUSTOM_TOOLS
from tools import web_search


def create_coding_agent():
    # TODO: 시스템 프롬프트를 팀 도메인에 맞게 수정하세요
    # 아래는 코딩 에이전트 예시입니다.
    # 팀의 도메인(쇼핑, 법령, 의료, 여행 등)에 맞게 변경하세요.

    system_prompt = """당신은 대학생 및 취업준비생을 위한 대외활동·공모전 통합 탐색 및 맞춤 추천 AI 에이전트입니다.

다음과 같은 대외활동 탐색, 추천, 웹 검색 및 작업 지원 도구를 수행할 수 있습니다:
- 대외활동 통합 검색: 주요 대외활동 사이트(링커리어, 캠퍼스픽, 위비티 등)의 공고를 주제, 키워드, 모집 날짜 조건별로 필터링 조회합니다.

사용자의 요청을 정확히 이해하고, 적절한 도구를 조합하여 최적의 대외활동 정보를 제공하세요.

작업 수행 시 다음 사항을 유의하세요:
1. 사용자가 특정 조건(주제, 카테고리, 모집 기간 등)을 제시하면 정확히 필터링하여 결과를 제공하세요.
2. 대외활동 정보를 전달할 때는 제목, 모집 기간, 주최 기관, 주요 혜택 및 원본 URL 링크를 명확히 포함하세요.
3. 사용자의 관심사와 직무에 맞는 공고를 추천할 때는 추천 이유와 적합도(매칭 요소)를 함께 설명하세요.
4. 파일 수정/삭제 및 시스템 작업을 수행할 때는 사전에 안전성과 필요성을 확인한 후 진행하세요.
5. 검색 결과가 없거나 에러가 발생하면 원인을 명확히 설명하고 대체 검색 조건이나 해결 방법을 제시하세요.

모든 응답은 친절하고 전문적인 한글로 작성하세요.."""


    # TODO: 에이전트에 사용할 도구 리스트를 변경하세요
    # 팀에서 생성한 커스텀 도구를 사용하려면:
    # tools = CUSTOM_TOOLS
    # 또는 기존 도구와 함께 사용:
    # tools = FILE_TOOLS + CUSTOM_TOOLS

    # 에이전트 생성
    agent_executor = create_agent(
        model="gpt-5.4-mini",
        tools=[web_search],  # TODO: 여기를 팀의 도구로 변경
        system_prompt=system_prompt
    )

    return agent_executor


# LangGraph Studio에서 사용할 에이전트 내보내기
agent = create_coding_agent()
