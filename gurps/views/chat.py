from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404


def chat_view(request):
    return render(request, "global/chat.html")
