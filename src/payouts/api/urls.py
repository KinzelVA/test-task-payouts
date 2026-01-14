from rest_framework.routers import DefaultRouter
from django.urls import path, include
from payouts.api.views import PayoutRequestViewSet

router = DefaultRouter()
router.register(r"payout-requests", PayoutRequestViewSet, basename="payout-requests")

urlpatterns = [
    path("", include(router.urls)),
]
