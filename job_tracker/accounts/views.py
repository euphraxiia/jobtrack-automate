"""
Views for the accounts app.

Handles user registration, login, profile management,
and account settings.
"""
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, TemplateView

from .models import UserProfile
from .forms import UserProfileForm, UserRegistrationForm


class RegisterView(TemplateView):
    """Handle new user registration."""
    template_name = 'accounts/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to JobTrack! Your account has been created.')
            return redirect('dashboard')
        return render(request, self.template_name, {'form': form})


class LoginView(TemplateView):
    """Handle user login."""
    template_name = 'accounts/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


def logout_view(request):
    """Log the user out and redirect to the home page."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """Allow the user to view and edit their profile."""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        # Always return the current user's profile
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated.')
        return super().form_valid(form)
