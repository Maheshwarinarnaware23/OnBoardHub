
from django.contrib import admin
from .models import Candidate, Document


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    readonly_fields = ('uploaded_at', 'reviewed_at', 'reviewed_by')


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'position', 'department', 'status', 'created_at')
    list_filter = ('status', 'department')
    search_fields = ('full_name', 'email', 'position')
    inlines = [DocumentInline]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'doc_type', 'status', 'uploaded_at', 'reviewed_by')
    list_filter = ('status', 'doc_type')