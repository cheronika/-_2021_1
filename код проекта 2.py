import datetime as dt
import sqlite3
import sys
from random import randrange
from typing import List, Callable

from PyQt5 import uic, QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTableWidgetItem, QInputDialog, QComboBox


class Board(QMainWindow):  # первая форма - главное окно игры
    time_interval: dt.timedelta
    have_time: dt.timedelta
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

    what_is = 'Что находится на карте под номером'
    congratulations = 'Поздравляю'
    time_interval = dt.timedelta(seconds=60)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.score_number = 0
        self.subject_number = 0
        self.timer = QtCore.QTimer()
        self.now_subject = ''
        self.have_time = dt.timedelta(milliseconds=self.timer.interval())
        # сколько времени осталось до конца игры - в начале игры осталась длина режима
        self.date = dt.date.today()
        # сегодняшняя дата
        self.second_form = ChooseAction()
        # вторая форма - форма выбора постигровой статистики

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.setGeometry(400, 400, 800, 800)
        self.stackedWidget.setCurrentIndex(0)  # открываем первую страницу многостраничного виджета
        self.send_mode_choice.clicked.connect(self.set_game_mode)
        self.send_rus.clicked.connect(self.send)
        self.idk_1.clicked.connect(self.idk)

    def set_game_mode(self):  # выбираем режим игры
        self.stackedWidget.setCurrentIndex(1)  # открываем вторую страницу многостраничного виджета
        self.start_time = dt.datetime.now()  # время начала игры
        # определение выбранного режима
        if self.russian_subjects.isChecked():
            self.now_game_mode = 1  # для внесения в БД даем режиму номер
            self.questions = 23  # сколько вопросов в этом режиме
            self.show_mode.setText('Режим 1: Субъекты Российской Федерации')
            self.pixmap = QPixmap('карта.jpg')
            self.image = QLabel(self)
            self.image.setPixmap(self.pixmap)
            f = open('subjects.txt', mode='rt', encoding='UTF-8')
            self.data = f.read().split("\n")
            self.game()

    def game(self):  # процесс игры
        ask: bool
        ask = True

        def ready():
            nonlocal ask
            ask = True

        self.stackedWidget.setCurrentIndex(1)
        self.timer.setInterval(self.time_interval // dt.timedelta(milliseconds=1))  # задаем время игры
        self.i = 0
        self.start_time = dt.datetime.now()
        self.str_start_time = self.start_time.strftime("%H:%M:%S")
        self.have_time = self.time_interval
        self.timer.start()
        while self.have_time > dt.timedelta() and self.i <= self.questions:
            # игра будет длиться, пока не закончится время или вопросы
            ask = False
            print(self.i)
            print(self.have_time)
            self.i += 1
            self.time_1.setText(str(self.have_time.seconds))
            self.subject_number = randrange(1, 24)
            # случайным образом выбираем, вопрос про какой объект карты будет задаваться
            self.now_subject = self.data[self.subject_number - 1].split(';')[1]
            print(self.now_subject)
            self.ex_1.setText(f"{self.what_is}{self.subject_number}?")  # вывод задания
            self.have_time = dt.timedelta(milliseconds=self.timer.remainingTime())
            self.idk(ready)
            # while not проверить сигнал нажатия кнопки and not проверить сигнал нажатия кнопки:
            #    pass

            while not ask:
                pass

        print(self.i)
        self.end_time = dt.datetime.now()  # время конца игры
        self.str_end_time = dt.datetime.now().strftime("%H:%M:%S")
        print(self.start_time)
        print(self.end_time)
        self.duration = abs(self.end_time - self.start_time)  # продолжительность игры
        con = sqlite3.connect('tries.sql.db3')
        cur = con.cursor()
        # определяем текстовое название режима игры
        game_mode = cur.execute('''SELECT name from game_modes WHERE number == ?''', (self.now_game_mode,)).fetchone()
        game_mode = str(game_mode[0])
        print(game_mode)
        # вносим в БД информацию о попытке
        cur.execute(
            '''INSERT INTO all_tries(game_mode, date, start_time, end_time, score) VALUES(?, ?, ?, ?, ?)''',
            (game_mode, self.date, self.str_start_time,
             self.str_end_time, self.score_number))
        con.commit()
        con.close()
        # открываем вторую форму
        self.open_choose_action()

    def send(self, ready: Callable[[], None]):
        print(repr(self.answer_1.text().lower()))
        print(repr(self.now_subject))
        print(repr(self.answer_1.text().lower() == self.now_subject))
        # проверка правильности ответа
        if self.answer_1.text().lower() == self.now_subject:
            self.score_number += 1
            self.score_lcd.display(self.score_number)
            self.wrong_answer.setText('')
        else:
            # пока ответ не будет правильным, или пока не закончится время, не переходить к следующему вопросу
            while self.answer_1.text().lower() != self.now_subject and self.have_time > dt.timedelta(milliseconds=0):
                self.have_time = dt.timedelta(milliseconds=self.timer.interval())
                self.wrong_answer.setText('К сожалению, ответ неверный')
            ready()

    def idk(self, ready: Callable[[], None]):
        con = sqlite3.connect('tries.sql.db3')
        cur = con.cursor()
        # проверка на существование объекта в таблице неугаданных
        result = cur.execute('''SELECT COUNT (*) FROM idk WHERE name_of_object LIKE ?''',
                             (self.now_subject,)).fetchone()
        print(result)
        if int(result[0]) == 0:  # если объекта нет
            cur.execute('''INSERT INTO idk(number_of_object, name_of_object, game_mode, count, last_date) 
                        VALUES(?, ?, ?, 1, ?)''', (self.subject_number - 1, self.now_subject, self.stackedWidget.currentIndex(), self.date))
        else:  # если есть
            cur.execute('''UPDATE idk SET count = count + 1 WHERE name_of_object == ?''', (self.now_subject,))
            cur.execute('''UPDATE idk SET last_date = ? WHERE name_of_object == ?''', (self.date, self.now_subject))
        con.commit()
        con.close()
        self.answer_1.setText(self.now_subject)
        self.wrong_answer.setText('Посмотрите на правильный ответ. Сейчас появится новое задание.')
        self.subject_number = randrange(1, 24)
        self.now_subject = self.data[self.subject_number - 1].split(';')[1]
        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(ready)
        timer.start(2_000)

    def open_choose_action(self):  # открытие второй формы
        self.second_form.show()


class ChooseAction(QMainWindow):  # вторая форма - выбор постигрового действия
    def __init__(self):
        super().__init__()
        self.third_form = ChooseStatistic()
        self.sixth_form = SendComment()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(3)
        self.setGeometry(400, 400, 800, 800)
        self.statistic.clicked.connect(self.show_statistic)
        self.send_comment.clicked.connect(self.open_send_comment)

    def open_send_comment(self):
        self.sixth_form.show()

    def show_statistic(self):
        self.third_form.show()


class ChooseStatistic(QMainWindow):  # третья форма - выбор БД со статистикой
    def __init__(self):
        super().__init__()
        self.forth_form = MainTable()
        self.fifth_form = SecondaryTable()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(4)
        self.setGeometry(400, 400, 800, 800)
        self.tries_statistic.clicked.connect(self.open_main_table)
        self.exercises_statistic.clicked.connect(self.open_secondary_table)

    def open_main_table(self):
        self.forth_form.show()

    def open_secondary_table(self):
        self.fifth_form.show()


class MainTable(QMainWindow):  # четвертая форма - БД с информацией обо всех попытках
    choice: QComboBox
    titles: list

    def __init__(self):
        super().__init__()
        self.initUI()
        self.choice = QComboBox(self)
        self.choice.move(40, 60)
        self.choice.resize(231, 51)
        self.choice.addItem('Номера попыток')
        self.choice.addItem('Режим игры')
        self.choice.addItem('Даты')

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(5)
        self.setGeometry(400, 400, 800, 800)
        self.show_1.clicked.connect(self.main_table_statistic)

    def main_table_statistic(self):
        con = sqlite3.connect('tries.sql.db3')
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
                                                    "Введите дату в формате дд:мм:гг")
            if ok_pressed:
                result = cur.execute('''SELECT * from all_tries WHERE date = ?''', (date,)).fetchall()
        elif self.choice.currentText() == 'Номера попыток':
            tries, ok_pressed = QInputDialog.getText(self, "Диапазон попыток",
                                                     "Введите попытки через пробел")
            if ok_pressed:
                result = cur.execute('''SELECT * from all_tries WHERE number_of_try BETWEEN ? AND ?''',
                                     (int(tries.split()[0]), int(tries.split()[1]))).fetchall()
        self.tableWidget.setRowCount(len(self.result))
        self.tableWidget.setColumnCount(len(self.result[0]))
        titles = ['Номер попытки', 'Режим игры', 'Дата', 'Время начала попытки', 'Время окончания попытки',
                  'Количество очков']
        self.tableWidget.setHorizontalHeaderLabels(titles)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))
        con.close()
        self.tableWidget.resizeColumnsToContents()


