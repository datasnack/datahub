from django.db import models
from django.contrib.auth.models import AbstractUser


# follow django documentation for own user model
# https://docs.djangoproject.com/en/5.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractUser):
    pass
