"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from administration.views import BranchListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/branches/', BranchListView.as_view(), name='branch-list'),
    path('api/notifications/', include('notifications.urls')),
    path('api/admin/', include('administration.urls')),
    path('api/admin/', include('agents.admin_urls')),
    path('api/principal/', include('principal.urls')),
    path('api/students/me/', include('students.urls')),
    path('api/student/application/', include('admissions.urls')),
    path('api/verification/', include('verification.urls')),
    path('api/officer/', include('admissions.urls')),
    path('api/officer/seats/', include('seats.urls')),
    path('api/seats/', include('seats.urls')),
    path('api/agents/', include('agents.urls')),
]
