from typing import Any
from django.db import models
from django.contrib.auth.models import User,AbstractUser
from django.contrib.auth.base_user import BaseUserManager
import uuid



class CustomManager(BaseUserManager):

    def create_user(self,email,password,**extra_fields):
        
        if not email:

            raise ValueError("The Email must be there.")
    

        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self,email,password,**extra_fields):

        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)
        extra_fields.setdefault("is_active",True)

        if extra_fields.get("is_staff") is not True:

            raise ValueError("Must be set to True for superuser.")
        
        if extra_fields.get("is_superuser") is not True:

            raise ValueError("Must be set to True for superuser.") 
    

        return self.create_user(email,password,**extra_fields)


class CustomUser(AbstractUser):

    CHOICES = (
        ("CREATOR","CREATOR"),
        ("EDITOR","EDITOR"),
    )

    id = models.UUIDField(default=uuid.uuid4,primary_key=True)
    username = None
    email = models.EmailField(unique=True)
    type = models.CharField(max_length=200,choices=CHOICES,default="CREATOR")
    full_name = models.CharField(max_length=200)
    credentials = models.JSONField(null=True,blank=True)
    avatar = models.CharField(max_length=300,blank=True,null=True)
    

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomManager()

    def __str__(self):

        return self.email

class CreatorToEditorLink(models.Model):

    STATUS = (
        ("CONNECTED","CONNECTED"),
        ("PENDING","PENDING"),
        ("NOTCONNECTED","NOTCONNECTED")
    )

    creator = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name="creator")
    editor = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name="editor")
    status = models.CharField(max_length=200,choices=STATUS,default="NOTCONNECTED")
    created_by = models.CharField(max_length=200,default="null")
    
    def __str__(self):

        return f'{self.creator} -- {self.editor}'

class Video(models.Model):

    PRIVACY_STATUS = (
        ("private","private"),
        ("public","public"),
        ("unlisted","unlisted"),
    )

    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.TextField()
    video_id = models.CharField(max_length=500,null=True,blank=True)
    privacy_status = models.CharField(max_length=100,choices=PRIVACY_STATUS,default="public")
    cloudinary_id = models.TextField(null=True,blank=True)
    video_file = models.FileField(upload_to="videos/")
    thumbnail = models.ImageField(upload_to="thumbnails/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.title
    