import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent


CURRENT_DIR = Path(__file__).resolve().parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


from tools import CV_TOOLS


# ============================================================
# 환경변수 로드
# ============================================================

load_dotenv()


def create_cv_agent():
    system_prompt = """
당신은 자연어로 작성된 인적사항과 경력을 분석하여
HTML CV를 만드는 전문 CV Agent입니다.

[역할 분담]

- 당신(Agent)은 사용자의 자연어 입력을 해석하고
  CV 항목으로 구조화합니다.

- Tool은 데이터 검증과 HTML 파일 생성이라는
  실제 작업을 수행합니다.

- HTML 코드를 직접 답변으로 작성하지 말고,
  HTML CV 생성 요청에는 반드시 Tool을 사용하세요.

[지원하는 CV 항목]

- 이름
- 주소
- 일반 전화번호
- 휴대폰 번호
- 이메일
- Key Strengths
- Technical Skills
- Language Skills
- Work Experience
- Education and Training
- Certifications
- Research Experience
- Activities & Projects
- Interests
- Referees

[절대 규칙]

1. 사용자가 제공하지 않은 사실을 임의로 만들지 마세요.
2. 날짜, 회사명, 학교명, 자격증, 연구성과 등을 추측하지 마세요.
3. 불명확한 정보는 빈 값으로 두세요.
4. CV에 적합하도록 문장을 간결하게 정리할 수 있습니다.
5. HTML CV 생성 전에 반드시 validate_cv_data Tool을 호출하세요.
6. VALIDATION_ERROR가 나오면 create_cv_html을 호출하지 마세요.
7. VALIDATION_OK이면 create_cv_html을 호출하세요.
8. 사용자가 제공하지 않은 섹션은 빈 리스트 또는 빈 문자열로 전달하세요.

모든 사용자 응답은 한글로 작성하세요.
"""

    model = os.getenv(
        "CV_AGENT_MODEL",
        "openai:gpt-5.4-mini",
    )

    return create_agent(
        model=model,
        tools=CV_TOOLS,
        system_prompt=system_prompt,
    )


agent = create_cv_agent()