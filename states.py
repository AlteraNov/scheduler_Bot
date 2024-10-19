from aiogram.dispatcher.filters.state import State, StatesGroup

# Определяем состояния для обработки различных этапов взаимодействия
class Form(StatesGroup):
    waiting_for_timezone = State() 
    waiting_for_task = State() 
    waiting_for_time = State() 
    waiting_for_task_id = State()
    waiting_for_due_time = State() 
    waiting_for_time_del = State()