import datetime as dt
import sqlite3
import sys
import time
from random import randint

from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTableWidgetItem, QInputDialog, QWidget


class Board(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.score_number = 0
        self.subject_number = 0
        self.what_is = 'Что находится на карте под номером'
        self.timer = QtCore.QTimer()
        self.congratulations = 'Поздравляю'
        self.now_subject = ''
        self.time_interval = 60
        self.have_time = self.timer.interval()
        self.date = dt.date.today()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.setGeometry(400, 400, 800, 800)
        self.stackedWidget.setCurrentIndex(0)
        self.send_mode_choice.clicked.connect(self.set_game_mode)
        self.send_rus.clicked.connect(self.send)
        self.idk_1.clicked.connect(self.idk)

    def set_game_mode(self):
        self.stackedWidget.setCurrentIndex(1)
        self.start_time = dt.datetime.now()
        if self.russian_subjects.isChecked():
            self.now_game_mode = 1
            self.questions = 23
            self.show_mode.setText('Режим 1: Субъекты Российской Федерации')
            self.pixmap = QPixmap('карта.jpg')
            self.image = QLabel(self)
            self.image.setPixmap(self.pixmap)
            self.f = open('subjects.txt', 'rt', encoding='utf-8')
            self.data = self.f.readlines()
            self.game()

    def game(self):
        self.timer.setInterval(self.time_interval * 1000000)
        self.timer.start(self.timer.interval())
        self.i = 0
        self.have_time = self.timer.interval()
        self.timer.start(self.timer.interval())
        while self.have_time > 0 and self.i <= self.questions:
            print(self.i)
            print(self.have_time)
            self.i += 1
            self.time_1.setText(str(self.have_time // 1000000))
            self.subject_number = randint(1, 23)
            self.now_subject = self.data[self.subject_number - 1].split(';')[1]
            self.ex_1.setText(self.what_is + str(self.subject_number) + '?')
            self.have_time = self.timer.interval()
            self.send_rus.clicked.connect(self.send)
            self.idk_1.clicked.connect(self.idk)
        print(self.i)
        self.end_time = dt.datetime.now()
        con = sqlite3.connect('tries.sql.db3')
        cur = con.cursor()
        game_mode = con.execute('''SELECT name from game_modes WHERE number == ?''', (self.now_game_mode,)).fetchone()
        game_mode = str(game_mode)
        result = con.execute('''INSERT INTO all_tries VALUES(?, ?, ?, ?, ?, ?)''', (self.i, game_mode, self.date, self.start_time,
                                                                                 self.end_time, self.score_number))
        self.open_choose_action()

    def send(self):
        print(repr(self.answer_1.text().lower()))
        print(repr(self.now_subject))
        print(repr(self.answer_1.text().lower() == self.now_subject))
        if self.answer_1.text().lower() == self.now_subject:
            self.score_number += 1
            self.score_lcd.display(self.score_number)
            self.wrong_answer.setText('')
        else:
            while self.answer_1.text().lower() != self.now_subject and self.have_time > 0:
                self.have_time = self.timer.interval()
                self.wrong_answer.setText('Неправильный ответ. Попробуйте еще раз.')

    def idk(self):
        con = sqlite3.connect('tries.sql.db3')
        cur = con.cursor()
        result = con.execute('''SELECT COUNT (*) FROM i_dont_know WHERE name_of_object LIKE ?''',
                             (self.now_subject,)).fetchone()
        print(result)
        if int(result[0]) == 0:
            con.execute('''INSERT INTO i_dont_know(name_of_object, mode_number, count) 
                        VALUES(?, ?, 1)''', (self.now_subject, self.stackedWidget.currentIndex()))
        else:
            con.execute('''UPDATE i_dont_know SET count = count + 1 WHERE name_of_object == ?''', (self.now_subject,))
        con.commit()
        self.answer_1.setText(self.now_subject)
        self.wrong_answer.setText('Посмотрите на правильный ответ. Сейчас появится новое задание.')
        time.sleep(2)
        self.subject_number = randint(1, 23)
        self.now_subject = self.data[self.subject_number - 1].split(';')[1]
        self.ex_1.setText(self.what_is + ' ' + str(self.subject_number) + '?')
        self.answer_1.setText('')

    def open_choose_action(self):
        self.second_form = ChooseAction()
        self.second_form.show()

    def show_statistic(self):
        self.stackedWidget.setCurrentIndex(4)

    def new_game(self):
        pass


class ChooseAction(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(3)
        self.setGeometry(400, 400, 800, 800)
        self.statictic.clicked.connect(self.show_statistic)
        self.tries_statistic.clicked.connect(self.main_table_statistic)
        self.exercises_statistic.clicked.connect(self.secondary_table_statistic)
        self.send_comment.clicked.connect(self.comment)
        self.start_new_game.clicked.connect(self.new_game)

    def open_main_table(self):
        self.third_form = MainTable()
        self.third_form.show()

    def open_secondary_table(self):
        self.forth_form = SecondaryTable()
        self.forth_form.show()

    def open_send_comment(self):
        self.fifth_form = SendComment()
        self.fifth_form.show()


class MainTable(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(4)
        self.setGeometry(400, 400, 800, 800)
        self.show_2.clicked.connect(self.main_table_statistic)

    def main_table_statistic(self):
        self.comboBox.addItems(['Номера попыток', 'Режим игры', 'Даты'])
        if self.comboBox.currentText() == 'Режим игры':
            mode, ok_pressed = QInputDialog.getItem(
                self, "Выберите режим игры для сортировки таблицы", "Какой режим?",
                ("Субъекты РФ", "Страны Европы"), 0, False)
            if ok_pressed:
                md = self.cur.execute('''SELECT number from game_modes WHERE name = ?''', (mode)).fetchone()
                self.result = self.cur.execute('''SELECT * from all_tries WHERE game_mode = ?''', (md, )).fetchall()
        elif self.comboBox.currentText() == 'Даты':
            date, ok_pressed = QInputDialog.getText(self, "Диапазон дат",
                                                    "Введите дату в формате дд:мм:гг")
            if ok_pressed:
                self.result = self.cur.execute('''SELECT * from all_tries WHERE date = ?''', (date, )).fetchall()
        elif self.comboBox.currentText() == 'Номера попыток':
            tries, ok_pressed = QInputDialog.getText(self, "Диапазон попыток",
                                                    "Введите попытки через пробел")
            if ok_pressed:
                self.result = self.cur.execute('''SELECT * from all_tries WHERE number_of_try BETWEEN ? AND ?''', (int(tries.split()[0]), int(tries.split()[1]))).fetchall()
        else:
            self.result = self.cur.execute('''SELECT * from all_tries''').fetchall()
        self.tableWidget.setRowCount(len(self.result))
        self.tableWidget.setColumnCount(len(self.result[0]))
        self.titles = ['Номер попытки', 'Режим игры', 'Дата', 'Длительность', 'Количество очков']
        self.tableWidget.setHorizontalHeaderLabels(self.titles)
        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem[1:-1]):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))


class SecondaryTable(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(5)
        self.setGeometry(400, 400, 800, 800)
        self.show_2.clicked.connect(self.secondary_table_statistic)

    def secondary_table_statistic(self):
        self.comboBox_2.addItems(['Номер объекта', 'Название объекта', 'Режим игры', 'Количество неугаданных'])
        if self.comboBox_2.currentText() == 'Режим игры':
            mode, ok_pressed = QInputDialog.getItem(
                self, "Выберите режим игры для сортировки таблицы", "Какой режим?",
                ("Субъекты РФ", "Страны Европы"), 0, False)
            if ok_pressed:
                md = self.cur.execute('''SELECT number from game_modes WHERE name = ?''', (mode)).fetchone()
                self.result = self.cur.execute('''SELECT * from all_tries WHERE game_mode = ?''', (md,)).fetchall()
        elif self.comboBox_2.currentText() == 'Количество неугаданных':
            count, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по количеству неугаданных раз", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if count == 'По возрастанию':
                    pass
                else:
                    pass
        elif self.comboBox_2.currentText() == 'Номер объекта':
            number, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по номеру объекта", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                pass
        elif self.comboBox_2.currentText() == 'Название объекта':
            name, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по названию объекта", "Как отсортировать?",
                ("В алфавитном порядке", "В обратном алфавитном порядке"), 0, False)
            if ok_pressed:
                pass
        self.tableWidget.setRowCount(len(self.result))
        self.tableWidget.setColumnCount(len(self.result[0]))
        self.titles = ['Номер объекта', 'Название объекта', 'Режим игры', 'Количество неугаданных раз']
        self.tableWidget.setHorizontalHeaderLabels(self.titles)
        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem[1:-1]):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))


class SendComment(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(6)
        self.setGeometry(400, 400, 800, 800)
        self.send_comment.clicked.connect(self.comment)

    def comment(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Board()
    ex.show()
    sys.exit(app.exec_())
