from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django import forms as djforms
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.conf import settings as django_settings

from .models import (
    SiteSettings, Course, Teacher, Result,
    Notice, GalleryImage, FAQ, BatchSchedule
)

from accounts.views import teacher_required


# ─────────────────────────────────────────
#  PWA (Progressive Web App)
# ─────────────────────────────────────────

@never_cache
def pwa_manifest(request):
    settings    = SiteSettings.objects.first()
    name        = settings.academy_name if settings else 'KSA'
    short_name  = name if len(name) <= 12 else 'KSA'
    theme_color = '#0C447C'

    manifest = {
        'name': name,
        'short_name': short_name,
        'description': 'Coaching center management: exams, results, attendance & more.',
        'start_url': '/accounts/login/',
        'scope': '/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#F3F1EB',
        'theme_color': theme_color,
        'lang': 'en',
        'icons': [
            {'src': '/static/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/static/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/static/icons/icon-maskable-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'maskable'},
            {'src': '/static/icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return JsonResponse(manifest)


@never_cache
def pwa_sw(request):
    content = (django_settings.BASE_DIR / 'static' / 'sw.js').read_text(encoding='utf-8')
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


# ─────────────────────────────────────────
#  Public home page
# ─────────────────────────────────────────

def home_view(request):
    settings    = SiteSettings.objects.first()
    courses     = Course.objects.only(
        'name', 'subject', 'description', 'icon', 'icon_bg_color',
        'icon_color', 'level', 'fee_per_month', 'order'
    )
    teachers    = Teacher.objects.only(
        'name', 'designation', 'subject', 'qualification',
        'experience_years', 'short_bio', 'photo',
        'avatar_initials', 'avatar_bg', 'avatar_color'
    )
    latest_year = Result.objects.values_list("year", flat=True).first()
    results     = Result.objects.filter(year=latest_year) if latest_year else []
    notices     = Notice.objects.only('title', 'body', 'notice_type', 'is_pinned', 'published_at')
    gallery     = GalleryImage.objects.only('title', 'image', 'caption', 'order')[:8]
    faqs        = FAQ.objects.only('question', 'answer', 'order')
    schedules   = BatchSchedule.objects.select_related("course", "teacher").all()

    is_teacher  = request.user.is_authenticated and request.user.role == 'teacher'

    return render(request, "home.html", {
        "settings":    settings,
        "courses":     courses,
        "teachers":    teachers,
        "results":     results,
        "latest_year": latest_year,
        "notices":     notices,
        "gallery":     gallery,
        "faqs":        faqs,
        "schedules":   schedules,
        "is_teacher":  is_teacher,
    })


@login_required
def notice_add(request):
    if request.user.role != 'teacher':
        return redirect('home')
    if request.method == 'POST':
        Notice.objects.create(
            title=request.POST['title'],
            body=request.POST['body'],
            notice_type=request.POST.get('notice_type', 'general'),
            is_pinned=request.POST.get('is_pinned') == 'on',
        )
    return redirect('home')


@login_required
def notice_edit(request, pk):
    if request.user.role != 'teacher':
        return redirect('home')
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.title       = request.POST['title']
        notice.body        = request.POST['body']
        notice.notice_type = request.POST.get('notice_type', 'general')
        notice.is_pinned   = request.POST.get('is_pinned') == 'on'
        notice.save()
    return redirect('home')


@login_required
def notice_delete(request, pk):
    if request.user.role != 'teacher':
        return redirect('home')
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    return redirect('home')


# ─────────────────────────────────────────
#  Content model registry
# ─────────────────────────────────────────

CONTENT_MODELS = {
    'course': {
        'model': Course,
        'label': 'Courses',
        'icon': 'ti ti-book-2',
        'columns': ('name', 'subject', 'level', 'fee_per_month'),
    },
    'teacher': {
        'model': Teacher,
        'label': 'Teachers',
        'icon': 'ti ti-school',
        'columns': ('name', 'subject', 'qualification'),
    },
    'result': {
        'model': Result,
        'label': 'Results',
        'icon': 'ti ti-trophy',
        'columns': ('year', 'label', 'value'),
    },
    'gallery': {
        'model': GalleryImage,
        'label': 'Gallery Images',
        'icon': 'ti ti-photo',
        'columns': ('title', 'caption'),
    },
    'faq': {
        'model': FAQ,
        'label': 'FAQs',
        'icon': 'ti ti-help-circle',
        'columns': ('question', 'answer'),
    },
    'schedule': {
        'model': BatchSchedule,
        'label': 'Batch Schedules',
        'icon': 'ti ti-calendar-event',
        'columns': ('batch_name', 'course', 'days', 'time_slot'),
    },
    'notice': {
        'model': Notice,
        'label': 'Notices',
        'icon': 'ti ti-bell',
        'columns': ('title', 'notice_type', 'is_pinned'),
    },
}


def _resolve_model(model_key):
    info = CONTENT_MODELS.get(model_key)
    if info is None:
        return None
    return info['model']


def _cell(value):
    if hasattr(value, 'url'):
        return str(value)
    if isinstance(value, models.Model):
        return str(value)
    if value is None or value == '':
        return '—'
    return str(value)


def _display_cell(obj, field):
    try:
        f = obj._meta.get_field(field)
        if f.choices:
            return _cell(getattr(obj, f'get_{field}_display')())
    except Exception:
        pass
    return _cell(getattr(obj, field))


def _build_rows(objects, columns):
    return [
        {
            'id': obj.pk,
            'cells': [_display_cell(obj, col) for col in columns],
        }
        for obj in objects
    ]


# ─────────────────────────────────────────
#  Generic content management
# ─────────────────────────────────────────

@teacher_required
def manage_content(request, model_key):
    model = _resolve_model(model_key)
    if model is None:
        return redirect('home')

    info   = CONTENT_MODELS[model_key]
    Form   = djforms.modelform_factory(model, fields='__all__')
    objects = model.objects.all()

    paginator = Paginator(objects, 5)
    page_obj  = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST':
        form = Form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_content', model_key=model_key)
    else:
        form = Form()

    context = {
        'info':      info,
        'model_key': model_key,
        'form':      form,
        'columns':   info['columns'],
        'rows':      _build_rows(page_obj.object_list, info['columns']),
        'page_obj':  page_obj,
        'total':     paginator.count,
    }
    return render(request, 'manage_list.html', context)


@teacher_required
def manage_edit(request, model_key, pk):
    model = _resolve_model(model_key)
    if model is None:
        return redirect('home')

    info = CONTENT_MODELS[model_key]
    Form = djforms.modelform_factory(model, fields='__all__')
    obj  = get_object_or_404(model, pk=pk)

    if request.method == 'POST':
        form = Form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('manage_content', model_key=model_key)
    else:
        form = Form(instance=obj)

    context = {
        'info':      info,
        'model_key': model_key,
        'form':      form,
        'object':    obj,
    }
    return render(request, 'manage_form.html', context)


@teacher_required
def manage_delete(request, model_key, pk):
    model = _resolve_model(model_key)
    if model is None:
        return redirect('home')

    info = CONTENT_MODELS[model_key]
    obj  = get_object_or_404(model, pk=pk)

    if request.method == 'POST':
        obj.delete()
        return redirect('manage_content', model_key=model_key)

    context = {
        'info':      info,
        'model_key': model_key,
        'object':    obj,
    }
    return render(request, 'manage_delete.html', context)


# ─────────────────────────────────────────
#  Site settings
# ─────────────────────────────────────────

@teacher_required
def manage_settings(request):
    settings = SiteSettings.objects.first()
    if settings is None:
        settings = SiteSettings.objects.create()

    Form = djforms.modelform_factory(SiteSettings, fields='__all__')

    if request.method == 'POST':
        form = Form(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = Form(instance=settings)

    context = {
        'form': form,
        'object': settings,
    }
    return render(request, 'manage_settings.html', context)
