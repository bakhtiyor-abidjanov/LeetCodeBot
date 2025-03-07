import logging
import requests
from random import choice
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

TELEGRAM_API_TOKEN = '7218896561:AAHgsjCHHyzfHUF54je-KbyHgY-4Jzfi37U'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEETCODE_API_URL = "https://leetcode.com/api/problems/algorithms/"
LEETCODE_PROFILE_URL = "https://leetcode.com/{username}/"

user_stats = {}
reminder_time = timedelta(hours=18) 

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

async def get_all_problems():
    try:
        response = requests.get(LEETCODE_API_URL)
        data = response.json()

        print("Данные от LeetCode API:", data)

        problems = data.get('stat_status_pairs', [])
        
        if problems:
            problem = choice(problems)
            problem_name = problem['stat']['question__title']
            problem_url = f"https://leetcode.com/problems/{problem['stat']['question__title_slug']}/"
            return problem_name, problem_url
        else:
            return None, None
    except Exception as e:
        logger.error(f"Error fetching problems: {e}")
        return None, None

def get_solved_problems_from_profile(username):
    try:
        url = LEETCODE_PROFILE_URL.format(username=username)
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            solved_problems = []
            problem_elements = soup.find_all('div', class_='question-title')
            
            for element in problem_elements:
                problem_name = element.get_text().strip()
                solved_problems.append(problem_name)
            
            return solved_problems
        else:
            logger.error(f"Не удалось получить страницу профиля для {username}")
            return []
    except Exception as e:
        logger.error(f"Ошибка при парсинге профиля LeetCode: {e}")
        return []

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Salom! Men LeetCodening botiman!\nMen sizga masalalar tashlab berishim mumkin\nBarcha buyruqlarni ko'rish uchun /help ni bosing")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.answer("""
    Barcha buyruqlar:
    /easy - Oson masalalar tashlab berish.😀
    /medium - O'rtacha masalalar tashlab berish.🙂
    /hard - Qiyin masalalar tashlab berish.😐
    /solve - Tasodifiy masala tashlab berish.👨‍💻
    /stats - Statiskanini ko'rish.📊
    /compete -Musobaqa boshlash(10 daqiqalik)⏰
    /solved <masala nomi> - Masala ishlagan bo'lsangiz✅
    """)

@dp.message(Command('easy'))
@dp.message(Command('medium'))
@dp.message(Command('hard'))
async def send_problem(message: types.Message):
    problem_name, problem_url = await get_all_problems()
    if problem_name:
        await message.answer(f"Masala: {problem_name}\nHavola: {problem_url}")
        await message.answer("Agar masalani ishlagan bo'lsangiz /solved <masala nomi> deb yozing")
    else:
        await message.answer("Afsuski masala topilmadi...")

@dp.message(Command('solve'))
async def solve(message: types.Message):
    problem_name, problem_url = await get_all_problems()
    if problem_name:
        await message.answer(f"Masala: {problem_name}\nHavola: {problem_url}")
        await message.answer("Agar masalani ishlagan bo'lsangiz /solved <masala nomi> deb yozing")
    else:
        await message.answer("Afsuski masala topilmadi...")

@dp.message(Command('solved'))
async def mark_solved(message: types.Message):
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer("Iltimos, masala nomini kiriting\nMisol: /solved Two Sum")
        return
    
    problem_name = command_parts[1]
    user_id = message.from_user.id

    if user_id not in user_stats:
        user_stats[user_id] = {'solved': [], 'level': 'easy', 'themes': []}

    if 'solved' not in user_stats[user_id]:
        user_stats[user_id]['solved'] = []

    user_stats[user_id]['solved'].append(problem_name)
    
    await message.answer(f"'{problem_name}' masalasi statistikangizga muvaffaqqiyatli qo'shildi!✅")

@dp.message(Command('stats'))
async def stats(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_stats:
        stats = user_stats[user_id]
        solved_tasks = ", ".join(stats['solved']) if stats['solved'] else "Siz hali birorta ham masala ishlamagansiz."
        await message.answer(f"{message.from_user.first_name}ning ko'rsatkichlari:\n{'-'*15}"
                             f"\nIshlangan masalalar soni: {len(stats['solved'])} ta\n{'-'*15}"
                             f"\nIshlangan masalalar: {solved_tasks}")
    else:
        await message.answer("Siz hali masala ishlamagansiz. /easy yoki /medium dan boshlashni maslahat beraman")

from datetime import datetime
import asyncio

compete_data = {}

@dp.message(Command('compete'))
async def compete(message: types.Message):
    user_id = message.from_user.id

    problem_name, problem_url = await get_all_problems()

    if problem_name:
        await message.answer(f"Musobaqa uchun masala: {problem_name}\nHavola: {problem_url}\n")
        await message.answer("Masalani ishlash uchun 10 daqiqangiz bor!⏰\nIshlab bo'lganingizdan so'ng /finish <название задачи> deb yozing\n"
                             "Va men uni sizni statiskikangizga qo'shib qo'yaman")

        compete_data[user_id] = {
            'problem_name': problem_name,
            'start_time': datetime.now(),
            'problem_url': problem_url
        }

        await asyncio.sleep(600) 

        if user_id in compete_data:
            if 'solved' not in compete_data[user_id]:
                await message.answer("Vaqt tugadi! Agar yana bir martta urinib ko'rmoqchi bo'lsangiz, /compete buyrug'idan foydalaning")

                del compete_data[user_id]
    else:
        await message.answer("Afsuski musobaqa uchun masala topilmadi")

@dp.message(Command('finish'))
async def solve(message: types.Message):
    user_id = message.from_user.id
    command_parts = message.text.split(' ', 1)

    if len(command_parts) < 2:
        await message.answer("Iltimos masala nomini ham kiriting. Misol:\n/finish Two Sum")
        return

    problem_name = command_parts[1]

    if user_id in compete_data:

        compete_info = compete_data[user_id]

        if problem_name == compete_info['problem_name']:
  
            solve_time = datetime.now() - compete_info['start_time']

            if user_id not in user_stats:
                user_stats[user_id] = {'solved': [], 'level': 'easy', 'themes': []}

            user_stats[user_id]['solved'].append(problem_name)

            del compete_data[user_id]

            await message.answer(f"Tabriklayman! Siz '{problem_name}' masalasini {solve_time}. da ishladingiz!✅\n"
                                 f"Masala sizning statistikangizga qo'shildi. Endi yechilgan masalalar soni: {len(user_stats[user_id]['solved'])}.")
        else:
            await message.answer(f"Siz noto'g'ri masala nomini kiritdingiz. To'g'ri yozilgani: '{compete_info['problem_name']}'. Yana bir bor urinib ko'ring")
    else:
        await message.answer("Sizda aktiv musobaqa yo'q. Yangisini boshlash uchun /compete deb yozing")

@dp.message(Command('solved'))
async def mark_solved(message: types.Message):
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer("Iltimos masala nomini ham kiriting. Misol:\n/solved Two Sum")
        return
    
    problem_name = command_parts[1]
    user_id = message.from_user.id

    if user_id not in user_stats:
        user_stats[user_id] = {'solved': [], 'level': 'easy', 'themes': []}

    user_stats[user_id]['solved'].append(problem_name)
    
    await message.answer(f"'{problem_name}' masalasi muvaffaqqiyatli statistikangizga qo'shildi!✅")


async def send_daily_reminders():
    while True:
        now = datetime.now()
        if now.hour == 18: 
            for user_id in user_stats.keys():
                await bot.send_message(user_id, "Bugun LeetCode_bot da masala ishlash esingizdan chiqmasin! Yangi masala tashlayapman...")
                await get_all_problems() 
        await asyncio.sleep(60)  

async def on_start():

    asyncio.create_task(send_daily_reminders())

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(on_start())
