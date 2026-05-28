
#accounts/views.py — Vues d'authentification et de profil


from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm
from .models import UserProfile

#inscription d'un nouvel user
def register_view(request):
    
    if request.user.is_authenticated:
        return redirect('contacts:list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue {user.first_name} ! Votre compte a été créé.")
            return redirect('contacts:list')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

#connexion d'un utlisateur existant
def login_view(request):
   
    if request.user.is_authenticated:
        return redirect('contacts:list')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Rediriger vers la page demandée ou la liste des contacts
            next_url = request.GET.get('next', 'contacts:list')
            messages.success(request, f"Bonjour {user.first_name or user.username} !")
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

#deconnexion
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Vous avez été déconnecté.")
    return redirect('accounts:login')

#affichage de la modification du profil utilisateur
@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})
