from django.contrib import admin
from .models import RegisterUser  # Importe o modelo RegisterUser


@admin.register(RegisterUser)
class RegisterUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_date", "is_staff")
    search_fields = ("username", "email")
