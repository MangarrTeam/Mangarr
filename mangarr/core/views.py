# core/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .utils import restart_app
from database.users.utils import get_user_by_token, validate_token

@csrf_exempt
@require_POST
def restart(request):
    # Optional: secure with a token
    if not validate_token(request.headers.get("Authorization")):
        return JsonResponse({"error": "Unauthorized", "detail": "Invalid Token."}, status=401)
    
    token_user = get_user_by_token(request.headers.get("Authorization"))

    if token_user is None or not token_user.has_perm("database.can_restart"):
        return JsonResponse({"error": "Unauthorized", "detail": "User is not permitted to restart server."}, status=401)

    try:
        restart_app()
        return JsonResponse({"status": "Restart triggered"}, status=202)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
