from django.contrib import admin
from .models import Exam, Subject, Result, MarkEntry


class SubjectInline(admin.TabularInline):
    model  = Subject
    extra  = 3
    fields = ('name', 'full_marks', 'pass_marks', 'is_optional')  # ✅ is_optional যোগ


class MarkEntryInline(admin.TabularInline):
    model  = MarkEntry
    extra  = 0
    fields = ('subject', 'marks_obtained', 'is_absent')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display    = ('name', 'exam_type', 'classroom', 'date', 'created_by')
    list_filter     = ('exam_type', 'classroom', 'date')
    search_fields   = ('name', 'created_by__username')
    inlines         = [SubjectInline]
    readonly_fields = ('created_at',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ('name', 'exam', 'full_marks', 'pass_marks', 'is_optional')  # ✅ is_optional যোগ
    list_filter   = ('exam__classroom', 'is_optional')                            # ✅ filter যোগ
    search_fields = ('name', 'exam__name')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display    = ('student', 'exam', 'serial', 'get_total', 'get_gpa', 'get_grade', 'get_status')
    list_filter     = ('exam__classroom', 'exam')
    search_fields   = ('student__full_name', 'exam__name')
    ordering        = ('exam', 'serial')
    inlines         = [MarkEntryInline]
    readonly_fields = ('serial',)

    @admin.display(description='Total')
    def get_total(self, obj):
        return f"{obj.total_marks()} / {obj.total_full_marks()}"

    @admin.display(description='GPA')
    def get_gpa(self, obj):
        return obj.gpa()

    @admin.display(description='Grade')
    def get_grade(self, obj):
        return obj.letter_grade()

    @admin.display(description='Status')
    def get_status(self, obj):
        return '❌ Fail' if obj.is_failed() else '✅ Pass'


@admin.register(MarkEntry)
class MarkEntryAdmin(admin.ModelAdmin):
    list_display  = ('result', 'subject', 'marks_obtained', 'is_absent', 'get_passed')
    list_filter   = ('subject__exam__classroom', 'subject__exam', 'is_absent')
    search_fields = ('result__student__full_name', 'subject__name')

    @admin.display(description='Pass?', boolean=True)
    def get_passed(self, obj):
        return obj.is_passed()