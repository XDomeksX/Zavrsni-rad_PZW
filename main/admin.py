from django.contrib import admin
from .models import Category, Task, Event, Habit, HabitCheckin


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    search_fields = ("name",)
    list_filter = ("owner",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "priority", "due_date", "estimated_time", "category")
    search_fields = ("title", "description")
    list_filter = ("status", "priority", "category", "owner")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "start_datetime", "end_datetime", "location", "category")
    search_fields = ("title", "description", "location")
    list_filter = ("category", "owner")


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "frequency", "target_count", "active")
    search_fields = ("name",)
    list_filter = ("active", "owner")


@admin.register(HabitCheckin)
class HabitCheckinAdmin(admin.ModelAdmin):
    list_display = ("habit", "performed_at", "done")
    list_filter = ("done", "performed_at")
