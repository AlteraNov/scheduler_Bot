from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаем клавиатуру с кнопками
def create_keyboard():
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
    return keyboard