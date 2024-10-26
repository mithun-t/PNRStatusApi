import requests
import re
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)

class PNRStatusView(View):
    CACHE_TIMEOUT = 300  # 5 minutes cache
    
    @method_decorator(require_GET)
    def get(self, request):
        """Handle GET request for PNR status"""
        pnr = request.GET.get('pnr', '').strip()
        
        # Input validation
        if not self._validate_pnr(pnr):
            return JsonResponse({
                "error": "Invalid PNR number. PNR should be 10 digits."
            }, status=400)

        # Check cache first
        cache_key = f'pnr_status_{pnr}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse(cached_result)

        try:
            return self._fetch_pnr_status(pnr, cache_key)
        except requests.RequestException as e:
            logger.error(f"Error fetching PNR status: {str(e)}")
            return JsonResponse({
                "error": "Failed to connect to PNR service"
            }, status=503)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({
                "error": "Internal server error"
            }, status=500)

    def _validate_pnr(self, pnr):
        """Validate PNR number format"""
        return bool(pnr and pnr.isdigit() and len(pnr) == 10)

    def _fetch_pnr_status(self, pnr, cache_key):
        """Fetch PNR status from the service"""
        url = f"https://www.confirmtkt.com/pnr-status/{pnr}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        response = requests.get(
            url, 
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        
        html_content = response.text
        pattern = r'data\s*=\s*({.*?});'
        match = re.search(pattern, html_content, re.DOTALL)
        
        if not match:
            return JsonResponse({
                "error": "PNR status not found"
            }, status=404)
            
        try:
            json_data = match.group(1)
            parsed_data = json.loads(json_data)
            
            # Cache the successful result
            cache.set(cache_key, parsed_data, self.CACHE_TIMEOUT)
            
            return JsonResponse(parsed_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for PNR {pnr}: {str(e)}")
            return JsonResponse({
                "error": "Failed to parse PNR status"
            }, status=500)