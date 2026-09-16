# Rockstar Character Hub

## Overview
An interactive command-line app for fans of Rockstar Games. Browse characters from **GTA**, **Red Dead Redemption** and **Bully**, rate them on multiple criteria, build your own tier list, compare characters side by side, and take a personality quiz to find out which character you are most like.

## Features & User Stories

#### As a user I should be able to:
- Browse all characters and filter them by game or role.
- Search for a character by name.
- View a character's info (game, role, affiliation, bio) without story spoilers.
- Turn spoiler mode on to see full story notes.
- Rate a character from 0 to 10 on writing, growth, charisma, combat and memorability.
- Get a weighted overall score and a tier (S, A, B, C, D) calculated automatically.
- Keep my ratings saved after I close the app.
- See my personal tier list.
- Compare two characters criterion by criterion.
- Choose a series (GTA, Red Dead or Bully) and take the "Which character are you?" quiz to see my top 3 matches.
- Enter my name before the quiz, so friends can take it too.
- See everyone's quiz results in one table and open any of them.

## Usage
1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
2. Run the app:
   ```
   python main.py
   ```
3. Use the **arrow keys** and **Enter** to choose from the menus:
   - **Browse characters** → pick a game or role to filter, then open a character.
   - **Search by name** → type part of a name, e.g. `arthur`.
   - **Rate a character** → choose a character and enter a score from 0 to 10 for each criterion.
   - **My tier list** → see all your rated characters grouped by tier.
   - **Compare two characters** → pick two rated characters to compare.
   - **Which character are you?** → enter a name, pick a series, answer 8 questions, and get your top 3 matches. Choose **All results** to see everyone who took it.
   - **Settings** → turn spoiler mode on/off or reset your ratings.
   - **Exit** → close the app (or press `Ctrl+C`).

## Project Structure
```
main.py          # menus and program flow
config.py        # paths, criteria, tiers, traits
storage.py       # load/save JSON
characters.py    # browse, filter, search
ratings.py       # scores, overall, tiers, compare
quiz.py          # personality quiz algorithm
display.py       # rich tables and colors
data/
  characters.json
  questions.json
```

## Credits
Character information is summarized from the [GTA Wiki](https://gta.fandom.com), [Red Dead Wiki](https://reddead.fandom.com) and [Bully Wiki](https://bully.fandom.com) (CC BY-SA). This is an unofficial student project; all characters belong to Rockstar Games.
