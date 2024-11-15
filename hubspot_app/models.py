
from django.db import models

class Contact(models.Model):
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=80)
    lastname = models.CharField(max_length=80)
    phone = models.CharField(max_length=20, null=True, blank=True)
    hubspot_id = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.email


class Deal(models.Model):
    deal_name = models.CharField(max_length=120)
    amount = models.FloatField(null=True, blank=True)
    stage = models.CharField(max_length=80)
    close_date = models.CharField(max_length=50, null=True, blank=True)
    hubspot_id = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.deal_name