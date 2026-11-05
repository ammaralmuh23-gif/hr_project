from django.contrib import admin
from .models import Interview

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'position', 'interview_date', 'result')
    list_filter = ('result', 'interview_date')
    search_fields = ('name', 'phone', 'position')