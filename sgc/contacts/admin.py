
#contacts/admin.py — Configuration de l'interface d'administration


from django.contrib import admin
from .models import Contact, ContactGroup


@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'user', 'contact_count', 'created_at')
    list_filter  = ('user',)
    search_fields = ('name',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'email', 'phone', 'company', 'is_favorite', 'is_deleted', 'user')
    list_filter   = ('is_favorite', 'is_deleted', 'user', 'groups')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    filter_horizontal = ('groups',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')

    def get_queryset(self, request):
        # Afficher TOUS les contacts dans l'admin (y compris supprimés)
        return Contact.all_objects.all()
