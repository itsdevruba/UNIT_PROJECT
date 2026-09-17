# Rockstar Character Hub

## Overview
An interactive command-line app for fans of Rockstar Games. Browse characters from **GTA**, **Red Dead Redemption** and **Bully**, rate them on multiple criteria, build your own tier list, compare characters side by side, and take a personality quiz to find out which character you are most like.

The hub has two kinds of users: **users**, who log in with their name and keep their own ratings and quiz results, and an **admin**, who manages quiz results, users and characters behind a password.

## Features & User Stories

#### As a user I should be able to:
- Log in with my name and keep my own ratings and quiz results.
- Browse all characters and filter them by game or role.
- Search for a character by name.
- View a character's info (game, role, affiliation, bio) without story spoilers.
- Turn spoiler mode on to see full story notes.
- Rate a character from 0 to 10 on writing, growth, charisma, combat and memorability.
- Get a weighted overall score and a tier (S, A, B, C, D) calculated automatically.
- See my personal tier list.
- Compare two of my rated characters criterion by criterion.
- Choose a series and take the "Which character are you?" quiz to see my top 3 matches.
- Take an "Interview with AI" instead: a local AI model asks me 5 questions, I answer in my own words, and I get matched with a character plus a short explanation.
- See all my past quiz results.
- Reset my own ratings.

#### As an admin I should be able to:
- Log in with a password (created the first time the admin logs in).
- See all quiz results, open any of them, delete one, or delete all.
- See every user with their number of ratings and quiz results.
- View a user's tier list, delete their ratings, delete their quiz results, or delete the user completely.
- Add a new character with its quiz traits.
- Edit a character's bio, spoiler notes, affiliation, role or quiz traits.
- Delete custom characters (original characters are protected).

## Usage
1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
2. *(Optional, for the AI interview)* Install [Ollama](https://ollama.com/download), then download the model:
   ```
   ollama pull llama3.2:3b
   ```
   Everything else works without Ollama.
3. Run the app:
   ```
   python main.py
   ```
4. Use the **arrow keys** and **Enter** to choose from the menus.

#### Start menu
- **Log in as user** → type your name. Typing the same name later brings back your data.
- **Log in as admin** → opens the admin menu. Demo mode is on by default, so no password is needed. To require a password, set `DEMO_MODE = False` in `hub/config.py`; the first time, you will be asked to create one.
- **Exit** → close the app (or press `Ctrl+C`).

#### User menu
- **Browse characters** → pick a game or role to filter, then open a character.
- **Search by name** → type part of a name, e.g. `arthur`.
- **Rate a character** → choose a series and a character, then enter a score from 0 to 10 for each criterion.
- **My tier list** → see your rated characters grouped by tier.
- **Compare two characters** → pick two of your rated characters.
- **Which character are you?** → pick **Take the quiz** (8 multiple-choice questions) or **Interview with AI** (5 open questions from the AI), pick a series, and get your top 3 matches. **My results** shows your past results.
- **Settings** → turn spoiler mode on/off or reset your ratings.
- **Log out** → go back to the start menu.

#### Admin menu
- **Quiz results** → open, delete one, or delete all results.
- **Users & ratings** → open a user to view their tier list or delete their data.
- **Manage characters** → add, edit, or delete custom characters.
- **Log out** → go back to the start menu.

## Project Structure
```
UNIT_PROJECT/
├── main.py                 # start here: user / admin login
├── hub/                    # the app package
│   ├── config.py           # paths, criteria, tiers, traits, limits
│   ├── storage.py          # load/save JSON safely
│   ├── display.py          # rich tables and panels
│   ├── characters.py       # browse, filter, search, add, delete
│   ├── ratings.py          # scores, overall, tiers, compare
│   ├── quiz.py             # personality quiz algorithm
│   ├── ai.py               # AI interview with a local Ollama model
│   ├── users.py            # names, per-user ratings and quiz results
│   ├── auth.py             # admin password (hashed, never stored as plain text)
│   └── menus/
│       ├── helpers.py      # shared menu pickers
│       ├── user_menu.py    # everything a user can do
│       └── admin_menu.py   # everything the admin can do
└── data/
    ├── characters.json
    └── questions.json
```
Files created while using the app (not tracked by git): `data/user_ratings.json`, `data/quiz_results.json`, `data/admin.json`.

## Credits
Character information is summarized from the [GTA Wiki](https://gta.fandom.com), [Red Dead Wiki](https://reddead.fandom.com) and [Bully Wiki](https://bully.fandom.com) (CC BY-SA). This is an unofficial student project; all characters belong to Rockstar Games.
