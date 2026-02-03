from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Event, Habit, HabitCheckin

User = get_user_model()


class PlannerTests(TestCase):
    def setUp(self):
        # create user
        self.user = User.objects.create_user(username="u1", password="pass12345")

        # create Inbox category for user
        self.inbox, _ = Category.objects.get_or_create(
            owner=self.user,
            is_inbox=True,
            defaults={"name": "Inbox"},
        )

        # create habit
        self.habit = Habit.objects.create(
            owner=self.user,
            name="Training",
            frequency="daily",
            target_count=1,
            active=True,
        )

    def test_login_required_for_task_list(self):
        """
        Unauthenticated user should be redirected to login page.
        """
        url = reverse("main:task_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_event_end_must_be_after_start(self):
        """
        EventForm validation: end_datetime must be after start_datetime.
        """
        self.client.login(username="u1", password="pass12345")

        start = timezone.now()
        end = start - timedelta(hours=1)

        url = reverse("main:event_add")
        response = self.client.post(
            url,
            data={
                "category": self.inbox.pk,
                "title": "Bad event",
                "description": "",
                "location": "",
                "start_datetime": start.strftime("%Y-%m-%dT%H:%M"),
                "end_datetime": end.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        # Form should be invalid -> page re-rendered (200) with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "End time must be after start time.")

    def test_habitcheckin_duplicate_minute_blocked(self):
        """
        HabitCheckinForm should prevent duplicates at same minute for same habit.
        """
        self.client.login(username="u1", password="pass12345")

        performed_at = timezone.now().replace(second=0, microsecond=0)

        # First checkin - OK
        HabitCheckin.objects.create(habit=self.habit, performed_at=performed_at, done=True)

        # Try to create another checkin at the same minute through the view
        url = reverse("main:habit_checkin_add", args=[self.habit.pk])
        response = self.client.post(
            url,
            data={
                "performed_at": performed_at.strftime("%Y-%m-%dT%H:%M"),
                "done": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "A check-in for this habit at the same minute already exists",
        )
