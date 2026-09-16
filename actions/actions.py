import re
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

# Formal: second-person formal pronouns and formal greetings/closings.
# \bu\b alone is too noisy (also an abbreviation), so require it as a word
# together with typical formal verb forms or standalone pronoun usage.
FORMAL_PATTERNS = [
    r"\bu\b",
    r"\buw\b",
    r"\bhebt u\b",
    r"\bheeft u\b",
    r"\bkunt u\b",
    r"\bgeachte\b",
    r"\bvriendelijke groet\b",
    r"\bdank u\b",
    r"\balvast bedankt\b",
]

INFORMAL_PATTERNS = [
    r"\bje\b",
    r"\bjij\b",
    r"\bjou\b",
    r"\bjouw\b",
    r"\bjullie\b",
    r"\bhoi\b",
    r"\bhey\b",
    r"\bhé\b",
    r"\bm'n\b",
    r"\bz'n\b",
    r"\bff\b",
    r"\btrouwens\b",
    r"\bgroetjes\b",
]


def detect_register(user_messages: List[Text]) -> Text:
    """Classify the customer's register as 'formeel' or 'informeel'.

    Counts formal vs informal marker occurrences across all user messages.
    Informal is the default: De Rode Winkel's own tone of voice is informal
    ("je"), so we only switch to formal when formal markers dominate.
    """
    def counts(text: Text):
        text = text.lower()
        return (sum(len(re.findall(p, text)) for p in FORMAL_PATTERNS),
                sum(len(re.findall(p, text)) for p in INFORMAL_PATTERNS))

    # The latest message decides when it carries any marker: a customer who
    # switches to "u" mid-conversation should be answered with "u" from then on.
    if user_messages:
        formal, informal = counts(user_messages[-1])
        if formal or informal:
            return "formeel" if formal > informal else "informeel"
    formal, informal = counts(" ".join(user_messages))
    return "formeel" if formal > informal else "informeel"


class ActionDetectRegister(Action):
    """Sets the klant_register slot from the customer's writing style.

    Runs at the start of pattern_search so the enterprise search prompt can
    instruct the LLM to mirror the customer's register (u vs je). Inspired by
    the author-features approach of Yazan et al. 2025 (arXiv:2504.08745).
    """

    def name(self) -> Text:
        return "action_detect_register"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_messages = [
            event.get("text", "")
            for event in tracker.events
            if event.get("event") == "user" and event.get("text")
        ]
        register = detect_register(user_messages)
        return [SlotSet("klant_register", register)]
