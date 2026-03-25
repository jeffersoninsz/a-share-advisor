"""
SQLite 数据库操作模块
负责初始化数据库、保存/查询分析报告、更新准确率记录。
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import DATABASE_PATH
from storage.models import AnalysisReport, ReportRecord, AccuracyRecord


def _get_connection() -> sqlite3.Connection:
    """获取数据库连接，确保父目录存在。"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库表结构（如果不存在则创建）。"""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                market_summary TEXT DEFAULT '',
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT DEFAULT '',
                action TEXT NOT NULL,
                confidence TEXT DEFAULT '',
                actual_result TEXT DEFAULT 'PENDING',
                marked_at TEXT,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );

            CREATE INDEX IF NOT EXISTS idx_reports_timestamp
                ON reports(timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_accuracy_report_id
                ON accuracy(report_id);
        """)
        conn.commit()
    finally:
        conn.close()


def save_report(report: AnalysisReport) -> int:
    """
    保存分析报告到数据库。

    Args:
        report: AnalysisReport 对象

    Returns:
        新插入的报告 ID
    """
    conn = _get_connection()
    try:
        report_json = report.model_dump_json(ensure_ascii=False)
        cursor = conn.execute(
            """
            INSERT INTO reports (timestamp, market_summary, report_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                report.timestamp,
                report.market_summary,
                report_json,
                datetime.now().isoformat(),
            ),
        )
        report_id = cursor.lastrowid
        conn.commit()

        # 同时插入准确率追踪记录
        for rec in report.recommendations:
            conn.execute(
                """
                INSERT INTO accuracy (report_id, symbol, name, action, confidence, actual_result)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
                """,
                (report_id, rec.symbol, rec.name, rec.action, rec.confidence),
            )
        conn.commit()

        return report_id
    finally:
        conn.close()


def get_history_reports(limit: int = 10) -> list[dict]:
    """
    查询最近的历史分析报告。

    Args:
        limit: 返回条数

    Returns:
        报告列表（按时间倒序）
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT id, timestamp, market_summary, report_json, created_at
            FROM reports
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_report_by_id(report_id: int) -> Optional[dict]:
    """根据 ID 获取单个报告。"""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_accuracy(record_id: int, actual_result: str) -> bool:
    """
    更新推荐准确率记录。

    Args:
        record_id: 准确率记录 ID
        actual_result: 实际结果 WIN / LOSE

    Returns:
        是否更新成功
    """
    if actual_result not in ("WIN", "LOSE"):
        return False

    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE accuracy
            SET actual_result = ?, marked_at = ?
            WHERE id = ?
            """,
            (actual_result, datetime.now().isoformat(), record_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_accuracy_stats() -> dict:
    """
    计算总体推荐准确率统计。

    Returns:
        包含 total, wins, losses, pending, win_rate 的字典
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_result = 'LOSE' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_result = 'PENDING' THEN 1 ELSE 0 END) as pending
            FROM accuracy
            """
        )
        row = cursor.fetchone()
        total = row["total"] or 0
        wins = row["wins"] or 0
        losses = row["losses"] or 0
        pending = row["pending"] or 0
        decided = wins + losses
        win_rate = round(wins / decided * 100, 1) if decided > 0 else 0.0

        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": win_rate,
        }
    finally:
        conn.close()


def get_accuracy_records(report_id: Optional[int] = None) -> list[dict]:
    """获取准确率记录列表，可按报告 ID 过滤。"""
    conn = _get_connection()
    try:
        if report_id:
            cursor = conn.execute(
                "SELECT * FROM accuracy WHERE report_id = ? ORDER BY id",
                (report_id,),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM accuracy ORDER BY id DESC LIMIT 100"
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
