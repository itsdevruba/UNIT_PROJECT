"""AI interview with a local Ollama model.

How it works (only 2 calls to the model, so it stays fast):
1. One call writes 5 open questions at once, one for each quiz trait.
   Each question is checked; an unclear one is swapped for our example question.
2. The user answers them in their own words (no waiting between questions).
3. One call scores the answers on the 5 traits (0-10) and writes a short summary.
4. Our own quiz algorithm (quiz.best_matches) picks the characters,
   so the result is always a real character from our data.
"""

import json
from datetime import datetime

import questionary

from hub import display, quiz
from hub.config import OLLAMA_MODEL, TRAITS

try:
    import ollama
except ImportError:          # the rest of the app still works without the library
    ollama = None

KEEP_MODEL_LOADED = "10m"   # keep the model in memory so the next interview starts faster

SERIES_WORLDS = {
    "GTA": "modern city crime: heists, gangs, cops, cars and big money",
    "Red Dead": "the Wild West around 1900: outlaw gangs, lawmen, horses and survival",
    "Bully": "a tough boarding school: cliques, pranks, bullies and strict teachers",
}

# What each trait question should reveal, and how to score the answer.
TRAIT_GUIDE = {
    "loyalty": "Would they stand by their friends/crew or betray them for themselves? "
               "Betraying, abandoning or selling out a partner = low. Protecting them at a cost = high.",
    "morality": "Do they follow principles or do whatever works? "
                "Stealing, cheating or hurting innocents = low. Refusing to do wrong even when it pays = high.",
    "temper": "How fast do they get angry or violent? "
              "Staying calm, talking it out = low. Threatening, fighting or shooting quickly = high.",
    "humor": "Do they joke and enjoy fun, or stay serious? "
             "Laughing, joking, playing along = high. Staying cold, serious or annoyed = low.",
    "ambition": "How much do they want money, power and status? "
                "Happy with a simple life = low. Taking big risks to get rich or powerful = high.",
}

# One clear example question per trait for each series.
# The model sees them as a style guide, and we fall back to them if a generated question is unclear.
EXAMPLE_QUESTIONS = {
    "GTA": {
        "loyalty": "Your partner gets arrested after a job and the cops offer you a deal to testify against him. What do you do?",
        "morality": "You find a wallet with $5,000 and the owner's ID inside. What do you do with it?",
        "temper": "A stranger scratches your car on purpose and laughs at you. How do you react?",
        "humor": "Your heist plan goes wrong and your whole crew ends up soaked in a fountain. How do you react?",
        "ambition": "A crime boss offers you a dangerous job that could make you a millionaire. What do you do?",
    },
    "Red Dead": {
        "loyalty": "The sheriff offers you a pardon if you tell him where your gang is hiding. What do you do?",
        "morality": "You could rob a poor family's farm to feed your hungry gang. What do you do?",
        "temper": "A drunk man in the saloon spills whiskey on you and calls you a coward. How do you react?",
        "humor": "Your horse throws you into the mud right in front of the whole camp. How do you react?",
        "ambition": "You hear about a train carrying enough gold to set you up for life. What do you do?",
    },
    "Bully": {
        "loyalty": "Your best friend gets blamed for a prank you pulled, and the principal asks you what happened. What do you do?",
        "morality": "You find the answers to tomorrow's big exam on a teacher's desk. What do you do?",
        "temper": "An older student shoves you into a locker in front of everyone. How do you react?",
        "humor": "You slip on a banana peel in the cafeteria and the whole school sees it. How do you react?",
        "ambition": "You get the chance to become the leader of the most powerful clique in school. What do you do?",
    },
}

AMBIGUOUS_WORDS = {"they", "them", "their", "theirs", "someone's"}

QUESTIONS_SCHEMA = {
    "type": "object",
    "properties": {trait: {"type": "string"} for trait in TRAITS},
    "required": TRAITS,
}

SCORES_SCHEMA = {
    "type": "object",
    "properties": {
        **{trait: {"type": "integer", "minimum": 0, "maximum": 10} for trait in TRAITS},
        "summary": {"type": "string"},
    },
    "required": TRAITS + ["summary"],
}


def chat_json(messages: list[dict], schema: dict, max_tokens: int, temperature: float) -> dict | None:
    """Ask the model for JSON that follows `schema`. Returns the parsed dict, or None on any failure."""
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
        display.error(f"The model '{OLLAMA_MODEL}' is not downloaded. Run: ollama pull {OLLAMA_MODEL}")
    except (ConnectionError, OSError):
        display.error("Can't reach Ollama. Make sure the Ollama app is running.")
    return False


