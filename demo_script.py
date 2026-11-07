"""Pure-data demo script with sample responses written by hand, not live AI output."""

DEMO_REPO_URL = "https://github.com/hafeza-zainab/codebuddy"

DEMO_TRACEBACK = '''Traceback (most recent call last):
  File "example.py", line 3, in <module>
    print(user_name)
NameError: name 'user_name' is not defined'''

SAMPLE_NOTE = "Demo uses sample responses written by hand, not live AI output."

DEMO_STEPS = [
    {
        "caption": "The intro screen and welcome message are visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "Welcome! Load a public GitHub repository to explore its code or get debugging hints.",
    },
    {
        "caption": "The sample repository URL and loaded status are visible.",
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
        "response": "CodeBuddy is a beginner-friendly helper for reading and debugging code. Give it a link to a public GitHub repository and it can do two things: explain what the project does and where to start reading, and help you fix an error by giving hints in stages instead of handing you the answer straight away.\n\nThe main files are:\n- app.py: the chat screen\n- repo_loader.py: fetches the repository's file list and README from GitHub\n- explain_mode.py: answers questions about the repository\n- debug_mode.py: turns an error message into step-by-step hints",
    },
    {
        "caption": "The user asks how to run the project, and the steps are visible.",
        "user_message": "How do I run it?",
        "mode": "explain",
        "hint_level": None,
        "response": "1. Install Python and download the project.\n2. Create a virtual environment and run: pip install -r requirements.txt\n3. For live answers, copy .env.example to .env and add your own GEMINI_API_KEY.\n4. Start the app with: streamlit run app.py\n\nWithout a key, the Run demo button still works because it uses sample responses.",
    },
    {
        "caption": "The NameError traceback and a response are visible in the chat.",
        "user_message": DEMO_TRACEBACK,
        "mode": "debug",
        "hint_level": None,
        "response": "Let's work through this error one hint at a time.",
    },
    {
        "caption": "The sidebar shows hint level 1 and a nudge is visible in the chat.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 1,
        "response": "This is a name error: Python reaches a name it does not recognize. Look for where that name is first used.",
    },
    {
        "caption": "The sidebar shows hint level 2 and a line-specific hint is visible in the chat.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 2,
        "response": "In example.py at line 3, check the name used in print(user_name). Look earlier in the code to see whether that name has been defined before it is used.",
    },
    {
        "caption": "The sidebar shows hint level 3 and an explanation with corrected code is visible in the chat.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 3,
        "response": "A NameError means Python reached a name it does not know. Here, user_name is printed on line 3, but it was never given a value first. Define it before printing it:\n\n```python\nuser_name = \"Ada\"\nprint(user_name)\n```",
    },
    {
        "caption": "The closing message is visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "Thanks for trying the CodeBuddy demo. You can now explore another public repository or paste an error to get hints.",
    },
]
