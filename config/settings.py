"""
ComplianceNavigator Configuration Settings
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # API Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///compliance_navigator.db", env="DATABASE_URL")
    
    # Vector Store Configuration
    chroma_persist_directory: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Regulatory APIs
    eu_open_data_api_key: Optional[str] = Field(default=None, env="EU_OPEN_DATA_API_KEY")
    german_regulatory_api_key: Optional[str] = Field(default=None, env="GERMAN_REGULATORY_API_KEY")
    
    # Agent Configuration
    max_concurrent_agents: int = Field(default=5, env="MAX_CONCURRENT_AGENTS")
    agent_timeout_seconds: int = Field(default=300, env="AGENT_TIMEOUT_SECONDS")
    
    # Monitoring Configuration
    monitoring_interval_hours: int = Field(default=24, env="MONITORING_INTERVAL_HOURS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="compliance_navigator.log", env="LOG_FILE")
    
    # UI Configuration
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    
    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_directory: Path = project_root / "data"
    regulations_directory: Path = data_directory / "regulations"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_directory.mkdir(exist_ok=True)
        self.regulations_directory.mkdir(exist_ok=True)
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings() 