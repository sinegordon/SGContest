import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from client.forms import (
    AdminSettingsForm,
    BulkImportProblemsForm,
    CourseLookupForm,
    CourseSettingsForm,
    CreateCourseForm,
    CreateUserForm,
    DumpLookupForm,
    ResetUserCourseForm,
    SelectProblemForm,
    SettingsForm,
    SubmitSolutionForm,
)
from client.models import CourseSettings
from client.services import (
    ContestApiClient,
    ContestApiError,
    ContestWebService,
    parse_bulk_problems_json,
    parse_optional_json_object,
)


SESSION_KEYS = (
    "server_url",
    "course",
    "language",
    "user_name",
    "user_data",
    "current_problem_index",
    "ops_server_url",
    "ops_admin_key",
    "ops_service_user",
    "ops_course",
    "ops_results",
)


OPS_RESULT_KEYS = (
    "courses",
    "problems",
    "users",
    "clear_result",
    "course_create_result",
    "course_settings_result",
    "reset_user_course_result",
    "user_create_result",
    "bulk_import_result",
)


def build_service(request):
    server_url = request.session.get("server_url", settings.CONTEST_SERVER_URL)
    course = request.session.get("course", "")
    language = request.session.get("language", "python")
    user_name = request.session.get("user_name", "")
    user_data = request.session.get("user_data", {})

    service = ContestWebService(
        ContestApiClient(server_url),
        course=course,
        problem_counts=get_course_problem_counts(course),
    )
    service.language = language
    service.user = user_name
    service.user_data = user_data
    return service


def build_ops_client(request, data=None):
    if data is None:
        server_url = request.session.get("ops_server_url", settings.CONTEST_SERVER_URL)
    else:
        server_url = data["server_url"]
    return ContestApiClient(server_url)


def save_service_state(request, service, current_problem_index):
    request.session["server_url"] = service.api_client.base_url
    request.session["course"] = service.course
    request.session["language"] = service.language
    request.session["user_name"] = service.user
    request.session["user_data"] = service.user_data
    request.session["current_problem_index"] = current_problem_index


def reset_session_state(request):
    for key in SESSION_KEYS:
        request.session.pop(key, None)


def decode_uploaded_file(uploaded_file):
    raw = uploaded_file.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1251")


def get_course_problem_counts(course):
    if not course:
        return {1: 1, 2: 0, 3: 0}
    settings_obj = CourseSettings.objects.filter(course=course).first()
    if settings_obj is None:
        return {1: 1, 2: 0, 3: 0}
    return settings_obj.problem_counts


def get_course_rating_limits(client, service_user, course):
    if not client or not course:
        return {1: 0, 2: 0, 3: 0}
    try:
        problems = client.get_courses_data(service_user, course)["result"]["problems"]
    except Exception:
        return {1: 0, 2: 0, 3: 0}

    limits = {1: 0, 2: 0, 3: 0}
    for problem in problems:
        rating = int(problem.get("rating", 0))
        if rating in limits:
            limits[rating] += 1
    return limits


def build_course_settings_initial(course):
    selected_problem_counts = get_course_problem_counts(course)
    return {
        "course": course,
        "rating_1_count": selected_problem_counts[1],
        "rating_2_count": selected_problem_counts[2],
        "rating_3_count": selected_problem_counts[3],
    }


def empty_ops_results():
    return {
        "courses": None,
        "problems": None,
        "users": None,
        "clear_result": None,
        "course_create_result": None,
        "course_settings_result": None,
        "reset_user_course_result": None,
        "user_create_result": None,
        "bulk_import_result": None,
    }


def persist_ops_results(request, ops_results):
    request.session["ops_results"] = {key: ops_results.get(key) for key in OPS_RESULT_KEYS}


def pop_ops_results(request):
    return request.session.pop("ops_results", empty_ops_results())


def build_select_problem_form(problem_count, current_problem_index, data=None):
    initial_index = 1 if problem_count <= 0 else max(1, min(current_problem_index + 1, problem_count))
    form_kwargs = {"problem_count": problem_count}
    if data is None:
        form_kwargs["initial"] = {"problem_index": initial_index}
    else:
        form_kwargs["data"] = data
    return SelectProblemForm(**form_kwargs)


