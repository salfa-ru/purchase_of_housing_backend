from django.contrib import admin

from complaints.models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('desc', 'owner', 'realty', 'is_new',)
    list_filter = ('is_new',)

    def desc(self, obj):
        return (f'{obj.description[:20]}'
                f'{"..." if len(obj.description) > 20 else ""}')

    desc.short_description = 'Жалоба'
