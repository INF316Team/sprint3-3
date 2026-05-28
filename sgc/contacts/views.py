# Sprint 1 Scrum : Authentification + CRUD Contacts


#contacts/views.py — Toutes les vues de l'application contacts


import csv
import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings
from django.utils import timezone

from .models import Contact, ContactGroup
from .forms import CSVImportForm, ContactForm, ContactGroupForm, SearchForm


# ═══════════════════════════════════════════════════════════════════════════
#  TABLEAU DE BORD
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_view(request):
    #Tableau de bord avec statistiques globales.
    contacts = Contact.objects.filter(user=request.user)

    # Statistiques
    total         = contacts.count()
    favorites     = contacts.filter(is_favorite=True).count()
    with_email    = contacts.exclude(email='').count()
    with_phone    = contacts.exclude(phone='').count()
    recent        = contacts.order_by('-created_at')[:5]

    # Répartition par groupe
    groups = ContactGroup.objects.filter(user=request.user).annotate(
        count=Count('contacts')
    )

    # Données pour le graphique (JSON pour Chart.js)
    chart_labels = [g.name for g in groups]
    chart_data   = [g.count for g in groups]
    chart_colors = [g.color for g in groups]

    context = {
        'total': total,
        'favorites': favorites,
        'with_email': with_email,
        'with_phone': with_phone,
        'recent': recent,
        'groups': groups,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'chart_colors': json.dumps(chart_colors),
    }
    return render(request, 'contacts/dashboard.html', context)


# ═══════════════════════════════════════════════════════════════════════════
#  LISTE DES CONTACTS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def contact_list(request):
    #Liste paginée avec recherche et filtrage.
    contacts = Contact.objects.filter(user=request.user)
    form = SearchForm(request.GET, user=request.user)

    if form.is_valid():
        q             = form.cleaned_data.get('q', '').strip()
        group         = form.cleaned_data.get('group')
        favorites_only = form.cleaned_data.get('favorites_only')

        if q:
            contacts = contacts.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)  |
                Q(email__icontains=q)      |
                Q(phone__icontains=q)      |
                Q(company__icontains=q)
            )
        if group:
            contacts = contacts.filter(groups=group)

        if favorites_only:
            contacts = contacts.filter(is_favorite=True)

    # Filtre alphabétique
    letter = request.GET.get('letter', '').upper()
    if letter and letter.isalpha():
        contacts = contacts.filter(first_name__istartswith=letter)

    # Pagination
    per_page  = getattr(settings, 'CONTACTS_PER_PAGE', 20)
    paginator = Paginator(contacts, per_page)
    page      = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page)

    # Alphabet pour la barre de navigation
    alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    context = {
        'page_obj':  page_obj,
        'form':      form,
        'alphabet':  alphabet,
        'letter':    letter,
        'total':     contacts.count(),
    }
    return render(request, 'contacts/list.html', context)


# ═══════════════════════════════════════════════════════════════════════════
#  DÉTAIL D'UN CONTACT
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def contact_detail(request, pk):
    #Page détail d'un contact.
    contact = get_object_or_404(Contact, pk=pk, user=request.user)
    return render(request, 'contacts/detail.html', {'contact': contact})


# ═══════════════════════════════════════════════════════════════════════════
#  CRÉER UN CONTACT
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def contact_create(request):
    #Création d'un nouveau contact."""
    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            form.save_m2m()  # Sauvegarder les groupes (ManyToMany)
            messages.success(request, f"Contact « {contact.full_name} » créé avec succès !")
            return redirect('contacts:detail', pk=contact.pk)
    else:
        form = ContactForm(user=request.user)

    return render(request, 'contacts/form.html', {
        'form': form,
        'title': 'Nouveau contact',
        'btn_label': 'Créer le contact',
    })


