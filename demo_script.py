"""Pure-data demo script. Responses are recorded outputs (currently placeholders)."""

DEMO_REPO_URL = "https://github.com/hafeza-zainab/codebuddy"

DEMO_TRACEBACK = '''Traceback (most recent call last):
  File "example.py", line 3, in <module>
    print(user_name)
NameError: name 'user_name' is not defined'''

DEMO_STEPS = [
    {
        "caption": "The intro screen is visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The sample repository URL and loaded status are visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The user asks what the project does.",
        "user_message": "What does this project do?",
        "mode": "explain",
        "hint_level": None,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The user asks how to run the project.",
        "user_message": "How do I run it?",
        "mode": "explain",
        "hint_level": None,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The NameError traceback and a response placeholder are visible in the chat.",
        "user_message": DEMO_TRACEBACK,
        "mode": "debug",
        "hint_level": None,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The sidebar shows hint level 1 and its response placeholder is visible.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 1,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The sidebar shows hint level 2 and its response placeholder is visible.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 2,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The sidebar shows hint level 3 and its response placeholder is visible.",
        "user_message": None,
        "mode": "debug",
        "hint_level": 3,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
    {
        "caption": "The closing screen is visible.",
        "user_message": None,
        "mode": None,
        "hint_level": None,
        "response": "PLACEHOLDER_REPLACE_WITH_RECORDED_OUTPUT",
    },
]
