from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import Interview, UserProfile
import arabic_reshaper
from bidi.algorithm import get_display

RESULT_MAP = {'pass': 'ناجح', 'fail': 'راسب', 'pending': 'قيد الانتظار'}

def filter_queryset(request):
    qs = Interview.objects.all().order_by('-interview_date')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(position__icontains=q))
    r = request.GET.get('result', '').strip()
    if r in ['pass', 'fail', 'pending']:
        qs = qs.filter(result=r)
    return qs

# ============ عرض المقابلات ============
class InterviewList(LoginRequiredMixin, ListView):
    model = Interview
    template_name = 'interviews/list.html'
    context_object_name = 'interviews'
    paginate_by = 20

    def get_queryset(self):
        return filter_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_query'] = self.request.GET.get('q', '')
        ctx['current_result'] = self.request.GET.get('result', '')
        ctx['total_count'] = self.get_queryset().count()
        ctx['user_role'] = self.request.user.profile.role if hasattr(self.request.user, 'profile') else 'viewer'
        return ctx

# ============ إضافة مقابلة ============
class InterviewCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Interview
    fields = ['name', 'phone', 'position', 'interview_date', 'result', 'notes']
    template_name = 'interviews/form.html'
    success_url = reverse_lazy('interview-list')

    def test_func(self):
        return self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role in ['admin', 'entry'])

# ============ تعديل مقابلة ============
class InterviewUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Interview
    fields = ['name', 'phone', 'position', 'interview_date', 'result', 'notes']
    template_name = 'interviews/form.html'
    success_url = reverse_lazy('interview-list')

    def test_func(self):
        return self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role in ['admin', 'entry'])

# ============ حذف مقابلة ============
class InterviewDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Interview
    template_name = 'interviews/confirm_delete.html'
    success_url = reverse_lazy('interview-list')

    def test_func(self):
        return self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')

