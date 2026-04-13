from django.urls import path

from .views import (
    SeatAvailabilityView,
    SeatAvailabilitySummaryView,
    OfficerAllocateView,
    OfficerDeallocateView,
    OfficerBulkAllocateView,
    OfficerAllocationSuggestView,
    OfficerAutoAllocateView,
)

urlpatterns = [
    path("availability/", SeatAvailabilityView.as_view(), name="seat-availability"),
    path("availability/summary/", SeatAvailabilitySummaryView.as_view(), name="seat-availability-summary"),
    path("allocate/<uuid:pk>/", OfficerAllocateView.as_view(), name="officer-allocate"),
    path("deallocate/<uuid:pk>/", OfficerDeallocateView.as_view(), name="officer-deallocate"),
    path("allocate/bulk/", OfficerBulkAllocateView.as_view(), name="officer-bulk-allocate"),
    path("allocation/suggest/", OfficerAllocationSuggestView.as_view(), name="officer-allocation-suggest"),
    path("allocation/auto-allocate/", OfficerAutoAllocateView.as_view(), name="officer-auto-allocate"),
]