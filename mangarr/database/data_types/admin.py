from django.contrib import admin
from .models import StringType, BoolType, IntType, FloatType, DateType, FormatsEnumType, AgeRatingEnumType, StatusEnumType

# Register your models here.
admin.site.register(StringType)
admin.site.register(BoolType)
admin.site.register(IntType)
admin.site.register(FloatType)
admin.site.register(DateType)
admin.site.register(FormatsEnumType)
admin.site.register(AgeRatingEnumType)
admin.site.register(StatusEnumType)