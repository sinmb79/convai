"""
Core Claude API wrapper.
Shared by all AI-powered features: daily reports, inspection gen, report gen, RAG.
"""
import anthropic
from app.config import settings

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def complete(
    messages: list[dict],
    system: str,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> str:
    """
    Call Claude and return the text response.
    Logs token usage for cost monitoring.
    """
    client = get_client()
    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=max_tokens or settings.CLAUDE_MAX_TOKENS,
        temperature=temperature,
        system=system,
        messages=messages,
    )

    # Log token usage
    usage = response.usage
    print(f"[AI] input={usage.input_tokens} output={usage.output_tokens} total={usage.input_tokens + usage.output_tokens}")

    return response.content[0].text


async def complete_json(
    messages: list[dict],
    system: str,
    temperature: float = 0.3,
) -> str:
    """Call Claude with JSON output instruction."""
    json_system = system + "\n\n반드시 유효한 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요."
    return await complete(messages, json_system, temperature)
