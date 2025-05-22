# core/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from server.functions import restart_app
from database.users.models import UserProfile
from django.contrib.auth.models import User

def get_user_by_token(auth_header: str) -> User:
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.removeprefix("Bearer ").strip()
    return UserProfile.objects.filter(token=token).first().user

def validate_token(auth_header: str) -> bool:
    if not auth_header or not auth_header.startswith("Bearer "):
        return False

    token = auth_header.removeprefix("Bearer ").strip()
    return UserProfile.objects.filter(token=token).exists()

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
        # Touch the settings file or any stable .py file
        restart_app()
        return JsonResponse({"status": "Restart triggered"}, status=202)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
