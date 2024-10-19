from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN

bot = Bot(token=API_TOKEN)
storage = MemoryStorage() # Создаем хранилище для состояний
dp = Dispatcher(bot, storage=storage) # Создаем диспетчер для обработки сообщений