def clean_text(text: str) -> str:
    """Trim spaces and quotes the model sometimes adds around a sentence."""
    return " ".join(str(text).split()).strip('"\'* ')


def is_clear_question(question: str) -> bool:
    """Simple checks that catch most confusing questions from a small model."""
    words = [word.strip(".,!?;:'\"").lower() for word in question.split()]
    return (
        question.endswith("?")
        and 8 <= len(words) <= 30
        and ("you" in words or "your" in words)
        and not AMBIGUOUS_WORDS.intersection(words)     # "refuses to testify against them" -> who?
        and " or " not in question.lower()               # we want open questions, not "A or B"
    )


def generate_questions(series: str) -> dict[str, str]:
    """One call: write one clear question per trait. Unclear ones are replaced with our example."""
    examples = EXAMPLE_QUESTIONS[series]
    guide = "\n".join(
        f"- {trait}: {TRAIT_GUIDE[trait].split('?')[0]}?  Example: \"{examples[trait]}\""
        for trait in TRAITS
    )
    messages = [
        {"role": "system", "content": "You write short, clear personality quiz questions in simple English. Reply with JSON only."},
        {"role": "user", "content": (
            f"Write 5 NEW questions for a personality quiz set in {SERIES_WORLDS[series]}.\n"
            f"One question for each trait. Here is what each trait means, with an example of a good question:\n"
            f"{guide}\n\n"
            f"Rules for every question:\n"
            f"1. Talk directly to the player using 'you' and 'your'.\n"
            f"2. Describe ONE simple situation, then ask 'What do you do?' or 'How do you react?'.\n"
            f"3. Do not use the words 'they', 'them' or 'their'. Name the person instead (a friend, the sheriff, a teacher).\n"
            f"4. No 'A or B' choices. One or two short sentences, under 25 words.\n"
            f"5. Do not copy the examples, and never mention game or character names."
        )},
    ]

    with display.console.status("[dim]The AI is writing your questions...[/dim]"):
        data = chat_json(messages, QUESTIONS_SCHEMA, max_tokens=350, temperature=0.8) or {}

    questions = {}
    replaced = 0
    for trait in TRAITS:
        question = clean_text(data.get(trait, ""))
        if not is_clear_question(question):
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
        display.console.print(f"\n[bold yellow]({number}/{len(TRAITS)})[/bold yellow] {questions[trait]}")
        while True:
            answer = questionary.text("Your answer:").ask()
            if answer is None:
                return None
            if answer.strip():
                answers[trait] = answer.strip()
                break
            display.error("Please type an answer.")
    return answers


def score_answers(questions: dict[str, str], answers: dict[str, str], attempts: int = 2) -> dict | None:
    """One call: score each trait from its own answer, plus a 2-sentence summary that matches the scores."""
    interview = "\n\n".join(
        f"[{trait}]\nQ: {questions[trait]}\nA: {answers[trait]}\nHow to score: {TRAIT_GUIDE[trait]}"
        for trait in TRAITS
    )
    messages = [
        {"role": "system", "content": "You score personality quiz answers fairly and consistently. Reply with JSON only."},
        {"role": "user", "content": (
            f"{interview}\n\n"
            f"Give each trait a score from 0 to 10 based mainly on the answer to its own question, "
            f"using the scoring guide. Use the full range: a clear answer should get a score near 0-2 or 8-10.\n"
            f"Then write 'summary': at most 2 short sentences (under 40 words) describing this person, "
            f"speaking to them as 'you'. The summary must agree with your scores and mention "
            f"at least one thing they actually said. Do not invent traits they did not show."
        )},
    ]
    for _ in range(attempts):
        with display.console.status("[dim]Reading your answers...[/dim]"):
            data = chat_json(messages, SCORES_SCHEMA, max_tokens=200, temperature=0)
        if data is None:
            continue
        try:
            traits = {trait: float(min(10, max(0, int(data[trait])))) for trait in TRAITS}
        except (KeyError, TypeError, ValueError):
            display.warning("The AI's scores were incomplete. Trying again...")
            continue
        return {"traits": traits, "summary": clean_text(data.get("summary", ""))}
    return None


def take_ai_interview(characters: list[dict], series: str, player: str) -> dict | None:
    """Full AI flow. Returns a result record like quiz.take_quiz, or None if it didn't work."""
    if not characters:
        display.warning(f"No characters found for {series}.")
        return None
    if not is_available():
        return None

    questions = generate_questions(series)

    display.console.print(f"[dim]Answer the {len(TRAITS)} questions in your own words. Press Ctrl+C to stop.[/dim]")
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
