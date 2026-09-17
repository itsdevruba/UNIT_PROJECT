"""AI interview with a local Ollama model.

How it works:
1. One call writes 5 open questions at once, one for each quiz trait.
   Each question is checked; an unclear one is swapped for our example question.
2. The user answers them in their own words (no waiting between questions).
3. Each answer gets its own tiny call: the model only picks "low", "medium" or "high"
   for that one trait. A small model is much more reliable at this than scoring
   everything at once.
4. Our code turns the levels into numbers and writes the summary, so the summary
   always agrees with the scores.
5. Our own quiz algorithm (quiz.best_matches) picks the characters,
   so the result is always a real character from our data.
"""

import json
from datetime import datetime

import questionary

from hub import display, quiz
from hub.config import OLLAMA_MODEL, TRAITS

try:
    import ollama
except ImportError:  # the rest of the app still works without the library
    ollama = None

KEEP_MODEL_LOADED = "10m"  # keep the model in memory so the next interview starts faster

SERIES_WORLDS = {
    "GTA": "modern city crime: heists, gangs, cops, cars and big money",
    "Red Dead": "the Wild West around 1900: outlaw gangs, lawmen, horses and survival",
    "Bully": "a tough boarding school: cliques, pranks, bullies and strict teachers",
}

# What each trait question should reveal (used when writing the questions).
TRAIT_TOPICS = {
    "loyalty": (
        "A friend or your crew needs you, and betraying them would help YOU. "
        "Would you stand by them?"
    ),
    "morality": (
        "YOU get a chance to do something wrong (steal, cheat, lie) that would help you. "
        "Would you do it?"
    ),
    "temper": "How fast do you get angry or violent?",
    "humor": "Do you joke and enjoy fun, or stay serious?",
    "ambition": "How much do you want money, power and status?",
}

# How to judge one answer for one trait (used when scoring).
TRAIT_LEVELS = {
    "loyalty": {
        "low": "betrays, abandons, tells on, sells out or leaves their friends or crew",
        "medium": "unclear, avoids the question, or only looks after themselves",
        "high": "defends, protects, helps or refuses to betray their friends or crew",
    },
    "morality": {
        "low": "steals, cheats, lies, hurts innocent people or breaks the rules for gain",
        "medium": "unclear, or does something neither good nor bad",
        "high": "refuses to do wrong, helps others, returns things or reports a crime",
    },
    "temper": {
        "low": "stays calm, ignores it, walks away or talks it out",
        "medium": "a little annoyed but stays in control",
        "high": "gets mad, yells, fights, threatens or shoots",
    },
    "humor": {
        "low": "gets embarrassed, angry, cold or upset",
        "medium": "a practical or neutral reaction, like cleaning up or getting back up",
        "high": "laughs, makes a joke or plays along",
    },
    "ambition": {
        "low": "says no, prefers a simple or quiet life",
        "medium": "unclear, or takes a small safe step",
        "high": "takes the chance, wants to lead, get rich or get more power",
    },
}

LEVEL_SCORES = {"low": 2.0, "medium": 5.0, "high": 8.0}

# Short phrases our code uses to write the summary.
SUMMARY_PHRASES = {
    "loyalty": {"high": "stand by your friends", "low": "look out for yourself first"},
    "morality": {"high": "stick to your principles", "low": "break the rules when it pays"},
    "temper": {"high": "lose your temper fast", "low": "keep a cool head"},
    "humor": {"high": "can laugh at yourself", "low": "take things seriously"},
    "ambition": {"high": "want more out of life", "low": "are happy with a simple life"},
}

# One clear example question per trait for each series.
# The model sees them as a style guide, and we use them instead of any unclear generated question.
EXAMPLE_QUESTIONS = {
    "GTA": {
        "loyalty": (
            "Your partner gets arrested after a job and the cops offer you a deal to testify "
            "against him. What do you do?"
        ),
        "morality": (
            "You find a wallet with $5,000 and the owner's ID inside. What do you do with it?"
        ),
        "temper": ("A stranger scratches your car on purpose and laughs at you. How do you react?"),
        "humor": (
            "Your heist plan goes wrong and your whole crew ends up soaked in a fountain. How"
            " do you react?"
        ),
        "ambition": (
            "A crime boss offers you a dangerous job that could make you a millionaire. What "
            "do you do?"
        ),
    },
    "Red Dead": {
        "loyalty": (
            "The sheriff offers you a pardon if you tell him where your gang is hiding. What "
            "do you do?"
        ),
        "morality": (
            "You could rob a poor family's farm to feed your hungry gang. What do you do?"
        ),
        "temper": (
            "A drunk man in the saloon spills whiskey on you and calls you a coward. How do "
            "you react?"
        ),
        "humor": (
            "Your horse throws you into the mud right in front of the whole camp. How do you react?"
        ),
        "ambition": (
            "You hear about a train carrying enough gold to set you up for life. What do you do?"
        ),
    },
    "Bully": {
        "loyalty": (
            "Your best friend gets blamed for a prank you pulled, and the principal asks you "
            "what happened. What do you do?"
        ),
        "morality": (
            "You find the answers to tomorrow's big exam on a teacher's desk. What do you do?"
        ),
        "temper": (
            "An older student shoves you into a locker in front of everyone. How do you react?"
        ),
        "humor": (
            "You slip on a banana peel in the cafeteria and the whole school sees it. How do "
            "you react?"
        ),
        "ambition": (
            "You get the chance to become the leader of the most powerful clique in school. "
            "What do you do?"
        ),
    },
}

