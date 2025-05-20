from django.contrib import admin
from .models import UserProfile, RegisterToken, MangaRequest

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(RegisterToken)
admin.site.register(MangaRequest)
