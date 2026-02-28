from django.db import models
from django.contrib.auth.models import User


class Candidate(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    position = models.CharField(max_length=200)
    department = models.CharField(max_length=200)
    joining_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_candidates')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    plain_password = models.CharField(max_length=100, blank=True)  # stored temporarily for email

    def __str__(self):
        return f"{self.full_name} ({self.position})"

    def get_doc_status(self):
        docs = self.documents.all()
        if not docs.exists():
            return 'pending'
        if docs.filter(status='rejected').exists():
            return 'rejected'
        if all(d.status == 'approved' for d in docs):
            return 'approved'
        return 'in_progress'


class Document(models.Model):
    DOC_TYPES = [
        ('aadhaar', 'Aadhaar Card'),
        ('pan', 'PAN Card'),
        ('photo', 'Passport Photo'),
        ('resume', 'Resume / CV'),
        ('marksheet', '10th / 12th Marksheet'),
        ('degree', 'Degree Certificate'),
        ('bank', 'Bank Details / Passbook'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hr_remarks = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('candidate', 'doc_type')

    def __str__(self):
        return f"{self.candidate.full_name} - {self.get_doc_type_display()}"