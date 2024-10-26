import requests
import re
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

@require_GET
def get_pnr_status(request):
    pnr = request.GET.get('pnr', None)
    if not pnr:
        return JsonResponse({"error": "PNR number not provided"}, status=400)

    url = f"https://www.confirmtkt.com/pnr-status/{pnr}"
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text
        pattern = r'data\s*=\s*({.*?;)'  # Regex pattern to extract data
        match = re.search(pattern, html_content, re.DOTALL)

        if match:
            json_data = match.group(1).replace(';', '')
            try:
                parsed_data = json.loads(json_data)
                return JsonResponse(parsed_data)
            except json.JSONDecodeError as e:
                return JsonResponse({"error": "Failed to parse PNR status"}, status=500)
        else:
            return JsonResponse({"error": "PNR status not found"}, status=404)
    else:
        return JsonResponse({"error": "Failed to retrieve PNR status"}, status=response.status_code)
