from django.urls import path
from . import views
from . import views_vote

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_page, name='login'),
    path('auth/firebase/verify/', views.firebase_verify, name='firebase_verify'),
    path('auth/firebase/log_otp_sent/', views.log_otp_sent, name='log_otp_sent'),
    path('profile/', views.profile, name='profile'),
    path('election/<int:election_id>/vote/', views_vote.cast_vote, name='cast_vote'),
    # Admin export endpoint (admin-only, protected by session auth)
    path('exports/election/<int:election_id>/csv/', views.admin_export_csv, name='admin_export_csv'),
]
