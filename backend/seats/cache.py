from django.core.cache import cache


def invalidate_seat_cache(branch_id=None, quota=None):
    """
    Invalidate seat cache for specific branch/quota or all seats.
    
    Usage:
        invalidate_seat_cache() - invalidate all
        invalidate_seat_cache(branch_id=uuid) - invalidate all quotas for branch
        invalidate_seat_cache(branch_id=uuid, quota='general') - invalidate specific
    """
    if branch_id is None and quota is None:
        cache.delete_pattern("seats:*")
        cache.delete_pattern("seats:summary")
        return
    
    if branch_id and quota:
        cache.delete(f"seats:{branch_id}:{quota}")
    elif branch_id:
        from administration.models import QuotaType
        for quota_value, _ in QuotaType.choices:
            cache.delete(f"seats:{branch_id}:{quota_value}")
    
    cache.delete("seats:summary")


def notify_seat_change(branch_id, quota):
    """
    Signal handler for seat allocation/revocation.
    Call this when a seat is allocated or revoked.
    """
    invalidate_seat_cache(branch_id=branch_id, quota=quota)