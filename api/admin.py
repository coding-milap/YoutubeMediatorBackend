from django.contrib import admin
from .models import CustomUser,CreatorToEditorLink,Video


admin.site.register(CustomUser)
admin.site.register(CreatorToEditorLink)
admin.site.register(Video)