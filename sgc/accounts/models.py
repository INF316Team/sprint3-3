
#accounts/models.py — Extension du modèle User Django


from django.db import models
from django.contrib.auth.models import User

#profil lié à chaque utlisateur
class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    bio = models.TextField(blank=True, verbose_name="À propos")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"Profil de {self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None
