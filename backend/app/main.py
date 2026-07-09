"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
import logging

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=== 应用启动中 ===")
    logger.info(f"环境: {'开发' if settings.DEBUG else '生产'}")
    logger.info(f"数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    # 初始化数据库表
    try:
        from app.database import engine, Base
        from app.models.user import User
        from app.models.recommendation import Recommendation
        from app.models.view_record import ViewRecord
        from app.models.daily_achievement import DailyAchievement

        logger.info("开始初始化数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info(f"✓ 数据库表初始化成功: {', '.join(Base.metadata.tables.keys())}")

        # 测试数据库连接
        with engine.connect() as conn:
            logger.info("✓ 数据库连接测试成功")

    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {str(e)}")
        logger.exception(e)
        # 不抛出异常，让应用继续启动以便查看日志

    yield

    # 关闭时执行
    logger.info("=== 应用关闭中 ===")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="赛事推演预测系统 API",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    """记录所有请求"""
    import json

    # 对于 POST/PUT 请求,记录请求体
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        if body:
            try:
                body_json = json.loads(body.decode())
                logger.debug(f"请求体: {json.dumps(body_json, ensure_ascii=False, indent=2)}")
            except:
                logger.debug(f"请求体(非JSON): {body[:200]}")

        # 重新构造请求以便后续处理
        from starlette.requests import Request
        async def receive():
            return {"type": "http.request", "body": body}
        request = Request(request.scope, receive)

    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "赛事推演预测系统 API",
        "version": "0.1.0",
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        from app.database import engine
        with engine.connect() as conn:
            return {
                "status": "ok",
                "database": "connected"
            }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }

@app.get(f"{settings.API_V1_PREFIX}/system/config")
async def get_system_config():
    """获取系统配置（公开接口，用于前端判断审核模式等）"""
    return {
        "review_mode": settings.REVIEW_MODE
    }

# 导入路由
from app.api import auth, recommendations, profile, history, view_records, daily_achievements, stats

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(recommendations.router, prefix=f"{settings.API_V1_PREFIX}", tags=["推荐"])
app.include_router(profile.router, prefix=f"{settings.API_V1_PREFIX}", tags=["个人资料"])
app.include_router(history.router, prefix=f"{settings.API_V1_PREFIX}", tags=["历史记录"])
app.include_router(view_records.router, prefix=f"{settings.API_V1_PREFIX}", tags=["浏览记录"])
app.include_router(daily_achievements.router, prefix=f"{settings.API_V1_PREFIX}", tags=["昨日战绩"])
app.include_router(stats.router, prefix=f"{settings.API_V1_PREFIX}/stats", tags=["统计数据"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )
