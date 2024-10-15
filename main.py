import os
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from datetime import datetime, timedelta
import pytz
from database import init_db, add_task, delete_task, delete_all_tasks, get_due_tasks
from datetime import datetime
# Настройки бота
API_TOKEN = '8020507153:AAEKpXpo9lFxWyze5wfYJaTx-L2sllq99Rc'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# States
class Form(StatesGroup):
    waiting_for_timezone = State()
    waiting_for_task = State()
    waiting_for_time = State()
    waiting_for_task_id = State()
    waiting_for_due_time = State()
    waiting_for_time_del =  State()

async def init_db():
    async with aiosqlite.connect('tasks.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                timezone TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task TEXT NOT NULL,
                due_time DATETIME NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        await db.commit()
async def send_due_task_notifications():
    async with aiosqlite.connect('tasks.db') as db:  # Open the connection once
        while True:
            current_time = datetime.now()
            async with db.execute('SELECT user_id, id, task FROM tasks WHERE due_time <= ? AND completed = FALSE', (current_time,)) as cursor:
                tasks = await cursor.fetchall()

            for user_id, task_id, task in tasks:
                await bot.send_message(user_id, f"🔔 Напоминание! Ваша задача: '{task}' должна быть выполнена.")
            await asyncio.sleep(30)  # Check every minute
@dp.message_handler(commands=['start',"help"])
async def start_command(message: types.Message):
    await message.reply("Привет! Я бот для планирования задач.\n \n"
                        "/add для добавления задачи. \n \n"
                        "/delete для удаления задачи. \n \n"
                        "/deleteall для удаления всех задач.\n \n"
                        "/list, чтобы показать список актуальных задач. \n \n"
                        "/complete, для завершения задачи. \n \n"
                        "Пожалуйста, укажите ваш часовой пояс (например, 'Europe/Moscow').")
    await Form.waiting_for_timezone.set()

@dp.message_handler(state=Form.waiting_for_timezone)
async def process_timezone(message: types.Message, state: FSMContext):
    timezone = message.text
    try:
        pytz.timezone(timezone)  # Проверка корректности часового пояса
        async with aiosqlite.connect('tasks.db') as db:
            await db.execute('INSERT OR IGNORE INTO users (username, timezone) VALUES (?, ?)', (message.from_user.username, timezone))
            await db.commit()
        await message.reply(f"Часовой пояс установлен на {timezone}. Теперь вы можете добавлять задачи. Введите вашу задачу.")
        await Form.waiting_for_task.set()
    except pytz.UnknownTimeZoneError:
        await message.reply("Неверный часовой пояс. Попробуйте еще раз.")

@dp.message_handler(state=Form.waiting_for_task)
async def process_task(message: types.Message, state: FSMContext):
    task = message.text
    await message.reply("Укажите время выполнения задачи в формате 'YYYY-MM-DD HH:MM'.")
    await state.update_data(task=task)
    await Form.waiting_for_due_time.set()

@dp.message_handler(state=Form.waiting_for_due_time)
async def process_due_time(message: types.Message, state: FSMContext):
    due_time_str = message.text
    data = await state.get_data()
    task = data.get('task') 
    try:
        # Преобразование строки в объект datetime
        due_time = datetime.strptime(due_time_str, '%Y-%m-%d %H:%M')
        user_id = message.from_user.id  
        async with aiosqlite.connect('tasks.db') as db:
            await db.execute('INSERT INTO tasks (user_id, task, due_time) VALUES (?, ?, ?)', (user_id, task, due_time))
            await db.commit()
        
        await message.reply(f"Задача '{task}' добавлена. Время выполнения: {due_time}.")
        await state.finish()
    except ValueError:
        await message.reply("Неверный формат даты и времени. Попробуйте еще раз.")

@dp.message_handler(commands=['add'])
async def process_add_command(message: types.Message):
    await Form.waiting_for_task.set()
    await message.reply("Введите текст задачи:")


@dp.message_handler(commands=['list'])
async def list_tasks(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute('SELECT id, task, due_time, completed FROM tasks WHERE user_id = ?', (user_id,)) as cursor:
            tasks = await cursor.fetchall() 
    if tasks:
        response = "Ваши задачи:\n"
        for task_id, task, due_time, completed in tasks:
            status = "✅ Завершено" if completed else "❌ Не завершено"
            response += f"{task_id}. - {task} (Срок: {due_time}) {status}\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет задач.")

@dp.message_handler(commands=['complete'])
async def complete_task(message: types.Message):
    await message.reply("Введите ID задачи, которую вы хотите завершить.")
    await Form.waiting_for_task_id.set()

@dp.message_handler(state=Form.waiting_for_task_id)
async def process_complete_task(message: types.Message, state: FSMContext):
    task_id = message.text
    user_id = message.from_user.id
    try:
        task_id = int(task_id)
        async with aiosqlite.connect('tasks.db') as db:
            result = await db.execute('UPDATE tasks SET completed = TRUE WHERE id = ? AND user_id = ?', (task_id, user_id))
            await db.commit()
            if result.rowcount == 0:
                await message.reply("Задача с таким ID не найдена.")
            else:
                await message.reply(f"Задача #{task_id} отмечена как завершена.")
        await state.finish()
    except ValueError:
        await message.reply("Пожалуйста, введите корректный ID задачи.")

@dp.message_handler(state=Form.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    time_str = message.text
    user_id = message.from_user.id
    data = await state.get_data()
    task = data.get('task')
    try:
        due_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        await add_task(user_id, task, due_time.strftime('%Y-%m-%d %H:%M:%S'))
        await message.reply("Задача добавлена!")
    except ValueError:
        await message.reply("Неверный формат времени. Пожалуйста, попробуйте снова.")

    await state.finish()
@dp.message_handler(commands=['delete'])
async def process_delete_command(message: types.Message):
    await message.reply("Введите ID задачи, которую хотите удалить:")
    await Form.waiting_for_time_del.set()
@dp.message_handler(state=Form.waiting_for_time_del)
async def process_delete_task(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text)
        await delete_task(task_id)
        await message.reply("Задача удалена.")
    except Exception as e:
        await message.reply("Ошибка при удалении задачи. Возможно, такой задачи не существует.")

    await state.finish()

@dp.message_handler(commands=['deleteall'])
async def process_delete_all_command(message: types.Message):
    user_id = message.from_user.id
    await delete_all_tasks(user_id)
    await message.reply("Все задачи удалены.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.create_task(send_due_task_notifications())
    executor.start_polling(dp, skip_updates=True)