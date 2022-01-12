import datetime as dt
import sqlite3
import sys
from random import randrange
from typing import List
from os import path

from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTableWidgetItem, QInputDialog, \
    QComboBox, QPushButton, QStackedWidget, QTableWidget

import resources

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return path.join(sys._MEIPASS, relative)
    return path.join(relative)


class Board(QMainWindow):  # первая форма - главное окно игры
    date: dt.date
    timer: QtCore.QTimer
    now_game_mode: int
    questions: int
    pixmap: QPixmap
    image: QLabel
    now_subject: str
    score_number: int
    subject_number: int
    data: List[str]
    start_time: dt.datetime
    end_time: dt.datetime
    str_end_time: str
    str_start_time: str
    i: int
    duration: dt.timedelta
    stackedWidget: QStackedWidget
    ask: bool
    str_game_mode: str
    lets_start_2: QPushButton

    what_is = 'Что находится на карте под номером'

    def __init__(self):
        super().__init__()
        self.initUI()
        self.date = dt.date.today()
        self.score_number = 0
        self.time_for_answer = 7_000
        self.i = 0  # i - это количество заданий, которые уже спросили
        self.timer = QtCore.QTimer()
        self.second_form = ChooseAction()  # вторая форма - форма выбора постигровой статистики
        self.end_game.clicked.connect(self.after_game)

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.setGeometry(400, 400, 1500, 800)
        self.setWindowTitle('Игра')
        self.stackedWidget.setCurrentIndex(9)  # открываем первую страницу многостраничного виджета
        self.okey.clicked.connect(self.show_rules)
        self.send_mode_choice.clicked.connect(self.set_game_mode)
        self.send_rus.clicked.connect(self.send)
        self.idk_1.clicked.connect(self.idk)
        self.lets_start_2.clicked.connect(self.choose_game_mode)

    def show_rules(self):
        self.stackedWidget.setCurrentIndex(11)

    def choose_game_mode(self):
        self.stackedWidget.setCurrentIndex(0)

    def set_game_mode(self):  # выбираем режим игры
        self.start_time = dt.datetime.now()  # время начала игры
        self.str_start_time = self.start_time.strftime("%H:%M:%S")
        # определение выбранного режима
        if self.russian_subjects.isChecked():
            self.now_game_mode = 1  # для внесения в БД даем режиму номер
            # определяем текстовое название режима игры
            con = sqlite3.connect(resource_path("tries.sql.db3"))
            cur = con.cursor()
            self.str_game_mode = cur.execute('''SELECT name from game_modes WHERE number == ?''',
                                             (self.now_game_mode,)).fetchone()
            self.str_game_mode = str(self.str_game_mode[0])
            self.questions = 85
            self.show_mode.setText('Режим 1: Субъекты Российской Федерации')

            f = open(resource_path('subjects.txt'), mode='rt', encoding='UTF-8')  # файл с субъектами РФ
            self.data = f.read().split("\n")
            self.game()

    def game(self):  # запуск процесса игры
        self.stackedWidget.setCurrentIndex(1)
        self.i += 1  #i - это количество уже заданных вопросов
        self.subject_number = randrange(1, self.questions)
        # случайным образом выбираем, вопрос про какой объект карты будет задаваться
        self.now_subject = self.data[self.subject_number - 1].split(';')[1]
        self.ex_1.setText(f"{self.what_is} {self.subject_number}?")  # вывод задания
        self.timer.timeout.connect(self.ask_question)
        self.timer.start(self.time_for_answer)

    def ask_question(self):
        self.timer.timeout.connect(self.ask_question)
        if self.i < self.questions:
            self.answer_1.clear()
            self.i += 1
            self.subject_number = randrange(1, self.questions)
            # случайным образом выбираем, вопрос про какой объект карты будет задаваться
            self.now_subject = self.data[self.subject_number - 1].split(';')[1]
            self.ex_1.setText(f"{self.what_is} {self.subject_number}?")  # вывод задания
            self.timer.start(self.time_for_answer)
        else:
            self.after_game()

    def ready(self):
        self.wrong_answer.setText('')
        self.ask_question()

    def send(self):
        self.timer.stop()
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        result = cur.execute('''SELECT COUNT (*) FROM all_answers WHERE name_of_object LIKE ?''',
                             (self.now_subject,)).fetchone()
        # проверка правильности ответа
        if self.answer_1.text().lower() == self.now_subject:
            self.score_number += 1
            self.score_lcd.display(self.score_number)
            self.wrong_answer.setText('')
            # заносим в бд информацию о правильности ответа
            # проверка, есть ли объект в бд
            if int(result[0]) == 0:  # если объекта нет
                cur.execute('''INSERT INTO 
                                all_answers(number_of_object, name_of_object, game_mode, count_of_right, count_of_wrong, 
                                percent_of_right) VALUES(?, ?, ?, 1, 0, 0)''',
                            (self.subject_number - 1, self.now_subject, self.str_game_mode))
            else:  # если есть
                cur.execute('''UPDATE all_answers SET count_of_right = count_of_right + 1 WHERE name_of_object == ?''',
                            (self.now_subject,))
            con.commit()
            con.close()
            self.ready()
        else:
            self.wrong_answer.setText('К сожалению, ответ неверный')
            if int(result[0]) == 0:  # если объекта нет
                cur.execute('''INSERT INTO 
                all_answers(number_of_object, name_of_object, game_mode, count_of_right, count_of_wrong, 
                percent_of_right) VALUES(?, ?, ?, 0, 1, 0)''',
                            (self.subject_number, self.now_subject, self.str_game_mode))
            else:  # если есть
                cur.execute('''UPDATE all_answers SET count_of_wrong = count_of_wrong + 1 WHERE name_of_object == ?''',
                            (self.now_subject, ))
                con.commit()
                con.close()
            self.timer.timeout.connect(self.ready)
            self.timer.start(2_000)

    def idk(self):
        self.timer.stop()
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        # проверка на существование объекта в таблице неугаданных
        result = cur.execute('''SELECT COUNT (*) FROM idk WHERE name_of_object LIKE ?''',
                             (self.now_subject,)).fetchone()
        if int(result[0]) == 0:  # если объекта нет
            cur.execute('''INSERT INTO idk(number_of_object, name_of_object, game_mode, count, last_date) 
                        VALUES(?, ?, ?, 1, ?)''',
                        (self.subject_number, self.now_subject, self.str_game_mode, self.date))
        else:  # если есть
            cur.execute('''UPDATE idk SET count = count + 1 WHERE name_of_object == ?''', (self.now_subject,))
            cur.execute('''UPDATE idk SET last_date = ? WHERE name_of_object == ?''', (self.date, self.now_subject))
        con.commit()
        con.close()
        self.answer_1.setText(self.now_subject)
        # показ правильного ответа
        self.wrong_answer.setText('Посмотрите на правильный ответ. Сейчас появится новое задание.')
        self.timer.timeout.connect(self.ready)
        self.timer.start(2_000)

    def after_game(self):
        self.timer.stop()
        self.end_time = dt.datetime.now()  # время конца игры
        self.str_end_time = dt.datetime.now().strftime("%H:%M:%S")
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        # вносим в БД информацию о попытке
        cur.execute(
            '''INSERT INTO all_tries(game_mode, date, start_time, end_time, score) VALUES(?, ?, ?, ?, ?)''',
            (self.str_game_mode, self.date, self.str_start_time,
             self.str_end_time, self.score_number))
        con.commit()
        for i in range(1, int(cur.execute('''SELECT COUNT (*) FROM all_answers''').fetchone()[0]) + 1):
            right_answers = cur.execute('''SELECT count_of_right FROM all_answers WHERE number = ?''', (i, )).fetchone()
            wrong_answers = cur.execute('''SELECT count_of_wrong FROM all_answers WHERE number = ?''', (i, )).fetchone()
            percent = right_answers[0] / (right_answers[0] + wrong_answers[0]) * 100
            cur.execute('''UPDATE all_answers SET percent_of_right = ? WHERE number = ?''', (percent, i))
            con.commit()
        con.close()
        self.open_choose_action()

    def open_choose_action(self):  # открытие второй формы
        self.score_lcd.setDigitCount(self.score_number)
        self.second_form.show()
        ex.close()


