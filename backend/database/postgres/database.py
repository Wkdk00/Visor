# Позже будет заменён на PostgreSQL + Alembic

import sqlite3

connection = sqlite3.connect('Employee.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, post TEXT NOT NULL)''')
connection.commit()

try:
    cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', 
                   (1, 'Астанин Георгий Константинович', 'УЧАСТНИК'))
    cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', 
                   (2, 'Иванов Иван Иванович', 'УЧАСТНИК'))
    cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', 
                   (3, 'Андреев Андрей Андреевич', 'УЧАСТНИК'))
    cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', 
                   (4, 'Петров Петр Петрович', 'ЭКСПЕРТ'))
    connection.commit()
except: 
    pass