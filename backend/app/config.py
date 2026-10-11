from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    app_env: str = "production"  # dev helpers and weak defaults only work with APP_ENV=development
    database_url: str = "sqlite+pysqlite:///./dev.db"
    jwt_secret: str = "change-me"
    jwt_hours: int = 12
    demo_email: str = "owner@paypilot.demo"
    demo_password: str = "change-me"

    paypal_mode: str = "sandbox"  # sandbox or fake
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"
    paypal_webhook_id: str = ""
    paypal_sender_note: str = "Payment from PayPilot Shield"

    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    cors_origins: str = "http://localhost:5173"

    # Layer 1 default policy (replaced by the signed policy in Layer 2)
    default_auto_limit: float = 500
    default_monthly_budget: float = 5000


settings = Settings()

_WEAK = {"change-me", "change-me-to-a-long-random-string", ""}


def check_production_settings(s: Settings = settings) -> None:
    """Refuse to start outside development with default or weak secrets."""
    if s.app_env == "development":
        return
    problems = []
    if s.jwt_secret in _WEAK or len(s.jwt_secret) < 32:
        problems.append("JWT_SECRET must be set to a random value of at least 32 characters")
    if s.demo_password in _WEAK or len(s.demo_password) < 12:
        problems.append("DEMO_PASSWORD must be set to at least 12 characters")
    if problems:
        raise RuntimeError("Unsafe configuration for APP_ENV=" + s.app_env + ": " + "; ".join(problems))
