import os
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
import pytz
from database import init_db, add_task, delete_task, delete_all_tasks, get_due_tasks, get_completed_tasks, get_active_tasks
from datetime import datetime
# Настройки бота
API_TOKEN = '8020507153:AAEKpXpo9lFxWyze5wfYJaTx-L2sllq99Rc'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage() # Создаем хранилище для состояний
dp = Dispatcher(bot, storage=storage) # Создаем диспетчер для обработки сообщений
# Определяем состояния для обработки различных этапов взаимодействия
class Form(StatesGroup):
    waiting_for_timezone = State() 
    waiting_for_task = State() 
    waiting_for_time = State() 
    waiting_for_task_id = State()
    waiting_for_due_time = State() 
    waiting_for_time_del =  State()

# Асинхронная функция для отправки уведомлений о задачах
async def send_due_task_notifications():
    async with aiosqlite.connect('tasks.db') as db:  
        while True: # Бесконечный цикл для периодической проверки задач
            current_time = datetime.now()
            # Выбираем задачи, которые необходимо выполнить
            async with db.execute('SELECT user_id, id, task FROM tasks WHERE due_time <= ? AND completed = FALSE', (current_time,)) as cursor:
                tasks = await cursor.fetchall()

            # Отправляем уведомления пользователям о задачах
            for user_id, task_id, task in tasks:
                await bot.send_message(user_id, f"🔔 Напоминание! Ваша задача: '{task}' должна быть выполнена.")
            await asyncio.sleep(30) 

# Создаем клавиатуру с кнопками
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_add = KeyboardButton('/add')
button_delete = KeyboardButton('/delete')
button_complete = KeyboardButton('/complete')
button_deleteall = KeyboardButton('/deleteall')
button_list = KeyboardButton('/list')
button_active = KeyboardButton('/active')
button_completed = KeyboardButton('/completed')
button_other = KeyboardButton('another')

# Добавляем кнопки на клавиатуру
keyboard.add(button_add, button_delete, button_complete, button_deleteall, button_list, button_active, button_completed, button_other)

# Обработчик команды /start и /help
@dp.message_handler(commands=['start',"help"])
async def start_command(message: types.Message):
    await message.reply("Привет! Доброе начало дня? Со мной теперь будет каждый день доброе))\n \n"
                        "Я твой личный помощник по составлению планов. Как ты уже понял, меня зовут Марвин.\n"
                        "И мой мозг запрограммирован на отслеживание задач. Уж моя современная консервнная банка ничего не забудет ;) \n \n"
                        "Так еще и тебе напомнит) \n"
                        "Кратенько о моих способностях: \n"
                        "/add для добавления задачи. \n \n"
                        "/delete для удаления задачи. \n \n"
                        "/deleteall для удаления всех задач.\n \n"
                        "/list, чтобы показать список актуальных задач. \n \n"
                        "/complete, для завершения задачи. \n \n"
                        "/active, чтобы показать активные задачи. \n \n"
                        "/completed, чтобы показать завершенные задачи. \n \n"
                        "А теперь мне нужна начальная информация, чтобы начать с тобой серьезный путь по развитию личности! Напиши, пожалуйста, свой часовой пояс в виде 'Europe/Moscow'.",
                        reply_markup=keyboard)
    await Form.waiting_for_timezone.set()

# Обработчик состояния ожидания часового пояса
@dp.message_handler(state=Form.waiting_for_timezone)
async def process_timezone(message: types.Message, state: FSMContext):
    timezone = message.text
    try:
        pytz.timezone(timezone)  # Проверка корректности часового пояса
        async with aiosqlite.connect('tasks.db') as db:
            # Вставляем пользователя в таблицу, если его еще нет
            await db.execute('INSERT OR IGNORE INTO users (username, timezone) VALUES (?, ?)', (message.from_user.username, timezone))
            await db.commit()
        await message.reply(f"Точно правильно ввел?))00)0 Часовой пояс установлен на {timezone}. Теперь введите вашу задачу.")
        await Form.waiting_for_task.set()  # Переходим к следующему состоянию - ожиданию задачи
    except pytz.UnknownTimeZoneError:
        await message.reply("Не-не, что-то не то. Попробуйте еще раз.Доступные часовые пояса России: \n"
                            "Europe/Moscow, Europe/Samara, Asia/Yekaterinburg, Asia/Omsk, \n" 
                            "Asia/Krasnoyarsk, Asia/Irkutsk, Asia/Vladivostok, Asia/Magadan, Asia/Kamchatka, Asia/Sakhalin.\n")
        
