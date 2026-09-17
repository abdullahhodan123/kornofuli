from django.contrib import admin
from .models import (
  
    SiteSettings,
    Course,
    Teacher,
    Result,
    Notice,
    GalleryImage,
    FAQ,
    BatchSchedule,
)





@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("academy_name", "phone_primary", "email")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "level", "fee_per_month")
    list_filter = ("subject", "level")
    search_fields = ("name",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "qualification", "experience_years")
    list_filter = ("subject",)
    search_fields = ("name",)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("year", "label")
    list_filter = ("year",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "notice_type", "classroom", "is_pinned", "published_at")
    list_filter = ("notice_type", "is_pinned", "classroom")
    search_fields = ("title",)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_at")
    list_filter = ("uploaded_at",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order")
    list_filter = ("order",)


@admin.register(BatchSchedule)
class BatchScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "batch_name",
        "course",
        "teacher",
        "time_slot",
        "seats_total",
        "seats_enrolled",
    )
    