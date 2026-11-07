"Demo replays sample responses recorded from live runs of this bot. Intro and closing messages are scripted."

DEMO_REPO_URL = "https://github.com/hafeza-zainab/codebuddy"

DEMO_TRACEBACK = '''Traceback (most recent call last):
  File "example.py", line 3, in <module>
    print(user_name)
NameError: name 'user_name' is not defined'''

SAMPLE_NOTE = "Demo replays sample responses recorded from live runs of this bot. Intro and closing messages are scripted."

DEMO_STEPS = [
    {
        "caption": "The intro screen and welcome message are visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "Welcome! Load a public GitHub repository to explore its code or get debugging hints.",
    },
    {
        "caption": "A scripted message says the sample repository is loaded.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "The CodeBuddy repository is loaded. Its README and file list are ready to explore.",
    },
    {
        "caption": "The user asks what the project does, and the explanation is visible.",
        "user_message": "What does this project do?",
        "mode": "explain",
        "hint_level": None,
        "response": "This project is a beginner-friendly chatbot designed to help you understand GitHub repositories and debug your code.\n\nIt provides two main features:\n*   **Repository Explanation:** You can provide a link to a public GitHub repository, and the chatbot will explain what the project does, where you should start reading the code, and how to run it.\n*   **Debugging Assistance:** If you paste an error message (a \"traceback\") into the chat, the bot acts as a tutor. Instead of just giving you the answer, it provides hints in stages, helping you learn how to fix the problem yourself.\n\n**How to run the project:**\nBased on the provided files, you can run the application using the [Streamlit](https://streamlit.io/) framework. \n\n1.  **Install dependencies:** Ensure you have Python installed, then install the required packages listed in `requirements.txt` by running:\n    `pip install -r requirements.txt`\n2.  **Configure the API key:** Copy the `.env.example` file to a new file named `.env` and add your `GEMINI_API_KEY` to it. This key allows the chatbot to generate responses using the Gemini AI model.\n3.  **Start the application:** Run the following command in your terminal:\n    `streamlit run app.py`\n\nIf you do not have an API key, you can still use the \"Run demo\" button within the app to see how it works using pre-written sample responses.",
    },
    {
        "caption": "The user asks how to run the project, and the steps are visible.",
        "user_message": "How do I run it?",
        "mode": "explain",
        "hint_level": None,
        "response": "To run this project, follow these steps:\n\n1.  **Install Python:** Ensure you have Python installed on your computer.\n2.  **Install Dependencies:** Open your terminal or command prompt, navigate to the project folder, and run the following command to install the necessary libraries:\n    `pip install -r requirements.txt`\n    *   *Note: `pip` is a tool used to install software packages written in Python.*\n3.  **Configure API Key:** Copy the `.env.example` file to a new file named `.env`. Open the `.env` file and add your own `GEMINI_API_KEY`.\n    *   *Note: An API key is a unique code that allows your application to connect to the Gemini service.*\n4.  **Start the App:** Run the following command in your terminal to start the chat interface:\n    `streamlit run app.py`\n\nIf you do not have an API key, you can still click the \"Run demo\" button in the application to see how it works using sample responses.",
    },
    {
        "caption": "The NameError traceback and a response are visible in the chat.",
        "user_message": DEMO_TRACEBACK,
        "mode": "debug",
        "hint_level": None,
        "response": "Let's work through this error one hint at a time.",
    },
    {
        "caption": "Hint level 1: a gentle nudge appears in the chat, without the fix.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 1,
        "response": "This error happens because the computer is trying to use a name that it hasn't been introduced to yet. Have you checked if you created and named this item before trying to print it?",
    },
    {
        "caption": "Hint level 2: the hint now points to the file and line.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 2,
        "response": "In `example.py` on line 3, the program is trying to use the name `user_name`, but it hasn't been created yet. A `NameError` happens when you try to use a variable that the computer doesn't recognize because it hasn't been assigned a value earlier in your code. Check if you spelled the name correctly or if you defined it before trying to print it.",
    },
    {
        "caption": "Hint level 3: a full explanation with corrected code appears.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 3,
        "response": "A `NameError` occurs when you try to use a variable name that the computer does not recognize. This usually happens because the variable has not been created yet, or because there is a spelling difference between where you defined the variable and where you are trying to use it.\n\nIn your code on line 3, you are trying to print `user_name`, but the computer has no record of a variable with that exact name. To fix this, you must define the variable before you try to print it.\n\nFor example, you need to assign a value to it first:\n\n```python\nuser_name = \"Alice\"  # You must define the variable first\nprint(user_name)     # Now the computer knows what user_name is\n```\n\nCheck to make sure that you have assigned a value to `user_name` earlier in your script and that the spelling matches exactly, including capitalization.",
    },
    {
        "caption": "The closing message is visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "Thanks for trying the CodeBuddy demo. You can now explore another public repository or paste an error to get hints.",
    },
]
