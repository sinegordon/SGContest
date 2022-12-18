import sys
from PyQt5 import QtWidgets
import design
import uuid
import requests
import aiohttp
import asyncio
import time


class ClientApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.push_code.clicked.connect(self.select_file)
        #self.addr = "http://cluster.vstu.ru:57888"
        self.addr = "http://localhost:57888"

    async def check_problem(self):
        id = str(uuid.uuid4())
        mqtt_key = '123'
        user = self.edit_name.text()
        language = self.edit_language.text()
        course = 'test'
        problem = str(self.spin_problem.value())
        variant = str(self.spin_variant.value())
        code = self.text_code.toPlainText()
        message = {'id': id, 'mqtt_key': mqtt_key, 'user': user,
                    'language': language, 'course': course, 'action': 'test_problem',
                    'problem': problem, 'variant': variant, 'code': code}
        resp = requests.post(f'{self.addr}/api/add_message', json=message)
        if not resp.ok:
            self.text_code.setPlainText("Не удалось отправить задачу")
            return
        self.text_code.setPlainText("Задача успешно отправлена. Ожидаем проверки.")
        message = {'id': id}
        flag = True
        count = 0
        b = time.time()
        while flag:
            count += 1
            # self.statusbar.showMessage(f"Выполняется попытка №{count}.")
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{self.addr}/api/get_message_result', json=message) as resp:
                    result = await resp.json()
                if result != None and 'error' not in result:
                    self.text_code.setPlainText(f"Задача проверена.\nРезультат:\n{result}")
                    self.statusbar.showMessage("")
                    break
            if time.time() - b > 30:
                self.text_code.setPlainText("Задача не была проверена за отведенное время. Попробуйте еще раз.")
                break

    def select_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, "Выбор файла с программой", None, "Python code (*.py);;C# code (*.cs)")[0]
        if not file_name:
            return
        with open(file_name, 'r') as f:
            self.text_code.setPlainText(f.read())
        asyncio.run(self.check_problem())

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ClientApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