# Some traits are about feelings, so their question must ask how the player reacts.
REQUIRED_ENDINGS = {
    "temper": "How do you react?",
    "humor": "How do you react?",
}
# The humor situation should be funny or embarrassing, not just a problem to solve.
HUMOR_WORDS = {
    "laugh",
    "laughs",
    "laughing",
    "embarrass",
    "embarrassing",
    "embarrassed",
    "funny",
    "joke",
    "jokes",
    "prank",
    "pranks",
    "silly",
    "trip",
    "trips",
    "slip",
    "slips",
    "falls",
    "fall",
    "mud",
    "everyone",
    "whole",
    "front",
}

AMBIGUOUS_WORDS = {"they", "them", "their", "theirs", "someone's"}

QUESTIONS_SCHEMA = {
    "type": "object",
    "properties": {trait: {"type": "string"} for trait in TRAITS},
    "required": TRAITS,
}

LEVEL_SCHEMA = {
    "type": "object",
    "properties": {"level": {"type": "string", "enum": list(LEVEL_SCORES)}},
    "required": ["level"],
}


def chat_json(
    messages: list[dict], schema: dict, max_tokens: int, temperature: float
) -> dict | None:
    """Ask the model for JSON that follows `schema`. Returns the parsed dict, or None on failure."""
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            format=schema,
            options={"temperature": temperature, "num_predict": max_tokens},
            keep_alive=KEEP_MODEL_LOADED,
        )
        return json.loads(response["message"]["content"])
    except ollama.ResponseError as error:
        display.error(f"Ollama error: {error.error}")
    except (ConnectionError, OSError):
        display.error("Can't reach Ollama. Make sure the Ollama app is running.")
    except json.JSONDecodeError:
        display.warning("The AI's reply wasn't in the right format.")
    return None


def is_available() -> bool:
    """True if the ollama library is installed, Ollama is running, and the model is downloaded."""
    if ollama is None:
        display.error("The 'ollama' Python library is not installed. Run: pip install ollama")
        return False
    try:
        ollama.show(OLLAMA_MODEL)
        return True
    except ollama.ResponseError:
        display.error(
            f"The model '{OLLAMA_MODEL}' is not downloaded. Run: ollama pull {OLLAMA_MODEL}"
        )
    except (ConnectionError, OSError):
        display.error("Can't reach Ollama. Make sure the Ollama app is running.")
    return False


def clean_text(text: str) -> str:
    """Trim spaces and quotes the model sometimes adds around a sentence."""
    return " ".join(str(text).split()).strip("\"'* ")


def is_clear_question(question: str, trait: str) -> bool:
    """Simple checks that catch most confusing or off-topic questions from a small model."""
    words = [word.strip(".,!?;:'\"").lower() for word in question.split()]
    clear = (
        question.endswith("?")
        and 8 <= len(words) <= 30
        and ("you" in words or "your" in words)
        and not AMBIGUOUS_WORDS.intersection(words)  # "refuses to testify against them" -> who?
        and " or " not in question.lower()  # we want open questions, not "A or B"
    )
    if trait in REQUIRED_ENDINGS and not question.endswith(REQUIRED_ENDINGS[trait]):
        return False
    if trait == "humor" and not HUMOR_WORDS.intersection(words):
        return False
    return clear


