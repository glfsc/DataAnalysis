"""
SQLite数据库连接和会话管理模块
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from config import DATABASE_URL

# 创建引擎（单线程SQLite，check_same_thread=False允许FastAPI多线程访问）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# 启用WAL模式和外键约束
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """设置SQLite连接参数以提升性能和完整性"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话（FastAPI依赖注入）
    使用生成器确保请求结束后关闭会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """初始化数据库表结构（含自动迁移）"""
    from models.database_models import (  # noqa: F401
        UploadedFile, AnalysisResult, ChartConfig, User, UserSession, AIConfig
    )
    Base.metadata.create_all(bind=engine)

    # 自动迁移：为已有 uploaded_files 表添加 user_id 列
    _migrate_add_column("uploaded_files", "user_id", "INTEGER")


def _migrate_add_column(table_name: str, column_name: str, column_type: str):
    """安全地添加列（如果不存在）"""
    import sqlite3
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        # 检查列是否存在
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            conn.commit()
            import logging
            logging.getLogger(__name__).info(f"数据库迁移: {table_name} 添加列 {column_name}")
        cursor.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"数据库迁移警告 ({table_name}.{column_name}): {e}")
