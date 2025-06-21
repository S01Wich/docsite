from django.contrib import admin
from .models import TemplateDoc

@admin.register(TemplateDoc)
class TemplateDocAdmin(admin.ModelAdmin):
    list_display = ('name', 'doc_file')