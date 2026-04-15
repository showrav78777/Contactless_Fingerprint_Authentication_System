from django.contrib import admin
from .models import Note, ProcessedImage

admin.site.register(Note)
admin.site.register(ProcessedImage)
