from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
import random

class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True)
    company = models.CharField(max_length=255)
    status = models.CharField(max_length=255,default="1")
    role=  models.CharField(max_length=255,default="company")
    company_id = models.CharField(max_length=255,unique=True)
    # is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_subs= models.BooleanField(default=False)
    def __str__(self):
        return self.username
    class Meta:
        db_table = "Users"
    
    
class Package(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    duration = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    seats = models.IntegerField()
    def __str__(self):
        return self.name
    class Meta:
        db_table = "Packages"
    
    
class Functionality(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    class Meta:
        db_table = "Functionalities"



class PackageDetail(models.Model):
    package = models.ForeignKey(Package,on_delete=models.CASCADE)
    function = models.ForeignKey(Functionality,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.package
    class Meta:
        db_table = "Package Details"

class Subscription(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    package = models.ForeignKey(Package,on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user.username
    class Meta:
        db_table = "Subscriptions"