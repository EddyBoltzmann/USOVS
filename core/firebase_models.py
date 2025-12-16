from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class FirebaseTokenUse(models.Model):
    # Store only hash of the Firebase ID token to prevent plaintext storage
    token_hash = models.CharField(max_length=64, unique=True)
    uid = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Token {self.uid} used at {self.used_at}"


class VerificationAttempt(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    uid = models.CharField(max_length=255, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, null=True, blank=True)
    details = models.JSONField(null=True, blank=True)


class OTPSendLog(models.Model):
    method = models.CharField(max_length=20)  # 'sms' or 'email'
    address = models.CharField(max_length=255, null=True, blank=True)
    uid = models.CharField(max_length=255, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True)