class ChooseAction(QMainWindow):  # вторая форма - выбор постигрового действия
    def __init__(self):
        super().__init__()
        self.third_form = ChooseStatistic()
        self.seventh_form = SendComment()
        self.timer = QtCore.QTimer()
        self.initUI()

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.stackedWidget.setCurrentIndex(3)
        self.label.setText('Игра закончена, поздравляем! Хотите ли сделать что-то после нее?')
        self.setGeometry(400, 400, 1500, 800)
        self.setWindowTitle('Выберете постигровое действие')
        self.statistic.clicked.connect(self.show_statistic)
        self.send_comment.clicked.connect(self.open_send_comment)
        self.exit.clicked.connect(self.goodbye)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(600_000)

    def goodbye(self):
        self.stackedWidget.setCurrentIndex(10)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(7_000)

    def open_send_comment(self):
        self.seventh_form.show()
        self.close_window()

    def show_statistic(self):
        self.third_form.show()

    def close_window(self):
        self.close()


class ChooseStatistic(QMainWindow):  # третья форма - выбор БД со статистикой
    tries: QPushButton
    exercises_statistic: QPushButton
    exercises_statistic_2: QPushButton

    def __init__(self):
        super().__init__()
        self.forth_form = FirstTable()
        self.fifth_form = SecondTable()
        self.sixth_form = ThirdTable()
        self.timer = QtCore.QTimer()
        self.initUI()

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.stackedWidget.setCurrentIndex(4)
        self.setGeometry(400, 400, 1500, 800)
        self.setWindowTitle('Выберете статистику')
        self.tries_statistic.clicked.connect(self.open_main_table)
        self.exercises_statistic.clicked.connect(self.open_secondary_table)
        self.exercises_statistic_2.clicked.connect(self.open_third_table)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(600_000)

    def open_main_table(self):
        self.forth_form.show()

    def open_secondary_table(self):
        self.fifth_form.show()

    def open_third_table(self):
        self.sixth_form.show()

    def close_window(self):
        self.close()


