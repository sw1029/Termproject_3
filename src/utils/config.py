from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Literal

class Settings(BaseSettings):
    data_dir: Path = Path('data')
    model_dir: Path = Path('model')

    # classifier model used for intent detection
    classifier_model_name: str = "Qwen/Qwen3-14B"

    # generator model configuration
    generator_model_type: Literal['local', 'openai'] = 'local'
    generator_model_name_or_path: str = "beomi/Llama-3-Open-Ko-8B"

settings = Settings()
