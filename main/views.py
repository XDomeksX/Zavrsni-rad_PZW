from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.db.models import Q

from .forms import TaskForm, EventForm, HabitForm, HabitCheckinForm
from .models import Task, Category, Event, Habit, HabitCheckin


def register(request):
    if request.user.is_authenticated:
        return redirect("main:home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after registration
            return redirect("main:home")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class HomeView(TemplateView):
    template_name = "main/home.html"


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "main/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        qs = Task.objects.filter(owner=self.request.user).order_by("-created_at")

        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["status"] = self.request.GET.get("status", "")
        context["status_choices"] = Task.Status.choices
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "main/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        # Sigurnost: user ne može otvoriti tuđi task preko URL-a
        return Task.objects.filter(owner=self.request.user)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "main/task_form.html"
    success_url = reverse_lazy("main:task_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user

        # Backend safety fallback: if user submits without a category
        if form.instance.category is None:
            inbox, _ = Category.objects.get_or_create(
                owner=self.request.user,
                is_inbox=True,
                defaults={"name": "Inbox"},
            )
            form.instance.category = inbox

        return super().form_valid(form)

    
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "main/task_form.html"
    success_url = reverse_lazy("main:task_list")

    def get_queryset(self):
        # user can edit only their own tasks
        return Task.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "main/task_confirm_delete.html"
    success_url = reverse_lazy("main:task_list")

    def get_queryset(self):
        # user može brisati samo svoje taskove
        return Task.objects.filter(owner=self.request.user)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "main/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user).order_by("name")


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = "main/category_form.html"
    success_url = reverse_lazy("main:category_list")
    fields = ["name"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = "main/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    template_name = "main/category_form.html"
    fields = ["name"]
    success_url = reverse_lazy("main:category_list")

    def get_queryset(self):
        # Inbox cannot be edited
        return Category.objects.filter(owner=self.request.user, is_inbox=False)


class CategoryDeleteView(LoginRequiredMixin, View):
    template_name = "main/category_delete_options.html"

    def get_category(self, request, pk):
        return get_object_or_404(Category, pk=pk, owner=request.user)

    def get_inbox(self, request):
        inbox, _ = Category.objects.get_or_create(
            owner=request.user,
            is_inbox=True,
            defaults={"name": "Inbox"},
        )
        return inbox

    def get(self, request, pk):
        category = self.get_category(request, pk)

        # Inbox se ne smije brisati
        if category.is_inbox:
            return redirect("main:category_detail", pk=category.pk)

        other_categories = Category.objects.filter(owner=request.user).exclude(pk=category.pk)
        inbox = self.get_inbox(request)

        return render(request, self.template_name, {
            "category": category,
            "other_categories": other_categories,
            "inbox": inbox,
        })

    def post(self, request, pk):
        category = self.get_category(request, pk)

        if category.is_inbox:
            return redirect("main:category_detail", pk=category.pk)

        action = request.POST.get("action")  # delete_all | move | inbox
        target_id = request.POST.get("target_category")

        inbox = self.get_inbox(request)

        tasks_qs = Task.objects.filter(owner=request.user, category=category)
        events_qs = Event.objects.filter(owner=request.user, category=category)

        if action == "delete_all":
            tasks_qs.delete()
            events_qs.delete()

        elif action == "move":
            target = get_object_or_404(Category, pk=target_id, owner=request.user)
            tasks_qs.update(category=target)
            events_qs.update(category=target)

        else:
            # default = move to Inbox
            tasks_qs.update(category=inbox)
            events_qs.update(category=inbox)

        category.delete()
        return redirect("main:category_list")

class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "main/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        qs = Event.objects.filter(owner=self.request.user).order_by("start_datetime")

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "main/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "main/event_form.html"
    success_url = reverse_lazy("main:event_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user

        # backend fallback -> Inbox
        if form.instance.category is None:
            inbox, _ = Category.objects.get_or_create(
                owner=self.request.user,
                is_inbox=True,
                defaults={"name": "Inbox"},
            )
            form.instance.category = inbox

        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "main/event_form.html"
    success_url = reverse_lazy("main:event_list")

    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = "main/event_confirm_delete.html"
    success_url = reverse_lazy("main:event_list")

    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)


class HabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "main/habit_list.html"
    context_object_name = "habits"

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user).order_by("name")


class HabitDetailView(LoginRequiredMixin, DetailView):
    model = Habit
    template_name = "main/habit_detail.html"
    context_object_name = "habit"

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)


class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    form_class = HabitForm
    template_name = "main/habit_form.html"
    success_url = reverse_lazy("main:habit_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class HabitUpdateView(LoginRequiredMixin, UpdateView):
    model = Habit
    form_class = HabitForm
    template_name = "main/habit_form.html"
    success_url = reverse_lazy("main:habit_list")

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class HabitDeleteView(LoginRequiredMixin, DeleteView):
    model = Habit
    template_name = "main/habit_confirm_delete.html"
    success_url = reverse_lazy("main:habit_list")

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)


class HabitCheckinListView(LoginRequiredMixin, ListView):
    model = HabitCheckin
    template_name = "main/habit_checkin_list.html"
    context_object_name = "checkins"

    def get_habit(self):
        return get_object_or_404(Habit, pk=self.kwargs["habit_pk"], owner=self.request.user)

    def get_queryset(self):
        habit = self.get_habit()
        return HabitCheckin.objects.filter(habit=habit).order_by("-performed_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["habit"] = self.get_habit()
        return context


class HabitCheckinCreateView(LoginRequiredMixin, CreateView):
    model = HabitCheckin
    form_class = HabitCheckinForm
    template_name = "main/habit_checkin_form.html"

    def get_habit(self):
        return get_object_or_404(Habit, pk=self.kwargs["habit_pk"], owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["habit"] = self.get_habit()
        return kwargs

    def get_success_url(self):
        return reverse_lazy("main:habit_checkin_list", kwargs={"habit_pk": self.kwargs["habit_pk"]})

    def form_valid(self, form):
        form.instance.habit = self.get_habit()
        return super().form_valid(form)


class HabitCheckinDeleteView(LoginRequiredMixin, DeleteView):
    model = HabitCheckin
    template_name = "main/habit_checkin_confirm_delete.html"

    def get_queryset(self):
        # delete only checkins of user's habits
        return HabitCheckin.objects.filter(habit__owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy("main:habit_checkin_list", kwargs={"habit_pk": self.object.habit.pk})
