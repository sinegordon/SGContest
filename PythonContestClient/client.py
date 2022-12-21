import sys
from PyQt5 import QtWidgets
import design
import uuid
import requests
import aiohttp
import asyncio
import time
import random
import json


class ClientApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.push_code.clicked.connect(self.select_file)
        self.user_data = {}
        # self.addr = "http://cluster.vstu.ru:57888"
        self.addr = "http://localhost:57888"

    def get_user(self):
        id = str(uuid.uuid4())
        user = self.edit_name.text()
        if user == "":
            self.text_code.setPlainText("Задайте имя студента!")
            return
        message = {"user_name": user}
        resp = requests.post(
            f"{self.addr}/api/get_user_info", json=message)
        if resp.status_code == 200 and "data" in resp.json():
            self.user_data = resp.json()["data"]
        if "test" not in self.user_data:
            id = str(uuid.uuid4())
            message = {"id": id, "mqtt_key": "234", "user": user, "type": "problems", "data_key": "test", "action": "get_data"}
            resp = requests.post(f"{self.addr}/api/add_message", json=message)
            time.sleep(2)
            message = {"id": id}
            resp = requests.post(f"{self.addr}/api/get_message_result", json=message)
            if resp.status_code == 200 and "result" in resp.json():
                problems = resp.json()["result"]["problems"]
                prmas = []
                for problem in problems:
                    pr = [x for x in problem.keys() if x.isnumeric()][0]
                    prmas.append(pr)
                prlist = random.sample(prmas, 3)
                test = [p for p in problems if len([x for x in prlist if x in p]) > 0]
                self.user_data["test"] = test
                message = {"user_name": user, "data": self.user_data}
                resp = requests.post(f"{self.addr}/api/add_user_info", json=message)
        self.text_code.setPlainText(
                    "Ваш тестовый вариант:\n" + json.dumps(self.user_data["test"]))


    async def check_problem(self):
        id = str(uuid.uuid4())
        mqtt_key = '123'
        user = self.edit_name.text()
        if user == "":
            self.text_code.setPlainText("Задайте имя студента!")
            return
        self.get_user()
        return
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
        #file_name = QtWidgets.QFileDialog.getOpenFileName(self, "Выбор файла с программой", None, "Python code (*.py);;C# code (*.cs)")[0]
        #if not file_name:
        #    return
        #with open(file_name, 'r') as f:
        #    self.text_code.setPlainText(f.read())
        asyncio.run(self.check_problem())

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ClientApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
