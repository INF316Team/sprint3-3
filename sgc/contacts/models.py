
#contacts/models.py — Modèles Contact et Groupe


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
#goupe/categorie pour organiser les contacts
class ContactGroup(models.Model):
    COLORS = [
        ('#3B82F6', 'Bleu'),
        ('#10B981', 'Vert'),
        ('#F59E0B', 'Jaune'),
        ('#EF4444', 'Rouge'),
        ('#8B5CF6', 'Violet'),
        ('#EC4899', 'Rose'),
        ('#06B6D4', 'Cyan'),
        ('#6B7280', 'Gris'),
    ]

    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_contact')
    name  = models.CharField(max_length=100, verbose_name="Nom du groupe")
    color = models.CharField(max_length=7, choices=COLORS, default='#3B82F6', verbose_name="Couleur")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        ordering = ['name']
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

    def contact_count(self):
        return self.contacts.count()

#modele principal d'un contact
class ContactManager(models.Manager):
    """Manager personnalisé — exclut les contacts supprimés."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Contact(models.Model):
    """Modèle principal d'un contact."""

    # Manager DANS la classe — plus fiable que add_to_class
    objects     = ContactManager()          # exclut les supprimés
    all_objects = models.Manager()          # inclut tout

    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    groups  = models.ManyToManyField(ContactGroup, blank=True, related_name='contacts', verbose_name="Groupes")

    first_name  = models.CharField(max_length=100, verbose_name="Prénom")
    last_name   = models.CharField(max_length=100, blank=True, verbose_name="Nom")
    photo       = models.ImageField(upload_to='contacts/', blank=True, null=True, verbose_name="Photo")
    email       = models.EmailField(blank=True, verbose_name="Email")
    phone       = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    address     = models.TextField(blank=True, verbose_name="Adresse")
    company     = models.CharField(max_length=150, blank=True, verbose_name="Entreprise")
    notes       = models.TextField(blank=True, verbose_name="Notes")
    is_favorite = models.BooleanField(default=False, verbose_name="Favori")
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return self.full_name[0].upper() if self.full_name else "?"

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    
#Manager personnalisé pour exclure les contacts supprimés.
class ContactManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


# # On surcharge le manager par défaut
# Contact.add_to_class('objects', ContactManager())
# Contact.add_to_class('all_objects', models.Manager())  # accès à tous, y compris supprimés
