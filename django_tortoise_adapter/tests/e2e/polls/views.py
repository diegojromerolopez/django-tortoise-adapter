import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# pylint: disable=unused-argument
# pylint: disable=wrong-import-order
from .models import Choice, Question


@csrf_exempt
async def async_create_question(request: HttpRequest) -> JsonResponse:
    question_text = "What's up?"
    if request.method == "POST" and request.body:
        try:
            body = json.loads(request.body)
            question_text = body.get("question_text", question_text)
        except json.JSONDecodeError:
            pass
    q = await Question.objects.create(question_text=question_text)
    return JsonResponse({"id": q.pk, "question_text": q.question_text})


@csrf_exempt
async def async_get_question(request: HttpRequest, question_text: str) -> JsonResponse:
    q = await Question.objects.get(question_text=question_text)
    return JsonResponse({"question_text": q.question_text})


@csrf_exempt
async def async_list_questions(request: HttpRequest) -> JsonResponse:
    questions = []
    async for q in Question.objects.all():
        questions.append(q.question_text)
    return JsonResponse({"questions": questions})


@csrf_exempt
async def async_create_choice(request: HttpRequest, question_id: int) -> JsonResponse:
    # We need to fetch the question first? Or pass ID?
    # Tortoise supports setting ID directly usually...
    # ...but Django foreign keys expect instance or ID?
    # Let's try fetching first to be safe and broadly compatible
    q = await Question.objects.get(pk=question_id)
    c = await Choice.objects.create(question=q, choice_text="Not much", votes=0)
    return JsonResponse({"id": c.pk, "choice_text": c.choice_text})
