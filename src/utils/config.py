from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Literal

# Absolute project root directory
ROOT_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # Use absolute paths so modules work regardless of the current working directory
    data_dir: Path = ROOT_DIR / 'data'
    model_dir: Path = ROOT_DIR / 'model'

    # classifier model used for intent detection
    classifier_model_name: str = "Qwen/Qwen3-14B"

    # generator model configuration
    generator_model_type: Literal['local', 'openai'] = 'local'
    generator_model_name_or_path: str = "beomi/Llama-3-Open-Ko-8B"

settings = Settings()
