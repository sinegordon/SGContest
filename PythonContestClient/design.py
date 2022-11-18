# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(344, 466)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setDocumentMode(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.formLayout = QtWidgets.QFormLayout(self.centralwidget)
        self.formLayout.setObjectName("formLayout")
        self.label_name = QtWidgets.QLabel(self.centralwidget)
        self.label_name.setObjectName("label_name")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_name)
        self.edit_name = QtWidgets.QLineEdit(self.centralwidget)
        self.edit_name.setObjectName("edit_name")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.edit_name)
        self.label_language = QtWidgets.QLabel(self.centralwidget)
        self.label_language.setObjectName("label_language")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_language)
        self.edit_language = QtWidgets.QLineEdit(self.centralwidget)
        self.edit_language.setEnabled(False)
        self.edit_language.setObjectName("edit_language")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.edit_language)
        self.label_course = QtWidgets.QLabel(self.centralwidget)
        self.label_course.setObjectName("label_course")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_course)
        self.edit_course = QtWidgets.QLineEdit(self.centralwidget)
        self.edit_course.setEnabled(False)
        self.edit_course.setObjectName("edit_course")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.edit_course)
        self.label_problem = QtWidgets.QLabel(self.centralwidget)
        self.label_problem.setObjectName("label_problem")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_problem)
        self.spin_problem = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_problem.setObjectName("spin_problem")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.spin_problem)
        self.label_variant = QtWidgets.QLabel(self.centralwidget)
        self.label_variant.setObjectName("label_variant")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_variant)
        self.spin_variant = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_variant.setObjectName("spin_variant")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.spin_variant)
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.formLayout.setLayout(9, QtWidgets.QFormLayout.LabelRole, self.formLayout_2)
        self.text_code = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.text_code.setReadOnly(True)
        self.text_code.setObjectName("text_code")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.SpanningRole, self.text_code)
        self.push_code = QtWidgets.QPushButton(self.centralwidget)
        self.push_code.setObjectName("push_code")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.SpanningRole, self.push_code)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Contest Client"))
        self.label_name.setText(_translate("MainWindow", "Имя студента в системе"))
        self.label_language.setText(_translate("MainWindow", "Язык программирования"))
        self.edit_language.setText(_translate("MainWindow", "python3"))
        self.label_course.setText(_translate("MainWindow", "Код учебного курса"))
        self.edit_course.setText(_translate("MainWindow", "Программирование"))
        self.label_problem.setText(_translate("MainWindow", "Номер задачи"))
        self.label_variant.setText(_translate("MainWindow", "Вариант"))
        self.push_code.setText(_translate("MainWindow", "Загрузить и проверить код"))
