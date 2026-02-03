from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from main.models import Category, Task, Event, Habit, HabitCheckin
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Generate test data for Planner app"

    def handle(self, *args, **options):
        self.stdout.write("Generating test data...")

        # --- USERS ---
        user1, _ = User.objects.get_or_create(
            username="testuser1",
            defaults={"email": "test1@example.com"},
        )
        user1.set_password("test1234")
        user1.save()

        user2, _ = User.objects.get_or_create(
            username="testuser2",
            defaults={"email": "test2@example.com"},
        )
        user2.set_password("test1234")
        user2.save()

        users = [user1, user2]

        for user in users:
            # --- CATEGORIES ---
            inbox, _ = Category.objects.get_or_create(
                owner=user,
                is_inbox=True,
                defaults={"name": "Inbox"},
            )

            work, _ = Category.objects.get_or_create(
                owner=user, name="Work"
            )
            personal, _ = Category.objects.get_or_create(
                owner=user, name="Personal"
            )

            categories = [inbox, work, personal]

            # --- TASKS ---
            for i in range(3):
                Task.objects.create(
                    owner=user,
                    category=random.choice(categories),
                    title=f"Task {i + 1} ({user.username})",
                    description="Auto-generated task",
                    priority=random.choice([1, 2, 3]),
                    status=random.choice(["todo", "in_progress", "done"]),
                    due_date=timezone.now().date() + timedelta(days=i),
                    estimated_time=random.choice([15, 30, 60]),
                )

            # --- EVENTS ---
            for i in range(2):
                start = timezone.now() + timedelta(days=i)
                Event.objects.create(
                    owner=user,
                    category=random.choice(categories),
                    title=f"Event {i + 1} ({user.username})",
                    description="Auto-generated event",
                    location="Online",
                    start_datetime=start,
                    end_datetime=start + timedelta(hours=2),
                )

            # --- HABITS ---
            habit1 = Habit.objects.create(
                owner=user,
                name="Training",
                frequency="weekly",
                target_count=3,
                preferred_weekdays="mon,wed,sat",
                active=True,
                reminder_enabled=True,
                reminder_start=timezone.now(),
                reminder_repeat="weekly",
                reminder_until=timezone.now().date() + timedelta(days=30),
            )

            habit2 = Habit.objects.create(
                owner=user,
                name="Read books",
                frequency="daily",
                target_count=1,
                preferred_times="08:00 PM",
                active=True,
            )

            # --- HABIT CHECK-INS ---
            for i in range(3):
                HabitCheckin.objects.create(
                    habit=habit1,
                    performed_at=timezone.now() - timedelta(days=i),
                    done=True,
                )

        self.stdout.write(self.style.SUCCESS("Test data generated successfully!"))
