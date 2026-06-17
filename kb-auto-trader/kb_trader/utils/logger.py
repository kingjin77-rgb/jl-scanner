"""로거 설정"""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: str = "logs", level: str = "INFO"):
    """loguru 기반 구조화 로거 설정"""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    logger.remove()

    # 콘솔 출력
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True
    )

    # 전체 로그 파일
    logger.add(
        log_path / "trading_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} | {message}",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        encoding="utf-8"
    )

    # 오류 전용 파일
    logger.add(
        log_path / "errors_{time:YYYY-MM}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} | {message}\n{exception}",
        rotation="1 month",
        retention="6 months",
        encoding="utf-8"
    )

    # 매매 전용 로그
    logger.add(
        log_path / "trades_{time:YYYY-MM}.log",
        level="SUCCESS",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda r: r["level"].name in ("SUCCESS", "WARNING", "CRITICAL"),
        rotation="1 month",
        encoding="utf-8"
    )

    logger.info("로거 초기화 완료 (레벨: {})", level)
    return logger
