from argparse import Action
from django.db import models
import uuid

# Create your models here.
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    UpdatedDate = models.DateTimeField(blank=True, null=True)
    DeletedDate = models.DateTimeField(blank=True, null=True)
    CreatedUserID = models.BigIntegerField(blank=True, null=True)
    UpdatedUserID = models.BigIntegerField(blank=True, null=True)
    DeletededUserID = models.BigIntegerField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    Action = models.CharField(max_length=128,default="A", blank=True, null=True)

    class Meta:
        abstract = True