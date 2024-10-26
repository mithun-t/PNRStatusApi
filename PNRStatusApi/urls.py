from django.urls import path
from .views import PNRStatusView

urlpatterns = [
    path('status/', PNRStatusView.as_view(), name='pnr_status'),
]