# Обработчик состояния ожидания задачи
@dp.message_handler(state=Form.waiting_for_task)
async def process_task(message: types.Message, state: FSMContext):
    task = message.text
    await message.reply("Воо, обожаю такое! Когда напомнить? \n \n"
                        "Укажите время выполнения задачи в формате 'YYYY-MM-DD HH:MM'.\n \n")
    await state.update_data(task=task)
    await Form.waiting_for_due_time.set() # Переходим к следующему состоянию - ожиданию времени выполнения

# Обработчик состояния ожидания времени выполнения задачи
@dp.message_handler(state=Form.waiting_for_due_time)
async def process_due_time(message: types.Message, state: FSMContext):
    due_time_str = message.text
    data = await state.get_data()
    task = data.get('task') 
    try:
        # Преобразование строки в объект datetime
        due_time = datetime.strptime(due_time_str, '%Y-%m-%d %H:%M')
        user_id = message.from_user.id   # Получаем ID пользователя
        async with aiosqlite.connect('tasks.db') as db:
            # Вставляем новую задачу в таблицу задач
            await db.execute('INSERT INTO tasks (user_id, task, due_time) VALUES (?, ?, ?)', (user_id, task, due_time))
            await db.commit()
        
        await message.reply(f"Задача '{task}' добавлена. Время выполнения: {due_time}.")
        await state.finish()
    except ValueError:
        await message.reply("Неверный формат даты и времени. Попробуйте еще раз.")

# Обработчик команды /add
@dp.message_handler(commands=['add'])
async def process_add_command(message: types.Message):
    await Form.waiting_for_task.set()
    await message.reply("Бегит, анжуманя и еще не забыть про") # Запрос на ввод задачи

