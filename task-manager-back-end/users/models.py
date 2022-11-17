from django.db import models

# Create your models here.
class UsersDetails(models.Model):
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.CASCADE)
    ProfilePic = models.ImageField(upload_to='profile/', blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    country = models.UUIDField(blank=True, null=True)
    # company = models.ForeignKey("company.Company", on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'users_details'

    def __str__(self):
        return self.user.username