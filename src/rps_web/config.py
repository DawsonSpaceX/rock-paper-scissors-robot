from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    opencv_device: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30

    host: str = "0.0.0.0"
    port: int = 8000

    bob_threshold_px: float = 35.0
    bob_cooldown_ms: int = 300
    lock_idle_sec: float = 1.0


settings = Settings()
