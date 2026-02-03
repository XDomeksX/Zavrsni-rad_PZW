from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    is_inbox = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        unique_together = [("owner", "name")]  # isti user ne može imati 2 iste kategorije
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name



class Task(models.Model):
    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(choices=Status.choices, default=Status.TODO, max_length=20)

    due_date = models.DateField(null=True, blank=True)

    # traženo: estimated_time (opcionalno)
    # u minutama (najjednostavnije za upis i računanje)
    estimated_time = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self) -> str:
        return self.title



class Event(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["start_datetime"]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self) -> str:
        return self.title



class Habit(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )

    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    class Frequency(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    frequency = models.CharField(
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.DAILY,
    )

    # e.g. 3 times per week, 1 time per day, etc.
    target_count = models.PositiveIntegerField(default=1)

    # Optional planning fields (simple text inputs; can be left empty)
    # Examples:
    # preferred_times: "8,20"  (meaning 08:00 and 20:00)
    # preferred_weekdays: "mon,wed,fri"
    # preferred_months: "1,6,12"
    preferred_times = models.CharField(max_length=200, blank=True)
    preferred_weekdays = models.CharField(max_length=200, blank=True)
    preferred_months = models.CharField(max_length=200, blank=True)

    # Reminder settings (we store preferences, but we won't implement notifications)
    reminder_enabled = models.BooleanField(default=False)
    reminder_start = models.DateTimeField(null=True, blank=True)
    class ReminderRepeat(models.TextChoices):
        NONE = "none", "No repeat"
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    reminder_repeat = models.CharField(
        max_length=10,
        choices=ReminderRepeat.choices,
        default=ReminderRepeat.NONE,
    )
    reminder_until = models.DateField(null=True, blank=True)  # blank = infinite

    class Meta:
        ordering = ["name"]
        unique_together = [("owner", "name")]
        verbose_name = "Habit"
        verbose_name_plural = "Habits"

    def __str__(self) -> str:
        return self.name



class HabitCheckin(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="checkins",
    )
    performed_at = models.DateTimeField(default=timezone.now)
    done = models.BooleanField(default=True)

    class Meta:
        ordering = ["-performed_at"]
        constraints = [
            models.UniqueConstraint(fields=["habit", "performed_at"], name="uniq_habit_performed_at")
        ]

    def __str__(self) -> str:
        status = "done" if self.done else "not done"
        return f"{self.habit.name} - {self.performed_at} ({status})"
    
    def save(self, *args, **kwargs):
        if self.performed_at is not None:
            self.performed_at = self.performed_at.replace(second=0, microsecond=0)
        super().save(*args, **kwargs)
