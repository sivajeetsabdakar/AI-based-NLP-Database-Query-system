"""
Database Health Monitoring Service
Comprehensive monitoring, alerting, and performance analysis
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from .database_manager import get_database_manager
from .redis_service import get_redis_service
from .chromadb_service import get_chromadb_service
from .database_utils import get_database_utils

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthMetric:
    """Health metric data structure"""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime

class HealthMonitor:
    """Comprehensive database health monitoring"""
    
    def __init__(self):
        self.logger = logger
        self.metrics_history = []
        self.alert_thresholds = {
            "response_time": {"warning": 1.0, "critical": 5.0},
            "connection_pool_usage": {"warning": 0.8, "critical": 0.95},
            "cache_hit_rate": {"warning": 0.7, "critical": 0.5},
            "memory_usage": {"warning": 0.8, "critical": 0.95},
            "disk_usage": {"warning": 0.8, "critical": 0.95}
        }
    
    def check_postgresql_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database health"""
        try:
            start_time = time.time()
            db_manager = get_database_manager()
            health_result = db_manager.health_check()
            response_time = time.time() - start_time
            
            # Analyze connection pool
            pool_status = health_result.get("pool_status", {})
            pool_usage = 0
            if pool_status.get("pool_size", 0) > 0:
                pool_usage = pool_status.get("checked_out", 0) / pool_status.get("pool_size", 1)
            
            # Determine health status
            status = HealthStatus.HEALTHY
            if response_time > self.alert_thresholds["response_time"]["critical"]:
                status = HealthStatus.CRITICAL
            elif response_time > self.alert_thresholds["response_time"]["warning"]:
                status = HealthStatus.WARNING
            elif pool_usage > self.alert_thresholds["connection_pool_usage"]["critical"]:
                status = HealthStatus.CRITICAL
            elif pool_usage > self.alert_thresholds["connection_pool_usage"]["warning"]:
                status = HealthStatus.WARNING
            
            return {
                "service": "postgresql",
                "status": status.value,
                "response_time": response_time,
                "pool_usage": pool_usage,
                "pool_status": pool_status,
                "timestamp": datetime.utcnow().isoformat(),
                "details": health_result
            }
            
        except Exception as e:
            self.logger.error(f"PostgreSQL health check failed: {str(e)}")
            return {
                "service": "postgresql",
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis cache health"""
        try:
            start_time = time.time()
            redis_service = get_redis_service()
            health_result = redis_service.health_check()
            response_time = time.time() - start_time
            
            # Analyze Redis metrics
            status = HealthStatus.HEALTHY
            if response_time > self.alert_thresholds["response_time"]["critical"]:
                status = HealthStatus.CRITICAL
            elif response_time > self.alert_thresholds["response_time"]["warning"]:
                status = HealthStatus.WARNING
            
            # Check memory usage if available
            memory_usage = 0
            if "used_memory" in health_result:
                # Parse memory usage (e.g., "1.2M", "500K")
                memory_str = health_result["used_memory"]
                if memory_str.endswith("M"):
                    memory_usage = float(memory_str[:-1]) / 1000  # Convert to GB
                elif memory_str.endswith("K"):
                    memory_usage = float(memory_str[:-1]) / 1000000  # Convert to GB
            
            return {
                "service": "redis",
                "status": status.value,
                "response_time": response_time,
                "memory_usage": memory_usage,
                "connected_clients": health_result.get("connected_clients", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "details": health_result
            }
            
        except Exception as e:
            self.logger.error(f"Redis health check failed: {str(e)}")
            return {
                "service": "redis",
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_chromadb_health(self) -> Dict[str, Any]:
        """Check ChromaDB vector database health"""
        try:
            start_time = time.time()
            chromadb_service = get_chromadb_service()
            health_result = chromadb_service.health_check()
            response_time = time.time() - start_time
            
            # Analyze ChromaDB metrics
            status = HealthStatus.HEALTHY
            if response_time > self.alert_thresholds["response_time"]["critical"]:
                status = HealthStatus.CRITICAL
            elif response_time > self.alert_thresholds["response_time"]["warning"]:
                status = HealthStatus.WARNING
            
            return {
                "service": "chromadb",
                "status": status.value,
                "response_time": response_time,
                "collections": health_result.get("collections", 0),
                "collection_names": health_result.get("collection_names", []),
                "timestamp": datetime.utcnow().isoformat(),
                "details": health_result
            }
            
        except Exception as e:
            self.logger.error(f"ChromaDB health check failed: {str(e)}")
            return {
                "service": "chromadb",
                "status": HealthStatus.CRITICAL.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_comprehensive_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status for all services"""
        try:
            health_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": HealthStatus.HEALTHY.value,
                "services": {}
            }
            
            # Check all services
            postgresql_health = self.check_postgresql_health()
            redis_health = self.check_redis_health()
            chromadb_health = self.check_chromadb_health()
            
            health_results["services"]["postgresql"] = postgresql_health
            health_results["services"]["redis"] = redis_health
            health_results["services"]["chromadb"] = chromadb_health
            
            # Determine overall status
            service_statuses = [
                postgresql_health.get("status"),
                redis_health.get("status"),
                chromadb_health.get("status")
            ]
            
            if HealthStatus.CRITICAL.value in service_statuses:
                health_results["overall_status"] = HealthStatus.CRITICAL.value
            elif HealthStatus.WARNING.value in service_statuses:
                health_results["overall_status"] = HealthStatus.WARNING.value
            elif HealthStatus.UNKNOWN.value in service_statuses:
                health_results["overall_status"] = HealthStatus.UNKNOWN.value
            
            # Add performance metrics
            health_results["performance_metrics"] = self._get_performance_metrics()
            
            return health_results
            
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive health status: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": HealthStatus.CRITICAL.value,
                "error": str(e)
            }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from database"""
        try:
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                db_utils = get_database_utils()
                stats = db_utils.get_database_stats(session)
                
                # Get cache statistics
                redis_service = get_redis_service()
                cache_stats = redis_service.get_cache_stats()
                
                return {
                    "database_stats": stats,
                    "cache_stats": cache_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {str(e)}")
            return {"error": str(e)}
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        try:
            alerts = []
            health_status = self.get_comprehensive_health_status()
            
            # Check service statuses
            for service_name, service_health in health_status.get("services", {}).items():
                status = service_health.get("status")
                
                if status == HealthStatus.CRITICAL.value:
                    alerts.append({
                        "level": "critical",
                        "service": service_name,
                        "message": f"{service_name} service is in critical state",
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": service_health
                    })
                elif status == HealthStatus.WARNING.value:
                    alerts.append({
                        "level": "warning",
                        "service": service_name,
                        "message": f"{service_name} service is in warning state",
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": service_health
                    })
            
            # Check performance thresholds
            performance_metrics = health_status.get("performance_metrics", {})
            database_stats = performance_metrics.get("database_stats", {})
            
            # Check cache hit rate
            cache_hit_rate = database_stats.get("cache_hit_rate", 1.0)
            if cache_hit_rate < self.alert_thresholds["cache_hit_rate"]["critical"]:
                alerts.append({
                    "level": "critical",
                    "service": "cache",
                    "message": f"Cache hit rate is critically low: {cache_hit_rate:.2%}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif cache_hit_rate < self.alert_thresholds["cache_hit_rate"]["warning"]:
                alerts.append({
                    "level": "warning",
                    "service": "cache",
                    "message": f"Cache hit rate is low: {cache_hit_rate:.2%}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to check alerts: {str(e)}")
            return [{
                "level": "critical",
                "service": "monitoring",
                "message": f"Health monitoring failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }]
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health monitoring history"""
        try:
            # Filter metrics from the last N hours
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_metrics = [
                metric for metric in self.metrics_history
                if metric.timestamp > cutoff_time
            ]
            
            return [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "status": metric.status.value,
                    "timestamp": metric.timestamp.isoformat()
                }
                for metric in recent_metrics
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get health history: {str(e)}")
            return []
    
    def record_metric(
        self, 
        name: str, 
        value: float, 
        unit: str,
        threshold_warning: Optional[float] = None,
        threshold_critical: Optional[float] = None
    ):
        """Record a health metric"""
        try:
            # Use default thresholds if not provided
            if threshold_warning is None:
                threshold_warning = self.alert_thresholds.get(name, {}).get("warning", 0.8)
            if threshold_critical is None:
                threshold_critical = self.alert_thresholds.get(name, {}).get("critical", 0.95)
            
            # Determine status based on thresholds
            if value >= threshold_critical:
                status = HealthStatus.CRITICAL
            elif value >= threshold_warning:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            metric = HealthMetric(
                name=name,
                value=value,
                unit=unit,
                status=status,
                threshold_warning=threshold_warning,
                threshold_critical=threshold_critical,
                timestamp=datetime.utcnow()
            )
            
            self.metrics_history.append(metric)
            
            # Keep only last 1000 metrics to prevent memory issues
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
        except Exception as e:
            self.logger.error(f"Failed to record metric: {str(e)}")

# Global health monitor instance
health_monitor: Optional[HealthMonitor] = None

def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    if health_monitor is None:
        raise RuntimeError("Health monitor not initialized")
    return health_monitor

def initialize_health_monitor() -> HealthMonitor:
    """Initialize the global health monitor"""
    global health_monitor
    health_monitor = HealthMonitor()
    return health_monitor
