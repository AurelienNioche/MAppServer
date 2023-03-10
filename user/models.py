from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models \
    import AbstractBaseUser, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def create_user(self, email, password, condition,
                    experiment_name,
                    **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_superuser', False)

        user = self._create_user(email=email,
                                 password=password,
                                 condition=condition,
                                 experiment_name=experiment_name,
                                 **extra_fields)
        return user


class User(AbstractBaseUser, PermissionsMixin):

    FEMALE = "female"
    MALE = "male"
    OTHER = "other"

    email = models.EmailField(unique=True)

    gender = models.TextField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

    condition = models.TextField(blank=True, null=True)

    experiment_name = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []  # removes email from REQUIRED_FIELDS

    objects = UserManager()

    # class Meta:
    #     db_table = 'user'
    #     app_label = 'user'
