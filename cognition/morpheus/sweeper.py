"""
Morpheus VRAM Sweeper.
Monitors GPU fragmentation and triggers cleanup operations to reclaim contiguous memory blocks.
"""
import time
import threading
import datetime as _dt
import os
import subprocess
from typing import Optional
from src.utils.logging_config import setup_logger
from ..morpheus.monitor import get_gpu_memory_info, get_fragmentation_estimate
from ..morpheus.loader import ModelLoader
from src.clotho.activity import ActivityMonitor
from src.architrave import GatewayArchitrave

logger = setup_logger(__name__)


class VRAMSweeper:
    """
    VRAM fragmentation monitor and cleanup agent.

    Triggers model unload when:
    - GPU VRAM used exceeds `swap_threshold` GB
    - Fragmentation estimate exceeds `frag_threshold` (0.0-1.0)
    """

    # Phase 11.18.15: Morpheus 8GB Dynamic Config moved to vram_config.py
    from .vram_config import MODEL_SETS, EVICTION_ORDER

    def __init__(self, swap_threshold_gb: Optional[float] = None, frag_threshold: Optional[float] = None):
        import os
        from ..morpheus.registry import GPU_USABLE_VRAM_GB
        self.swap_threshold = swap_threshold_gb or float(os.getenv("VRAM_SWAP_THRESHOLD_GB", "6.5"))
        self.frag_threshold = frag_threshold or float(os.getenv("VRAM_FRAG_THRESHOLD", "0.3"))
        self._lock = threading.Lock()
        self._sweep_count = 0
        self._last_sweep_time = 0.0

    def check_and_sweep(self, loader: Optional[ModelLoader] = None, required_vram_gb: float = 0.0) -> bool:
        """
        Check GPU state and sweep if thresholds are exceeded.
        Returns True if sweep was performed.
        """
        with self._lock:
            gpu_info = get_gpu_memory_info()
            used_gb = gpu_info.get("used_gb", 0)
            free_gb = gpu_info.get("free_gb", 0)
            frag = get_fragmentation_estimate()

            # Phase 11.18.15: Dynamic thresholding including required_vram_gb
            should_sweep = (used_gb >= self.swap_threshold) or (frag >= self.frag_threshold) or (free_gb < required_vram_gb)

            if not should_sweep:
                return False

            now = time.time()
            if now - self._last_sweep_time < 5.0:  # Reduced cooldown for emergency sweeps
                return False

            logger.warning(
                f"VRAMSweeper: Sweep triggered (used={used_gb}GB, free={free_gb}GB, "
                f"req={required_vram_gb}GB, frag={frag:.2f})"
            )

            if loader:
                loader.sync_from_ollama()
                current_model = loader.loaded
                if current_model:
                    # Check if model is pinned
                    if loader.should_pin(current_model):
                        # Pinned models are only evicted if they are low-priority in the EVICTION_ORDER
                        # or if we are extremely low on VRAM.
                        priority_idx = self.EVICTION_ORDER.index(current_model) if current_model in self.EVICTION_ORDER else 99
                        if priority_idx > 5 and free_gb > 0.5: # Don't evict high-priority pinned models unless desperate
                            logger.info(f"VRAMSweeper: Model '{current_model}' is pinned and high priority. Skipping sweep.")
                            return False
                    
                    logger.info(f"VRAMSweeper: Evicting '{current_model}' based on EVICTION_ORDER.")
                    loader.unload_current()

            # Phase 11.19: Ollama Health Check & Self-Healing
            if not self.check_ollama_health():
                if self._has_active_operations():
                    logger.info("VRAMSweeper: Ollama health check failed, but active operations detected. Skipping heal_ollama to prevent context cancellation.")
                else:
                    logger.warning("VRAMSweeper: Ollama unresponsive. Triggering self-healing restart...")
                    self.heal_ollama()

            # Phase 11.22.1: Gateway Health Check (Proxy Tunnel)
            if not self.check_gateway_health():
                logger.warning("VRAMSweeper: Antigravity Gateway (Proxy Tunnel) is DOWN. localhost:32553 unreachable.")

            self._sweep_count += 1
            self._last_sweep_time = now
            
            # Trigger Database Pruning after successful VRAM sweep (Operational Hardening)
            self.prune_databases()
            
            return True

    def _has_active_operations(self) -> bool:
        """Returns True if any tool or agent is currently active."""
        return ActivityMonitor().is_busy

    def check_ollama_health(self) -> bool:
        """Checks if Ollama API is responding to heartbeats."""
        try:
            import requests
            url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").replace("/v1", "")
            resp = requests.get(f"{url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def check_gateway_health(self) -> bool:
        """Checks if Antigravity Gateway (Proxy Tunnel) is responding."""
        try:
            # Singleton instance to use the 30s cache
            return GatewayArchitrave().is_gateway_healthy()
        except Exception:
            return False

    def heal_ollama(self):
        """Forcefully restarts Ollama service components if they hang."""
        try:
            # 1. Kill hanging processes
            subprocess.run(["taskkill", "/F", "/IM", "ollama*", "/T"], capture_output=True)
            time.sleep(2)
            # 2. Start Ollama App (Windows specific path or command)
            # Using start command to run in background
            subprocess.Popen(["cmd", "/c", "start", "ollama", "app"], shell=True)
            logger.info("VRAMSweeper: Ollama restart command issued.")
            time.sleep(5) # Wait for bootstrap
        except Exception as e:
            logger.error(f"VRAMSweeper: Self-healing failed ({e})")

    def _load_governance_config(self) -> dict:
        """Loads db_maintenance config from rules.json (GOVERNANCE_CONFIG)."""
        import json
        default = {"retention_days": 30, "row_limit": 1000, "exclude_tables": []}
        try:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            path = os.path.join(base, ".antigravity", "rules.json")
            with open(path) as f:
                cfg = json.load(f)
            return cfg.get("db_maintenance", default)
        except Exception as e:
            logger.debug(f"VRAMSweeper: Governance config load failed ({e}), using defaults")
            return default

    @staticmethod
    def _cutoff_val(time_type: str, days: int = 30) -> float:
        cutoff_s = int(time.time()) - (days * 86400)
        if time_type == "int_ms":
            return cutoff_s * 1000
        if time_type == "float":
            return cutoff_s
        return _dt.datetime.fromtimestamp(cutoff_s, tz=_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _prune_sqlite(self, gov: dict, stats: dict) -> None:
        import os, sqlite3
        retention_days = gov.get("retention_days", 30)
        row_limit = gov.get("row_limit", 1000)
        exclude = set(gov.get("exclude_tables", []))
        opencode_home = os.getenv("OPENCODE_CONFIG_DIR", os.path.join(os.getcwd(), "opencode"))
        databases = [
            ("data/mnemosyne.db", [
                ("temporal_metrics","timestamp","float"),("operational_logs_v2","timestamp","text_iso"),
                ("episodes","created_at","text_iso"),("events","created_at","text_iso"),
                ("meta_cognition","created_at","text_iso"),("goals","created_at","text_iso"),
                ("tool_paths","last_used","text_iso"),
                ("entities", "last_seen", "text_iso"), ("semantic_relations", "created_at", "text_iso"),
                ("reflections", "created_at", "text_iso"), ("failure_memory", "updated_at", "text_iso"),
                ("visual_memories", "timestamp", "text_iso")
            ]),
            ("data/spatial.db", [("spatial_modules","last_indexed","text_iso")]),
            ("data/reliability.db", [("agent_reliability","updated_at","text_iso")]),
            (os.path.join(opencode_home,"opencode.db"), [("session","time_created","int_ms"),("message","time_created","int_ms")]),
        ]
        for db_path, table_configs in databases:
            if not os.path.exists(db_path):
                continue
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
                cursor = conn.cursor()
                for table, time_col, time_type in table_configs:
                    if table in exclude:
                        continue
                    try:
                        cv = self._cutoff_val(time_type, retention_days)
                        sql_time = f"DELETE FROM {table} WHERE {time_col} < ?"
                        sql_limit = f"DELETE FROM {table} WHERE ROWID IN (SELECT ROWID FROM {table} ORDER BY {time_col} DESC LIMIT -1 OFFSET {row_limit})"
                        cursor.execute(sql_time, (cv,))
                        cursor.execute(sql_limit)
                        stats["pruned_sqlite"] += cursor.rowcount
                    except Exception as te:
                        logger.debug(f"VRAMSweeper: Skipped {db_path}.{table} ({te})")
                conn.commit()
                conn.execute("PRAGMA incremental_vacuum(50)")
            except Exception as dbe:
                logger.warning(f"VRAMSweeper: Failed to prune {db_path} ({dbe})")
            finally:
                conn.close()

    def _prune_files(self, gov: dict, stats: dict) -> None:
        import os, subprocess
        short_days = gov.get("short_retention_days", 15)
        opencode_home = os.getenv("OPENCODE_CONFIG_DIR", os.path.join(os.getcwd(), "opencode"))
        for path in (os.path.join(opencode_home, "log"), os.path.join(opencode_home, "storage", "session_diff")):
            if os.path.isdir(path):
                for f in os.listdir(path):
                    f_path = os.path.join(path, f)
                    if os.path.getmtime(f_path) < (time.time() - (short_days * 24 * 3600)):
                        try:
                            os.remove(f_path)
                            stats["pruned_files"] += 1
                        except Exception:
                            pass
        snapshot_path = os.path.join(opencode_home, "snapshot")
        if os.path.isdir(os.path.join(snapshot_path, ".git")):
            try:
                subprocess.run(["git", "-C", snapshot_path, "gc", "--prune=now", "--quiet"], check=True)
            except Exception as ge:
                logger.warning(f"VRAMSweeper: OpenCode git gc failed ({ge})")
        audit_keep = gov.get("audit_log_keep", 5)
        audit_dir = "logs"
        if os.path.isdir(audit_dir):
            audit_files = sorted([f for f in os.listdir(audit_dir) if f.startswith("audit_")],
                                key=lambda x: os.path.getmtime(os.path.join(audit_dir, x)), reverse=True)
            if len(audit_files) > audit_keep:
                for old_log in audit_files[audit_keep:]:
                    try:
                        os.remove(os.path.join(audit_dir, old_log))
                        stats["pruned_files"] += 1
                    except Exception:
                        pass
        
        # Phase 11.18.17: Vision Cache Cleanup
        cache_dir = os.path.join(os.getcwd(), "scratch", "vision_cache")
        if os.path.isdir(cache_dir):
            try:
                # Remove files older than 24h
                cutoff = time.time() - 86400
                for f in os.listdir(cache_dir):
                    f_path = os.path.join(cache_dir, f)
                    if os.path.getmtime(f_path) < cutoff:
                        os.remove(f_path)
                        stats["pruned_files"] += 1
                logger.info("VRAMSweeper: Vision cache pruned.")
            except Exception:
                pass

    def _prune_lancedb(self, gov: dict, stats: dict) -> None:
        try:
            from ..mnemosyne.semantic_store import SemanticStore, FailureMemoryStore
            from ..mnemosyne.temporal_store import TemporalStore
            lancedb_max = gov.get("lancedb_max_items", 500)
            short_days = gov.get("short_retention_days", 15)
            short_cutoff = float(time.time()) - (short_days * 24 * 3600)
            
            # General Semantic Store
            ss = SemanticStore()
            table = ss.db.open_table(ss.table_name)
            count = table.count_rows()
            if count > lancedb_max:
                table.delete(f"timestamp < {short_cutoff}")
                stats["pruned_lancedb"] += count - table.count_rows()
            ss.optimize()

            # Failure Memory Store (Axis 6 extension)
            try:
                fms = FailureMemoryStore()
                fmt = fms.db.open_table(fms.table_name)
                fm_count = fmt.count_rows()
                if fm_count > lancedb_max // 2:
                    fmt.delete(f"timestamp < {short_cutoff}")
                    stats["pruned_lancedb"] += fm_count - fmt.count_rows()
            except Exception as fe:
                logger.debug(f"VRAMSweeper: FailureMemoryStore pruning skipped ({fe})")

            TemporalStore().optimize()
        except Exception as le:
            logger.warning(f"VRAMSweeper: LanceDB pruning failed ({le})")

    def _calc_weekly_summary(self, conn, now: float, cutoff: float):
        """[SRC:axis_4] Aggregates weekly data into summary table."""
        conn.execute("""
            INSERT INTO weekly_summary (event_type, avg_latency, total_count, period, created_at)
            SELECT event_type, AVG(latency_ms), COUNT(*), strftime('%W', datetime(timestamp, 'unixepoch')), ?
            FROM temporal_metrics
            WHERE timestamp < ?
            GROUP BY event_type, strftime('%W', datetime(timestamp, 'unixepoch'))
        """, (now, cutoff))

    def _calc_monthly_trend(self, conn, now: float, cutoff: float):
        """[SRC:axis_4] Aggregates monthly data into trend table."""
        conn.execute("""
            INSERT INTO monthly_trend (event_type, avg_latency, total_count, period, created_at)
            SELECT event_type, AVG(latency_ms), COUNT(*), strftime('%m', datetime(timestamp, 'unixepoch')), ?
            FROM temporal_metrics
            WHERE timestamp < ?
            GROUP BY event_type, strftime('%m', datetime(timestamp, 'unixepoch'))
        """, (now, cutoff))

    def _retention_sweep(self) -> int:
        """[SRC:axis_4] Tiered retention: Aggregate old raw data into summaries before deletion."""
        import sqlite3
        from ..mnemosyne.temporal_store import TemporalStore
        store = TemporalStore()
        now = time.time()
        cutoff_30d = now - (30 * 86400)
        
        conn = sqlite3.connect(store._db_path)
        try:
            # 1. Weekly Aggregation
            self._calc_weekly_summary(conn, now, cutoff_30d)
            
            # 2. Monthly Aggregation
            self._calc_monthly_trend(conn, now, cutoff_30d)
            
            # 3. Raw Deletion
            cursor = conn.execute("DELETE FROM temporal_metrics WHERE timestamp < ?", (cutoff_30d,))
            count = cursor.rowcount
            conn.commit()
            logger.info(f"VRAMSweeper: Retention sweep complete. {count} raw metrics archived/purged.")
            return count
        except Exception as e:
            logger.error(f"VRAMSweeper: Retention sweep failed ({e})")
            return 0
        finally:
            conn.close()

    def prune_databases(self) -> dict:
        """Prunes historical data from SQLite, LanceDB, and OpenCode storage."""
        # Phase 11.18.15: Ensure maintenance runs on E-cores
        try:
            import psutil
            psutil.Process().cpu_affinity([12, 13, 14, 15])
        except Exception:
            pass

        gov = self._load_governance_config()
        stats = {"pruned_sqlite": 0, "pruned_lancedb": 0, "pruned_files": 0, "archived_metrics": 0}
        try:
            # Phase 11.18.13: Tiered Retention
            stats["archived_metrics"] = self._retention_sweep()
            
            self._prune_sqlite(gov, stats)
            self._prune_files(gov, stats)
            self._prune_lancedb(gov, stats)
            logger.info(f"VRAMSweeper: Hardening complete. SQL={stats['pruned_sqlite']}, Lance={stats['pruned_lancedb']}, Files={stats['pruned_files']}, Archived={stats['archived_metrics']}")
        except Exception as e:
            logger.error(f"VRAMSweeper: Storage hardening failed ({e})")
        return stats

    @property
    def sweep_count(self) -> int:
        return self._sweep_count

    @property
    def state(self) -> dict:
        gpu_info = get_gpu_memory_info()
        return {
            "used_gb": gpu_info.get("used_gb", 0),
            "free_gb": gpu_info.get("free_gb", 0),
            "fragmentation": get_fragmentation_estimate(),
            "sweep_count": self._sweep_count,
            "swap_threshold": self.swap_threshold,
            "frag_threshold": self.frag_threshold,
        }


if __name__ == "__main__":
    logger.info("=== Morpheus Sweeper: Firmitas Test ===")
    sweeper = VRAMSweeper(swap_threshold_gb=15, frag_threshold=0.3)
    state = sweeper.state
    logger.info(f"Sweeper State: {state['free_gb']}GB free, frag={state['fragmentation']:.2f}")
    # Don't actually sweep in test mode
    logger.info(f"Sweeper connectivity verified. Swap threshold: {sweeper.swap_threshold}GB")
