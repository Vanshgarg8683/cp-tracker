from django.contrib.auth.models import AbstractUser  # gives default user fields like username, password
from django.db import models

class User(AbstractUser):  # extending default Django user
    cf_handle = models.CharField(max_length=100, blank=True, null=True)  # optional CF username
