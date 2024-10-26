from django.urls import path
from .views import get_pnr_status

urlpatterns = [
    path('status/', get_pnr_status, name='get_pnr_status'),
]
