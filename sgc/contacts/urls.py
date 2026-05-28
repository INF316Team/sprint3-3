
#contacts/urls.py — Routes de l'application contacts


from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    # Dashboard
    path('dashboard/',        views.dashboard_view,   name='dashboard'),

    # Contacts CRUD
    path('',                  views.contact_list,     name='list'),
    path('new/',              views.contact_create,   name='create'),
    path('<int:pk>/',         views.contact_detail,   name='detail'),
    path('<int:pk>/edit/',    views.contact_update,   name='update'),
    path('<int:pk>/delete/',  views.contact_delete,   name='delete'),

    # Actions rapides
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('import/csv/', views.import_csv, name='import_csv'),

    # Groupes
    path('groups/',               views.group_list,   name='groups'),
    path('groups/new/',           views.group_create, name='group_create'),
    path('groups/<int:pk>/edit/', views.group_update, name='group_update'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),

    # Export
    path('export/csv/', views.export_csv, name='export_csv'),

    # Import
    path('import/csv/', views.import_csv, name='import_csv'),
]
