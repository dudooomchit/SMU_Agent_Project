from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field


# ============================================================
# CV 데이터 모델
# ============================================================

class WorkExperience(BaseModel):
    """경력 항목."""

    organisation: str = Field(
        description="회사, 기관, 조직명"
    )

    role: str = Field(
        default="",
        description="직무, 직책, 역할"
    )

    date: str = Field(
        default="",
        description="근무 기간 또는 날짜"
    )

    details: list[str] = Field(
        default_factory=list,
        description="주요 업무, 성과, 담당 내용"
    )


class EducationItem(BaseModel):
    """학력 항목."""

    degree: str = Field(
        default="",
        description="학위 또는 과정명"
    )

    major: str = Field(
        default="",
        description="전공"
    )

    institution: str = Field(
        default="",
        description="학교 또는 교육기관"
    )

    year: str = Field(
        default="",
        description="졸업연도 또는 재학 기간"
    )

    details: list[str] = Field(
        default_factory=list,
        description="추가 학력 설명"
    )


class CertificationItem(BaseModel):
    """자격증 항목."""

    name: str = Field(
        description="자격증 또는 인증명"
    )

    issuer: str = Field(
        default="",
        description="발급 기관"
    )

    date: str = Field(
        default="",
        description="취득일 또는 취득연도"
    )


class ResearchItem(BaseModel):
    """연구 이력 항목."""

    title: str = Field(
        description="연구명, 논문명 또는 연구 주제"
    )

    organisation: str = Field(
        default="",
        description="연구실, 학교, 기관명"
    )

    date: str = Field(
        default="",
        description="연구 기간"
    )

    details: list[str] = Field(
        default_factory=list,
        description="연구 내용, 역할, 결과"
    )


class ActivityItem(BaseModel):
    """대외활동 또는 프로젝트 항목."""

    organisation: str = Field(
        default="",
        description="기관, 팀 또는 프로젝트명"
    )

    role: str = Field(
        default="",
        description="역할 또는 직책"
    )

    date: str = Field(
        default="",
        description="활동 기간"
    )

    details: list[str] = Field(
        default_factory=list,
        description="활동 내용과 성과"
    )


class RefereeItem(BaseModel):
    """추천인 항목."""

    name: str = Field(
        description="추천인 이름"
    )

    relation: str = Field(
        default="",
        description="지원자와의 관계 또는 직책"
    )

    contact: str = Field(
        default="",
        description="이메일, 전화번호 등 연락처"
    )


# ============================================================
# 내부 유틸리티 함수
#
# Tool이 아님.
# HTML 생성 Tool 내부에서만 사용하는 일반 Python 함수임.
# ============================================================

def _clean(value: Optional[str]) -> str:
    """HTML 출력용 문자열을 안전하게 변환."""

    if value is None:
        return ""

    return html.escape(str(value).strip())


def _safe_filename(filename: str) -> str:
    """파일명에서 위험한 경로 문자를 제거."""

    filename = Path(filename or "cv.html").name

    filename = re.sub(
        r"[^\w.\-가-힣 ]+",
        "_",
        filename,
        flags=re.UNICODE,
    ).strip()

    if not filename:
        filename = "cv.html"

    if not filename.lower().endswith(".html"):
        filename += ".html"

    return filename


def _render_bullets(items: list[str]) -> str:
    """문자열 리스트를 HTML bullet list로 변환."""

    cleaned = [
        _clean(item)
        for item in items
        if str(item).strip()
    ]

    if not cleaned:
        return ""

    li = "".join(
        f"<li>{item}</li>"
        for item in cleaned
    )

    return f'<ul class="bullet-list">{li}</ul>'


def _render_section(title: str, body: str) -> str:
    """내용이 존재할 경우에만 HTML section 생성."""

    if not body.strip():
        return ""

    return f"""
    <section class="section">
        <h2>{_clean(title)}</h2>
        {body}
    </section>
    """


# ============================================================
# Tool 1
# CV 데이터 검증
# ============================================================

