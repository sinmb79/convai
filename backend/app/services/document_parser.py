"""
설계도서 파싱 서비스 (Phase 3)
PDF 설계도서에서 공종·수량·규격을 AI로 자동 추출합니다.
HWP 출력은 Pandoc을 통해 변환합니다.
"""
import base64
import json
import re
import subprocess
import tempfile
import os
from pathlib import Path
from anthropic import AsyncAnthropic
from app.config import settings

_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_PARSE_SYSTEM = """당신은 건설 설계도서 분석 전문가입니다.
제공된 설계도서 내용에서 다음 정보를 추출하세요:
1. 공종 목록 (work_types): 주요 공종과 세부 공종
2. 수량 목록 (quantities): 각 공종별 수량과 단위
3. 규격 (specifications): 재료 규격, 강도, 등급
4. 특기 사항 (notes): 시공 시 주의사항, 특수 조건

JSON 형식으로만 반환하세요."""


async def parse_design_document_text(text: str) -> dict:
    """
    설계도서 텍스트에서 공종/수량/규격 추출 (Claude API).
    RAG 시드 스크립트로 읽은 텍스트를 직접 전달하는 용도.
    """
    prompt = f"""다음 설계도서 내용을 분석해주세요:

{text[:8000]}

JSON 형식으로만 반환하세요:
{{
  "work_types": ["터파기", "철근콘크리트", ...],
  "quantities": [
    {{"work_type": "터파기", "quantity": 500, "unit": "m³"}},
    ...
  ],
  "specifications": [
    {{"item": "콘크리트", "spec": "fck=24MPa", "notes": ""}},
    ...
  ],
  "notes": ["주의사항1", ...]
}}"""

    response = await _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2048,
        system=_PARSE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"error": "파싱 실패", "raw": raw[:500]}


async def parse_design_document_image(image_data: bytes, media_type: str = "image/jpeg") -> dict:
    """
    설계 도면 이미지에서 공종/수량/규격 추출 (Claude Vision).
    도면 스캔 이미지나 PDF 페이지를 직접 분석합니다.
    """
    image_b64 = base64.standard_b64encode(image_data).decode()

    response = await _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2048,
        system=_PARSE_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                {"type": "text", "text": "이 설계 도면/도서에서 공종, 수량, 규격을 추출해주세요. JSON으로만 반환하세요."},
            ],
        }],
    )

    raw = response.content[0].text.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"error": "파싱 실패", "raw": raw[:500]}


def convert_to_hwp(html_content: str, output_path: str | None = None) -> bytes | str:
    """
    HTML → HWP 변환 (Pandoc 필요).
    output_path 미지정 시 바이트 반환.

    사전 요구사항: pandoc 설치 필요
    설치: https://pandoc.org/installing.html
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
            f.write(html_content)
            html_path = f.name

        if output_path:
            out = output_path
        else:
            out = html_path.replace(".html", ".hwp")

        result = subprocess.run(
            ["pandoc", html_path, "-o", out, "--from=html"],
            capture_output=True, text=True, timeout=30,
        )

        os.unlink(html_path)

        if result.returncode != 0:
            raise RuntimeError(f"Pandoc 변환 실패: {result.stderr}")

        if output_path:
            return output_path
        else:
            with open(out, "rb") as f:
                data = f.read()
            os.unlink(out)
            return data

    except FileNotFoundError:
        raise RuntimeError(
            "Pandoc이 설치되지 않았습니다.\n"
            "설치: https://pandoc.org/installing.html\n"
            "Windows: winget install JohnMacFarlane.Pandoc"
        )