def generate_questions(series: str) -> dict[str, str]:
    """One call: write one clear question per trait. Unclear ones are replaced with our example."""
    examples = EXAMPLE_QUESTIONS[series]
    guide = "\n".join(
        f'- {trait}: {TRAIT_TOPICS[trait]}  Example: "{examples[trait]}"' for trait in TRAITS
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You write short, clear personality quiz questions in simple English. "
                "Reply with JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Write 5 NEW questions for a personality quiz set in {SERIES_WORLDS[series]}.\n"
                f"One question for each trait. Here is what each trait means, "
                f"with an example of a good question:\n"
                f"{guide}\n\n"
                f"Rules for every question:\n"
                f"1. Talk directly to the player using 'you' and 'your'.\n"
                "2. Describe ONE simple situation. End the loyalty, morality and ambition "
                "questions with 'What do you do?'. End the temper and humor questions with "
                "'How do you react?'.\n"
                "3. The humor question must be a funny or embarrassing moment "
                "(for example you slip, fall in the mud, or everyone laughs at you).\n"
                "4. In the loyalty and morality questions, the choice must be YOURS: "
                "you decide whether to betray someone or do something wrong. "
                "Do not make the question about someone else doing wrong.\n"
                f"5. Do not use the words 'they', 'them' or 'their'. "
                f"Name the person instead (a friend, the sheriff, a teacher).\n"
                f"6. No 'A or B' choices. One or two short sentences, under 25 words.\n"
                f"7. Do not copy the examples, and never mention game or character names."
            ),
        },
    ]

    with display.console.status("[dim]The AI is writing your questions...[/dim]"):
        data = chat_json(messages, QUESTIONS_SCHEMA, max_tokens=350, temperature=0.8) or {}

    questions = {}
    replaced = 0
    for trait in TRAITS:
        question = clean_text(data.get(trait, ""))
        if not is_clear_question(question, trait):
            question = examples[trait]
            replaced += 1
        questions[trait] = question

    if replaced == len(TRAITS):
        display.warning("The AI's questions weren't clear, so you'll get our standard questions.")
    return questions


def ask_answers(questions: dict[str, str]) -> dict[str, str] | None:
    """Show each question and collect the user's answer. None if they press Ctrl+C."""
    answers = {}
    for number, trait in enumerate(TRAITS, start=1):
        display.console.print(
            f"\n[bold yellow]({number}/{len(TRAITS)})[/bold yellow] {questions[trait]}"
        )
        while True:
            answer = questionary.text("Your answer:").ask()
            if answer is None:
                return None
            if answer.strip():
                answers[trait] = answer.strip()
                break
            display.error("Please type an answer.")
    return answers


def classify_answer(trait: str, question: str, answer: str, attempts: int = 2) -> str | None:
    """One tiny call: is this answer low, medium or high for this trait?"""
    levels = TRAIT_LEVELS[trait]
    messages = [
        {"role": "system", "content": "You judge one quiz answer. Reply with JSON only."},
        {
            "role": "user",
            "content": (
                f"Question: {question}\n"
                f"Answer: {answer}\n\n"
                f"How much {trait.upper()} does this answer show?\n"
                f"- low: {levels['low']}\n"
                f"- medium: {levels['medium']}\n"
                f"- high: {levels['high']}\n\n"
                f"Judge only {trait}.\n"
                f"Choose low or high ONLY if the answer clearly matches that description. "
                f"If the answer is short, neutral, unclear or mixed (for example 'normal', "
                f"'nothing', 'I don't know'), choose medium."
            ),
        },
    ]
    for _ in range(attempts):
        data = chat_json(messages, LEVEL_SCHEMA, max_tokens=20, temperature=0)
        if data and data.get("level") in LEVEL_SCORES:
            return data["level"]
    return None


def write_summary(levels: dict[str, str]) -> str:
    """Build the summary from the high and low traits, so it always matches the scores."""
    phrases = [
        SUMMARY_PHRASES[trait][level] for trait, level in levels.items() if level != "medium"
    ]
    if not phrases:
        return "You're balanced: nothing pushes you too far in any direction."
    if len(phrases) == 1:
        return f"You {phrases[0]}."
    return f"You {', '.join(phrases[:-1])} and {phrases[-1]}."


def score_answers(questions: dict[str, str], answers: dict[str, str]) -> dict | None:
    """Judge each answer on its own trait, then turn the levels into scores and a summary."""
    levels = {}
    for number, trait in enumerate(TRAITS, start=1):
        with display.console.status(f"[dim]Reading your answers ({number}/{len(TRAITS)})...[/dim]"):
            level = classify_answer(trait, questions[trait], answers[trait])
        if level is None:
            return None
        levels[trait] = level

    return {
        "traits": {trait: LEVEL_SCORES[level] for trait, level in levels.items()},
        "summary": write_summary(levels),
    }


def take_ai_interview(characters: list[dict], series: str, player: str) -> dict | None:
    """Full AI flow. Returns a result record like quiz.take_quiz, or None if it didn't work."""
    if not characters:
        display.warning(f"No characters found for {series}.")
        return None
    if not is_available():
        return None

    questions = generate_questions(series)

    display.console.print(
        f"[dim]Answer the {len(TRAITS)} questions in your own words. Press Ctrl+C to stop.[/dim]"
    )
    answers = ask_answers(questions)
    if answers is None:
        return None

    scored = score_answers(questions, answers)
    if scored is None:
        display.error("The AI couldn't score your answers.")
        return None

    return {
        "player": player,
        "series": series,
        "mode": "AI",
        "traits": scored["traits"],
        "matches": quiz.best_matches(scored["traits"], characters),
        "reason": scored["summary"],
        "taken_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
