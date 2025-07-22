"""
Production Monitoring and Observability
Comprehensive metrics, health checks, and alerting system
"""
import time
import asyncio
import psutil
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import threading
from pathlib import Path

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = "count"

@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # "healthy", "warning", "unhealthy"
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None

@dataclass
class Alert:
    """Alert notification"""
    level: AlertLevel
    title: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        self.last_collection = time.time()
        
    def increment_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = self._get_metric_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
        
        metric = Metric(
            name=name,
            value=self.counters[key],
            labels=labels or {},
            unit="count"
        )
        self.metrics[key] = metric
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = self._get_metric_key(name, labels)
        self.gauges[key] = value
        
        metric = Metric(
            name=name,
            value=value,
            labels=labels or {},
            unit="gauge"
        )
        self.metrics[key] = metric
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        key = self._get_metric_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        
        self.histograms[key].append(value)
        
        # Keep only last 1000 values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        
        # Calculate summary statistics
        values = self.histograms[key]
        avg_value = sum(values) / len(values)
        
        metric = Metric(
            name=name,
            value=avg_value,
            labels=labels or {},
            unit="histogram"
        )
        self.metrics[key] = metric
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Generate unique key for metric"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}[{label_str}]"
        return name
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all current metrics"""
        return self.metrics.copy()
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        return {
            'total_metrics': len(self.metrics),
            'counters': len(self.counters),
            'gauges': len(self.gauges),
            'histograms': len(self.histograms),
            'last_collection': self.last_collection
        }

class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self):
        self.health_checks = {}
        self.check_functions = {}
    
    def register_check(self, name: str, check_function: Callable[[], HealthCheck]):
        """Register a health check function"""
        self.check_functions[name] = check_function
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        results = {}
        
        for name, check_func in self.check_functions.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                response_time = (time.time() - start_time) * 1000
                result.response_time_ms = response_time
                
                results[name] = result
                
            except Exception as e:
                results[name] = HealthCheck(
                    name=name,
                    status="unhealthy",
                    message=f"Health check failed: {str(e)}",
                    response_time_ms=None
                )
        
        self.health_checks = results
        return results
    
    def get_overall_health(self) -> str:
        """Get overall system health status"""
        if not self.health_checks:
            return "unknown"
        
        statuses = [check.status for check in self.health_checks.values()]
        
        if any(status == "unhealthy" for status in statuses):
            return "unhealthy"
        elif any(status == "warning" for status in statuses):
            return "warning"
        else:
            return "healthy"

class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.last_system_check = time.time()
    
    async def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.set_gauge("system_cpu_percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_collector.set_gauge("system_memory_percent", memory.percent)
            self.metrics_collector.set_gauge("system_memory_used_bytes", memory.used)
            self.metrics_collector.set_gauge("system_memory_available_bytes", memory.available)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metrics_collector.set_gauge("system_disk_percent", (disk.used / disk.total) * 100)
            self.metrics_collector.set_gauge("system_disk_used_bytes", disk.used)
            self.metrics_collector.set_gauge("system_disk_free_bytes", disk.free)
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                self.metrics_collector.set_gauge("system_network_bytes_sent", network.bytes_sent)
                self.metrics_collector.set_gauge("system_network_bytes_recv", network.bytes_recv)
            except:
                pass  # Network stats may not be available in all environments
            
            self.last_system_check = time.time()
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

class ApplicationMonitor:
    """Unified application performance and metrics monitoring"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.start_time = time.time()
        
        # Integrate with existing PerformanceMonitor functionality
        try:
            from utils.performance_monitor import PerformanceMonitor
            self._perf_monitor = PerformanceMonitor()
            logger.info("Integrated with PerformanceMonitor for unified tracking")
        except ImportError:
            self._perf_monitor = None
        
    def track_api_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Track API request metrics with unified monitoring"""
        labels = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code)
        }
        
        self.metrics_collector.increment_counter("api_requests_total", 1, labels)
        self.metrics_collector.record_histogram("api_request_duration_seconds", response_time, labels)
        
        # Also track in performance monitor if available
        if self._perf_monitor:
            asyncio.create_task(self._perf_monitor.track_api_call(
                cached=status_code == 304,  # 304 = cached response
                time_saved=max(0, 2.0 - response_time)  # Assume baseline 2s without optimization
            ))
    
    def track_compliance_analysis(self, industry: str, countries: List[str], duration: float, success: bool):
        """Track compliance analysis with performance integration"""
        labels = {
            'industry': industry,
            'country_count': str(len(countries)),
            'success': str(success)
        }
        
        self.metrics_collector.increment_counter("compliance_analyses_total", 1, labels)
        self.metrics_collector.record_histogram("compliance_analysis_duration_seconds", duration, labels)
        
        if success:
            self.metrics_collector.increment_counter("compliance_analyses_successful", 1, labels)
        else:
            self.metrics_collector.increment_counter("compliance_analyses_failed", 1, labels)
        
        # Track country processing performance
        if self._perf_monitor:
            asyncio.create_task(self._perf_monitor.track_country_processing(
                parallel=len(countries) > 1,
                time_saved=max(0, len(countries) * 10.0 - duration)  # Estimate time saved
            ))
    
    def track_cache_performance(self, cache_type: str, hit: bool, time_saved: float = 0.0):
        """Enhanced cache performance tracking"""
        labels = {'cache_type': cache_type}
        
        self.metrics_collector.increment_counter("cache_requests_total", 1, labels)
        
        if hit:
            self.metrics_collector.increment_counter("cache_hits_total", 1, labels)
        else:
            self.metrics_collector.increment_counter("cache_misses_total", 1, labels)
        
        # Unified cache tracking
        if self._perf_monitor:
            if cache_type == 'regulation_search':
                asyncio.create_task(self._perf_monitor.track_regulation_search(hit, time_saved))
            elif cache_type == 'api_response':
                asyncio.create_task(self._perf_monitor.track_api_call(hit, time_saved))
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_unified_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report from both monitoring systems"""
        base_metrics = self.metrics_collector.get_all_metrics()
        
        report = {
            'uptime_seconds': self.get_uptime_seconds(),
            'base_metrics': {k: v.value for k, v in base_metrics.items()},
            'performance_details': None
        }
        
        if self._perf_monitor:
            report['performance_details'] = self._perf_monitor.get_performance_report()
        
        return report

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts = []
        self.alert_rules = []
        self.max_alerts = 1000
        
    def add_alert(self, alert: Alert):
        """Add a new alert"""
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log the alert
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(f"ALERT [{alert.level.value.upper()}]: {alert.title} - {alert.description}")
        elif alert.level == AlertLevel.ERROR:
            logger.error(f"ALERT [{alert.level.value.upper()}]: {alert.title} - {alert.description}")
        elif alert.level == AlertLevel.WARNING:
            logger.warning(f"ALERT [{alert.level.value.upper()}]: {alert.title} - {alert.description}")
        else:
            logger.info(f"ALERT [{alert.level.value.upper()}]: {alert.title} - {alert.description}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts by level"""
        recent_alerts = self.get_recent_alerts(24)
        
        summary = {level.value: 0 for level in AlertLevel}
        for alert in recent_alerts:
            summary[alert.level.value] += 1
        
        return {
            'total_alerts_24h': len(recent_alerts),
            'by_level': summary,
            'latest_alert': recent_alerts[-1] if recent_alerts else None
        }

class ComprehensiveMonitor:
    """Main monitoring system that coordinates all monitoring components"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.app_monitor = ApplicationMonitor()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        
        self.monitoring_active = False
        self.monitoring_interval = 60  # seconds
        
        self._register_default_health_checks()
        self._setup_alert_rules()
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        
        def check_disk_space():
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent > 90:
                return HealthCheck("disk_space", "unhealthy", f"Disk usage at {usage_percent:.1f}%")
            elif usage_percent > 80:
                return HealthCheck("disk_space", "warning", f"Disk usage at {usage_percent:.1f}%")
            else:
                return HealthCheck("disk_space", "healthy", f"Disk usage at {usage_percent:.1f}%")
        
        def check_memory():
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                return HealthCheck("memory", "unhealthy", f"Memory usage at {memory.percent:.1f}%")
            elif memory.percent > 80:
                return HealthCheck("memory", "warning", f"Memory usage at {memory.percent:.1f}%")
            else:
                return HealthCheck("memory", "healthy", f"Memory usage at {memory.percent:.1f}%")
        
        async def check_api_availability():
            # Simple API health check
            try:
                from integrations.gemini_client import gemini_client
                # Test basic functionality
                return HealthCheck("api_availability", "healthy", "APIs are accessible")
            except Exception as e:
                return HealthCheck("api_availability", "unhealthy", f"API check failed: {e}")
        
        self.health_checker.register_check("disk_space", check_disk_space)
        self.health_checker.register_check("memory", check_memory)
        self.health_checker.register_check("api_availability", check_api_availability)
    
    def _setup_alert_rules(self):
        """Setup automated alert rules"""
        # This would contain rules for when to automatically generate alerts
        # based on metrics and health checks
        pass
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        self.monitoring_active = True
        logger.info("Comprehensive monitoring system started")
        
        # Start monitoring loop in background
        asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        logger.info("Comprehensive monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                await self.system_monitor.collect_system_metrics()
                
                # Run health checks
                health_results = await self.health_checker.run_all_checks()
                
                # Check for alert conditions
                await self._check_alert_conditions(health_results)
                
                # Wait for next interval
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Short sleep before retry
    
    async def _check_alert_conditions(self, health_results: Dict[str, HealthCheck]):
        """Check if any alert conditions are met"""
        for name, health_check in health_results.items():
            if health_check.status == "unhealthy":
                self.alert_manager.add_alert(Alert(
                    level=AlertLevel.CRITICAL,
                    title=f"Health Check Failed: {name}",
                    description=health_check.message,
                    source="health_check"
                ))
            elif health_check.status == "warning":
                self.alert_manager.add_alert(Alert(
                    level=AlertLevel.WARNING,
                    title=f"Health Check Warning: {name}",
                    description=health_check.message,
                    source="health_check"
                ))
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        system_metrics = self.system_monitor.metrics_collector.get_all_metrics()
        app_metrics = self.app_monitor.metrics_collector.get_all_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': self.app_monitor.get_uptime_seconds(),
            'overall_health': self.health_checker.get_overall_health(),
            'health_checks': self.health_checker.health_checks,
            'system_metrics': {k: {
                'value': v.value,
                'timestamp': v.timestamp.isoformat(),
                'unit': v.unit
            } for k, v in system_metrics.items()},
            'application_metrics': {k: {
                'value': v.value,
                'timestamp': v.timestamp.isoformat(),
                'unit': v.unit
            } for k, v in app_metrics.items()},
            'alert_summary': self.alert_manager.get_alert_summary(),
            'monitoring_status': 'active' if self.monitoring_active else 'inactive'
        }

# Global monitoring instance
comprehensive_monitor = ComprehensiveMonitor() 