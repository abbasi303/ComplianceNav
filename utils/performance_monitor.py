"""
Performance Monitoring for ComplianceNavigator
Tracks optimization improvements and system performance
"""
import time
import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime, timedelta
import json

class PerformanceMonitor:
    """Monitor performance metrics and optimization effectiveness"""
    
    def __init__(self):
        self.metrics = {
            'api_calls': {'total': 0, 'cached': 0, 'time_saved': 0.0},
            'country_processing': {'total': 0, 'parallel': 0, 'time_saved': 0.0}, 
            'regulation_searches': {'total': 0, 'cached': 0, 'time_saved': 0.0},
            'session_reuse': {'connections': 0, 'reused': 0}
        }
        self.start_time = time.time()
        
    async def track_api_call(self, cached: bool = False, time_saved: float = 0.0):
        """Track API call performance"""
        self.metrics['api_calls']['total'] += 1
        if cached:
            self.metrics['api_calls']['cached'] += 1
            self.metrics['api_calls']['time_saved'] += time_saved
    
    async def track_country_processing(self, parallel: bool = False, time_saved: float = 0.0):
        """Track country processing performance"""
        self.metrics['country_processing']['total'] += 1
        if parallel:
            self.metrics['country_processing']['parallel'] += 1
            self.metrics['country_processing']['time_saved'] += time_saved
    
    async def track_regulation_search(self, cached: bool = False, time_saved: float = 0.0):
        """Track regulation search performance"""
        self.metrics['regulation_searches']['total'] += 1
        if cached:
            self.metrics['regulation_searches']['cached'] += 1
            self.metrics['regulation_searches']['time_saved'] += time_saved
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        runtime = time.time() - self.start_time
        
        # Calculate efficiency percentages
        api_cache_rate = (
            self.metrics['api_calls']['cached'] / max(self.metrics['api_calls']['total'], 1) * 100
        )
        
        parallel_rate = (
            self.metrics['country_processing']['parallel'] / max(self.metrics['country_processing']['total'], 1) * 100
        )
        
        search_cache_rate = (
            self.metrics['regulation_searches']['cached'] / max(self.metrics['regulation_searches']['total'], 1) * 100
        )
        
        total_time_saved = (
            self.metrics['api_calls']['time_saved'] +
            self.metrics['country_processing']['time_saved'] +
            self.metrics['regulation_searches']['time_saved']
        )
        
        return {
            'performance_summary': {
                'runtime_seconds': round(runtime, 2),
                'total_time_saved_seconds': round(total_time_saved, 2),
                'efficiency_improvement': f"{round(total_time_saved/runtime*100, 1)}%" if runtime > 0 else "0%"
            },
            'api_optimization': {
                'total_calls': self.metrics['api_calls']['total'],
                'cached_calls': self.metrics['api_calls']['cached'],
                'cache_hit_rate': f"{round(api_cache_rate, 1)}%",
                'time_saved_seconds': round(self.metrics['api_calls']['time_saved'], 2)
            },
            'parallel_processing': {
                'total_country_operations': self.metrics['country_processing']['total'],
                'parallel_operations': self.metrics['country_processing']['parallel'],
                'parallel_usage_rate': f"{round(parallel_rate, 1)}%",
                'time_saved_seconds': round(self.metrics['country_processing']['time_saved'], 2)
            },
            'regulation_caching': {
                'total_searches': self.metrics['regulation_searches']['total'],
                'cached_searches': self.metrics['regulation_searches']['cached'],
                'cache_hit_rate': f"{round(search_cache_rate, 1)}%",
                'time_saved_seconds': round(self.metrics['regulation_searches']['time_saved'], 2)
            },
            'optimization_status': self._get_optimization_status()
        }
    
    def _get_optimization_status(self) -> Dict[str, str]:
        """Get optimization status indicators"""
        api_cache_rate = (
            self.metrics['api_calls']['cached'] / max(self.metrics['api_calls']['total'], 1) * 100
        )
        
        search_cache_rate = (
            self.metrics['regulation_searches']['cached'] / max(self.metrics['regulation_searches']['total'], 1) * 100
        )
        
        parallel_rate = (
            self.metrics['country_processing']['parallel'] / max(self.metrics['country_processing']['total'], 1) * 100
        )
        
        status = {}
        
        # API Caching Status
        if api_cache_rate >= 70:
            status['api_caching'] = '🟢 Excellent'
        elif api_cache_rate >= 40:
            status['api_caching'] = '🟡 Good'  
        else:
            status['api_caching'] = '🔴 Needs Improvement'
        
        # Parallel Processing Status
        if parallel_rate >= 80:
            status['parallel_processing'] = '🟢 Excellent'
        elif parallel_rate >= 50:
            status['parallel_processing'] = '🟡 Good'
        else:
            status['parallel_processing'] = '🔴 Needs Improvement'
            
        # Search Caching Status  
        if search_cache_rate >= 60:
            status['search_caching'] = '🟢 Excellent'
        elif search_cache_rate >= 30:
            status['search_caching'] = '🟡 Good'
        else:
            status['search_caching'] = '🔴 Needs Improvement'
        
        return status
    
    def log_performance_summary(self):
        """Log performance summary"""
        report = self.get_performance_report()
        
        logger.info("🚀 PERFORMANCE OPTIMIZATION REPORT 🚀")
        logger.info(f"Runtime: {report['performance_summary']['runtime_seconds']}s")
        logger.info(f"Time Saved: {report['performance_summary']['total_time_saved_seconds']}s")
        logger.info(f"Efficiency Gain: {report['performance_summary']['efficiency_improvement']}")
        
        logger.info(f"API Cache Hit Rate: {report['api_optimization']['cache_hit_rate']}")
        logger.info(f"Parallel Processing Rate: {report['parallel_processing']['parallel_usage_rate']}")
        logger.info(f"Search Cache Hit Rate: {report['regulation_caching']['cache_hit_rate']}")
        
        # Log status indicators
        for optimization, status in report['optimization_status'].items():
            logger.info(f"{optimization.replace('_', ' ').title()}: {status}")

# Global performance monitor
performance_monitor = PerformanceMonitor() 