@tool(parse_docstring=True)
def validate_cv_data(
    name: str,
    email: str = "",
    mobile: str = "",
    education: Optional[list[EducationItem]] = None,
    work_experience: Optional[list[WorkExperience]] = None,
) -> str:
    """HTML CV 생성 전에 핵심 CV 데이터가 사용 가능한지 검사합니다.

    이름은 필수로 검사합니다.
    이메일과 휴대폰 번호는 값이 있을 경우 간단한 형식 검사를 수행합니다.
    학력과 경력이 없는 경우 오류가 아닌 경고를 반환합니다.

    Args:
        name: 지원자 이름.
        email: 이메일 주소.
        mobile: 휴대폰 번호.
        education: 학력 목록.
        work_experience: 경력 목록.

    Returns:
        검증 결과. 치명적인 문제가 있으면 VALIDATION_ERROR,
        생성 가능한 경우 VALIDATION_OK를 반환합니다.
    """

    errors: list[str] = []
    warnings: list[str] = []

    # --------------------------------------------------------
    # 이름 검사
    # --------------------------------------------------------

    if not name.strip():
        errors.append("이름이 없습니다.")

    # --------------------------------------------------------
    # 이메일 검사
    # --------------------------------------------------------

    if email.strip():

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(email_pattern, email.strip()):
            warnings.append(
                "이메일 형식이 일반적인 형식과 다릅니다."
            )

    # --------------------------------------------------------
    # 전화번호 검사
    # --------------------------------------------------------

    if mobile.strip():

        digits = re.sub(
            r"\D",
            "",
            mobile,
        )

        if len(digits) < 8:
            warnings.append(
                "휴대폰 번호가 너무 짧아 보입니다."
            )

    # --------------------------------------------------------
    # 학력 / 경력 검사
    # --------------------------------------------------------

    if not education:
        warnings.append(
            "학력 정보가 없습니다."
        )

    if not work_experience:
        warnings.append(
            "경력 정보가 없습니다."
        )

    # --------------------------------------------------------
    # 결과
    # --------------------------------------------------------

    if errors:

        result = ["VALIDATION_ERROR"]

        result.extend(
            f"- 오류: {item}"
            for item in errors
        )

        result.extend(
            f"- 경고: {item}"
            for item in warnings
        )

        return "\n".join(result)

    result = ["VALIDATION_OK"]

    if warnings:

        result.extend(
            f"- 경고: {item}"
            for item in warnings
        )

    else:

        result.append(
            "- 핵심 데이터 검사 완료"
        )

    return "\n".join(result)


# ============================================================
# Tool 2
# HTML CV 생성
# ============================================================

