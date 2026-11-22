from django.contrib import admin
from .models import Category, Report, ReportHistory, AdminReply

class ReportHistoryInline(admin.TabularInline):
    model = ReportHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'comment', 'changed_by', 'created_at')
    can_delete = False

class AdminReplyInline(admin.StackedInline):
    model = AdminReply
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'order', 'report_count')
    list_editable = ('order',)
    search_fields = ('name',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'title', 'category', 'region', 'district', 'status', 'created_at')
    list_filter = ('status', 'category', 'region', 'created_at')
    search_fields = ('tracking_code', 'title', 'description', 'address', 'applicant_name', 'applicant_phone')
    readonly_fields = ('tracking_code', 'created_at', 'updated_at')
    inlines = [ReportHistoryInline, AdminReplyInline]

@admin.register(ReportHistory)
class ReportHistoryAdmin(admin.ModelAdmin):
    list_display = ('report', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at')
    search_fields = ('report__tracking_code', 'comment')

@admin.register(AdminReply)
class AdminReplyAdmin(admin.ModelAdmin):
    list_display = ('report', 'author', 'created_at')
    search_fields = ('report__tracking_code', 'message')
