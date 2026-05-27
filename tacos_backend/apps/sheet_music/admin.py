from django.contrib import admin

from .models import Sheet, SheetDownloadLog


@admin.register(Sheet)
class SheetAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "composer",
        "arranger",
        "visible_to_all",
        "visible_to_alumni",
        "is_restricted",
        "upload_time",
        "public_id",
    )
    search_fields = (
        "title",
        "composer",
        "arranger",
        "lyricist",
        "public_id",
    )
    list_filter = (
        "visible_to_all",
        "visible_to_alumni",
        "is_restricted",
    )
    readonly_fields = (
        "public_id",
        "upload_time",
        "updated_at",
    )
    filter_horizontal = (
        "visible_events",
        "visible_members",
    )


@admin.register(SheetDownloadLog)
class SheetDownloadLogAdmin(admin.ModelAdmin):
    list_display = (
        "sheet",
        "user",
        "downloaded_at",
        "ip_address",
    )
    search_fields = (
        "sheet__title",
        "user__user_id",
        "user__username",
        "ip_address",
    )
    date_hierarchy = "downloaded_at"
