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