@tool(parse_docstring=True)
def create_cv_html(
    name: str,
    address: str = "",
    landline: str = "",
    mobile: str = "",
    email: str = "",
    strengths_heading: str = "Key Strengths",
    strengths: Optional[list[str]] = None,
    work_experience: Optional[list[WorkExperience]] = None,
    education: Optional[list[EducationItem]] = None,
    certifications: Optional[list[CertificationItem]] = None,
    research: Optional[list[ResearchItem]] = None,
    activities: Optional[list[ActivityItem]] = None,
    interests: Optional[list[str]] = None,
    referees: Optional[list[RefereeItem]] = None,
    output_filename: str = "cv.html",
) -> str:
    """구조화된 CV 데이터를 단정한 A4 HTML CV로 생성합니다.

    값이 없는 선택 섹션은 HTML에서 자동으로 생략합니다.
    생성된 파일은 프로젝트의 output 디렉터리에 저장합니다.

    Args:
        name: 지원자 이름.
        address: 주소.
        landline: 일반 전화번호.
        mobile: 휴대폰 번호.
        email: 이메일 주소.
        strengths_heading: 강점 섹션 제목.
        strengths: 핵심 강점 또는 기술 목록.
        work_experience: 경력 목록.
        education: 학력 목록.
        certifications: 자격증 목록.
        research: 연구 이력 목록.
        activities: 대외활동 또는 프로젝트 목록.
        interests: 관심사 또는 취미 목록.
        referees: 추천인 목록.
        output_filename: 생성할 HTML 파일명.

    Returns:
        생성 성공 여부와 저장된 HTML 파일 경로.
    """

    # --------------------------------------------------------
    # None → 빈 리스트
    # --------------------------------------------------------

    strengths = strengths or []
    work_experience = work_experience or []
    education = education or []
    certifications = certifications or []
    research = research or []
    activities = activities or []
    interests = interests or []
    referees = referees or []

    # --------------------------------------------------------
    # 필수값 검사
    # --------------------------------------------------------

    if not name.strip():
        return "생성 실패: 이름은 필수입니다."

    # ========================================================
    # Contact
    # ========================================================

    left_contact = ""

    if address.strip():

        left_contact = (
            f'<div class="contact-address">'
            f'{_clean(address)}'
            f'</div>'
        )

    right_rows = []

    if landline.strip():

        right_rows.append(
            f"<div>"
            f"<span>Landline</span>"
            f"{_clean(landline)}"
            f"</div>"
        )

    if mobile.strip():

        right_rows.append(
            f"<div>"
            f"<span>Mobile</span>"
            f"{_clean(mobile)}"
            f"</div>"
        )

    if email.strip():

        right_rows.append(
            f"<div>"
            f"<span>Email</span>"
            f"{_clean(email)}"
            f"</div>"
        )

    right_contact = "".join(right_rows)

    # ========================================================
    # Key Strengths
    # ========================================================

    strengths_html = _render_section(
        strengths_heading or "Key Strengths",
        _render_bullets(strengths),
    )

    # ========================================================
    # Work Experience
    # ========================================================

    work_blocks = []

    for item in work_experience:

        details = _render_bullets(
            item.details
        )

        work_blocks.append(
            f"""
            <article class="entry">

                <div class="entry-title">
                    {_clean(item.organisation)}
                </div>

                <div class="entry-meta">
                    <span>{_clean(item.role)}</span>
                    <span>{_clean(item.date)}</span>
                </div>

                {details}

            </article>
            """
        )

    work_html = _render_section(
        "Work Experience",
        "".join(work_blocks),
    )

    # ========================================================
    # Education
    # ========================================================

    education_blocks = []

    for item in education:

        title_parts = [
            part
            for part in [
                item.degree,
                item.major,
            ]
            if part.strip()
        ]

        title = " · ".join(
            title_parts
        )

        institution_line = _clean(
            item.institution
        )

        details = _render_bullets(
            item.details
        )

        education_blocks.append(
            f"""
            <article class="entry">

                <div class="entry-meta strong">
                    <span>{_clean(title)}</span>
                    <span>{_clean(item.year)}</span>
                </div>

                <div class="entry-subtitle">
                    {institution_line}
                </div>

                {details}

            </article>
            """
        )

    education_html = _render_section(
        "Education and Training",
        "".join(education_blocks),
    )

    # ========================================================
    # Certifications
    # ========================================================

    certification_blocks = []

    for item in certifications:

        subtitle_parts = [
            part
            for part in [
                item.issuer,
                item.date,
            ]
            if part.strip()
        ]

        subtitle = " · ".join(
            subtitle_parts
        )

        certification_blocks.append(
            f"""
            <article class="compact-entry">

                <div class="entry-title">
                    {_clean(item.name)}
                </div>

                <div class="entry-subtitle">
                    {_clean(subtitle)}
                </div>

            </article>
            """
        )

    certifications_html = _render_section(
        "Certifications",
        "".join(certification_blocks),
    )

    # ========================================================
    # Research
    # ========================================================

    research_blocks = []

    for item in research:

        research_blocks.append(
            f"""
            <article class="entry">

                <div class="entry-title">
                    {_clean(item.title)}
                </div>

                <div class="entry-meta">
                    <span>{_clean(item.organisation)}</span>
                    <span>{_clean(item.date)}</span>
                </div>

                {_render_bullets(item.details)}

            </article>
            """
        )

    research_html = _render_section(
        "Research Experience",
        "".join(research_blocks),
    )

    # ========================================================
    # Activities / Projects
    # ========================================================

    activity_blocks = []

    for item in activities:

        activity_blocks.append(
            f"""
            <article class="entry">

                <div class="entry-title">
                    {_clean(item.organisation)}
                </div>

                <div class="entry-meta">
                    <span>{_clean(item.role)}</span>
                    <span>{_clean(item.date)}</span>
                </div>

                {_render_bullets(item.details)}

            </article>
            """
        )

    activities_html = _render_section(
        "Activities & Projects",
        "".join(activity_blocks),
    )

    # ========================================================
    # Interests
    # ========================================================

    interests_html = _render_section(
        "Interests",
        _render_bullets(interests),
    )

    # ========================================================
    # Referees
    # ========================================================

    referee_blocks = []

    for item in referees:

        lines = [
            f"<strong>{_clean(item.name)}</strong>",
            _clean(item.relation),
            _clean(item.contact),
        ]

        lines = [
            line
            for line in lines
            if line
        ]

        referee_blocks.append(
            f"""
            <div class="referee">
                {"<br>".join(lines)}
            </div>
            """
        )

    referees_body = ""

    if referee_blocks:

        referees_body = (
            f'<div class="referee-grid">'
            f'{"".join(referee_blocks)}'
            f'</div>'
        )

    referees_html = _render_section(
        "Referees",
        referees_body,
    )

    # ========================================================
    # HTML 문서
    # ========================================================

    document = f"""<!DOCTYPE html>

<html lang="ko">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>{_clean(name)} - CV</title>

    <style>

        @page {{
            size: A4;
            margin: 16mm 18mm;
        }}


        * {{
            box-sizing: border-box;
        }}


        body {{
            margin: 0;

            background: #f3f3f3;

            color: #202020;

            font-family:
                Arial,
                "Noto Sans KR",
                "Malgun Gothic",
                sans-serif;

            font-size: 10.5pt;

            line-height: 1.45;
        }}


        .page {{
            width: 210mm;

            min-height: 297mm;

            margin: 18px auto;

            padding: 16mm 18mm;

            background: white;

            box-shadow:
                0 2px 12px
                rgba(0, 0, 0, 0.12);
        }}


        h1 {{
            margin:
                0
                0
                12px
                0;

            font-size: 25pt;

            font-weight: 700;

            letter-spacing: -0.4px;
        }}


        .contact {{
            display: grid;

            grid-template-columns:
                1fr
                1fr;

            gap: 24px;

            margin-bottom: 22px;

            font-size: 9.5pt;
        }}


        .contact-address {{
            white-space: pre-line;
        }}


        .contact-right {{
            justify-self: end;

            min-width: 230px;
        }}


        .contact-right div {{
            display: grid;

            grid-template-columns:
                66px
                1fr;

            gap: 8px;

            margin-bottom: 2px;
        }}


        .contact-right span {{
            font-weight: 700;
        }}


        .section {{
            margin-top: 18px;

            break-inside: avoid;
        }}


        h2 {{
            margin:
                0
                0
                8px
                0;

            padding-bottom: 4px;

            border-bottom:
                1px
                solid
                #333;

            font-size: 13.5pt;

            font-weight: 700;
        }}


        .entry {{
            margin:
                0
                0
                12px
                0;

            break-inside: avoid;
        }}


        .compact-entry {{
            margin-bottom: 7px;

            break-inside: avoid;
        }}


        .entry-title {{
            font-weight: 700;
        }}


        .entry-meta {{
            display: flex;

            justify-content:
                space-between;

            gap: 20px;

            margin-top: 1px;
        }}


        .entry-meta.strong {{
            font-weight: 700;
        }}


        .entry-subtitle {{
            margin-top: 1px;
        }}


        .bullet-list {{
            margin:
                4px
                0
                0
                18px;

            padding: 0;
        }}


        .bullet-list li {{
            margin: 1px 0;

            padding-left: 2px;
        }}


        .referee-grid {{
            display: grid;

            grid-template-columns:
                repeat(
                    2,
                    minmax(0, 1fr)
                );

            gap:
                12px
                30px;
        }}


        .referee {{
            break-inside: avoid;
        }}


        @media print {{

            body {{
                background: white;
            }}


            .page {{
                width: auto;

                min-height: auto;

                margin: 0;

                padding: 0;

                box-shadow: none;
            }}

        }}


        @media screen and (max-width: 850px) {{

            .page {{
                width: 100%;

                min-height: 0;

                margin: 0;

                padding: 28px;
            }}


            .contact {{
                grid-template-columns:
                    1fr;
            }}


            .contact-right {{
                justify-self: start;
            }}

        }}

    </style>

</head>


<body>

    <main class="page">

        <header>

            <h1>
                {_clean(name)}
            </h1>

            <div class="contact">

                <div>
                    {left_contact}
                </div>

                <div class="contact-right">
                    {right_contact}
                </div>

            </div>

        </header>


        {strengths_html}

        {work_html}

        {education_html}

        {certifications_html}

        {research_html}

        {activities_html}

        {interests_html}

        {referees_html}


    </main>

</body>

</html>
"""

    # ========================================================
    # 파일 저장
    # ========================================================

    project_dir = (
        Path(__file__)
        .resolve()
        .parent
    )

    output_dir = (
        project_dir
        / "output"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = _safe_filename(
        output_filename
    )

    output_path = (
        output_dir
        / safe_filename
    )

    output_path.write_text(
        document,
        encoding="utf-8",
    )

    return (
        "CV HTML 생성 완료\n"
        f"- 파일: {output_path}\n"
        "- 브라우저에서 열어 확인할 수 있습니다."
    )


# ============================================================
# CV Agent가 사용할 Tool 목록
# ============================================================

CV_TOOLS = [
    validate_cv_data,
    create_cv_html,
]