# ═══════════════════════════════════════════════════════════════════════════
#  MODIFIER UN CONTACT
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def contact_update(request, pk):
    #Modification d'un contact existant.
    contact = get_object_or_404(Contact, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES, instance=contact, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contact « {contact.full_name} » mis à jour.")
            return redirect('contacts:detail', pk=contact.pk)
    else:
        form = ContactForm(instance=contact, user=request.user)

    return render(request, 'contacts/form.html', {
        'form': form,
        'contact': contact,
        'title': f'Modifier — {contact.full_name}',
        'btn_label': 'Sauvegarder',
    })


# ═══════════════════════════════════════════════════════════════════════════
#  SUPPRIMER UN CONTACT (soft delete)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def contact_delete(request, pk):
    #Suppression douce d'un contact (avec confirmation).
    contact = get_object_or_404(Contact, pk=pk, user=request.user)

    if request.method == 'POST':
        name = contact.full_name
        contact.soft_delete()
        messages.success(request, f"Contact « {name} » supprimé.")
        return redirect('contacts:list')

    return render(request, 'contacts/confirm_delete.html', {'contact': contact})


# ═══════════════════════════════════════════════════════════════════════════
#  TOGGLE FAVORI (AJAX)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def toggle_favorite(request, pk):
    #Bascule le statut favori d'un contact via AJAX.
    if request.method == 'POST':
        contact = get_object_or_404(Contact, pk=pk, user=request.user)
        contact.is_favorite = not contact.is_favorite
        contact.save()
        return JsonResponse({'is_favorite': contact.is_favorite})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# ═══════════════════════════════════════════════════════════════════════════
#  GROUPES
# ═══════════════════════════════════════════════════════════════════════════


@login_required
def group_list(request):
    #Liste des groupes avec nombre de contacts
    groups = ContactGroup.objects.filter(user=request.user).annotate(
        count=Count('contacts')
    )
    return render(request, 'contacts/groups.html', {'groups': groups})


@login_required
def group_create(request):
    #Création d'un groupe.
    if request.method == 'POST':
        form = ContactGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.user = request.user
            group.save()
            messages.success(request, f"Groupe « {group.name} » créé.")
            return redirect('contacts:groups')
    else:
        form = ContactGroupForm()
    return render(request, 'contacts/group_form.html', {'form': form, 'title': 'Nouveau groupe'})


@login_required
def group_update(request, pk):
    #Modification d'un groupe.
    group = get_object_or_404(ContactGroup, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ContactGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Groupe « {group.name} » modifié.")
            return redirect('contacts:groups')
    else:
        form = ContactGroupForm(instance=group)
    return render(request, 'contacts/group_form.html', {'form': form, 'title': f'Modifier — {group.name}'})


@login_required
def group_delete(request, pk):
    #Suppression d'un groupe.
    group = get_object_or_404(ContactGroup, pk=pk, user=request.user)
    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f"Groupe « {name} » supprimé.")
        return redirect('contacts:groups')
    return render(request, 'contacts/group_confirm_delete.html', {'group': group})


# ═══════════════════════════════════════════════════════════════════════════
#  EXPORT CSV
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def export_csv(request):
    #Export de tous les contacts en fichier CSV.
    contacts = Contact.objects.filter(user=request.user)

    # Créer la réponse HTTP avec le bon Content-Type
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    # BOM UTF-8 pour Excel (Windows)
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')

    # En-têtes
    writer.writerow([
        ' Prénom ', ' Nom ', ' Email ', ' Téléphone ',
        ' Entreprise ', ' Adresse ', ' Groupes ', ' Favori ', ' Notes ', ' Créé le '
    ])

    # Données
    for c in contacts:
        groups_str = ', '.join([g.name for g in c.groups.all()])
        writer.writerow([
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.company,
            c.address,
            groups_str,
            'Oui' if c.is_favorite else 'Non',
            c.notes,
            c.created_at.strftime('%d/%m/%Y'),
        ])

    return response


import csv
import io

@login_required
def import_csv(request):
    """Import de contacts depuis un fichier CSV."""

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)

        if form.is_valid():
            fichier = request.FILES['fichier_csv']

            # Vérifier l'extension
            if not fichier.name.endswith('.csv'):
                messages.error(request, "Le fichier doit être au format .csv")
                return render(request, 'contacts/import_csv.html', {'form': form})

            # Vérifier la taille (max 5 MB)
            if fichier.size > 5 * 1024 * 1024:
                messages.error(request, "Le fichier ne doit pas dépasser 5 MB.")
                return render(request, 'contacts/import_csv.html', {'form': form})

            # Lire avec gestion des encodages UTF-8 et Windows-1252
            try:
                contenu = fichier.read()
                try:
                    texte = contenu.decode('utf-8-sig')
                except UnicodeDecodeError:
                    texte = contenu.decode('windows-1252')
            except Exception:
                messages.error(request, "Impossible de lire le fichier.")
                return render(request, 'contacts/import_csv.html', {'form': form})

            # Détecter le séparateur
            reader = csv.DictReader(io.StringIO(texte), delimiter=';')
            if reader.fieldnames is None or len(reader.fieldnames) <= 1:
                reader = csv.DictReader(io.StringIO(texte), delimiter=',')

            def normaliser(cle):
                if cle is None:
                    return ''
                return cle.strip().lower().replace(' ', '_')

            crees = ignores = erreurs = 0
            doublons = []

            for numero_ligne, ligne in enumerate(reader, start=2):
                ligne_norm = {normaliser(k): (v.strip() if v else '')
                              for k, v in ligne.items()}

                prenom = (ligne_norm.get('prenom') or
                          ligne_norm.get('prénom') or
                          ligne_norm.get('firstname') or '')

                nom    = (ligne_norm.get('nom') or
                          ligne_norm.get('lastname') or '')

                email  = (ligne_norm.get('email') or
                          ligne_norm.get('mail') or '')

                telephone  = (ligne_norm.get('telephone') or
                              ligne_norm.get('téléphone') or
                              ligne_norm.get('phone') or '')

                entreprise = (ligne_norm.get('entreprise') or
                              ligne_norm.get('company') or '')

                adresse    = (ligne_norm.get('adresse') or
                              ligne_norm.get('address') or '')

                notes      = (ligne_norm.get('notes') or '')

                # Ignorer les lignes vides
                if not prenom and not nom:
                    ignores += 1
                    continue

                # Détecter les doublons par email
                if email:
                    if Contact.objects.filter(
                        user=request.user,
                        email__iexact=email
                    ).exists():
                        doublons.append({
                            'ligne': numero_ligne,
                            'nom': f"{prenom} {nom}".strip(),
                            'email': email,
                        })
                        ignores += 1
                        continue

                # Créer le contact
                try:
                    Contact.objects.create(
                        user=request.user,
                        first_name=prenom,
                        last_name=nom,
                        email=email,
                        phone=telephone,
                        company=entreprise,
                        address=adresse,
                        notes=notes,
                    )
                    crees += 1
                except Exception:
                    erreurs += 1

            # Message de résultat
            if crees > 0:
                messages.success(request,
                    f"{crees} contact(s) importé(s). "
                    f"{ignores} ignoré(s). {erreurs} erreur(s).")
            else:
                messages.warning(request,
                    f"Aucun contact importé. "
                    f"{ignores} ignoré(s), {erreurs} erreur(s).")

            if doublons:
                request.session['doublons_import'] = doublons

            return redirect('contacts:list')

    else:
        form = CSVImportForm()

    return render(request, 'contacts/import_csv.html', {'form': form})

