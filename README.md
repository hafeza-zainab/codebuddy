# CodeBuddy

CodeBuddy is a beginner-friendly coding helper that explains public GitHub repositories and guides people through debugging errors.

## The problem and who it helps

Beginners can get lost in an unfamiliar repository and stuck when an error appears. CodeBuddy is for students and first-time contributors who want a clearer place to start and helpful steps for understanding an error.

## Features

- **Explain mode:** Ask what a repository does, where to start reading, or how to run it. The answer uses its file tree, README, and selected source files.
- **Debug mode:** Choose one of three hint levels: a nudge, a file-and-line pointer, or a full explanation with corrected code.
- **Repo-aware debugging:** When a traceback points to a file in the loaded repository, CodeBuddy reads nearby lines for context.
- **Mismatch check:** If the referenced code does not match the error, the prompt tells Gemini to say so and avoid inventing an explanation.
- **Run demo:** Replay a sample conversation without a Gemini key.
- **Optional own-key field:** Enter a Gemini key in the password field for the current browser session.
- The repository loader accepts public GitHub repositories, filters common binary and generated files, and skips files over 100 KB.

## How the AI is used

Live answers use the Gemini API. The model chain is `gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, then `gemini-3.5-flash`.

For HTTP 500, 503, 429, or timeout responses, the client waits two seconds and tries the next model when one is available. A 404 skips directly to the next model; 401 and 403 stop the chain. The client allows up to four attempts, including a retry of `gemini-3.5-flash` without its low thinking setting if that setting receives HTTP 400. It shows a friendly busy or rate-limit message when those retries are exhausted.

The system prompts ask for plain beginner language. Explain mode focuses on what the project does, where to start, and how to run it when the files support that. Debug mode follows the selected hint level without skipping ahead, and uses supplied repository code to check whether the error and code match.

## Try it

Get a free Gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). After copying `.env.example` to `.env`, open `.env` and paste your key after `GEMINI_API_KEY=`. The project ignores `.env`; keep real keys out of commits and leave `.env.example` blank.

### Windows PowerShell

```powershell
git clone https://github.com/hafeza-zainab/codebuddy.git
cd codebuddy
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
streamlit run app.py
```

Make sure the file is named .env, not .env.txt. Notepad sometimes adds .txt.

In Notepad, add your key after `GEMINI_API_KEY=` and save the file.

### Unix shell

```sh
git clone https://github.com/hafeza-zainab/codebuddy.git
cd codebuddy
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
streamlit run app.py
```

In the editor, add your key after GEMINI_API_KEY= and save the file.

You can also skip the .env step: paste a key into the sidebar field after starting the app, or press Run demo, which needs no key.

## The demo

The **Run demo** button replays sample responses recorded from live runs of this bot. The intro, repo-loaded, and closing messages are scripted. The demo needs no Gemini key.

The demo has optional voice-over narration (the Play narration toggle, off by default because browser autoplay rules can make it unreliable). The nine narration clips were generated with the edge-tts library using Microsoft's en-US-JennyNeural voice, so the narration is AI-generated. The generator is tools/generate_narration.py and the clips are in assets/audio/. The demo video includes the same voice-over.

## Example session

**Explain question:** What does this project do?

This project is a beginner-friendly chatbot designed to help you understand GitHub repositories and debug your code.

It provides two main features:
*   **Repository Explanation:** You can provide a link to a public GitHub repository, and the chatbot will explain what the project does, where you should start reading the code, and how to run it.
*   **Debugging Assistance:** If you paste an error message (a "traceback") into the chat, the bot acts as a tutor. Instead of just giving you the answer, it provides hints in stages, helping you learn how to fix the problem yourself.

(Shortened; the Run demo button shows the full answer.)

**Debug example:** The demo uses this `NameError` traceback at each hint level:

The traceback's `example.py` name is part of the sample text; it is not a file in this repository.

```text
Traceback (most recent call last):
  File "example.py", line 3, in <module>
    print(user_name)
NameError: name 'user_name' is not defined
```

**Hint level 1:**

This error happens because the computer is trying to use a name that it hasn't been introduced to yet. Have you checked if you created and named this item before trying to print it?

**Hint level 2:**

In `example.py` on line 3, the program is trying to use the name `user_name`, but it hasn't been created yet. A `NameError` happens when you try to use a variable that the computer doesn't recognize because it hasn't been assigned a value earlier in your code. Check if you spelled the name correctly or if you defined it before trying to print it.

**Hint level 3:**

A `NameError` occurs when you try to use a variable name that the computer does not recognize. This usually happens because the variable has not been created yet, or because there is a spelling difference between where you defined the variable and where you are trying to use it.

In your code on line 3, you are trying to print `user_name`, but the computer has no record of a variable with that exact name. To fix this, you must define the variable before you try to print it.

For example, you need to assign a value to it first:

```python
user_name = "Alice"  # You must define the variable first
print(user_name)     # Now the computer knows what user_name is
```

Check to make sure that you have assigned a value to `user_name` earlier in your script and that the spelling matches exactly, including capitalization.

## Limitations

- Only public GitHub repositories are supported.
- Branch names containing slashes are not supported in repository URLs.
- GitHub may mark a very large repository's recursive file tree as truncated; CodeBuddy then reports that it is too large to load fully.
- Live mode depends on Gemini availability and free-tier capacity. It may show a busy or rate-limit message.
- AI hints can be wrong. Check suggestions against your code and the full error.

## Built with

Python, Streamlit, the GitHub REST API, and the Gemini API.

## Hackathon disclosure

This project was built for **Build Your First AI App 2026** and work started after October 27, 2026. Codex was used for coding assistance; Gemini powers the app. edge-tts was used once to generate narration audio. Streamlit, python-dotenv, and the GitHub API are used under their own terms.

## Live demo and demo video

Live demo: LIVE_DEMO_URL_TO_ADD

Demo video: VIDEO_URL_TO_ADD

## What I learned

WHAT_I_LEARNED_TO_ADD
