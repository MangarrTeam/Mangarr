from django.contrib import admin
from .models import Library, MangaRequest, Manga, Volume, Chapter

# Register your models here.
admin.site.register(Library)
admin.site.register(MangaRequest)
admin.site.register(Manga)
admin.site.register(Volume)
admin.site.register(Chapter)