class FirstTable(QMainWindow):  # четвертая форма - БД с информацией обо всех попытках
    choice: QComboBox
    titles: list
    tableWidget: QTableWidget
    date: str
    start_date: list
    start_date_for_bd: str
    end_date: list
    end_date_for_bd: str
    show_1: QPushButton

    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.initUI()
        self.choice = QComboBox(self)
        self.choice.move(40, 60)
        self.choice.resize(231, 51)
        self.choice.addItem('Номера попыток')
        self.choice.addItem('Режим игры')
        self.choice.addItem('Даты')

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.stackedWidget.setCurrentIndex(5)
        self.setGeometry(400, 400, 1500, 800)
        self.setWindowTitle('Статистика по попыткам')
        self.show_1.clicked.connect(self.main_table_statistic)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(600_000)

    def main_table_statistic(self):
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        result = cur.execute('''SELECT * from all_tries''').fetchall()
        # сортировка таблицы по разным столбцам
        if self.choice.currentText() == 'Режим игры':
            mode, ok_pressed = QInputDialog.getItem(
                self, "Выберите режим игры для сортировки таблицы", "Какой режим?",
                ("Субъекты РФ", "Страны Европы"), 0, False)
            if ok_pressed:
                result = cur.execute('''SELECT * from all_tries WHERE game_mode = ?''', (mode,)).fetchall()
        elif self.choice.currentText() == 'Даты':
            date, ok_pressed = QInputDialog.getText(self, "Диапазон дат",
                                                    "Введите диапазон дат через пробел, каждую дату в формате дд:мм:гг")
            if ok_pressed:
                if ' ' not in date:
                    date_for_bd = date.split(':')[2] + '-' + date.split(':')[1] + '-' + date.split(':')[0]
                    result = cur.execute('''SELECT * from all_tries WHERE date >= ?''',
                                         (date_for_bd, )).fetchall()
                else:
                    date = date.split()
                    start_date = date[0].split(':')
                    start_date_for_bd = start_date[2] + '-' + start_date[1] + '-' + start_date[0]
                    end_date = date[1].split(':')
                    end_date_for_bd = end_date[2] + '-' + end_date[1] + '-' + end_date[0]
                    print(start_date_for_bd, end_date_for_bd)
                    result = cur.execute('''SELECT * from all_tries WHERE date BETWEEN ? AND ?''',
                                         (start_date_for_bd, end_date_for_bd)).fetchall()
        elif self.choice.currentText() == 'Номера попыток':
            tries, ok_pressed = QInputDialog.getText(self, "Диапазон попыток",
                                                     "Введите попытки через пробел")
            if ok_pressed:
                if ' ' not in tries:
                    result = cur.execute('''SELECT * from all_tries WHERE number_of_try >= ?''',
                                         (tries, )).fetchall()
                else:
                    result = cur.execute('''SELECT * from all_tries WHERE number_of_try BETWEEN ? AND ?''',
                                         (int(tries.split()[0]), int(tries.split()[1]))).fetchall()
        self.tableWidget.setRowCount(len(result))
        self.tableWidget.setColumnCount(len(result[0]))
        titles = ['Номер попытки', 'Режим игры', 'Дата', 'Время начала попытки', 'Время окончания попытки',
                  'Количество очков']
        self.tableWidget.setHorizontalHeaderLabels(titles)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
        con.close()
        self.tableWidget.resizeColumnsToContents()

    def close_window(self):
        self.close()


