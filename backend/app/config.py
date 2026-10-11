from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    app_env: str = "development"
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
