from django.contrib.auth.models import AbstractUser
from django.db import models


# follow django documentation for own user model
# https://docs.djangoproject.com/en/5.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractUser):
    pass


class BearerToken(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    description = models.TextField(blank=True, null=True)
    token = models.CharField(max_length=128, unique=True)