class SecondTable(QMainWindow):  # пятая форма - БД с информацией об объектах, которые не знаешь
    titles_2: list
    choice_2: QComboBox
    tableWidget_2: QTableWidget
    show_2: QPushButton

    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.initUI()
        self.choice_2 = QComboBox(self)
        self.choice_2.move(40, 60)
        self.choice_2.resize(231, 51)
        self.choice_2.addItem('Номер объекта')
        self.choice_2.addItem('Название объекта')
        self.choice_2.addItem('Режим игры')
        self.choice_2.addItem('Количество неугаданных')
        self.choice_2.addItem('Не сортировать')

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.stackedWidget.setCurrentIndex(6)
        self.setGeometry(400, 400, 1500, 800)
        self.setWindowTitle('Статистика по заданиям, на которые не был дан ответ')
        self.show_2.clicked.connect(self.secondary_table_statistic)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(600_000)

    def secondary_table_statistic(self):
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        result = cur.execute('''SELECT * FROM idk''').fetchall()
        # сортировка таблицы по разным столбцам
        if self.choice_2.currentText() == 'Режим игры':
            mode, ok_pressed = QInputDialog.getItem(
                self, "Выберите режим игры для сортировки таблицы", "Какой режим?",
                ("Субъекты РФ", "Страны Европы"), 0, False)
            if ok_pressed:
                result = cur.execute('''SELECT * from idk WHERE game_mode = ?''', (mode,)).fetchall()
        elif self.choice_2.currentText() == 'Количество неугаданных':
            count, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по количеству неугаданных раз", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if count == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM idk ORDER by count''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM idk ORDER by count DESC''').fetchall()
        elif self.choice_2.currentText() == 'Номер объекта':
            number, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по номеру объекта", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if number == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM idk ORDER by number_of_object''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM idk ORDER by number_of_object DESC''').fetchall()
        elif self.choice_2.currentText() == 'Название объекта':
            name, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по названию объекта", "Как отсортировать?",
                ("В алфавитном порядке", "В обратном алфавитном порядке"), 0, False)
            if ok_pressed:
                if name == 'В алфавитном порядке':
                    result = cur.execute('''SELECT * FROM idk ORDER by name_of_object''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM idk ORDER by name_of_object DESC''').fetchall()
        self.tableWidget_2.setRowCount(len(result))
        self.tableWidget_2.setColumnCount(len(result[0]))
        self.titles_2 = ['Номер объекта', 'Название объекта', 'Режим игры', 'Количество неугаданных раз']
        self.tableWidget_2.setHorizontalHeaderLabels(self.titles_2)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget_2.setItem(i, j, QTableWidgetItem(str(val)))
        self.tableWidget_2.resizeColumnsToContents()
        con.close()

    def close_window(self):
        self.close()


