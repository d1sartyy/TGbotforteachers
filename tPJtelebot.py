import telebot
from telebot import types
import sqlite3
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from sqlite3 import connect
from telebot import TeleBot

API_TOKEN = '6527726726:AAHOE6LbrRujtO91QhhRT94kZ_WFIesELWg'

bot = telebot.TeleBot(API_TOKEN)

conn = sqlite3.connect('school_db.db', check_same_thread=False)
cursor = conn.cursor()
select_cursor = conn.cursor()
insert_cursor = conn.cursor()

select_cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        class_id INTEGER,
        age INTEGER,
        average_grade REAL
    )
''')

select_cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_number INTEGER,
        class_letter TEXT
    )
''')

conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        grade INTEGER
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS class_teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        class_id INTEGER,
        FOREIGN KEY(class_id) REFERENCES classes(id)
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        day_of_week TEXT,
        lesson_number INTEGER,
        subject TEXT,
        teacher_id INTEGER,
        FOREIGN KEY(class_id) REFERENCES classes(id),
        FOREIGN KEY(teacher_id) REFERENCES teachers(id)
    )
''')
conn.commit()

def create_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Учні")
    btn2 = types.KeyboardButton("Класи")
    btn3 = types.KeyboardButton("Вчителі")
    btn4 = types.KeyboardButton("Розклад уроків")
    btn5 = types.KeyboardButton("Оцінки")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, "Привіт! Я твій SchoolyBot. Чим можу допомогти?", reply_markup=create_menu())

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    if message.text == "Учні":
        add_student(message)
    elif message.text == "Класи":
        handle_classes_menu(message)
    elif message.text == "Вчителі":
        handle_teachers_menu(message)
    elif message.text == "Розклад уроків":
        handle_schedule_menu(message)
    elif message.text == "Оцінки":
        handle_grades_menu(message)

def add_student(message):
    bot.send_message(message.chat.id, "Введи ім'я та прізвище учня:")
    bot.register_next_step_handler(message, process_student_name)

def process_student_name(message):
    student_name = message.text
    insert_cursor.execute('INSERT INTO students (name) VALUES (?)', (student_name,))
    conn.commit()
    bot.send_message(message.chat.id, f"Учень {student_name} доданий успішно!", reply_markup=create_menu())


def view_classes(message):
    cursor.execute('SELECT * FROM classes')
    classes = cursor.fetchall()

    response_text = "Список класів:\n"
    for class_info in classes:
        response_text += f"{class_info[0]}. {class_info[1]}{class_info[2]}\n"

    bot.send_message(message.chat.id, response_text, reply_markup=create_menu())


def handle_classes_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    add_class_button = types.KeyboardButton("Додати клас")
    view_classes_button = types.KeyboardButton("Переглянути класи")
    markup.add(add_class_button, view_classes_button)

    bot.send_message(message.chat.id, "Це меню класів. Виберіть опцію:", reply_markup=markup)
    bot.register_next_step_handler(message, process_classes_option)


def process_classes_option(message):
    option = message.text

    if option == "Додати клас":
        add_class(message)
    elif option == "Переглянути класи":
        view_classes(message)
    else:
        bot.send_message(message.chat.id, "Оберіть валідну опцію.")


def add_class(message):
    bot.send_message(message.chat.id, "Введіть номер та літеру класу, наприклад, '11-А':")
    bot.register_next_step_handler(message, process_add_class)


def process_add_class(message):
    class_name = message.text
    cursor.execute('INSERT INTO classes (class_number, class_letter) VALUES (?, ?)', (class_name[:-1], class_name[-1]))
    conn.commit()

    bot.send_message(message.chat.id, f"Клас {class_name} успішно додано!", reply_markup=create_menu())


@bot.message_handler(func=lambda message: message.text == "Вчителі")
def handle_teachers_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    add_teacher_button = types.KeyboardButton("Додати вчителя")
    make_class_teacher_button = types.KeyboardButton("Назначити класним керівником")
    markup.add(add_teacher_button, make_class_teacher_button)

    bot.send_message(message.chat.id, "Це меню вчителів. Виберіть опцію:", reply_markup=markup)
    bot.register_next_step_handler(message, process_teachers_option)

def process_teachers_option(message):
    option = message.text

    if option == "Додати вчителя":
        add_teacher(message)
    elif option == "Назначити класним керівником":
        make_class_teacher(message)
    else:
        bot.send_message(message.chat.id, "Оберіть валідну опцію.")

@bot.message_handler(func=lambda message: message.text == "Додати вчителя")
def add_teacher(message):
    bot.send_message(message.chat.id, "Введіть ім'я та прізвище вчителя:")
    bot.register_next_step_handler(message, process_add_teacher)

def process_add_teacher(message):
    teacher_name = message.text

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    ''')
    conn.commit()

    cursor.execute('INSERT INTO teachers (name) VALUES (?)', (teacher_name,))
    conn.commit()

    bot.send_message(message.chat.id, f"Вчитель {teacher_name} успішно доданий!", reply_markup=create_menu())


