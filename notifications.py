import asyncio
from datetime import datetime
from database import get_due_tasks  
from bot import bot  
import aiosqlite

# Асинхронная функция для отправки уведомлений о задачах
async def send_due_task_notifications():
    async with aiosqlite.connect('tasks.db') as db:
        while True:  # Бесконечный цикл для периодической проверки задач
            current_time = datetime.now()
            # Выбираем задачи, которые необходимо выполнить
            async with db.execute('SELECT user_id, id, task FROM tasks WHERE due_time <= ? AND completed = FALSE', (current_time,)) as cursor:
                tasks = await cursor.fetchall()

            # Отправляем уведомления пользователям о задачах
            for user_id, task_id, task in tasks:
                await bot.send_message(user_id, f"🔔 Ваша задача: '{task}' должна быть выполнена.")
            await asyncio.sleep(20)  # Ждет 20 секунд, после проверяет базу данных