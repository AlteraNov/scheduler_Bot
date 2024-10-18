import aiosqlite

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
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        await db.commit()

async def add_task(user_id: int, task: str, due_time: str, completed: bool = False, completed_at: str = None):
    async with aiosqlite.connect('tasks.db') as db:
        await db.execute('INSERT INTO tasks (user_id, task, due_time, completed, completed_at) VALUES (?, ?, ?, ?, ?)', 
                         (user_id, task, due_time, completed, completed_at))
        await db.commit()

async def delete_task(task_id: int):
    async with aiosqlite.connect('tasks.db') as db:
        await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        await db.commit()

async def delete_all_tasks(user_id: int):
    async with aiosqlite.connect('tasks.db') as db:
        await db.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
        await db.commit()

async def get_due_tasks(user_id: int):
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute('SELECT * FROM tasks WHERE user_id = ? AND due_time > datetime("now") AND completed = FALSE', (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_completed_tasks(user_id: int):
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute('SELECT id, task, due_time, completed_at FROM tasks WHERE user_id = ? AND completed = TRUE ORDER BY completed_at DESC', (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_active_tasks(user_id: int):
    async with aiosqlite.connect('tasks.db') as db:
        async with db.execute('SELECT id, task, due_time, completed FROM tasks WHERE user_id = ? AND completed = FALSE', (user_id,)) as cursor:
            return await cursor.fetchall()
        
#async def add_task(user_id: int, task: str, due_time: str):
    #async with aiosqlite.connect('tasks.db') as db:
        #await db.execute('INSERT INTO tasks (user_id, task, due_time) VALUES (?, ?, ?)', (user_id, task, due_time))
        #await db.commit()

#async def delete_task(task_id: int):
    #async with aiosqlite.connect('tasks.db') as db:
        #await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        #await db.commit()

#async def delete_all_tasks(user_id: int):
    #async with aiosqlite.connect('tasks.db') as db:
        #await db.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
        #await db.commit()

#async def get_due_tasks(user_id: int):
    #async with aiosqlite.connect('tasks.db') as db:
        #async with db.execute('SELECT * FROM tasks WHERE user_id = ? AND due_time > datetime("now")', (user_id,)) as cursor:
            #return await cursor.fetchall()
        