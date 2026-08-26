# CV Agent Project

## 1. 프로젝트 소개

이 프로젝트는 LangChain / LangGraph 기반의 AI Agent와 Tool 사용 방식을 학습하기 위해 제작한 CV 자동 생성 프로젝트임.

사용자가 이름, 연락처, 학력, 경력, 자격증, 연구이력, 프로젝트, 대외활동, 기술 스택 등의 정보를 자연어 형태로 입력하면 AI Agent가 해당 내용을 분석하고 CV 항목에 맞게 구조화한 뒤 HTML 형식의 CV 파일을 생성함.

이 프로젝트의 핵심 목표는 단순히 LLM에게 CV를 작성시키는 것이 아니라, **Agent와 Tool의 역할을 명확하게 분리하여 실제 Agent 시스템의 동작 구조를 이해하는 것**임.

---

## 2. 프로젝트 목표

주요 목표는 다음과 같음.

- LangChain의 `create_agent()` 사용법 학습
- LangChain Tool 구조 이해
- `@tool` 기반 Custom Tool 제작
- LangGraph 기반 Agent 실행 구조 학습
- Agent가 상황에 맞는 Tool을 선택하는 과정 확인
- 자연어 데이터를 구조화된 CV 데이터로 변환
- Pydantic을 활용한 구조화 데이터 정의
- Tool을 통한 데이터 검증
- Tool을 통한 HTML 파일 생성
- LangGraph Studio를 이용한 Agent / Tool 호출 과정 확인

---

## 3. 전체 동작 구조

프로젝트는 다음과 같은 흐름으로 동작함.

```text
사용자 자연어 입력
        ↓
     CV Agent
        ↓
CV 항목 분석 및 구조화
        ↓
validate_cv_data Tool
        ↓
   데이터 검증
        ↓
create_cv_html Tool
        ↓
HTML CV 파일 생성
        ↓
output/cv.html
```

예를 들어 사용자가 다음과 같이 입력할 수 있음.

```text
이름은 홍길동이고 상명대학교 전자공학과를 졸업했다.

2025년 ABC전자에서 인턴으로 근무했고
PCB 설계와 MCU 펌웨어 개발을 담당했다.

Python, C, 회로 설계가 가능하다.
```

Agent는 위 내용을 분석하여 다음과 같은 정보로 구분함.

```text
Name
→ 홍길동

Education
→ 상명대학교
→ 전자공학과

Work Experience
→ ABC전자
→ Intern

Work Details
→ PCB 설계
→ MCU 펌웨어 개발

Technical Skills
→ Python
→ C
→ 회로 설계
```

이후 Agent가 CV 생성에 필요한 Tool을 호출함.

---

## 4. Agent와 Tool 역할 분리

이 프로젝트에서 가장 중요하게 설계한 부분임.

### agent.py

`agent.py`는 판단과 의사결정을 담당함.

주요 역할:

- 사용자의 자연어 입력 이해
- CV 항목 분류
- 경력 / 학력 / 기술 / 활동 등 정보 구분
- Tool에 전달할 데이터 구성
- 어떤 Tool을 호출할지 결정
- Tool 호출 순서 결정
- Tool 실행 결과 확인

즉 다음 질문에 답하는 역할임.

```text
무엇을 해야 하는가?
```

---

### tools.py

`tools.py`는 실제 기능 실행을 담당함.

현재 주요 Tool은 다음과 같음.

#### validate_cv_data

CV 생성 전에 데이터를 검사함.

주요 기능:

- 이름 존재 여부 확인
- 이메일 형식 확인
- 휴대폰 번호 형식 확인
- 학력 정보 존재 여부 확인
- 경력 정보 존재 여부 확인

문제가 없으면:

```text
VALIDATION_OK
```

를 반환함.

필수 정보가 없는 경우:

```text
VALIDATION_ERROR
```

를 반환함.

---

#### create_cv_html

Agent가 구조화한 CV 데이터를 실제 HTML 파일로 변환함.

주요 기능:

- CV HTML 생성
- CSS 스타일 적용
- A4 출력 형식 적용
- CV 섹션 자동 생성
- 데이터가 없는 섹션 자동 제외
- HTML 파일 저장

