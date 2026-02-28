import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Candidate, Document


# ─── Helpers ────────────────────────────────────────────────────────────────

def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(chars, k=length))


def is_hr(user):
    return user.is_staff or user.is_superuser


# ─── Auth Views ─────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('hr_dashboard' if is_hr(request.user) else 'candidate_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('hr_dashboard' if is_hr(user) else 'candidate_dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'boarding/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── HR Views ───────────────────────────────────────────────────────────────

@login_required
def hr_dashboard(request):
    if not is_hr(request.user):
        return redirect('candidate_dashboard')
    candidates = Candidate.objects.select_related('user').prefetch_related('documents').order_by('-created_at')
    stats = {
        'total': candidates.count(),
        'pending': candidates.filter(status='pending').count(),
        'in_progress': candidates.filter(status='in_progress').count(),
        'completed': candidates.filter(status='completed').count(),
    }
    return render(request, 'boarding/hr_dashboard.html', {'candidates': candidates, 'stats': stats})


@login_required
def create_candidate(request):
    if not is_hr(request.user):
        return redirect('candidate_dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        position = request.POST.get('position', '').strip()
        department = request.POST.get('department', '').strip()
        joining_date = request.POST.get('joining_date') or None
        phone = request.POST.get('phone', '').strip()

        if User.objects.filter(email=email).exists():
            messages.error(request, f'A candidate with email {email} already exists.')
            departments = ['Engineering', 'Product', 'Design', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Legal']
            return render(request, 'boarding/create_candidate.html', {'post': request.POST, 'departments': departments})

        # Generate username from email prefix
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        password = generate_password()
        user = User.objects.create_user(username=username, email=email, password=password,
                                        first_name=full_name.split()[0],
                                        last_name=' '.join(full_name.split()[1:]))

        candidate = Candidate.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            position=position,
            department=department,
            joining_date=joining_date,
            created_by=request.user,
            plain_password=password,
        )

        # Send welcome email
        try:
            send_mail(
                subject=f"Welcome to {settings.COMPANY_NAME} – Your Onboarding Portal Access",
                message=f"""Dear {full_name},

Congratulations and welcome to {settings.COMPANY_NAME}!

We are excited to have you join us as {position} in the {department} department.

Please log in to our Onboarding Portal to complete your document submission:

🔗 Portal URL: {settings.SITE_URL}
👤 Username: {username}
🔑 Password: {password}

You will be asked to upload the following documents:
• Aadhaar Card
• PAN Card
• Passport Photo
• Resume / CV
• 10th & 12th Marksheets
• Degree Certificate
• Bank Passbook / Details

Please change your password after your first login.

If you have any questions, please contact HR.

Best regards,
{request.user.get_full_name() or request.user.username}
HR Team – {settings.COMPANY_NAME}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, f'Candidate {full_name} created and login credentials sent to {email}.')
        except Exception as e:
            messages.warning(request, f'Candidate created but email failed: {e}')

        return redirect('hr_dashboard')

    departments = ['Engineering', 'Product', 'Design', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Legal']
    return render(request, 'boarding/create_candidate.html', {'departments': departments})


@login_required
def candidate_detail(request, pk):
    if not is_hr(request.user):
        return redirect('candidate_dashboard')
    candidate = get_object_or_404(Candidate, pk=pk)
    documents = candidate.documents.all()
    return render(request, 'boarding/candidate_detail.html', {
        'candidate': candidate,
        'documents': documents,
        'doc_types': Document.DOC_TYPES,
    })


@login_required
def review_document(request, doc_id):
    if not is_hr(request.user):
        return redirect('candidate_dashboard')
    doc = get_object_or_404(Document, pk=doc_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '').strip()
        if action in ('approved', 'rejected'):
            doc.status = action
            doc.hr_remarks = remarks
            doc.reviewed_at = timezone.now()
            doc.reviewed_by = request.user
            doc.save()

            # Update candidate overall status
            candidate = doc.candidate
            all_docs = candidate.documents.all()
            uploaded_types = {d.doc_type for d in all_docs}
            required_types = {t[0] for t in Document.DOC_TYPES}
            if required_types.issubset(uploaded_types) and all(d.status == 'approved' for d in all_docs):
                candidate.status = 'completed'
            elif all_docs.exists():
                candidate.status = 'in_progress'
            candidate.save()

            messages.success(request, f'Document {action}.')
        return redirect('candidate_detail', pk=doc.candidate.pk)
    return redirect('hr_dashboard')


# ─── Candidate Views ─────────────────────────────────────────────────────────

@login_required
def candidate_dashboard(request):
    if is_hr(request.user):
        return redirect('hr_dashboard')
    candidate = get_object_or_404(Candidate, user=request.user)
    uploaded = {doc.doc_type: doc for doc in candidate.documents.all()}
    doc_list = [
        {'key': key, 'label': label, 'doc': uploaded.get(key)}
        for key, label in Document.DOC_TYPES
    ]
    total = len(Document.DOC_TYPES)
    done = len(uploaded)
    progress = int((done / total) * 100)
    return render(request, 'boarding/candidate_dashboard.html', {
        'candidate': candidate,
        'doc_list': doc_list,
        'progress': progress,
        'done': done,
        'total': total,
    })


@login_required
def upload_document(request):
    if is_hr(request.user):
        return redirect('hr_dashboard')
    candidate = get_object_or_404(Candidate, user=request.user)

    if request.method == 'POST':
        doc_type = request.POST.get('doc_type')
        file = request.FILES.get('file')
        valid_types = [t[0] for t in Document.DOC_TYPES]

        if doc_type not in valid_types:
            messages.error(request, 'Invalid document type.')
            return redirect('candidate_dashboard')
        if not file:
            messages.error(request, 'Please select a file.')
            return redirect('candidate_dashboard')

        allowed_ext = ['.pdf', '.jpg', '.jpeg', '.png']
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_ext:
            messages.error(request, 'Only PDF, JPG, and PNG files are allowed.')
            return redirect('candidate_dashboard')

        # Replace existing doc of same type
        Document.objects.filter(candidate=candidate, doc_type=doc_type).delete()
        Document.objects.create(candidate=candidate, doc_type=doc_type, file=file)

        if candidate.status == 'pending':
            candidate.status = 'in_progress'
            candidate.save()

        messages.success(request, f'{dict(Document.DOC_TYPES)[doc_type]} uploaded successfully.')
        return redirect('candidate_dashboard')

    return redirect('candidate_dashboard')
