from django.contrib import admin
from .models import UserProfile, RegisterToken

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(RegisterToken)