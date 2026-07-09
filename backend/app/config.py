"""
配置文件
"""
from pydantic_settings import BaseSettings
from typing import List, Union
import json


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "12345678"
    DB_NAME: str = "lottery_wxapp"
    DB_CHARSET: str = "utf8mb4"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30

    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "赛事推演预测系统"

    # 数据源配置
    USE_API: bool = True
    API_FOOTBALL_KEY: str = ""
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"

    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = True

    # CORS 配置 - 支持字符串或列表
    CORS_ORIGINS: Union[str, List[str]] = '["*"]'

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""

    # 小程序URL配置（用于分享卡片二维码）
    MINIAPP_URL: str = "pages/entry/entry"

    # API基础URL（用于生成分享卡片URL）
    API_BASE_URL: str = "http://localhost:8000"

    REVIEW_MODE: bool = False

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接 URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"

    def get_cors_origins(self) -> List[str]:
        """获取 CORS 允许的源列表"""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        try:
            # 尝试解析 JSON 字符串
            return json.loads(self.CORS_ORIGINS)
        except:
            # 如果解析失败，返回默认值
            return ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True


# 创建配置实例
# 环境变量优先级最高，然后是 .env 文件
# 云托管环境直接使用环境变量，本地开发使用 .env 文件
settings = Settings()
