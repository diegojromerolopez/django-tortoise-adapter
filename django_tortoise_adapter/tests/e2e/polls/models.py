from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from django_tortoise_adapter.core import TortoiseManager


class Question(models.Model):
    question_text: models.CharField = models.CharField(max_length=200)
    pub_date: models.DateTimeField = models.DateTimeField(
        "date published", default=timezone.now
    )
    if TYPE_CHECKING:
        objects: TortoiseManager  # type: ignore[misc]
    else:
        objects = models.Manager()  # type: ignore[assignment]

    def __str__(self) -> str:
        return str(self.question_text)


class Choice(models.Model):
    question: models.ForeignKey = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text: models.CharField = models.CharField(max_length=200)
    votes: models.IntegerField = models.IntegerField(default=0)
    if TYPE_CHECKING:
        objects: TortoiseManager  # type: ignore[misc]
    else:
        objects = models.Manager()  # type: ignore[assignment]

    def __str__(self) -> str:
        return str(self.choice_text)
