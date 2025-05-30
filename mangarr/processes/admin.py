from django.contrib import admin
from .models import MonitorManga, MonitorChapter, EditChapter

# Register your models here.
admin.site.register(MonitorManga)
admin.site.register(MonitorChapter)
admin.site.register(EditChapter)
