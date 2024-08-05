from django.contrib import admin
from django.utils.safestring import mark_safe

from realty_photos.models import RealtyPhoto


@admin.register(RealtyPhoto)
class RealtyPhotoAdmin(admin.ModelAdmin):
    list_display = ('preview', 'filename', 'realty',)

    fields = [
        'realty',
        ('preview', 'image'),
    ]
    readonly_fields = ('preview',)

    def preview(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" style="width: 100px">')

    def filename(self, obj):
        return obj.image.name

    preview.short_description = 'Превью'
    filename.short_description = 'Файл'
