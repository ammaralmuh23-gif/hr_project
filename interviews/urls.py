from django.urls import path
from . import views

urlpatterns = [
    # المقابلات
    path('', views.InterviewList.as_view(), name='interview-list'),
    path('add/', views.InterviewCreate.as_view(), name='interview-add'),
    path('<int:pk>/edit/', views.InterviewUpdate.as_view(), name='interview-edit'),
    path('<int:pk>/delete/', views.InterviewDelete.as_view(), name='interview-delete'),
    path('export/excel/', views.InterviewExportExcel.as_view(), name='interview-export-excel'),
    path('export/pdf/', views.InterviewExportPDF.as_view(), name='interview-export-pdf'),

    # المستخدمين
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/add/', views.UserCreateView.as_view(), name='user-add'),
    path('users/<int:user_id>/toggle/', views.toggle_user_active, name='user-toggle'),
    path('users/<int:user_id>/role/', views.change_user_role, name='user-role'),
        # تسجيل حساب جديد
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('users/<int:user_id>/password/', views.change_user_password, name='user-password'),
    path('users/<int:user_id>/edit/', views.edit_user, name='user-edit'),
    path('users/<int:user_id>/delete/', views.delete_user, name='user-delete'),
    path('reset-users/', views.reset_all_users, name='reset-users'),
]
