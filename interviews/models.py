from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Interview(models.Model):
    RESULT_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('pass', 'ناجح'),
        ('fail', 'راسب'),
    ]

    name = models.CharField('الاسم', max_length=100)
    phone = models.CharField('الهاتف', max_length=20)
    email = models.EmailField('البريد الإلكتروني', blank=True)
    position = models.CharField('الوظيفة المتقدم لها', max_length=100)
    interview_date = models.DateField('تاريخ المقابلة') # رجعناها عادية
    result = models.CharField('النتيجة', max_length=10, choices=RESULT_CHOICES, default='pending')
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مقابلة'
        verbose_name_plural = 'المقابلات'
        ordering = ['-interview_date']

    def __str__(self):
        return f"{self.name} - {self.position}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'مدير النظام'),
        ('entry', 'مدخل بيانات'),
        ('viewer', 'مشاهد'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('الدور', max_length=10, choices=ROLE_CHOICES, default='viewer')
    
    # الحقل الجديد لعرض كلمة المرور
    plain_password = models.CharField('كلمة المرور الصريحة', max_length=128, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# إنشاء بروفايل تلقائي عند إنشاء أي مستخدم
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)        