생성된 파일은 기본적으로 다음 위치에 저장됨.

```text
output/cv.html
```

즉 Tool은 다음 질문에 답하는 역할임.

```text
실제로 어떻게 수행할 것인가?
```

---

## 5. Agent와 Tool의 관계

프로젝트에서는 다음 원칙을 사용함.

```text
Agent
= 판단 / 분석 / Tool 선택

Tool
= 실제 기능 실행
```

예를 들어:

```text
"이 내용은 경력이다."
→ Agent 판단

"ABC전자를 Organisation에 넣는다."
→ Agent 판단

"CV 데이터가 올바른지 검사한다."
→ validate_cv_data Tool

"CV를 HTML로 만든다."
→ create_cv_html Tool
```

HTML 생성 코드를 Agent 내부에 직접 작성하지 않고 Tool로 분리함.

이를 통해 실제 AI Agent 시스템에서 중요한 **Reasoning과 Action의 분리 구조**를 학습할 수 있음.

---

## 6. 지원하는 CV 정보

현재 Agent는 다음과 같은 정보를 처리하도록 구성되어 있음.

### 기본 정보

- Name
- Address
- Landline
- Mobile
- Email

### Skills

- Key Strengths
- Technical Skills
- Language Skills

### Experience

- Work Experience
- Research Experience
- Activities
- Projects

### Education

- Education
- Major
- Degree
- Institution
- Graduation Year

### 기타

- Certifications
- Interests
- Referees

사용자가 제공하지 않은 정보는 Agent가 임의로 생성하지 않도록 System Prompt에서 제한함.

---

## 7. CV HTML 구조

기본 CV 형식은 다음 순서로 구성됨.

```text
Name / Contact

Key Strengths

Work Experience

Education and Training

Certifications

Research Experience

Activities & Projects

Interests

Referees
```

선택 항목에 데이터가 없는 경우 해당 영역은 HTML 결과에서 자동으로 제외됨.

---

## 8. 주요 기술

프로젝트에서 사용한 주요 기술은 다음과 같음.

### AI / Agent

- LangChain
- LangGraph
- OpenAI API
- Tool Calling
- Custom Tool
- Agent Workflow

### Python

- Python
- Pydantic
- pathlib
- os
- re
- html
- python-dotenv

### Output

- HTML
- CSS
- A4 Print Layout

### Development

- VS Code
- PowerShell
- uv
- Python Virtual Environment
- LangGraph Studio

---

## 9. 프로젝트 구조

```text
project/
│
├── agent.py
│
├── tools.py
│
├── langgraph.json
│
├── requirements.txt
│
├── .env
│
├── .gitignore
│
│
└── output/
    └── cv.html
```

---

## 10. 파일 설명

### agent.py

CV Agent를 생성하는 파일임.

주요 내용:

- System Prompt
- 모델 설정
- Tool 등록
- `create_agent()` 실행
- LangGraph에 사용할 Agent export

---

### tools.py

Custom Tool과 CV 데이터 구조가 정의된 파일임.

포함 내용:

- Pydantic CV 데이터 모델
- WorkExperience
- EducationItem
- CertificationItem
- ResearchItem
- ActivityItem
- RefereeItem
- validate_cv_data
- create_cv_html

---

### langgraph.json

LangGraph 개발 서버에서 어떤 Agent를 실행할지 지정함.

예:

```json
{
    "dependencies": [
        "."
    ],
    "graphs": {
        "cv_agent": "./agent.py:agent"
    },
    "env": "./.env"
}
```

---

### .env

API Key 및 모델 설정을 저장함.

예:

```text
OPENAI_API_KEY=YOUR_API_KEY

CV_AGENT_MODEL=openai:gpt-5.4-mini
```

`.env` 파일은 외부에 공개하거나 Git Repository에 업로드하면 안 됨.

---

## 11. 실행 방법

프로젝트 디렉터리로 이동함.

```powershell
cd 프로젝트경로
```

필요한 패키지를 설치함.

```powershell
uv pip install -r requirements.txt
```

