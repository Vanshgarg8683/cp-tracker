from django.db import models
from django.conf import settings

class CPProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    # one profile per user

    cf_handle = models.CharField(max_length=100)  # store handle
    rating = models.IntegerField(null=True, blank=True)  # current rating
    max_rating = models.IntegerField(null=True, blank=True)  # max rating

class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    # many submissions → one user

    problem_name = models.CharField(max_length=200)  # problem title

    verdict = models.CharField(max_length=50)  # OK / WRONG_ANSWER

    tags = models.JSONField()  
    # stores list like ["dp", "graphs"]

    rating = models.IntegerField(null=True, blank=True)  
    # difficulty (may be None)

    creation_time = models.DateTimeField()  
    # submission time