class ThirdTable(QMainWindow):  # шестая форма - БД со статистикой по заданиям
    titles_3: list
    choice_3: QComboBox
    tableWidget_3: QTableWidget
    show_3: QPushButton

    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.initUI()
        self.choice_3 = QComboBox(self)
        self.choice_3.move(40, 60)
        self.choice_3.resize(231, 51)
        self.choice_3.addItem('Номер объекта')
        self.choice_3.addItem('Название объекта')
        self.choice_3.addItem('Режим игры')
        self.choice_3.addItem('Количество правильных ответов')
        self.choice_3.addItem('Количество неправильных ответов')
        self.choice_3.addItem('Процент угаданного')
        self.choice_3.addItem('Не сортировать')

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.stackedWidget.setCurrentIndex(7)
        self.setGeometry(400, 400, 1500, 800)
        self.setWindowTitle('Статистика по всем заданиям')
        self.show_3.clicked.connect(self.third_table_statistic)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(600_000)

    def third_table_statistic(self):
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        result = cur.execute('''SELECT * FROM all_answers''').fetchall()
        # сортировка таблицы по разным столбцам
        if self.choice_3.currentText() == 'Режим игры':
            mode, ok_pressed = QInputDialog.getItem(
                self, "Выберите режим игры для сортировки таблицы", "Какой режим?",
                ("Субъекты РФ", "Страны Европы"), 0, False)
            if ok_pressed:
                result = cur.execute('''SELECT * from all_answers WHERE game_mode = ?''', (mode,)).fetchall()
        elif self.choice_3.currentText() == 'Количество неправильных ответов':
            count, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по количеству неправильных ответов", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if count == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM all_answers ORDER by count_of_wrong''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM all_answers ORDER by count_of_wrong DESC''').fetchall()
        elif self.choice_3.currentText() == 'Номер объекта':
            number, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по номеру объекта", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if number == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM all_answers ORDER by number_of_object''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM all_answers ORDER by number_of_object DESC''').fetchall()
        elif self.choice_3.currentText() == 'Название объекта':
            name, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по названию объекта", "Как отсортировать?",
                ("В алфавитном порядке", "В обратном алфавитном порядке"), 0, False)
            if ok_pressed:
                if name == 'В алфавитном порядке':
                    result = cur.execute('''SELECT * FROM all_answers ORDER by name_of_object''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM all_answers ORDER by name_of_object DESC''').fetchall()
        elif self.choice_3.currentText() == 'Количество правильных ответов':
            count, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по количеству правильных ответов", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if count == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM all_answers ORDER by count_of_right''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM all_answers ORDER by count_of_right DESC''').fetchall()
        elif self.choice_3.currentText() == 'Процент угаданного':
            count, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по проценту угаданного", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if count == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM all_answers ORDER by percent_of_right''').fetchall()
                else:
                    result = cur.execute('''SELECT * FROM all_answers ORDER by percent_of_right DESC''').fetchall()
        elif self.choice_3.currentText() == 'Не сортировать':
            result = cur.execute('''SELECT * FROM all_answers ORDER by number''').fetchall()
        self.tableWidget_3.setRowCount(len(result))
        self.tableWidget_3.setColumnCount(len(result[0]))
        self.titles_3 = ['Номер', 'Номер объекта', 'Название объекта', 'Режим игры', 'Количество правильных ответов',
                         'Количество неправильных ответов', 'Процент угаданного']
        self.tableWidget_3.setHorizontalHeaderLabels(self.titles_3)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget_3.setItem(i, j, QTableWidgetItem(str(val)))
                if j == 4:
                    self.tableWidget_3.item(i, j).setBackground(QColor(0, 255,  0))
                if j == 5:
                    self.tableWidget_3.item(i, j).setBackground(QColor(255, 0,  0))
        self.tableWidget_3.resizeColumnsToContents()
        con.close()

    def close_window(self):
        self.close()


class SendComment(QMainWindow):  # седьмая форма - отправка комментария
    commentary: str
    date: dt.date

    def __init__(self):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.date = dt.date.today()
        self.initUI()

    def initUI(self):
        uic.loadUi(resource_path("дизайн_2.ui"), self)
        self.stackedWidget.setCurrentIndex(8)
        self.setGeometry(400, 400, 800, 800)
        self.pushButton.clicked.connect(self.comment)

    def comment(self):
        con = sqlite3.connect(resource_path("tries.sql.db3"))
        cur = con.cursor()
        cur.execute('''INSERT INTO comments(comment, date) VALUES(?, ?)''', (self.com.text(), self.date))
        con.commit()
        con.close()
        # запуск таймера на закрытие окна
        self.stackedWidget.setCurrentIndex(12)
        self.timer.timeout.connect(self.close_window)
        self.timer.start(7_000)

    def close_window(self):
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Board()
    ex.show()
    sys.exit(app.exec_())
