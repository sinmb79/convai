import secrets
import warnings
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "CONAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = ""  # 반드시 .env에서 설정 (예: python -c "import secrets; print(secrets.token_hex(32))")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/conai"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/conai"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "conai-documents"

    # Claude AI
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-5"
    CLAUDE_MAX_TOKENS: int = 4096

    # Weather API (기상청)
    KMA_API_KEY: str = ""
    KMA_BASE_URL: str = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"

    # Kakao
    KAKAO_APP_KEY: str = ""
    KAKAO_ADMIN_KEY: str = ""
    KAKAO_CHANNEL_ID: str = ""

    # S3 / Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET: str = "conai-files"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://conai.app"]

    # Embedding (Voyage AI or OpenAI)
    VOYAGE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "voyage-3"
    EMBEDDING_DIMENSIONS: int = 1024


settings = Settings()

# 운영 환경에서 기본 SECRET_KEY 사용 방지
if not settings.SECRET_KEY:
    if not settings.DEBUG:
        raise ValueError(
            "SECRET_KEY가 설정되지 않았습니다.\n"
            ".env 파일에 SECRET_KEY를 추가하세요:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            "위 명령으로 생성한 값을 SECRET_KEY=값 형태로 .env에 입력하세요."
        )
    else:
        # 개발 환경에서만 임시 키 허용 (경고 표시)
        settings.SECRET_KEY = secrets.token_hex(32)
        warnings.warn(
            "개발 모드: SECRET_KEY가 자동 생성되었습니다. 운영 환경에서는 .env에 고정 값을 설정하세요.",
            stacklevel=2,
        )
