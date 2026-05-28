
#contacts/forms.py — Formulaires pour les contacts et groupes


from django import forms
from .models import Contact, ContactGroup

#formulaire de creation et modification d'un contact
class ContactForm(forms.ModelForm):
    

    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'photo',
            'email', 'phone', 'address',
            'company', 'groups', 'notes', 'is_favorite',
        ]
        widgets = {
            'first_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom *'}),
            'last_name':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'photo':       forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237 6XX XXX XXX'}),
            'address':     forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Adresse'}),
            'company':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entreprise'}),
            'groups':      forms.CheckboxSelectMultiple(),
            'notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes libres…'}),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Limiter les groupes à ceux de l'utilisateur connecté
        if user:
            self.fields['groups'].queryset = ContactGroup.objects.filter(user=user)
        self.fields['first_name'].required = True

#formulaire de creation et modication d'un groupe
class ContactGroupForm(forms.ModelForm):
    class Meta:
        model = ContactGroup
        fields = ['name', 'color']
        widgets = {
            'name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du groupe'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
        }

#formulaire de recherche et filtrage de contact
class SearchForm(forms.Form):
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un contact…',
            'id': 'search-input',
        })
    )
    group = forms.ModelChoiceField(
        queryset=ContactGroup.objects.none(),
        required=False,
        empty_label="Tous les groupes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    favorites_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['group'].queryset = ContactGroup.objects.filter(user=user)


class CSVImportForm(forms.Form):
    """Formulaire d'import de fichier CSV."""
    fichier_csv = forms.FileField(
        label="Fichier CSV",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
        }),
        help_text="Colonnes attendues : prenom ; nom ; email ; telephone ; entreprise ; adresse ; notes"
    )

class CSVImportForm(forms.Form):
    """Formulaire d'import de fichier CSV."""
    fichier_csv = forms.FileField(
        label="Fichier CSV",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
        }),
        help_text="Colonnes attendues : prenom ; nom ; email ; telephone ; entreprise ; adresse ; notes"
    )
