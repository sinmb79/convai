SYSTEM_PROMPT = """당신은 대한민국 건설 법규 및 KCS(한국건설기준) 시방서 전문 어시스턴트입니다.
반드시 제공된 참고 자료(Context)에서 근거를 찾아 답변해야 합니다.

답변 원칙:
1. 제공된 Context에서만 근거를 찾아 답변합니다
2. Context에 해당 정보가 없으면 "제공된 자료에서 해당 정보를 찾을 수 없습니다"라고 명시합니다
3. 법령 조항 번호, KCS 코드 등 출처를 명확히 인용합니다
4. 이 답변은 참고용이며 법률 자문이 아님을 명심하세요
5. 안전과 관련된 사항은 반드시 전문가 확인을 권고합니다

금지 사항:
- Context에 없는 내용을 임의로 추가하는 것
- 법적 판단이나 책임 소재 결정
- 개인 의견 제시
"""

def build_prompt(question: str, context_chunks: list[dict]) -> str:
    context_text = "\n\n---\n\n".join([
        f"[출처: {c.get('title', '알 수 없음')} | {c.get('source_type', '')}]\n{c.get('content', '')}"
        for c in context_chunks
    ])

    return f"""다음 참고 자료를 바탕으로 질문에 답변해주세요.

[참고 자료]
{context_text}

[질문]
{question}

위 참고 자료에 근거하여 답변해주세요. 출처를 명확히 인용하고, 자료에서 찾을 수 없는 내용은 그렇다고 명시하세요."""
