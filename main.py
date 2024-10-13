import logging
from datetime import datetime, timedelta
from dateutil.parser import parse
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения задач пользователей
user_tasks = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой бот для управления задачами. Введи /help для получения помощи.")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/new_task <задача> - Создать новую задачу\n"
        "/list_tasks - Список всех задач\n"
        "/done <номер задачи> - Отметить задачу как выполненную\n"
        "/delete <номер задачи> - Удалить задачу\n"
    )
    await update.message.reply_text(help_text)

# Команда для создания задач
async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_tasks:
        user_tasks[user_id] = []

    task_text = ' '.join(context.args)
    if not task_text:
        await update.message.reply_text("Пожалуйста, введите текст задачи.")
        return

    # Добавление задачи с текущим временем
    task = {
        'text': task_text,
        'created_at': datetime.now(),
        'completed': False
    }
    user_tasks[user_id].append(task)
    await update.message.reply_text(f"Задача добавлена: {task_text}")
# Команда для отображения списка задач
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await update.message.reply_text("У вас нет задач.")
        return

    message = "Ваши задачи:\n"
    for i, task in enumerate(tasks, start=1):
        status = "✅" if task['done'] else "❌"
        message += f"{i}. {status} {task['text']} (Добавлено: {task['timestamp'].strftime('%Y-%m-%d %H:%M')})\n"

    await update.message.reply_text(message)

# Команда для отображения задач
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await update.message.reply_text("У вас нет активных задач.")
        return

    tasks_list = "\n".join([f"{i+1}. {task['text']} - {'Выполнена' if task['completed'] else 'Активна'}" for i, task in enumerate(tasks)])
    await update.message.reply_text(f"Ваши задачи:\n{tasks_list}")

# Команда для отметки задачи как выполненной
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    task_index = int(context.args[0]) - 1
    tasks = user_tasks.get(user_id, [])
    
    if 0 <= task_index < len(tasks):
        tasks[task_index]['completed'] = True
        await update.message.reply_text(f"Задача выполнена: {tasks[task_index]['text']}")
        if len([t for t in tasks if t['completed']]) >= 5:
            completed_tasks = [i for i, t in enumerate(tasks) if t['completed']]
            for i in completed_tasks[:5]:
                del tasks[i]  # Удаляем выполненные задачи если их больше 5
    else:
        await update.message.reply_text("Задача не найдена.")
# Команда для удаления задачи
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        task_index = int(context.args[0]) - 1
        if user_id in user_tasks and 0 <= task_index < len(user_tasks[user_id]):
            deleted_task = user_tasks[user_id].pop(task_index)
            await update.message.reply_text(f"Задача удалена: {deleted_task['text']}")
        else:
            await update.message.reply_text("Задача не найдена.")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите номер задачи правильно.")
# Основная функция
def main():
    application = ApplicationBuilder().token('8020507153:AAEKpXpo9lFxWyze5wfYJaTx-L2sllq99Rc').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new_task", new_task))
    application.add_handler(CommandHandler("list_tasks", list_tasks))
    application.add_handler(CommandHandler("done", done_task))

    application.run_polling()

if __name__ == '__main__':
    main()