def make_class_teacher(message):
    cursor.execute('SELECT id, name FROM teachers')
    teachers = cursor.fetchall()

    if not teachers:
        bot.send_message(message.chat.id, "У вас немає вчителів. Спочатку додайте вчителя.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for teacher_info in teachers:
        teacher_button = types.KeyboardButton(teacher_info[1])
        markup.add(teacher_button)

    bot.send_message(
        message.chat.id,
        "Виберіть вчителя, якого назначити класним керівником:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, process_selected_teacher_for_class)

def process_selected_teacher_for_class(message):
    teacher_name = message.text

    cursor.execute('SELECT id, class_number, class_letter FROM classes')
    classes = cursor.fetchall()

    if not classes:
        bot.send_message(message.chat.id, "Немає класів. Спочатку додайте клас.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for class_info in classes:
        class_button = types.KeyboardButton(f"{class_info[1]}{class_info[2]}")
        markup.add(class_button)

    bot.send_message(
        message.chat.id,
        "Виберіть клас, до якого додати обраного вчителя:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, add_class_teacher)

def add_class_teacher(message):
    teacher_name = message.text

    selected_class_name = message.text

    cursor.execute('SELECT id FROM classes WHERE class_number||class_letter=?', (selected_class_name,))
    selected_class_id = cursor.fetchone()

    if selected_class_id:
        cursor.execute('INSERT INTO class_teachers (teacher_name, class_id) VALUES (?, ?)',
                       (teacher_name, selected_class_id[0]))
        conn.commit()

        bot.send_message(message.chat.id, f"Класного керівника {teacher_name} додано до класу {selected_class_name}!", reply_markup=create_menu())
    else:
        bot.send_message(message.chat.id, "Помилка: обраний клас не знайдено. Спробуйте ще раз.")

def process_schedule_changes(message):
    new_schedule = message.text
    add_schedule_to_database(new_schedule)
    bot.send_message(message.chat.id, "Розклад уроків змінено та збережено успішно!", reply_markup=create_menu())

def view_schedule(message):
    cursor.execute('SELECT timetable FROM schedule ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()

    if result:
        schedule = result[0]
        bot.send_message(message.chat.id, f"Розклад уроків:\n{schedule}", reply_markup=create_menu())
    else:
        bot.send_message(message.chat.id, "Розклад уроків ще не збережено.")

def handle_schedule_menu(message):
    bot.send_message(message.chat.id, "Це меню розкладу уроків.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Змінити розклад")
    btn3 = types.KeyboardButton("Переглянути розклад")
    markup.add(btn1, btn3)

    bot.send_message(message.chat.id, "Виберіть опцію:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_schedule_submenu)

def handle_schedule_submenu(message):
    if message.text == "Змінити розклад":
        bot.send_message(message.chat.id, "Введіть новий розклад уроків:")
        bot.register_next_step_handler(message, process_schedule_changes)
    elif message.text == "Переглянути розклад":
        view_schedule(message)
    else:
        pass


def handle_grades_menu(message):
    bot.send_message(message.chat.id, "Це меню оцінок.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_view_grades = types.KeyboardButton("Переглянути оцінки")
    btn_enter_grades = types.KeyboardButton("Ввести оцінки")
    markup.add(btn_view_grades, btn_enter_grades)

    bot.send_message(message.chat.id, "Виберіть опцію:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_grades_submenu)

def handle_grades_submenu(message):
    if message.text == "Переглянути оцінки":
        view_grades(message)
    elif message.text == "Ввести оцінки":
        enter_grades(message)
    else:
        pass


def view_grades(message):
    cursor.execute("SELECT id, name FROM students")
    students_data = cursor.fetchall()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for student_id, student_name in students_data:
        btn_student_grades = types.KeyboardButton(f"Переглянути оцінки {student_id}")
        markup.row(btn_student_grades)

    bot.send_message(message.chat.id, "Виберіть учня для перегляду оцінок:", reply_markup=markup)
    bot.register_next_step_handler(message, process_grades_view)

def process_grades_view(message):
    student_id = message.text.split()[-1]
    cursor.execute("SELECT subject, grade FROM grades WHERE student_id=?", (student_id,))
    grades_data = cursor.fetchall()

    grades_text = (f"Оцінки для учня {student_id}:\n")
    for record in grades_data:
        subject, grade = record
        grades_text += f"Предмет: {subject}, Оцінка: {grade}\n"

    bot.send_message(message.chat.id, grades_text, reply_markup=create_menu())

@bot.message_handler(func=lambda message: True)
def handle_grades_actions(message):
    if message.text.startswith("Переглянути оцінки"):
        view_grades(message)
    elif message.text.startswith("Виставити оцінки"):
        enter_grades(message)
    else:
        pass

def enter_grades(message):
    cursor.execute("SELECT id, name FROM students")
    students_data = cursor.fetchall()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for student_id, student_name in students_data:
        btn_student_grades = types.KeyboardButton(f"Виставити оцінки {student_id}")
        markup.row(btn_student_grades)
    bot.send_message(message.chat.id, "Виберіть учня для виставлення оцінок:", reply_markup=markup)

    bot.register_next_step_handler(message, process_grades_entry)

def process_grades_entry(message):
    student_id = message.text.split()[-1]
    bot.send_message(message.chat.id, f"Введіть оцінки для учня {student_id} (формат: предмет1:оцінка1, предмет2:оцінка2, ...)")
    bot.register_next_step_handler(message, save_grades, student_id)

def save_grades(message, student_id):
    grades_input = message.text
    grade_pairs = [pair.split(":") for pair in grades_input.split(",")]
    for subject, grade in grade_pairs:
        cursor.execute("INSERT INTO grades (student_id, subject, grade) VALUES (?, ?, ?)", (student_id, subject.strip(), grade.strip()))
    conn.commit()

    bot.send_message(message.chat.id, f"Оцінки для учня {student_id} збережено успішно!", reply_markup=create_menu())
    create_menu()



if __name__ == "__main__":
    bot.infinity_polling()
#/

