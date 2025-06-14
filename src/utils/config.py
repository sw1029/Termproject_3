from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    data_dir: Path = Path('data')
    model_dir: Path = Path('model')
    model_name: str = "dnotitia/Llama-DNA-1.0-8B-Instruct"
    openai_api_key: str = 'YOUR_API_KEY'

settings = Settings()
