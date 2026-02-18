from django.urls import path
from polls import views  # type: ignore[import-not-found]

urlpatterns = [
    path("", views.async_list_questions, name="list_questions"),
    path("create/", views.async_create_question, name="create_question"),
    path("get/<str:question_text>/", views.async_get_question, name="get_question"),
    path(
        "<int:question_id>/choice/create/",
        views.async_create_choice,
        name="create_choice",
    ),
]