class SecondaryTable(QMainWindow):  # пятая форма - БД с информацией о неугаданных объектах
    titles_2: list

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(6)
        self.setGeometry(400, 400, 800, 800)
        self.show_2.clicked.connect(self.secondary_table_statistic)

    def secondary_table_statistic(self):
        con = sqlite3.connect('tries.sql.db3')
        cur = con.cursor()
        self.comboBox_2.addItems('Номер объекта', 'Название объекта', 'Режим игры', 'Количество неугаданных',
                                 'Не сортировать')
        result = cur.execute('''SELECT * FROM idk''')
        # сортировка таблицы по разным столбцам
        if self.comboBox_2.currentText() == 'Режим игры':
            mode, ok_pressed = QInputDialog.getItem(
                self, "Выберите режим игры для сортировки таблицы", "Какой режим?",
                ("Субъекты РФ", "Страны Европы"), 0, False)
            if ok_pressed:
                md = cur.execute('''SELECT number from game_modes WHERE name = ?''', (mode, )).fetchone()
                result = cur.execute('''SELECT * from all_tries WHERE game_mode = ?''', (md,)).fetchall()
        elif self.comboBox_2.currentText() == 'Количество неугаданных':
            count, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по количеству неугаданных раз", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if count == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM i_don't_know ORDER by count''')
                else:
                    result = cur.execute('''SELECT * FROM i_don't_know ORDER by count DESC''')
        elif self.comboBox_2.currentText() == 'Номер объекта':
            number, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по номеру объекта", "Как отсортировать?",
                ("По возрастанию", "По убыванию"), 0, False)
            if ok_pressed:
                if number == 'По возрастанию':
                    result = cur.execute('''SELECT * FROM idk ORDER by number_of_object''')
                else:
                    result = cur.execute('''SELECT * FROM idk ORDER by number_of_object DESC''')
        elif self.comboBox_2.currentText() == 'Название объекта':
            name, ok_pressed = QInputDialog.getItem(
                self, "Сортировка по названию объекта", "Как отсортировать?",
                ("В алфавитном порядке", "В обратном алфавитном порядке"), 0, False)
            if ok_pressed:
                if name == 'В алфавитном порядке':
                    result = cur.execute('''SELECT * FROM idk ORDER by name_of_object''')
                else:
                    result = cur.execute('''SELECT * FROM idk ORDER by name_of_object DESC''')
        self.tableWidget_2.setRowCount(len(result))
        self.tableWidget_2.setColumnCount(len(result[0]))
        self.titles_2 = ['Номер объекта', 'Название объекта', 'Режим игры', 'Количество неугаданных раз']
        self.tableWidget_2.setHorizontalHeaderLabels(self.titles)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget_2.setItem(i, j, QTableWidgetItem(str(val)))
        self.tableWidget_2.resizeColumnsToContents()
        con.close()


class SendComment(QMainWindow):  # шестая форма - отправка комментария
    commentary: str

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi("дизайн_2.ui", self)
        self.stackedWidget.setCurrentIndex(7)
        self.setGeometry(400, 400, 800, 800)
        self.pushButton.clicked.connect(self.comment)

    def comment(self):
        self.commentary = self.plainTextEdit.toPlainText()
        d = open('comments.txt', 'wt', encoding='utf-8')
        data = d.readlines()
        data.append(self.commentary)
        d.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Board()
    ex.show()
    sys.exit(app.exec_())

