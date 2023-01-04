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
        self.push_code.clicked.connect(self.do_process)
        self.user = ""
        self.test_code = ""
        self.user_data = {}
        self.test_problerms_count1 = 1
        self.test_problerms_count2 = 8
        self.test_problerms_count3 = 1
        self.addr = "http://cluster.vstu.ru:57888"
        #self.addr = "http://localhost:57888"
        self.spin_problem.setMinimum(1)
        self.spin_problem.valueChanged.connect(self.select_problem)
        self.state = 0

    # Ищем среди ключей первый числовой - он для этого словаря номер задачи
    def get_problem_number(self, data):
        return int([key for key in data.keys() if key.isnumeric()][0])

    # Ищем среди ключей первый числовой совпадающий с данным и возващаем его индекс
    def get_problem_index(self, data, pr):
        return int([i for i, key in enumerate(data.keys()) if int(key) == pr][0])

    def do_process(self):
        if self.state == 0:
            self.get_user_data()
            if "test" in self.user_data:
                self.state = 1
                self.push_code.setText("Загрузить и проверить код")
                self.spin_problem.setMaximum(len(self.user_data["test"]))
        elif self.state == 1:
            self.select_file()

    def select_problem(self):
        max_spin = self.test_problerms_count1 + self.test_problerms_count2 + self.test_problerms_count3
        if self.state != 1:
            return
        i = self.spin_problem.value()
        if i <= max_spin and i > 0:
            last_result = self.user_data["test"][i-1].get("last_result", "")
            if last_result != "": last_result = "\n-----\n" + last_result
            self.text_code.setPlainText(self.user_data["test"][i-1]["task"] + last_result)

    def get_user_data(self):
        id = str(uuid.uuid4())
        self.user = self.edit_name.text()
        if self.user == "":
            self.text_code.setPlainText("Задайте имя студента!")
            return
        message = {"user_name": self.user}
        resp = requests.post(
            f"{self.addr}/api/get_user_info", json=message)
        if resp.status_code == 200 and "data" in resp.json():
            self.user_data = resp.json()["data"]["data"]
            self.edit_name.setEnabled(False)
        if "test" not in self.user_data:
            id = str(uuid.uuid4())
            message = {"id": id, "mqtt_key": "234", "user": self.user, "type": "problems", "data_key": "test", "action": "get_data"}
            resp = requests.post(
                f"{self.addr}/api/get_courses_data", json=message)
            if resp.status_code == 200 and "data" in resp.json():
                problems = resp.json()["data"]["problems"]
                prmas1 = []
                prmas2 = []
                prmas3 = []
                for problem in problems:
                    pr = [x for x in problem.keys() if x.isnumeric()][0]
                    if 'rating' in problem and problem['rating'] == 1:
                        prmas1.append(pr)
                    elif 'rating' in problem and problem['rating'] == 2:
                        prmas2.append(pr)
                    elif 'rating' in problem and problem['rating'] == 3:
                        prmas3.append(pr)
                prlist1 = random.sample(prmas1, self.test_problerms_count1)
                prlist2 = random.sample(prmas2, self.test_problerms_count2)
                prlist3 = random.sample(prmas3, self.test_problerms_count3)
                prlist = prlist1 + prlist2 + prlist3
                test = [p for p in problems if len([x for x in prlist if x in p]) > 0]
                self.user_data["test"] = test
                message = {"user_name": self.user, "data": self.user_data}
                resp = requests.post(f"{self.addr}/api/add_user_info", json=message)
        self.spin_problem.setValue(1)
        self.text_code.setPlainText(self.user_data["test"][0]["task"])

    async def check_problem(self):
        id = str(uuid.uuid4())
        mqtt_key = '123'
        language = self.edit_language.text()
        course = 'test'
        problem = self.spin_problem.value()
        variant = str(self.spin_variant.value())
        code = self.test_code
        message = {'id': id, 'mqtt_key': mqtt_key, 'user': self.user,
                    'language': language, 'course': course, 'action': 'test_problem',
                    'problem': self.get_problem_number(self.user_data["test"][problem - 1]), 'variant': variant, 'code': code}
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
                if result is not None and 'error' not in result:
                    if result['result']['max_res_score'] == result['result']['res_score']:
                        bad_in = ""
                    else:
                        bad_in = "Ошибочные результаты получены на следующих входных данных:\n"
                        i = 1
                        for key in result['result']:
                            if isinstance(result['result'][key], type(result['result'])) \
                             and 'test_in' in result['result'][key] \
                             and result['result'][key]['score'] == 0:
                                bad_in += f"{i}) " + str(result['result'][key]['test_in'].strip()) + "\n"
                                i += 1
                                # Показываем только первую ошибку
                                break
                    last_result = f"Задача проверена.\nРезультат:\nНабрано {result['result']['res_score']} баллов из {result['result']['max_res_score']} возможных.\n{bad_in}"
                    self.user_data["test"][problem - 1]["last_result"] = last_result
                    self.text_code.setPlainText(self.user_data["test"][problem - 1]["task"] + "\n-------\n" + last_result)
                    self.statusbar.showMessage("")
                    message = {"user_name": self.user, "data": self.user_data}
                    requests.post(f"{self.addr}/api/add_user_info", json=message)
                    break
            if time.time() - b > 30:
                self.text_code.setPlainText("Задача не была проверена за отведенное время. Попробуйте еще раз.")
                break

    def select_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, "Выбор файла с программой", None, "Python code (*.py);;C# code (*.cs)")[0]
        if not file_name:
            return
        with open(file_name, 'r') as f:
            self.test_code = f.read()
        asyncio.run(self.check_problem())


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ClientApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
