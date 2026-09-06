from customtkinter import *


class ConnectWindow(CTk):
    """
    Стартове вікно гри - форма підключення до сервера.
    Дає користувачу ввести ім'я, адресу хоста та порт,
    після чого зберігає ці дані в атрибутах об'єкта і закриває вікно.
    Головний файл клієнта створює цей об'єкт, чекає закриття вікна (mainloop),
    а потім читає win.name / win.host / win.port.
    """
    def __init__(self):
        super().__init__()

        # Поки користувач нічого не ввів - значення за замовчуванням None.
        # Якщо вікно закрити хрестиком, а не кнопкою, ці поля так і лишаться None
        self.name = None
        self.host = None
        self.port = None

        self.title('Agario Launcher')
        self.geometry('300x400')  # фіксований розмір вікна: 300x400 пікселів

        # Заголовок форми
        CTkLabel(self, text='Connect to server:', font=('Comic Sans MS', 20, 'bold')).pack(pady=15, padx=20, anchor='w')

        # Поле для введення імені гравця (те, що показуватиметься над гравцем в грі)
        self.name_entry = CTkEntry(self, placeholder_text='Введіть ім`я: ', height=50)
        self.name_entry.pack(padx=20, anchor='w', fill='x')

        # Поле для введення адреси сервера (наприклад "localhost" або IP)
        self.host_entry = CTkEntry(self, placeholder_text='Введіть хост: ', height=50)
        self.host_entry.pack(padx=20, pady=15, anchor='w', fill='x')

        # Поле для введення номера порту сервера
        self.port_entry = CTkEntry(self, placeholder_text='Введіть порт сервера: ', height=50)
        self.port_entry.pack(padx=20, anchor='w', fill='x')

        # Кнопка підтвердження - зчитує введені дані і закриває вікно
        CTkButton(self, text='Приєднатися', command=self.open_game, height=50).pack(pady=15, padx=20, fill='x')

    def open_game(self):
        """Викликається по натисканню кнопки 'Приєднатися'."""
        self.name = self.name_entry.get()
        self.host = self.host_entry.get()
        self.port = int(self.port_entry.get())  # конвертуємо порт у число; впаде з ValueError, якщо ввели не число
        self.destroy()  # закриваємо вікно -> завершується win.mainloop() у клієнтському коді