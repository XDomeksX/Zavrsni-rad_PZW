from django import forms
from .models import Task, Category, Event, Habit, HabitCheckin


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["category", "title", "description", "priority", "status", "due_date", "estimated_time"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "estimated_time": forms.NumberInput(attrs={"placeholder": "e.g. 30 (min)"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(owner=user).order_by("name")

            # default Inbox on create
            if self.instance.pk is None:
                inbox, _ = Category.objects.get_or_create(
                    owner=user,
                    is_inbox=True,
                    defaults={"name": "Inbox"},
                )
                self.fields["category"].initial = inbox.pk


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["category", "title", "description", "location", "start_datetime", "end_datetime"]
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(owner=user).order_by("name")

            # default Inbox on create
            if self.instance.pk is None:
                inbox, _ = Category.objects.get_or_create(
                    owner=user,
                    is_inbox=True,
                    defaults={"name": "Inbox"},
                )
                self.fields["category"].initial = inbox.pk

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        # end is optional, but if provided it must be after start
        if start and end and end <= start:
            self.add_error("end_datetime", "End time must be after start time.")

        return cleaned_data


class HabitForm(forms.ModelForm):
    WEEKDAYS = [
        ("mon", "Mon"),
        ("tue", "Tue"),
        ("wed", "Wed"),
        ("thu", "Thu"),
        ("fri", "Fri"),
        ("sat", "Sat"),
        ("sun", "Sun"),
    ]

    MONTHS = [
        ("1", "Jan"),
        ("2", "Feb"),
        ("3", "Mar"),
        ("4", "Apr"),
        ("5", "May"),
        ("6", "Jun"),
        ("7", "Jul"),
        ("8", "Aug"),
        ("9", "Sep"),
        ("10", "Oct"),
        ("11", "Nov"),
        ("12", "Dec"),
    ]

    # UI fields (not model fields): checkbox multi-select
    preferred_weekdays_list = forms.MultipleChoiceField(
        choices=WEEKDAYS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Preferred weekdays",
    )

    preferred_months_list = forms.MultipleChoiceField(
        choices=MONTHS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Preferred months",
    )
    
    class Meta:
        model = Habit
        fields = [
            "name",
            "active",
            "frequency",
            "target_count",
            "preferred_times",
            "reminder_enabled",
            "reminder_start",
            "reminder_repeat",
            "reminder_until",
        ]
        widgets = {
            "reminder_start": forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
            "reminder_until": forms.DateInput(attrs={"type": "date"}),
            "preferred_times": forms.TextInput(attrs={"placeholder": "e.g. 08:00,20:00"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Populate checkbox fields from stored CSV strings
        if self.instance and self.instance.pk:
            if self.instance.preferred_weekdays:
                self.initial["preferred_weekdays_list"] = self.instance.preferred_weekdays.split(",")
            if self.instance.preferred_months:
                self.initial["preferred_months_list"] = self.instance.preferred_months.split(",")

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")

        qs = Habit.objects.all()
        if self.user is not None:
            qs = qs.filter(owner=self.user)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(name__iexact=name).exists():
            raise forms.ValidationError("You already have a habit with this name.")

        return name

    def clean_preferred_times(self):
        times = (self.cleaned_data.get("preferred_times") or "").strip()
        if not times:
            return ""

        parts = [p.strip() for p in times.split(",") if p.strip()]
        # Validate format HH:MM
        for p in parts:
            try:
                hh, mm = p.split(":")
                hh_i = int(hh)
                mm_i = int(mm)
                if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
                    raise ValueError()
            except Exception:
                raise forms.ValidationError("Preferred times must be comma-separated in HH:MM format (e.g. 08:00,20:00).")

        # Remove duplicates and normalize
        parts = sorted(set(parts))
        return ",".join(parts)

    def clean(self):
        cleaned = super().clean()

        freq = cleaned.get("frequency")
        reminder_enabled = cleaned.get("reminder_enabled")
        reminder_start = cleaned.get("reminder_start")
        reminder_repeat = cleaned.get("reminder_repeat")
        reminder_until = cleaned.get("reminder_until")

        # Save checkbox selections into model CSV fields
        cleaned["preferred_weekdays"] = ",".join(cleaned.get("preferred_weekdays_list") or [])
        cleaned["preferred_months"] = ",".join(cleaned.get("preferred_months_list") or [])

        # Reminder validation
        if reminder_enabled and not reminder_start:
            self.add_error("reminder_start", "Reminder start is required when reminders are enabled.")

        if reminder_enabled and reminder_repeat == "none":
            # ok - no repeat
            pass

        if not reminder_enabled and reminder_repeat and reminder_repeat != "none":
            self.add_error("reminder_repeat", "Enable reminders before choosing a repeat option.")

        if reminder_start and reminder_until and reminder_until < reminder_start.date():
            self.add_error("reminder_until", "Reminder 'until' date cannot be before reminder start date.")

        # Frequency-based logic (keep it minimal; UI will handle hiding)
        if freq == Habit.Frequency.HOURLY:
            # weekdays/months don't make sense, but we allow them empty; could warn:
            pass

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Copy UI checkbox fields into actual model fields
        instance.preferred_weekdays = ",".join(self.cleaned_data.get("preferred_weekdays_list") or [])
        instance.preferred_months = ",".join(self.cleaned_data.get("preferred_months_list") or [])
        if commit:
            instance.save()
        return instance


class HabitCheckinForm(forms.ModelForm):
    class Meta:
        model = HabitCheckin
        fields = ["performed_at", "done"]
        widgets = {
            "performed_at": forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}),
        }

    def __init__(self, *args, habit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.habit = habit

    def clean_performed_at(self):
        performed_at = self.cleaned_data.get("performed_at")

        if performed_at is not None:
            performed_at = performed_at.replace(second=0, microsecond=0)

        if self.habit is not None and performed_at is not None:
            qs = HabitCheckin.objects.filter(habit=self.habit, performed_at=performed_at)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "A check-in for this habit at the same minute already exists. Choose a different time."
                )

        return performed_at