LangGraph 개발 서버를 실행함.

```powershell
uv run langgraph dev
```

정상적으로 실행되면 다음과 같은 주소가 출력됨.

```text
API
http://127.0.0.1:2024

LangGraph Studio
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

API Docs
http://127.0.0.1:2024/docs
```

LangGraph Studio에서 Agent를 직접 테스트할 수 있음.

---

## 12. 테스트 예시

다음과 같은 Prompt를 입력할 수 있음.

```text
내 CV를 HTML로 만들어줘.

이름은 김민수이고 서울에 살고 있다.
휴대폰은 010-1234-5678이고 이메일은 minsu@example.com이다.

상명대학교 전자공학과를 졸업했다.

2025년 ABC Electronics에서 연구개발 인턴으로 근무했다.

주요 업무는 STM32 펌웨어 개발,
센서 인터페이스 회로 설계,
PCB 설계 및 디버깅이었다.

Python, C, STM32, PCB 설계,
회로 분석을 사용할 수 있다.

전자기사 자격증이 있다.

취미는 사진 촬영과 전자기기 수리이다.
```

Agent가 정상적으로 동작하면 다음 과정이 실행됨.

```text
Human Message

↓

Agent

↓

validate_cv_data

↓

VALIDATION_OK

↓

Agent

↓

create_cv_html

↓

output/cv.html
```

LangGraph Studio에서 이 과정을 시각적으로 확인할 수 있음.

---

## 13. 프로젝트에서 학습한 내용

이 프로젝트를 통해 LLM이 단순히 텍스트를 생성하는 것과 AI Agent가 실제 작업을 수행하는 것의 차이를 학습할 수 있었음.

일반적인 LLM 사용에서는:

```text
User
↓
LLM
↓
Text Response
```

구조가 대부분임.

반면 이번 프로젝트에서는:

```text
User
↓
Agent
↓
Reasoning
↓
Tool Selection
↓
Tool Execution
↓
Result
```

구조를 사용함.

특히 Agent가 모든 기능을 직접 처리하도록 만들지 않고 기능별 Tool을 분리함으로써 Agent 기반 시스템의 기본 구조를 구현함.

---

## 14. 향후 개선 방향

현재 프로젝트를 기반으로 다음 기능을 추가할 수 있음.

### CV Template 선택 기능

여러 HTML / CSS Template 중 원하는 형식을 선택할 수 있도록 개선 가능함.

```text
Simple
Professional
Engineering
Research
Modern
```

등의 Template을 지원할 수 있음.

---

### PDF 생성 기능

HTML CV를 기반으로 PDF까지 자동 생성하는 Tool을 추가할 수 있음.

예:

```text
create_cv_html
↓
convert_html_to_pdf
↓
cv.pdf
```

---

### CV 평가 Tool

작성된 CV를 분석하여 다음 항목을 검사하는 Tool을 추가할 수 있음.

- 정보 누락
- 문장 길이
- 반복 표현
- 기술 키워드
- 프로젝트 설명 품질
- 직무 관련성

---

### Job Description 분석

지원하려는 회사의 채용공고를 입력하면 요구 기술을 분석한 뒤 CV를 맞춤형으로 생성하도록 확장할 수 있음.

```text
CV Data
+
Job Description

↓

Agent

↓

Relevant Skill Selection

↓

Customized CV
```

---

### Web Search Tool

기업, 학교, 자격증 등의 공식 명칭을 확인하기 위해 검색 Tool을 추가할 수 있음.

단, 사용자가 제공하지 않은 경력이나 사실을 자동으로 생성하지 않도록 검증 과정이 필요함.

---

## 15. 최종 목표

이 프로젝트의 최종 목표는 단순한 CV 작성 프로그램이 아니라,

```text
자연어 입력
+
LLM Reasoning
+
Structured Data
+
Custom Tools
+
File Generation
```

을 결합한 Agent 기반 자동화 시스템을 구현하는 것임.

CV 생성이라는 비교적 명확한 문제를 통해 Agent, Tool Calling, Structured Data, LangGraph Workflow의 기본 구조를 학습하고 실제로 구현하는 것을 목표로 함.
