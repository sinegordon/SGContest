import sys
from PyQt5 import QtWidgets
import design
import uuid
import requests
import time

class ClientApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.push_code.clicked.connect(self.select_file)
    
    def check_problem(self):
        id = str(uuid.uuid4())
        mqtt_key = '123'
        user = self.edit_name.text()
        language = self.edit_language.text()
        course = 'na'
        problem = str(self.spin_problem.value())
        variant = str(self.spin_variant.value())
        code = self.text_code.toPlainText()
        message = {'id': id, 'mqtt_key': mqtt_key, 'user': user, 'language': language, 'course': course, 
            'problem': problem, 'variant': variant, 'code': code}
        resp = requests.post('http://localhost:8000/api/add_message', json=message)
        if not resp.ok:
            self.text_code.setPlainText("Не удалось отправить задачу")
            return
        self.statusbar.showMessage("Задача успешно отправлена. Ожидаем проверки.")
        time.sleep(3)
        flag = True
        count = 0
        while flag:
            count += 1
            self.statusbar.showMessage(f"Попытка проверки №{count}.")
            message = {'id': id}
            resp = requests.post('http://localhost:8000/api/get_message_result', json=message)
            if 'error' not in resp.json():
                self.text_code.setPlainText(f"Задача проверена.\nРезультат:\n{resp.json()}")
                self.statusbar.showMessage("")
                return
            time.sleep(3)

    
    def select_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, "Выбор файла с программой", None, "Python code (*.py)")[0]
        if not file_name:
            return
        with open(file_name, 'r') as f:
            self.text_code.setPlainText(f.read())
        self.check_problem()



def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ClientApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()