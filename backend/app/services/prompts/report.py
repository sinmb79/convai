WEEKLY_SYSTEM_PROMPT = """당신은 대한민국 토목건설 현장의 공사관리 전문가입니다.
주간 공정보고서를 작성합니다. 발주처에 제출하는 공식 문서입니다.

작성 원칙:
1. 객관적 데이터를 기반으로 작성합니다
2. 계획 대비 실적을 명확히 비교합니다
3. 다음 주 예정 공사를 구체적으로 기술합니다
4. 문제점과 대책을 포함합니다
5. 전문적이고 간결한 문체를 사용합니다
"""

MONTHLY_SYSTEM_PROMPT = """당신은 대한민국 토목건설 현장의 공사관리 전문가입니다.
월간 공정보고서를 작성합니다. 발주처에 제출하는 공식 문서입니다.

작성 원칙:
1. 당월 주요 공사 실적을 종합합니다
2. 공정률 현황과 기성 현황을 포함합니다
3. 주요 문제점과 해결 내용을 기술합니다
4. 익월 공사 계획을 수립합니다
5. 공사 품질/안전 현황을 포함합니다
"""

def build_weekly_prompt(
    project_name: str,
    period_start: str,
    period_end: str,
    daily_summaries: list[dict],
    overall_progress_pct: float,
    weather_issues: list[str],
) -> str:
    summaries_text = "\n".join([
        f"- {s.get('date', '')}: {s.get('work_content', '')[:100]}"
        for s in daily_summaries
    ])

    return f"""다음 정보를 바탕으로 주간 공정보고서 '금주 공사현황' 섹션을 작성해주세요.

[보고 기간]
- 공사명: {project_name}
- 기간: {period_start} ~ {period_end}

[일별 작업 현황]
{summaries_text if summaries_text else "작업일보 없음"}

[공정 현황]
- 전체 공정률: {overall_progress_pct:.1f}%

[날씨 영향]
{chr(10).join(weather_issues) if weather_issues else "날씨 특이사항 없음"}

주간 공정보고서 형식으로 400~600자 분량으로 작성해주세요:
1. 금주 주요 공사 내용
2. 공정 현황 (계획 대비 실적)
3. 특이사항 및 대책
4. 차주 예정 공사"""


def build_monthly_prompt(
    project_name: str,
    period_start: str,
    period_end: str,
    weekly_summaries: list[str],
    overall_progress_pct: float,
) -> str:
    return f"""다음 정보를 바탕으로 월간 공정보고서를 작성해주세요.

[보고 기간]
- 공사명: {project_name}
- 기간: {period_start} ~ {period_end}
- 전체 공정률: {overall_progress_pct:.1f}%

[주간별 현황 요약]
{chr(10).join(weekly_summaries) if weekly_summaries else "주간 현황 없음"}

월간 공정보고서 형식으로 600~800자 분량으로 작성해주세요:
1. 당월 공사 개요
2. 공정 현황 (계획 대비 실적, 공정률)
3. 주요 시공 내용
4. 품질/안전 현황
5. 문제점 및 대책
6. 익월 공사 계획"""
