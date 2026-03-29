from django.contrib import admin
from .models import User

admin.site.register(User)  # makes user visible in admin panel