def index_view(request):
    service = build_service(request)
    current_problem_index = request.session.get("current_problem_index", 0)
    user_loaded = bool(request.session.get("user_name"))
    settings_form = SettingsForm(
        initial={
            "user_name": request.session.get("user_name", ""),
            "server_url": request.session.get("server_url", settings.CONTEST_SERVER_URL),
            "course": request.session.get("course", ""),
            "language": request.session.get("language", "python"),
        }
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "reset":
            reset_session_state(request)
            messages.success(request, "Сессия сброшена.")
            return redirect("index")

        if action == "load_user":
            settings_form = SettingsForm(request.POST)
            if settings_form.is_valid():
                service = ContestWebService(
                    ContestApiClient(settings_form.cleaned_data["server_url"]),
                    course=settings_form.cleaned_data["course"],
                    problem_counts=get_course_problem_counts(settings_form.cleaned_data["course"]),
                )
                service.language = settings_form.cleaned_data["language"]
                try:
                    service.load_user_data(settings_form.cleaned_data["user_name"])
                except (ValueError, ContestApiError) as err:
                    messages.error(request, str(err))
                else:
                    save_service_state(request, service, 0)
                    messages.success(request, "Пользователь загружен.")
                    return redirect("index")
            else:
                messages.error(request, "Проверьте поля формы загрузки пользователя.")
        elif action == "select_problem":
            form = build_select_problem_form(service.get_problem_count(), current_problem_index, data=request.POST)
            if form.is_valid() and service.get_problem_count() > 0:
                selected_index = max(0, min(form.cleaned_data["problem_index"] - 1, service.get_problem_count() - 1))
                save_service_state(request, service, selected_index)
                return redirect("index")
        elif action == "submit_solution" and service.get_problem_count() > 0:
            form = SubmitSolutionForm(request.POST, request.FILES)
            if form.is_valid():
                service.language = form.cleaned_data["language"]
                try:
                    code = decode_uploaded_file(form.cleaned_data["code_file"])
                    result_text = service.submit_solution(
                        current_problem_index,
                        service.language,
                        code,
                    )
                except ContestApiError as err:
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse({"ok": False, "error": str(err)}, status=400)
                    messages.error(request, str(err))
                else:
                    save_service_state(request, service, current_problem_index)
                    request.session["language"] = form.cleaned_data["language"]
                    current_text = service.get_problem_statement(current_problem_index)
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                        return JsonResponse(
                            {
                                "ok": True,
                                "message": "Решение проверено.",
                                "result_text": result_text,
                                "current_text": current_text,
                            }
                        )
                    messages.success(request, "Решение проверено.")
                    return redirect("index")
            elif request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": "Проверьте форму загрузки решения."}, status=400)

    current_problem = None
    current_text = ""
    problem_count = service.get_problem_count()
    if problem_count > 0:
        current_problem_index = max(0, min(current_problem_index, problem_count - 1))
        current_problem = service.user_data[service.course][current_problem_index]
        current_text = service.get_problem_statement(current_problem_index)

    context = {
        "settings_form": settings_form,
        "select_problem_form": build_select_problem_form(problem_count, current_problem_index),
        "submit_solution_form": SubmitSolutionForm(
            initial={
                "language": request.session.get("language", "python"),
            }
        ),
        "is_loaded": user_loaded or problem_count > 0,
        "has_problems": problem_count > 0,
        "problem_count": problem_count,
        "current_problem_index": current_problem_index + 1,
        "current_problem": current_problem,
        "current_text": current_text,
        "course": request.session.get("course", ""),
        "language": request.session.get("language", "python"),
        "user_name": request.session.get("user_name", ""),
    }
    return render(request, "client/index.html", context)


@staff_member_required
def ops_view(request):
    ops_results = empty_ops_results()

    initial_settings = {
        "server_url": request.session.get("ops_server_url", settings.CONTEST_SERVER_URL),
        "admin_key": request.session.get("ops_admin_key", ""),
        "service_user": request.session.get("ops_service_user", "admin"),
    }
    selected_ops_course = request.session.get("ops_course", "")
    ops_client = build_ops_client(request)
    service_user = request.session.get("ops_service_user", "admin")
    settings_form = AdminSettingsForm(initial=initial_settings)
    course_form = CourseLookupForm(initial={"course": selected_ops_course})
    create_course_form = CreateCourseForm(initial={"course": selected_ops_course})
    selected_rating_limits = get_course_rating_limits(ops_client, service_user, selected_ops_course)
    course_settings_initial = build_course_settings_initial(selected_ops_course)
    course_settings_form = CourseSettingsForm(initial=course_settings_initial, rating_limits=selected_rating_limits)
    reset_user_course_form = ResetUserCourseForm(initial={"course": selected_ops_course})
    create_user_form = CreateUserForm()
    dump_form = DumpLookupForm()
    bulk_import_form = BulkImportProblemsForm(initial={"course": selected_ops_course})

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_ops_settings":
            settings_form = AdminSettingsForm(request.POST)
            if settings_form.is_valid():
                request.session["ops_server_url"] = settings_form.cleaned_data["server_url"]
                request.session["ops_admin_key"] = settings_form.cleaned_data["admin_key"]
                request.session["ops_service_user"] = settings_form.cleaned_data["service_user"]
                messages.success(request, "Административные настройки сохранены.")
                return redirect("ops")
        else:
            settings_form = AdminSettingsForm(initial=initial_settings)
            client = build_ops_client(request)
            service_user = request.session.get("ops_service_user", "admin")
            admin_key = request.session.get("ops_admin_key", "")

            try:
                if action == "list_courses":
                    ops_results["courses"] = client.get_courses_catalog(service_user)["result"]["courses"]
                elif action == "list_users":
                    ops_results["users"] = client.get_user_info("*")["result"]
                elif action == "show_problems":
                    course_form = CourseLookupForm(request.POST)
                    if course_form.is_valid():
                        course = course_form.cleaned_data["course"]
                        request.session["ops_course"] = course
                        ops_results["problems"] = client.get_courses_data(service_user, course)["result"]["problems"]
                elif action == "clear_course":
                    course_form = CourseLookupForm(request.POST)
                    if course_form.is_valid():
                        course = course_form.cleaned_data["course"]
                        request.session["ops_course"] = course
                        ops_results["clear_result"] = client.clear_course(service_user, course)["result"]
                        messages.success(request, f"Курс '{course}' очищен.")
                elif action == "create_course":
                    create_course_form = CreateCourseForm(request.POST)
                    if create_course_form.is_valid():
                        course = create_course_form.cleaned_data["course"]
                        request.session["ops_course"] = course
                        ops_results["course_create_result"] = client.create_course(course)["result"]
                        messages.success(request, f"Курс '{course}' создан.")
                elif action == "load_course_settings":
                    course_form = CourseLookupForm(request.POST)
                    if course_form.is_valid():
                        selected_ops_course = course_form.cleaned_data["course"]
                        request.session["ops_course"] = selected_ops_course
                        selected_rating_limits = get_course_rating_limits(client, service_user, selected_ops_course)
                        course_settings_form = CourseSettingsForm(
                            initial=build_course_settings_initial(selected_ops_course),
                            rating_limits=selected_rating_limits,
                        )
                        reset_user_course_form = ResetUserCourseForm(initial={"course": selected_ops_course})
                        bulk_import_form = BulkImportProblemsForm(initial={"course": selected_ops_course})
                        create_course_form = CreateCourseForm(initial={"course": selected_ops_course})
                        messages.success(
                            request,
                            f"Данные курса '{selected_ops_course}' загружены. "
                            "Лимиты по уровням обновлены по текущему составу задач.",
                        )
                elif action == "save_course_settings":
                    posted_course = request.POST.get("course", "")
                    request.session["ops_course"] = posted_course
                    course_settings_form = CourseSettingsForm(
                        request.POST,
                        rating_limits=get_course_rating_limits(client, service_user, posted_course),
                    )
                    if course_settings_form.is_valid():
                        course = course_settings_form.cleaned_data["course"]
                        request.session["ops_course"] = course
                        settings_obj, _ = CourseSettings.objects.update_or_create(
                            course=course,
                            defaults={
                                "rating_1_count": course_settings_form.cleaned_data["rating_1_count"],
                                "rating_2_count": course_settings_form.cleaned_data["rating_2_count"],
                                "rating_3_count": course_settings_form.cleaned_data["rating_3_count"],
                            },
                        )
                        ops_results["course_settings_result"] = {
                            "course": settings_obj.course,
                            "problem_counts": settings_obj.problem_counts,
                        }
                        messages.success(request, f"Настройки набора задач для курса '{course}' сохранены.")
                elif action == "create_user":
                    create_user_form = CreateUserForm(request.POST)
                    if create_user_form.is_valid():
                        user_name = create_user_form.cleaned_data["user_name"]
                        user_data = parse_optional_json_object(
                            create_user_form.cleaned_data["user_data_json"],
                            "user_data_json",
                        )
                        ops_results["user_create_result"] = client.create_or_update_user(user_name, user_data)["result"]
                        messages.success(request, f"Пользователь '{user_name}' сохранён.")
                elif action == "reset_user_course":
                    reset_user_course_form = ResetUserCourseForm(request.POST)
                    if reset_user_course_form.is_valid():
                        user_name = reset_user_course_form.cleaned_data["user_name"]
                        course = reset_user_course_form.cleaned_data["course"]
                        request.session["ops_course"] = course
                        user_info = client.get_user_info(user_name)["result"]
                        user_data = dict(user_info.get("data", {}))
                        removed = course in user_data
                        if removed:
                            user_data.pop(course, None)
                            client.create_or_update_user(user_name, user_data)
                        ops_results["reset_user_course_result"] = {
                            "user_name": user_name,
                            "course": course,
                            "removed": removed,
                        }
                        if removed:
                            messages.success(
                                request,
                                f"Набор задач курса '{course}' удалён у студента '{user_name}'.",
                            )
                        else:
                            messages.success(
                                request,
                                f"У студента '{user_name}' не было назначенного набора задач по курсу '{course}'.",
                            )
                elif action == "get_dump":
                    dump_form = DumpLookupForm(request.POST)
                    if dump_form.is_valid():
                        dump = client.get_base_dump(
                            dump_form.cleaned_data["date"],
                            dump_form.cleaned_data["processor_name"],
                            admin_key,
                        )["result"]
                        filename = (
                            f"contest_dump_{dump_form.cleaned_data['processor_name']}_"
                            f"{dump_form.cleaned_data['date']}.json"
                        )
                        response = HttpResponse(
                            json.dumps(dump, ensure_ascii=False, indent=2),
                            content_type="application/json; charset=utf-8",
                        )
                        response["Content-Disposition"] = f'attachment; filename="{filename}"'
                        return response
                elif action == "bulk_import":
                    bulk_import_form = BulkImportProblemsForm(request.POST, request.FILES)
                    if bulk_import_form.is_valid():
                        course = bulk_import_form.cleaned_data["course"]
                        request.session["ops_course"] = course
                        raw_json = decode_uploaded_file(bulk_import_form.cleaned_data["problems_file"])
                        problems = parse_bulk_problems_json(raw_json)
                        imported = []
                        for problem in problems:
                            problem_type = problem.get("type", bulk_import_form.cleaned_data["default_type"])
                            rating = problem.get("rating", bulk_import_form.cleaned_data["default_rating"])
                            task = problem.get("task", "")
                            for variant, tests in problem.get("variants", {}).items():
                                result = client.add_or_update_problem(
                                    service_user,
                                    course,
                                    problem["problem"],
                                    variant,
                                    problem_type,
                                    rating,
                                    task,
                                    tests,
                                )["result"]
                                imported.append(
                                    {
                                        "problem": problem["problem"],
                                        "variant": variant,
                                        "result": result,
                                    }
                                )
                        ops_results["bulk_import_result"] = imported
                        ops_results["problems"] = client.get_courses_data(service_user, course)["result"]["problems"]
                        messages.success(request, f"Импортировано вариантов: {len(imported)} в курс '{course}'.")
            except ContestApiError as err:
                messages.error(request, str(err))
            else:
                if any(value is not None for value in ops_results.values()):
                    persist_ops_results(request, ops_results)
                    return redirect("ops_results")

    context = {
        "settings_form": settings_form,
        "course_form": course_form,
        "create_course_form": create_course_form,
        "course_settings_form": course_settings_form,
        "course_rating_limits": selected_rating_limits,
        "reset_user_course_form": reset_user_course_form,
        "create_user_form": create_user_form,
        "dump_form": dump_form,
        "bulk_import_form": bulk_import_form,
    }
    return render(request, "client/ops.html", context)


@staff_member_required
def ops_results_view(request):
    return render(
        request,
        "client/ops_results.html",
        {
            "ops_results": pop_ops_results(request),
            "ops_course": request.session.get("ops_course", ""),
            "ops_server_url": request.session.get("ops_server_url", settings.CONTEST_SERVER_URL),
            "ops_service_user": request.session.get("ops_service_user", "admin"),
        },
    )
