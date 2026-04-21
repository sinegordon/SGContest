from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render

from client.forms import (
    AdminSettingsForm,
    BulkImportProblemsForm,
    CourseLookupForm,
    DeleteProblemForm,
    DumpLookupForm,
    ProblemCrudForm,
    SelectProblemForm,
    SettingsForm,
    SubmitSolutionForm,
)
from client.services import (
    ContestApiClient,
    ContestApiError,
    ContestWebService,
    parse_bulk_problems_json,
    parse_problem_tests,
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
)


def build_service(request):
    server_url = request.session.get("server_url", "http://62.76.72.55:57888")
    course = request.session.get("course", "kate_test")
    language = request.session.get("language", "python")
    user_name = request.session.get("user_name", "")
    user_data = request.session.get("user_data", {})

    service = ContestWebService(ContestApiClient(server_url), course=course)
    service.language = language
    service.user = user_name
    service.user_data = user_data
    return service


def build_ops_client(request, data=None):
    if data is None:
        server_url = request.session.get("ops_server_url", "http://62.76.72.55:57888")
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


def index_view(request):
    service = build_service(request)
    current_problem_index = request.session.get("current_problem_index", 0)

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
        elif action == "select_problem":
            form = SelectProblemForm(request.POST)
            if form.is_valid() and service.get_problem_count() > 0:
                selected_index = max(0, min(form.cleaned_data["problem_index"] - 1, service.get_problem_count() - 1))
                save_service_state(request, service, selected_index)
                return redirect("index")
        elif action == "submit_solution" and service.get_problem_count() > 0:
            form = SubmitSolutionForm(request.POST, request.FILES)
            if form.is_valid():
                service.language = request.session.get("language", "python")
                try:
                    code = decode_uploaded_file(form.cleaned_data["code_file"])
                    service.submit_solution(current_problem_index, form.cleaned_data["variant"], service.language, code)
                except ContestApiError as err:
                    messages.error(request, str(err))
                else:
                    save_service_state(request, service, current_problem_index)
                    messages.success(request, "Решение проверено.")
                    return redirect("index")

    current_problem = None
    current_text = ""
    problem_count = service.get_problem_count()
    if problem_count > 0:
        current_problem_index = max(0, min(current_problem_index, problem_count - 1))
        current_problem = service.user_data[service.course][current_problem_index]
        current_text = service.get_problem_statement(current_problem_index)
        variant_count = service.get_problem_variant_count(current_problem_index)
    else:
        variant_count = 1

    context = {
        "settings_form": SettingsForm(
            initial={
                "user_name": request.session.get("user_name", ""),
                "server_url": request.session.get("server_url", "http://62.76.72.55:57888"),
                "course": request.session.get("course", "kate_test"),
                "language": request.session.get("language", "python"),
            }
        ),
        "select_problem_form": SelectProblemForm(initial={"problem_index": current_problem_index + 1}),
        "submit_solution_form": SubmitSolutionForm(initial={"variant": 1}),
        "is_loaded": problem_count > 0,
        "problem_count": problem_count,
        "variant_range": range(1, variant_count + 1),
        "current_problem_index": current_problem_index + 1,
        "current_problem": current_problem,
        "current_text": current_text,
        "course": request.session.get("course", "kate_test"),
        "language": request.session.get("language", "python"),
    }
    return render(request, "client/index.html", context)


@staff_member_required
def ops_view(request):
    ops_results = {
        "courses": None,
        "problems": None,
        "users": None,
        "dump": None,
        "clear_result": None,
        "problem_save_result": None,
        "problem_delete_result": None,
        "bulk_import_result": None,
    }

    initial_settings = {
        "server_url": request.session.get("ops_server_url", "http://62.76.72.55:57888"),
        "admin_key": request.session.get("ops_admin_key", ""),
        "service_user": request.session.get("ops_service_user", "admin"),
    }
    settings_form = AdminSettingsForm(initial=initial_settings)
    course_form = CourseLookupForm()
    dump_form = DumpLookupForm()
    problem_form = ProblemCrudForm()
    delete_problem_form = DeleteProblemForm()
    bulk_import_form = BulkImportProblemsForm()

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
                        ops_results["problems"] = client.get_courses_data(service_user, course)["result"]["problems"]
                elif action == "clear_course":
                    course_form = CourseLookupForm(request.POST)
                    if course_form.is_valid():
                        course = course_form.cleaned_data["course"]
                        ops_results["clear_result"] = client.clear_course(service_user, course)["result"]
                        messages.success(request, f"Курс '{course}' очищен.")
                elif action == "get_dump":
                    dump_form = DumpLookupForm(request.POST)
                    if dump_form.is_valid():
                        ops_results["dump"] = client.get_base_dump(
                            dump_form.cleaned_data["date"],
                            dump_form.cleaned_data["processor_name"],
                            admin_key,
                        )["result"]
                elif action == "save_problem":
                    problem_form = ProblemCrudForm(request.POST)
                    if problem_form.is_valid():
                        tests = parse_problem_tests(
                            problem_form.cleaned_data["tests_text"],
                            problem_form.cleaned_data["tests_json"],
                        )
                        ops_results["problem_save_result"] = client.add_or_update_problem(
                            service_user,
                            problem_form.cleaned_data["course"],
                            problem_form.cleaned_data["problem"],
                            problem_form.cleaned_data["variant"],
                            problem_form.cleaned_data["problem_type"],
                            problem_form.cleaned_data["rating"],
                            problem_form.cleaned_data["task"],
                            tests,
                        )["result"]
                        messages.success(request, "Задача сохранена.")
                elif action == "delete_problem":
                    delete_problem_form = DeleteProblemForm(request.POST)
                    if delete_problem_form.is_valid():
                        ops_results["problem_delete_result"] = client.clear_problem(
                            service_user,
                            delete_problem_form.cleaned_data["course"],
                            delete_problem_form.cleaned_data["problem"],
                        )["result"]
                        messages.success(request, "Задача удалена.")
                elif action == "bulk_import":
                    bulk_import_form = BulkImportProblemsForm(request.POST, request.FILES)
                    if bulk_import_form.is_valid():
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
                                    bulk_import_form.cleaned_data["course"],
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
                        messages.success(request, f"Импортировано вариантов: {len(imported)}.")
            except ContestApiError as err:
                messages.error(request, str(err))

    context = {
        "settings_form": settings_form,
        "course_form": course_form,
        "dump_form": dump_form,
        "problem_form": problem_form,
        "delete_problem_form": delete_problem_form,
        "bulk_import_form": bulk_import_form,
        "ops_results": ops_results,
    }
    return render(request, "client/ops.html", context)
