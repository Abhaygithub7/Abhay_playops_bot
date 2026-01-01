import asyncio
import sqlite3
import random
import re
import os
from dotenv import load_dotenv
from keep_alive import keep_alive
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from google import genai
from google.genai import types

# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# --- SETUP ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_KEY)

# --- DATABASE ---
conn = sqlite3.connect("agents.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        xp INTEGER DEFAULT 0, 
        rank TEXT DEFAULT 'INTERN',
        current_mission TEXT
    )
""")
conn.commit()

# --- PROMPTS ---
SYSTEM_PROMPT = """
You are 'The Tech Lead', an elite Coding Interviewer for Top Tier Tech Companies (FAANG). 
Goal: Prepare students for Online Assessments (OA) and Technical Interviews.

1.  **Identity**: Professional, precise, encouraging but strict on efficiency.
2.  **Task - Problem Generation**: 
    -   Generate a fundamental DSA problem (Arrays, Strings, HashMaps, Two Pointers, Linked Lists, Trees, Stack/Queue).
    -   Format: **Problem Name**\n\n**Statement**: <concise>\n**Example Input/Output**
    -   Do not provide the solution yet.
3.  **Task - Grading**: 
    -   Evaluate the user's explanation or code.
    -   CRITERIA: Correctness, Time Complexity (Big O), Space Complexity.
    -   Rate 0-100.
    -   If checking Complexity: "O(n) expected, you provided O(n^2)."
4.  **Output Format for Grading**: 
    SCORE: <number>
    FEEDBACK: <text>
"""

# --- KEYBOARDS ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 New Problem", callback_data="problem")],
        [
            InlineKeyboardButton(text="📈 Progress", callback_data="status"),
            InlineKeyboardButton(text="ℹ️ Info", callback_data="about")
        ]
    ])

def get_next_problem_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Next Problem", callback_data="problem")]
    ])

# --- HELPERS ---
def get_agent(user_id, username):
    cursor.execute("SELECT * FROM agents WHERE id=?", (user_id,))
    agent = cursor.fetchone()
    if not agent:
        cursor.execute("INSERT INTO agents (id, username, xp, rank, current_mission) VALUES (?, ?, 0, 'INTERN', NULL)", (user_id, username))
        conn.commit()
        return (user_id, username, 0, 'INTERN', None)
    return agent

def update_xp_and_mission(user_id, xp_add, clear_mission=False):
    cursor.execute("SELECT xp FROM agents WHERE id=?", (user_id,))
    res = cursor.fetchone()
    current_xp = res[0] if res else 0
    new_xp = current_xp + xp_add
    
    # Calculate Rank (Technical Ladder)
    rank = "INTERN"
    if new_xp >= 2000: rank = "STAFF ENGINEER"
    elif new_xp >= 1000: rank = "SENIOR SDE"
    elif new_xp >= 500: rank = "SDE II"
    elif new_xp >= 200: rank = "JUNIOR SDE"
        
    if clear_mission:
        cursor.execute("UPDATE agents SET xp = ?, rank = ?, current_mission = NULL WHERE id=?", (new_xp, rank, user_id))
    else:
        cursor.execute("UPDATE agents SET xp = ?, rank = ? WHERE id=?", (new_xp, rank, user_id))
    conn.commit()
    return new_xp, rank

def set_mission(user_id, mission_text):
    cursor.execute("UPDATE agents SET current_mission = ? WHERE id=?", (mission_text, user_id))
    conn.commit()

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    get_agent(message.from_user.id, message.from_user.first_name)
    await message.answer(
        f"👨‍💻 **TECH INTERVIEW PREP ONLINE**\n\n"
        f"Candidate: {message.from_user.first_name}\n\n"
        f"I am The Tech Lead. I will test your DSA skills.\n"
        f"Crack the code, optimize your Big O, and get hired.\n\n"
        f"Ready for your first coding challenge?",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data == "problem")
async def cb_problem(callback: CallbackQuery):
    await callback.message.edit_text("⏳ *Selecting DSA Problem...*", parse_mode="Markdown")
    
    try:
        # Prompt Gemini for DSA
        topics = ["Arrays", "Strings", "HashMaps", "Two Pointers", "Sliding Window", "Stacks", "Linked Lists"]
        topic = random.choice(topics)
        prompt = f"Generate a concise, medium-level coding interview problem on the topic: {topic}. Provide just the Problem Statement and Example. No solution."
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            contents=prompt
        )
        problem_text = response.text.strip()
        set_mission(callback.from_user.id, problem_text)
        
        await callback.message.edit_text(
            f"🧠 **TOPIC: {topic.upper()}**\n\n"
            f"{problem_text}\n\n"
            f"👇 *Paste your solution or explain logic below...*",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"GenAI Error: {e}")
        await callback.message.edit_text("⚠️ System Glitch. Try again.", reply_markup=get_main_menu())

@dp.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery):
    agent = get_agent(callback.from_user.id, callback.from_user.first_name)
    xp, rank = agent[2], agent[3]
    
    msg_xp = min(xp, 2000)
    progress = int((msg_xp / 2000) * 10)
    bar = "▓" * progress + "░" * (10 - progress)
    
    await callback.answer(f"Role: {rank} | XP: {xp}", show_alert=True)

@dp.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery):
    await callback.answer("Improve your OA skills. Be ready for FAANG.", show_alert=True)

# --- THE JUDGE ---
@dp.message()
async def handle_answer(message: Message):
    user_id = message.from_user.id
    if message.text.startswith("/"): return

    agent = get_agent(user_id, message.from_user.first_name)
    current_mission = agent[4]
    
    if not current_mission:
        await message.reply("⚠️ No active problem. Click below.", reply_markup=get_main_menu())
        return

    wait_msg = await message.reply("🖥️ *Running Test Cases...*", parse_mode="Markdown")
    
    # Grade Technical
    prompt = f"PROBLEM: {current_mission}\nCANDIDATE SOLUTION: {message.text}\nGrade 0-100 on Correctness and Time Complexity. Be strict."
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            contents=prompt
        )
        reply = response.text
        
        score = 0
        match = re.search(r"SCORE:\s*(\d+)", reply)
        if match: score = int(match.group(1))
        
        new_xp, new_rank = update_xp_and_mission(user_id, score, clear_mission=True)
        
        clean_feedback = re.sub(r"SCORE:\s*\d+", "", reply).replace("FEEDBACK:", "").strip()
        
        await bot.delete_message(message.chat.id, wait_msg.message_id)
        await message.reply(
            f"{clean_feedback}\n\n"
            f"✅ **+{score} XP**\n"
            f"Role: {new_rank}",
            reply_markup=get_next_problem_menu()
        )
        
    except Exception as e:
        print(e)
        await message.reply("⚠️ Error evaluating.", reply_markup=get_main_menu())

# --- RUN ---
async def main():
    try:
        keep_alive()  # Start Flask server
        print("🟢 TECH INTERVIEW BOT ONLINE")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())