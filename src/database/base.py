from loguru import logger


def init_db() -> None:
    """Initialize database connections and run migrations if needed.

    This is a placeholder to keep the app boot sequence working. Replace with
    SQLAlchemy engine/session setup when a real DB is introduced.
    """
    logger.info("init_db: no-op (database not configured yet)")
