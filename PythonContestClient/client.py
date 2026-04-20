import sys

from PyQt5 import QtCore, QtWidgets

import design
from api import ContestApiClient, ContestApiError
from services import ContestClientService


class CheckSolutionWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, service, problem_index, variant, language, code):
        super().__init__()
        self.service = service
        self.problem_index = problem_index
        self.variant = variant
        self.language = language
        self.code = code

    @QtCore.pyqtSlot()
    def run(self):
        try:
            result = self.service.submit_solution(
                problem_index=self.problem_index,
                variant=self.variant,
                language=self.language,
                code=self.code,
            )
        except ContestApiError as err:
            self.failed.emit(str(err))
            return
        except Exception as err:
            self.failed.emit(f"Неожиданная ошибка: {err}")
            return
        self.finished.emit(result)


class ClientApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.push_code.clicked.connect(self.do_process)
        self.push_reset.clicked.connect(self.reset_session)
        self.spin_problem.setMinimum(1)
        self.spin_problem.valueChanged.connect(self.select_problem)
        self.spin_variant.setMinimum(1)
        self.settings = QtCore.QSettings("SGContest", "PythonContestClient")
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress)

        self.restore_settings()
        self.api_client = ContestApiClient(self.edit_server.text().strip())
        self.service = ContestClientService(self.api_client, course=self.edit_course.text().strip())

        self.state = 0
        self.test_code = ""
        self.worker_thread = None
        self.worker = None

    def do_process(self):
        if self.state == 0:
            self.load_user()
        elif self.state == 1:
            self.select_file()

    def apply_runtime_settings(self):
        server_url = self.edit_server.text().strip()
        course = self.edit_course.text().strip()
        if not server_url:
            raise ValueError("Задайте адрес сервера!")
        if not course:
            raise ValueError("Задайте код курса!")
        self.api_client = ContestApiClient(server_url)
        self.service = ContestClientService(self.api_client, course=course)

    def restore_settings(self):
        self.edit_name.setText(self.settings.value("user_name", self.edit_name.text(), type=str))
        self.edit_server.setText(self.settings.value("server_url", self.edit_server.text(), type=str))
        self.edit_course.setText(self.settings.value("course", self.edit_course.text(), type=str))
        language = self.settings.value("language", self.edit_language.currentText(), type=str)
        language_index = self.edit_language.findText(language)
        if language_index >= 0:
            self.edit_language.setCurrentIndex(language_index)

    def save_settings(self):
        self.settings.setValue("user_name", self.edit_name.text().strip())
        self.settings.setValue("server_url", self.edit_server.text().strip())
        self.settings.setValue("course", self.edit_course.text().strip())
        self.settings.setValue("language", self.edit_language.currentText())

    def set_busy(self, is_busy, message=""):
        self.progress.setVisible(is_busy)
        self.push_code.setEnabled(not is_busy)
        self.push_reset.setEnabled(not is_busy and self.state == 1)
        self.statusbar.showMessage(message if is_busy else "")

    def load_user(self):
        user_name = self.edit_name.text().strip()
        try:
            self.apply_runtime_settings()
            self.save_settings()
            problems = self.service.load_user_data(user_name)
        except ValueError as err:
            self.text_code.setPlainText(str(err))
            return
        except ContestApiError as err:
            self.text_code.setPlainText(f"Ошибка загрузки данных: {err}")
            return

        self.edit_name.setEnabled(False)
        self.edit_server.setEnabled(False)
        self.edit_course.setEnabled(False)
        self.state = 1
        self.push_reset.setEnabled(True)
        self.push_code.setText("Загрузить и проверить код")
        self.spin_problem.setMaximum(len(problems))
        self.spin_problem.setValue(1)
        self.show_problem(0)

    def show_problem(self, problem_index):
        self.spin_variant.setMaximum(self.service.get_problem_variant_count(problem_index))
        self.spin_variant.setValue(1)
        self.text_code.setPlainText(self.service.get_problem_statement(problem_index))

    def select_problem(self):
        if self.state != 1:
            return
        problem_index = self.spin_problem.value() - 1
        if problem_index >= 0:
            self.show_problem(problem_index)

    def select_file(self):
        extension = self.edit_language.currentData()
        file_name = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выбор файла с программой",
            None,
            f"Code file ({extension})",
        )[0]
        if not file_name:
            return
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                self.test_code = file.read()
        except UnicodeDecodeError:
            with open(file_name, "r", encoding="cp1251") as file:
                self.test_code = file.read()
        self.check_problem()

    def check_problem(self):
        if self.worker_thread is not None:
            self.text_code.setPlainText("Проверка уже выполняется. Дождитесь завершения.")
            return

        self.save_settings()
        self.text_code.setPlainText("Задача успешно отправлена. Ожидаем проверки.")
        self.set_busy(True, "Проверка решения...")

        self.worker_thread = QtCore.QThread(self)
        self.worker = CheckSolutionWorker(
            service=self.service,
            problem_index=self.spin_problem.value() - 1,
            variant=self.spin_variant.value(),
            language=self.edit_language.currentText(),
            code=self.test_code,
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_check_finished)
        self.worker.failed.connect(self.on_check_failed)
        self.worker.finished.connect(self.cleanup_worker)
        self.worker.failed.connect(self.cleanup_worker)
        self.worker_thread.start()

    def on_check_finished(self, result_text):
        self.statusbar.showMessage("Проверка завершена.")
        self.text_code.setPlainText(
            self.service.get_problem_statement(self.spin_problem.value() - 1)
        )

    def on_check_failed(self, message):
        self.statusbar.showMessage("")
        self.text_code.setPlainText(message)

    def cleanup_worker(self, _message):
        self.set_busy(False)
        if self.worker_thread is not None:
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker = None
        self.worker_thread = None

    def reset_session(self):
        if self.worker_thread is not None:
            self.text_code.setPlainText("Дождитесь завершения текущей проверки.")
            return
        self.state = 0
        self.test_code = ""
        self.service.user_data = {}
        self.service.user = ""
        self.edit_name.setEnabled(True)
        self.edit_server.setEnabled(True)
        self.edit_course.setEnabled(True)
        self.push_reset.setEnabled(False)
        self.push_code.setEnabled(True)
        self.push_code.setText("Загрузить вариант")
        self.spin_problem.setValue(1)
        self.spin_problem.setMaximum(99)
        self.spin_variant.setValue(1)
        self.spin_variant.setMaximum(99)
        self.text_code.setPlainText("")
        self.statusbar.showMessage("")


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ClientApp()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