# Обработчик команды /list для отображения всех задач
@dp.message_handler(commands=['list'])
async def list_tasks(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('tasks.db') as db: # Открываем соединение с базой данных
        async with db.execute('SELECT id, task, due_time, completed FROM tasks WHERE user_id = ?', (user_id,)) as cursor:
            tasks = await cursor.fetchall()
    if tasks:
        response = "Ваши задачи:\n"
        for task_id, task, due_time, completed in tasks:
            status = "✅ Завершено" if completed else "❌ Не завершено"
            due_time_formatted = datetime.strptime(due_time, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M')
            response += f"{task_id}. - {task} (Срок: {due_time_formatted}) {status}\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет задач.")

# Обработчик команды /complete для завершения задачи
@dp.message_handler(commands=['complete'])
async def complete_task(message: types.Message):
    await message.reply("Введите ID задачи, которую вы хотите завершить.")
    await Form.waiting_for_task_id.set() # Устанавливаем состояние ожидания ID задачи

# Обработчик состояния ожидания ID задачи для завершения
@dp.message_handler(state=Form.waiting_for_task_id)
async def process_complete_task(message: types.Message, state: FSMContext):
    task_id = message.text
    user_id = message.from_user.id
    try:
        task_id = int(task_id) # Преобразуем ID задачи в целое число
        async with aiosqlite.connect('tasks.db') as db:
            result = await db.execute('UPDATE tasks SET completed = TRUE, completed_at = ? WHERE id = ? AND user_id = ?', 
                                      (datetime.now(), task_id, user_id)) # Обновляем статус задачи
            await db.commit()
        if result.rowcount == 0:
            await message.reply("Задача с таким ID не найдена.")
        else:
            await message.reply(f"Задача #{task_id} отмечена как завершена.")
        await state.finish()
    except ValueError:
        await message.reply("Пожалуйста, введите корректный ID задачи.")

# Обработчик сообщений, когда бот ожидает ввод времени
@dp.message_handler(state=Form.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    time_str = message.text # Получаем текст сообщения, который должен содержать время
    user_id = message.from_user.id
    data = await state.get_data()
    task = data.get('task')
    try:
        due_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M') # Преобразуем строку времени в объект datetime
        await add_task(user_id, task, due_time.strftime('%Y-%m-%d %H:%M:%S'))
        await message.reply("Задача добавлена!")
    except ValueError:
        await message.reply("Неверный формат времени. Пожалуйста, попробуйте снова.")

    await state.finish()

# Обработчик команды /delete для удаления задачи
@dp.message_handler(commands=['delete'])
async def process_delete_command(message: types.Message):
    await message.reply("Теперь нам уже не нужно. Введите ID задачи, которую хотите удалить:")
    await Form.waiting_for_time_del.set()

# Обработчик состояния ожидания ID задачи для удаления
@dp.message_handler(state=Form.waiting_for_time_del)
async def process_delete_task(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text) # Преобразуем текст сообщения в целое число (ID задачи)
        await delete_task(task_id)
        await message.reply("Кыш-кыш, мы уже на другом уровне осуществления целей ;)")
    except Exception as e:
        await message.reply("Ошибка при удалении задачи. Возможно, такой задачи не существует.")

    await state.finish()

# Обработчик команды /deleteall для удаления всех задач
@dp.message_handler(commands=['deleteall'])
async def process_delete_all_command(message: types.Message):
    user_id = message.from_user.id
    await delete_all_tasks(user_id) # Удаляем все задачи для данного пользователя
    await message.reply("Все задачи удалены.")

# Обработчик команды /active для отображения активных задач
@dp.message_handler(commands=['active'])
async def list_active_tasks(message: types.Message):
    user_id = message.from_user.id
    active_tasks = await get_active_tasks(user_id) # Извлекаем активные задачи для пользователя
    if active_tasks:
        response = "Так-так... На данный момент у нас в активном:\n"
        for task_id, task, due_time, completed in active_tasks:  # Проходим по всем активным задачам
            response += f"{task_id}. - {task} (Срок: {due_time})\n" # Формируем строку для каждой задачи
        await message.reply(response)
    else:
        await message.reply("У вас нет активных задач.")

# Обработчик команды /completed для отображения завершенных задач
@dp.message_handler(commands=['completed'])
async def list_completed_tasks(message: types.Message):
    user_id = message.from_user.id
    completed_tasks = await get_completed_tasks(user_id)   # Извлекаем завершенные задачи для пользователя
    completed_tasks = completed_tasks[:10]   # Ограничиваем вывод до 10 завершенных задач
    if completed_tasks:
        response = "Ваши первые 10 завершенных задач:\n"
        for task_id, task, due_time, completed_at in completed_tasks:
            due_time_formatted = datetime.strptime(due_time, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M')
            response += f"{task_id}. - {task} (Срок: {due_time_formatted}) (Завершено: {completed_at})\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет завершенных задач.")

# Обработчик для кнопки "Другое"
@dp.message_handler(lambda message: message.text == 'another')
async def other_command(message: types.Message):
    await message.reply("А тут пока пустовато. Давайте без буллинга, я тут новенький...")

if __name__ == '__main__':
    loop = asyncio.get_event_loop() # Получаем текущий асинхронный цикл событий
    loop.run_until_complete(init_db())  # Запускаем и ждем завершения инициализации базы данных
    loop.create_task(send_due_task_notifications()) # Создаем задачу для отправки уведомлений о задачах
    executor.start_polling(dp, skip_updates=True) # Запускаем бота, пропуская все обновления, которые пришли, пока бот был отключен