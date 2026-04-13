import json
import logging
from typing import Any, Dict, Optional, Union
from django.conf import settings
from django.utils import timezone
from rest_framework.request import Request

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def compute_diff(before: Optional[Dict], after: Optional[Dict]) -> tuple[Optional[Dict], Optional[Dict]]:
    """
    Compute diff between two dictionaries, only including changed fields.
    Returns (before_diff, after_diff) with only the fields that changed.
    """
    if before is None and after is None:
        return None, None
    
    if before is None:
        before = {}
    if after is None:
        after = {}
    
    before_diff = {}
    after_diff = {}
    
    all_keys = set(before.keys()) | set(after.keys())
    
    for key in all_keys:
        before_val = before.get(key)
        after_val = after.get(key)
        
        if before_val != after_val:
            if before_val is not None:
                before_diff[key] = before_val
            if after_val is not None:
                after_diff[key] = after_val
    
    return before_diff if before_diff else None, after_diff if after_diff else None


class AuditLogger:
    """
    Centralized audit logging service.
    
    Usage:
        AuditLogger.record(
            entity=application,
            action='field_edit',
            before={'current_value': 'old_value'},
            after={'current_value': 'new_value'},
            request=request
        )
    """
    
    @staticmethod
    def record(
        entity: Any,
        action: str,
        before: Optional[Dict] = None,
        after: Optional[Dict] = None,
        request: Optional[Request] = None,
        actor: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> Any:
        """
        Record an audit log entry.
        
        Args:
            entity: The entity being audited (Application, Document, etc.) or entity_id
            action: The action being performed (e.g., 'field_edit', 'lock', 'unlock')
            before: State before the action
            after: State after the action
            request: DRF Request object (auto-captures actor and IP)
            actor: Explicit actor (user) - required if request not provided
            ip_address: Explicit IP address - overrides request IP
            user_agent: Explicit user agent - overrides request user agent
            entity_type: Override entity type detection
        
        Returns:
            AuditLog instance or raises ValueError if validation fails
        """
        from verification.models import AuditLog
        from admissions.models import Application
        from documents.models import Document
        
        resolved_actor = None
        resolved_ip = ip_address or '0.0.0.0'
        resolved_ua = user_agent
        resolved_entity_type = entity_type
        resolved_entity_id = None
        resolved_application = None
        
        if request is not None:
            resolved_actor = getattr(request, 'user', None)
            if resolved_actor and not hasattr(resolved_actor, 'is_authenticated'):
                resolved_actor = None
            if not ip_address:
                resolved_ip = get_client_ip(request)
            if not user_agent:
                resolved_ua = request.META.get('HTTP_USER_AGENT', '')
        
        if actor is not None:
            resolved_actor = actor
        
        if resolved_actor is None:
            raise ValueError("Actor is required for audit logging. Provide request or actor.")
        
        if not hasattr(resolved_actor, 'id') or resolved_actor.id is None:
            raise ValueError("Actor must have a valid user ID.")
        
        if hasattr(entity, '_meta'):
            resolved_entity_type = entity._meta.model_name
            resolved_entity_id = entity.pk
            
            # Try to resolve application
            if isinstance(entity, Application):
                resolved_application = entity
            elif isinstance(entity, Document):
                resolved_application = entity.student.application_set.first()
            elif hasattr(entity, 'application'):
                resolved_application = entity.application
            elif hasattr(entity, 'document'):
                resolved_application = entity.document.student.application_set.first()
        elif hasattr(entity, 'id'):
            resolved_entity_type = entity_type or 'unknown'
            resolved_entity_id = entity.id
        else:
            resolved_entity_type = entity_type or 'unknown'
            resolved_entity_id = entity
        
        before_diff, after_diff = compute_diff(before, after)
        
        if before_diff is None and after_diff is None:
            logger.debug(f"AuditLogger: No changes detected for action '{action}', skipping log")
            return None
        
        try:
            audit_log = AuditLog.objects.create(
                entity_type=resolved_entity_type,
                entity_id=resolved_entity_id,
                application=resolved_application,
                action=action,
                user=resolved_actor,
                before_json=before_diff,
                after_json=after_diff,
                ip_address=resolved_ip,
                user_agent=resolved_ua
            )
            logger.info(f"AuditLog created: {action} on {resolved_entity_type}:{resolved_entity_id}")
            return audit_log
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            raise
    
    @staticmethod
    def record_field_change(
        entity: Any,
        field_name: str,
        old_value: Any,
        new_value: Any,
        request: Request,
        action: str = 'field_edit'
    ) -> Any:
        """Convenience method for recording field changes."""
        return AuditLogger.record(
            entity=entity,
            action=action,
            before={field_name: old_value},
            after={field_name: new_value},
            request=request
        )
    
    @staticmethod
    def record_status_change(
        entity: Any,
        old_status: str,
        new_status: str,
        request: Request,
        action: str = 'status_change',
        extra_after: Optional[Dict] = None
    ) -> Any:
        """Convenience method for recording status changes."""
        after = {'status': new_status}
        if extra_after:
            after.update(extra_after)
        
        return AuditLogger.record(
            entity=entity,
            action=action,
            before={'status': old_status},
            after=after,
            request=request
        )
    
    @staticmethod
    def record_lock(
        application: Any,
        request: Request,
        locked: bool = True
    ) -> Any:
        """Convenience method for recording lock/unlock actions."""
        action = 'lock' if locked else 'unlock'
        
        if locked:
            return AuditLogger.record(
                entity=application,
                action=action,
                before={'is_locked': False},
                after={'is_locked': True, 'locked_at': timezone.now().isoformat()},
                request=request
            )
        else:
            return AuditLogger.record(
                entity=application,
                action=action,
                before={'is_locked': True},
                after={'is_locked': False},
                request=request
            )


def audit_log(
    entity: Any,
    action: str,
    before: Optional[Dict] = None,
    after: Optional[Dict] = None,
    request: Optional[Request] = None,
    actor: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> Any:
    """
    Convenience function for audit logging.

    Usage:
        audit_log(application, 'field_edit', 
                  before={'name': 'old'}, 
                  after={'name': 'new'}, 
                  request=request)
    """
    return AuditLogger.record(
        entity=entity,
        action=action,
        before=before,
        after=after,
        request=request,
        actor=actor,
        ip_address=ip_address,
        user_agent=user_agent,
        entity_type=entity_type
    )