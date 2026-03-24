SYSTEM_PROMPT = """당신은 대한민국 토목건설 현장의 작업일보 작성 전문가입니다.
현장소장이 제공하는 정보를 바탕으로 공식적인 작업일보를 작성합니다.

작업일보 작성 원칙:
1. 건설기술진흥법 시행규칙에 따른 서식 기준을 준수합니다
2. 객관적이고 사실에 근거한 내용만 기록합니다
3. 전문 건설 용어를 사용하되, 명확하고 이해하기 쉽게 작성합니다
4. 날씨, 인원, 장비, 작업내용을 구조적으로 기술합니다
5. 특이사항이 있으면 간결하게 기록합니다

응답 형식:
- 작업내용은 공종별로 구분하여 기술
- 각 항목은 간결하고 명확하게
- 존칭이나 과도한 수식어 사용 금지
"""

def build_prompt(
    project_name: str,
    report_date: str,
    weather_summary: str,
    temperature: str,
    workers: dict,
    equipment: list,
    work_items: list[str],
    issues: str | None,
) -> str:
    workers_text = ", ".join([f"{k} {v}명" for k, v in workers.items()])
    equipment_text = ", ".join([f"{e.get('type', '')} {e.get('count', 1)}대" for e in equipment])
    work_text = "\n".join([f"- {item}" for item in work_items])

    prompt = f"""다음 정보를 바탕으로 작업일보의 '작업내용' 항목을 작성해주세요.

[현장 정보]
- 공사명: {project_name}
- 작업일자: {report_date}
- 날씨: {weather_summary}, 기온 {temperature}

[투입 인원]
{workers_text}

[투입 장비]
{equipment_text if equipment_text else "장비 없음"}

[당일 작업 항목]
{work_text}

[특이사항]
{issues if issues else "특이사항 없음"}

위 정보를 기반으로 공식 작업일보의 '금일 작업내용' 항목을 200~400자로 작성해주세요.
공종별로 나누어 구체적이고 전문적으로 기술하세요."""
    return prompt
