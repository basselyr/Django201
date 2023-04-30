from typing import Any, Dict
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.views.generic import DetailView, View
from feed.models import Post
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from followers.models import Follower
from .forms import UpdateProfile, UpdateUser
from .models import Profile
from django.contrib import messages
from sorl.thumbnail import ImageField

# Create your views here.

class ProfileDetailView(DetailView):
    http_method_names = ["get"]
    template_name = "profiles/detail.html"
    model = User
    context_object_name = "user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.get_object()
        context = super().get_context_data(**kwargs)
        context['total_posts'] = Post.objects.filter(author=user).count()
        context['total_followers'] = Follower.objects.filter(following=user).count()
        context['total_following'] = Follower.objects.filter(followed_by=user).count()
        
        if self.request.user.is_authenticated:
            context['you_follow'] = Follower.objects.filter(following=user, followed_by=self.request.user).exists()
            if context['you_follow']:
                context['followAction'] = "unfollow"
                context['followStyle'] = "text-red-500 hover:bg-red-500 border-red-500"
            else:
                context['followAction'] = "follow"
                context['followStyle'] = "text-blue-500 hover:bg-blue-500 border-blue-500"
            
        return context
    
class FollowView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        if "action" not in data or "username" not in data:
            return HttpResponseBadRequest("Missing data")
        
        try:
            other_user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            return HttpResponseBadRequest("Missing User")
        
        if data['action'] == 'follow':
            #follow
            follower, created = Follower.objects.get_or_create(
                followed_by = request.user,
                following = other_user
            )
        else:
            #Unfollow
            try:
                follower = Follower.objects.get(
                    followed_by = request.user,
                    following = other_user
                )
            except Follower.DoesNotExist:
                follower = None

            if follower:
                follower.delete()

        return JsonResponse({
            'success': True,
            'wording': "Unfollow" if data['action'] == "follow" else "Follow"
        })

def profupdate(request):
    if request.method == 'POST':
        user_form = UpdateUser(request.POST, instance=request.user)
        profile_form = UpdateProfile(request.POST, request.FILES,instance=request.user.profile)
    
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect(to="/")
    else:
        user_form = UpdateUser(instance=request.user)
        profile_form = UpdateProfile(instance=request.user.profile)
    
    return render(request, 'profiles/update.html', {'user_form': user_form, 'profile_form': profile_form})