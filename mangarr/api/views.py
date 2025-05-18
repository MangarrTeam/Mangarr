from django.contrib.auth.models import User, Permission
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from server.functions import superuser_or_staff_required, superuser_required
from database.models import UserProfile, RegisterToken
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

# Create your views here.
@superuser_or_staff_required
def get_user_permissions(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user_permissions = user.user_permissions.all()
    userprofile_ct = ContentType.objects.get_for_model(UserProfile)
    custom_permissions = Permission.objects.filter(
        content_type=userprofile_ct,
        codename__in=user.profile.get_custom_permissions()
    )
    all_permissions = set(list(custom_permissions) + list(user_permissions))

    return JsonResponse({
        "permissions": [
            {"id": perm.id, "name": _(perm.name), "codename": perm.codename, "has": perm in user_permissions}
            for perm in all_permissions
        ]
   })


@superuser_or_staff_required
def update_user_permissions(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id)
        permission_str = request.POST.get('permissions')
        permission_ids = permission_str.split(",") if len(permission_str) > 0 else []
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.user_permissions.set(permissions)
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@superuser_required
def toggle_staff_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            return JsonResponse({"error": "Forbidden"}, status=403)
        user.is_staff = not user.is_staff
        user.save()
        source = request.POST.get("zource")
        if source is None:
            source = 'index'
        try:
            reverse(source)
        except:
            source = 'index'

        return redirect(source)
    return JsonResponse({"error": "Forbidden"}, status=400)

@superuser_or_staff_required
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            return JsonResponse({"error": "Forbidden"}, status=403)
        user.delete()
        return JsonResponse({'success': True})
    return JsonResponse({"error": "Forbidden"}, status=400)

@superuser_or_staff_required
def delete_token(request, token_id):
    if request.method == 'POST':
        token = get_object_or_404(RegisterToken, id=token_id)
        token.delete()
        return JsonResponse({'success': True})
    return JsonResponse({"error": "Forbidden"}, status=400)