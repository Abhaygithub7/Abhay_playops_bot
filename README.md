# The PlayOps Recruiter (Tech Interview Prep Bot)

A Telegram Bot powered by Google's Gemini 2.5 Flash that acts as an elite **Tech Interviewer**. It helps students and developers prepare for Online Assessments (OA) and Technical Interviews at top tech companies.

## 🚀 Features

*   **Mock Technical Interviews**: Generates random medium-level DSA problems (Arrays, Trees, HashMaps, Two Pointers, etc.).
*   **AI Grading**: Evaluates your solution based on **Correctness**, **Time Complexity (Big O)**, and **Space Complexity**.
*   **Ranking System**: Level up from **Intern** to **Staff Engineer** by solving problems efficiently.
*   **Interactive UI**: Clean, inline button interface for a professional app-like experience.

## 🛠️ Tech Stack

*   **Python 3.10+**
*   **Aiogram 3.x**: Asynchronous Telegram Bot API framework.
*   **Google Gemini 2.5 Flash**: State-of-the-art AI model for generating problems and grading code.
*   **SQLite**: Lightweight database for tracking user progress.

## ⚙️ Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Abhaygithub7/Abhay_playops_bot.git
    cd Abhay_playops_bot
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**
    Create a `.env` file in the root directory and add your keys:
    ```env
    BOT_TOKEN=your_telegram_bot_token
    GEMINI_KEY=your_gemini_api_key
    ```

4.  **Run the Bot**
    ```bash
    python bot.py
    ```

## 🎮 Usage

1.  Start the bot with `/start`.
2.  Click **💻 New Problem** to get a DSA challenge.
3.  Reply with your code or logic explanation.
4.  Get instant feedback on your Big O complexity and correctness!

## 📜 License

MIT
