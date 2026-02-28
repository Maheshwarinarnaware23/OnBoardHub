from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # HR
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/create-candidate/', views.create_candidate, name='create_candidate'),
    path('hr/candidate/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('hr/document/<int:doc_id>/review/', views.review_document, name='review_document'),

    # Candidate
    path('portal/', views.candidate_dashboard, name='candidate_dashboard'),
    path('portal/upload/', views.upload_document, name='upload_document'),
]
