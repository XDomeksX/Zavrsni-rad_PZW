from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),

    # Tasks
    path("tasks/", views.TaskListView.as_view(), name="task_list"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("tasks/add/", views.TaskCreateView.as_view(), name="task_add"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),

    #Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category_add"),
    path("categories/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    #Events
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("events/add/", views.EventCreateView.as_view(), name="event_add"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_edit"),
    path("events/<int:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),

    #Habits
    path("habits/", views.HabitListView.as_view(), name="habit_list"),
    path("habits/add/", views.HabitCreateView.as_view(), name="habit_add"),
    path("habits/<int:pk>/", views.HabitDetailView.as_view(), name="habit_detail"),
    path("habits/<int:pk>/edit/", views.HabitUpdateView.as_view(), name="habit_edit"),
    path("habits/<int:pk>/delete/", views.HabitDeleteView.as_view(), name="habit_delete"),

    #HabitCheckIns
    path("habits/<int:habit_pk>/checkins/", views.HabitCheckinListView.as_view(), name="habit_checkin_list"),
    path("habits/<int:habit_pk>/checkins/add/", views.HabitCheckinCreateView.as_view(), name="habit_checkin_add"),
    path("checkins/<int:pk>/delete/", views.HabitCheckinDeleteView.as_view(), name="habit_checkin_delete"),
]
