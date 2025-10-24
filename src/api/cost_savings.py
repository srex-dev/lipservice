"""
Cost savings dashboard API endpoints for PostHog App integration
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from src.storage.database import get_db
from src.storage.models import LogEntry, SamplingPolicy, PatternStats
from src.api.services import get_service_by_name

router = APIRouter(prefix="/api/v1/services", tags=["cost-savings"])

logger = logging.getLogger(__name__)


@router.get("/{service_name}/cost-savings")
async def get_cost_savings(
    service_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get cost savings data for a service
    """
    try:
        # Get service
        service = get_service_by_name(db, service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Calculate time range (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Get log statistics
        total_logs_query = db.query(LogEntry).filter(
            LogEntry.service_id == service.id,
            LogEntry.timestamp >= start_date,
            LogEntry.timestamp <= end_date
        )

        total_logs = total_logs_query.count()
        sampled_logs = total_logs_query.filter(LogEntry.sampled == True).count()

        # Get pattern statistics
        patterns_count = db.query(PatternStats).filter(
            PatternStats.service_id == service.id
        ).count()

        # Get current policy
        current_policy = db.query(SamplingPolicy).filter(
            SamplingPolicy.service_id == service.id
        ).order_by(SamplingPolicy.created_at.desc()).first()

        # Calculate cost savings (assuming $0.50 per 1M logs)
        cost_per_million_logs = 0.50
        original_cost = (total_logs / 1_000_000) * cost_per_million_logs
        sampled_cost = (sampled_logs / 1_000_000) * cost_per_million_logs
        cost_savings = original_cost - sampled_cost
        savings_percentage = (cost_savings / original_cost * 100) if original_cost > 0 else 0

        # Calculate daily averages
        daily_total_logs = total_logs / 30
        daily_sampled_logs = sampled_logs / 30

        return {
            "service_name": service_name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": 30
            },
            "total_logs": total_logs,
            "sampled_logs": sampled_logs,
            "daily_total_logs": int(daily_total_logs),
            "daily_sampled_logs": int(daily_sampled_logs),
            "cost_savings": round(cost_savings, 2),
            "savings_percentage": round(savings_percentage, 1),
            "patterns_detected": patterns_count,
            "policy_version": current_policy.version if current_policy else 0,
            "estimated_monthly_savings": round(cost_savings, 2),
            "cost_per_million_logs": cost_per_million_logs
        }

    except Exception as e:
        logger.error(f"Error calculating cost savings for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{service_name}/logs")
async def get_recent_logs(
    service_name: str,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get recent logs for a service
    """
    try:
        # Get service
        service = get_service_by_name(db, service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Get recent logs
        logs = db.query(LogEntry).filter(
            LogEntry.service_id == service.id
        ).order_by(LogEntry.timestamp.desc()).limit(limit).all()

        # Format logs for frontend
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "sampled": log.sampled,
                "sampling_rate": log.sampling_rate,
                "signature": log.signature,
                "attributes": log.attributes
            })

        return {
            "service_name": service_name,
            "logs": formatted_logs,
            "total_count": len(formatted_logs),
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error fetching logs for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{service_name}/patterns")
async def get_pattern_stats(
    service_name: str,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get pattern statistics for a service
    """
    try:
        # Get service
        service = get_service_by_name(db, service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Get pattern statistics
        patterns = db.query(PatternStats).filter(
            PatternStats.service_id == service.id
        ).order_by(PatternStats.count.desc()).limit(limit).all()

        # Format patterns for frontend
        formatted_patterns = []
        for pattern in patterns:
            formatted_patterns.append({
                "signature": pattern.signature,
                "message_sample": pattern.message_sample,
                "count": pattern.count,
                "severity_distribution": pattern.severity_distribution,
                "first_seen": pattern.first_seen.isoformat(),
                "last_seen": pattern.last_seen.isoformat(),
                "sampling_rate": pattern.sampling_rate
            })

        return {
            "service_name": service_name,
            "patterns": formatted_patterns,
            "total_count": len(formatted_patterns),
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error fetching patterns for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{service_name}/sampling-stats")
async def get_sampling_stats(
    service_name: str,
    days: int = 7,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sampling statistics for a service
    """
    try:
        # Get service
        service = get_service_by_name(db, service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

        # Calculate time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get sampling statistics by severity
        severity_stats = {}
        severity_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for severity in severity_levels:
            total_query = db.query(LogEntry).filter(
                LogEntry.service_id == service.id,
                LogEntry.level == severity,
                LogEntry.timestamp >= start_date,
                LogEntry.timestamp <= end_date
            )
            
            total_count = total_query.count()
            sampled_count = total_query.filter(LogEntry.sampled == True).count()
            
            sampling_rate = (sampled_count / total_count) if total_count > 0 else 0
            
            severity_stats[severity] = {
                "total": total_count,
                "sampled": sampled_count,
                "sampling_rate": round(sampling_rate, 3),
                "percentage": round(sampling_rate * 100, 1)
            }

        # Get daily sampling rates
        daily_stats = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_total = db.query(LogEntry).filter(
                LogEntry.service_id == service.id,
                LogEntry.timestamp >= day_start,
                LogEntry.timestamp < day_end
            ).count()
            
            day_sampled = db.query(LogEntry).filter(
                LogEntry.service_id == service.id,
                LogEntry.timestamp >= day_start,
                LogEntry.timestamp < day_end,
                LogEntry.sampled == True
            ).count()
            
            day_rate = (day_sampled / day_total) if day_total > 0 else 0
            
            daily_stats.append({
                "date": day_start.date().isoformat(),
                "total_logs": day_total,
                "sampled_logs": day_sampled,
                "sampling_rate": round(day_rate, 3),
                "cost_savings": round((day_total - day_sampled) * 0.50 / 1_000_000, 2)
            })

        return {
            "service_name": service_name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "severity_stats": severity_stats,
            "daily_stats": daily_stats,
            "summary": {
                "total_logs": sum(stat["total"] for stat in severity_stats.values()),
                "total_sampled": sum(stat["sampled"] for stat in severity_stats.values()),
                "overall_sampling_rate": round(
                    sum(stat["sampled"] for stat in severity_stats.values()) / 
                    sum(stat["total"] for stat in severity_stats.values()) if 
                    sum(stat["total"] for stat in severity_stats.values()) > 0 else 0, 3
                )
            }
        }

    except Exception as e:
        logger.error(f"Error fetching sampling stats for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
