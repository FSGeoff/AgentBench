from tqdm import tqdm
from typing import List
import re
import threading
import jsonlines
import yaml
import json
import numpy as np
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

def bleu_score(reference, candidate):
    reference_tokens = reference.split()
    candidate_tokens = candidate.split()

    smoothie = SmoothingFunction().method4
    score = sentence_bleu([reference_tokens], candidate_tokens, smoothing_function=smoothie)
    return score

def process_ob(ob):
    if ob.startswith('You arrive at loc '):
        ob = ob[ob.find('. ')+2:]    
    return ob


def normalize_agent_turn(output):
    """Keep one real ALFWorld action in each model turn.

    Completion-style models may continue by inventing USER feedback or
    additional ACTION turns. Those continuations never occurred in the
    environment and must not enter the next inference context.
    """
    text = (output or "").strip()
    action_match = re.search(
        r"\bACTION\s*:\s*",
        text,
        flags=re.IGNORECASE,
    )

    if not action_match:
        return text

    prefix = text[:action_match.start()].strip()
    remainder = text[action_match.end():].lstrip()

    # An ALFWorld command occupies one line.
    action = re.split(r"[\r\n]", remainder, maxsplit=1)[0].strip()

    # Stop same-line fabricated continuations such as:
    # ACTION: look USER: ... ACTION: go to shelf 1
    action = re.split(
        r"\s+(?=(?:USER|AGENT|ASSISTANT|THOUGHT|ACTION)\s*:)",
        action,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()

    normalized_action = f"ACTION: {action}"
    if prefix:
        return f"{prefix}\n{normalized_action}"
    return normalized_action


def process_action(action, choices, limit=0.01, to_print=False):
    if to_print:
        print("preprocess action: ", action)
    match = re.search("ACTION:(.*)", action)
    if match:
        action = match.group(1)
    else:
        return False

    action = action.strip().lower().split("\n")[0]
    if not choices:
        return action
    if action in choices:
        return action
    try:
        bleus = [bleu_score(choice, action) for choice in choices]
        max_index = np.argmax(np.array(bleus))
        max_score = bleus[max_index]
        if max_score > limit:
            if to_print:
                print("processed action: ", choices[max_index], " score: ", max_score)
            return choices[max_index]
    except Exception as e:
        print("encounter exception: ", e)
        print("choices: ", choices)
        print("action: ", action)
    return action

def load_prompts(prompts_file):
    with open(prompts_file, 'r') as f:
        d = json.load(f)
        f.close()
    return d

def load_config(config_file):
    with open(config_file) as reader:
        config = yaml.safe_load(reader)
    return config