@login_required
def import_csv(request):
    """Import de contacts depuis un fichier CSV."""

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)

        if form.is_valid():
            fichier = request.FILES['fichier_csv']

            # Vérifier l'extension
            if not fichier.name.endswith('.csv'):
                messages.error(request, "Le fichier doit être au format .csv")
                return render(request, 'contacts/import_csv.html', {'form': form})

            # Vérifier la taille (max 5 MB)
            if fichier.size > 5 * 1024 * 1024:
                messages.error(request, "Le fichier ne doit pas dépasser 5 MB.")
                return render(request, 'contacts/import_csv.html', {'form': form})

            # Lire avec gestion des encodages UTF-8 et Windows-1252
            try:
                contenu = fichier.read()
                try:
                    texte = contenu.decode('utf-8-sig')
                except UnicodeDecodeError:
                    texte = contenu.decode('windows-1252')
            except Exception:
                messages.error(request, "Impossible de lire le fichier.")
                return render(request, 'contacts/import_csv.html', {'form': form})

            # Détecter le séparateur (; ou ,)
            reader = csv.DictReader(io.StringIO(texte), delimiter=';')
            if reader.fieldnames is None or len(reader.fieldnames) <= 1:
                reader = csv.DictReader(io.StringIO(texte), delimiter=',')

            def normaliser(cle):
                if cle is None:
                    return ''
                return cle.strip().lower().replace(' ', '_')

            crees = ignores = erreurs = 0
            doublons = []

            for numero_ligne, ligne in enumerate(reader, start=2):
                ligne_norm = {normaliser(k): (v.strip() if v else '')
                              for k, v in ligne.items()}

                prenom = (ligne_norm.get('prenom') or
                          ligne_norm.get('prénom') or
                          ligne_norm.get('firstname') or '')

                nom    = (ligne_norm.get('nom') or
                          ligne_norm.get('lastname') or '')

                email  = (ligne_norm.get('email') or
                          ligne_norm.get('mail') or '')

                telephone  = (ligne_norm.get('telephone') or
                              ligne_norm.get('téléphone') or
                              ligne_norm.get('phone') or '')

                entreprise = (ligne_norm.get('entreprise') or
                              ligne_norm.get('company') or '')

                adresse    = (ligne_norm.get('adresse') or
                              ligne_norm.get('address') or '')

                notes      = (ligne_norm.get('notes') or '')

                # Ignorer les lignes sans prénom ni nom
                if not prenom and not nom:
                    ignores += 1
                    continue

                # Détecter les doublons par email (US9)
                if email:
                    if Contact.objects.filter(
                        user=request.user,
                        email__iexact=email
                    ).exists():
                        doublons.append({
                            'ligne': numero_ligne,
                            'nom': f"{prenom} {nom}".strip(),
                            'email': email,
                        })
                        ignores += 1
                        continue

                # Créer le contact
                try:
                    Contact.objects.create(
                        user=request.user,
                        first_name=prenom,
                        last_name=nom,
                        email=email,
                        phone=telephone,
                        company=entreprise,
                        address=adresse,
                        notes=notes,
                    )
                    crees += 1
                except Exception:
                    erreurs += 1

            # Message de résultat
            if crees > 0:
                messages.success(request,
                    f"{crees} contact(s) importé(s). "
                    f"{ignores} ignoré(s). {erreurs} erreur(s).")
            else:
                messages.warning(request,
                    f"Aucun contact importé. "
                    f"{ignores} ignoré(s), {erreurs} erreur(s).")

            # Stocker les doublons en session pour les afficher (US9)
            if doublons:
                request.session['doublons_import'] = doublons

            return redirect('contacts:list')

    else:
        form = CSVImportForm()

    return render(request, 'contacts/import_csv.html', {'form': form})