# ============ تصدير Excel ============
class InterviewExportExcel(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        qs = filter_queryset(request)
        wb = Workbook()
        ws = wb.active
        ws.title = "المقابلات"
        ws.sheet_view.rightToLeft = True
        headers = ['#', 'الاسم', 'الهاتف', 'الوظيفة', 'تاريخ المقابلة', 'النتيجة', 'ملاحظات']
        ws.append(headers)
        header_fill = PatternFill("solid", fgColor="2C3E50")
        header_font = Font(color="FFFFFF", bold=True)
        for col in ws[1]:
            col.fill = header_fill
            col.font = header_font
            col.alignment = Alignment(horizontal='center', vertical='center')
        for idx, obj in enumerate(qs, start=1):
            ws.append([idx, obj.name, obj.phone or '', obj.position, str(obj.interview_date), RESULT_MAP.get(obj.result, obj.result), obj.notes or ''])
        
        for i, w in enumerate([5, 20, 15, 20, 15, 12, 30], start=1):
            ws.column_dimensions[chr(64 + i)].width = w

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="interviews.xlsx"'
        wb.save(response)
        return response

# ============ تصدير PDF ============
class InterviewExportPDF(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        qs = filter_queryset(request)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="interviews.pdf"'
        doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
        
        arabic = 'Helvetica'
        for path in ['C:/Windows/Fonts/tahoma.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
            try:
                pdfmetrics.registerFont(TTFont('Arabic', path))
                arabic = 'Arabic'
                break
            except: continue
            
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleAr', parent=styles['Heading1'], fontName=arabic, alignment=1, fontSize=16)
        cell_style = ParagraphStyle('CellAr', parent=styles['Normal'], fontName=arabic, fontSize=9, alignment=1)
        
        title_text = get_display(arabic_reshaper.reshape("تقرير المقابلات"))
        elements = [Paragraph(title_text, title_style), Spacer(1, 12)]
        
        headers = [
            get_display(arabic_reshaper.reshape('ملاحظات')),
            get_display(arabic_reshaper.reshape('النتيجة')),
            get_display(arabic_reshaper.reshape('التاريخ')),
            get_display(arabic_reshaper.reshape('الوظيفة')),
            get_display(arabic_reshaper.reshape('الهاتف')),
            get_display(arabic_reshaper.reshape('الاسم')),
            get_display(arabic_reshaper.reshape('#'))
        ]
        data = [headers]
        
        for idx, obj in enumerate(qs, start=1):
            result_text = get_display(arabic_reshaper.reshape(RESULT_MAP.get(obj.result, obj.result)))
            notes_text = get_display(arabic_reshaper.reshape((obj.notes or '')[:40]))
            data.append([
                Paragraph(notes_text, cell_style),
                Paragraph(result_text, cell_style),
                str(obj.interview_date), 
                Paragraph(get_display(arabic_reshaper.reshape(obj.position)), cell_style), 
                Paragraph(get_display(arabic_reshaper.reshape(obj.phone)), cell_style), 
                Paragraph(get_display(arabic_reshaper.reshape(obj.name)), cell_style), 
                str(idx)
            ])
            
        table = Table(data, colWidths=[130, 70, 70, 100, 80, 100, 25])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), arabic),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        elements.append(table)
        doc.build(elements)
        return response


# =========================================================
# ============ إدارة المستخدمين (للمدير فقط) ============
# =========================================================

class UserList(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'users/form.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('user-list')

    def test_func(self):
        return self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')

    def form_valid(self, form):
        user = form.save()
        role = self.request.POST.get('role', 'viewer')
        raw_password = form.cleaned_data.get('password1')
        
        if hasattr(user, 'profile'):
            user.profile.role = role
            user.profile.plain_password = raw_password
            user.profile.save()
            
        messages.success(self.request, f'تم إنشاء المستخدم {user.username} بنجاح.')
        return super().form_valid(form)


def toggle_user_active(request, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        return redirect('interview-list')
    
    try:
        user = User.objects.get(id=user_id)
        if user != request.user:
            user.is_active = not user.is_active
            user.save()
    except User.DoesNotExist:
        pass
    return redirect('user-list')


def change_user_role(request, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        return redirect('interview-list')
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        try:
            user = User.objects.get(id=user_id)
            if hasattr(user, 'profile'):
                user.profile.role = new_role
                user.profile.save()
        except User.DoesNotExist:
            pass
    return redirect('user-list')


# ============ صفحة إنشاء حساب جديد ============
class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        raw_password = form.cleaned_data.get('password1')
        
        # أول حساب فقط يصير أدمن
        if User.objects.count() == 0: 
            user.is_active = True
            user.is_superuser = True
            user.is_staff = True
            user.save()
            if hasattr(user, 'profile'):
                user.profile.role = 'admin'
                user.profile.plain_password = raw_password
                user.profile.save()
            messages.success(self.request, 'تم إنشاء حساب المدير بنجاح! يمكنك الآن تسجيل الدخول.')
        else:
            user.is_active = False
            user.save()
            if hasattr(user, 'profile'):
                user.profile.role = 'viewer'
                user.profile.plain_password = raw_password
                user.profile.save()
            messages.success(self.request, 'تم إنشاء الحساب! يرجى انتظار موافقة مدير النظام لتفعيل الحساب.')
            
        return super().form_valid(form)


def change_user_password(request, user_id):
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        return redirect('interview-list')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = SetPasswordForm(user_obj, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تغيير كلمة مرور المستخدم {user_obj.username} بنجاح.')
            return redirect('user-list')
    else:
        form = SetPasswordForm(user_obj)
        
    return render(request, 'users/change_password.html', {'form': form, 'user_obj': user_obj})


def edit_user(request, user_id):
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        return redirect('interview-list')
    
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        if username:
            user_obj.username = username
        
        if password:
            user_obj.set_password(password)
            if hasattr(user_obj, 'profile'):
                user_obj.profile.plain_password = password
                
        if hasattr(user_obj, 'profile') and role:
            user_obj.profile.role = role
            user_obj.profile.save()
            
        user_obj.save()
        messages.success(self.request, f'تم تحديث بيانات المستخدم {user_obj.username} بنجاح.')
        return redirect('user-list')
        
    return render(request, 'users/edit_user.html', {'user_obj': user_obj})

# ============ دالة حذف مستخدم ============
def delete_user(request, user_id):
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        return redirect('interview-list')
    
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj != request.user:
        user_obj.delete()
        messages.success(request, f'تم حذف المستخدم بنجاح.')
    return redirect('user-list')

# ============ دالة تصفير الحسابات (تبقي Admin فقط) ============
def reset_all_users(request):
    if request.user.is_authenticated and request.user.username == 'Admin':
        User.objects.exclude(username='Admin').delete()
        messages.success(self.request, 'تم مسح جميع الحسابات الأخرى بنجاح! أنت الآن المدير الوحيد.')
    return redirect('user-list')
