# Interrogative agenda: clarifying questions before the bot chooses a route

Started 2026-11-11. This directory is the starting point of a third line of work on the De Rode Winkel prototype. The idea is that the bot asks a clarifying question when a customer message fits several intents, and that the choice of question follows from a formal account of what the bot is uncertain about. The method we want to build on is the interrogative-agenda work of the Palmigiano group, which weights agendas with Dempster-Shafer mass functions. The exact source paper has not been pinned down yet, so every definition below is provisional and is marked as such where it matters. What exists today is a small, tested Dempster-Shafer module, a toy example, and this design note.

## Why this line

The bot commits to one flow on the first customer message. The command generator reads the message, outputs `start flow ...` with slot values, and the conversation proceeds on that route. The knowledge-graph line showed where this goes wrong: a message that names a brand, a payment method or a delivery term can concern several different things, and a wrong commitment produces a confident, sourced answer to a question the customer did not ask. The e2e work of 2026-11-10 found one such case by accident, when "in termijnen" was rewritten to "achteraf betalen" and the graph answered "ja".

Two samples of the pseudonymized WhatsApp conversations, read on 2026-11-11, show how the shop's employees handle the same situation. They ask before they answer. A customer who reports a broken zipper is first asked whether the jeans were bought at the shop and whether the customer is in the customer file, and the answer decides between warranty, paid repair and referral. The same samples contain questions that only make sense in context, such as a question about shipping costs that concerns sending a garment in for repair. A router that takes that message on its own would hand it to the shipping-cost fact and answer about webshop orders.

## The method as we currently understand it

This section is written from memory of the Palmigiano group's papers on flexible categorization with formal concept analysis and Dempster-Shafer theory, and of their application to outlier detection in auditing. It has to be checked against the papers before anything is built on it.

A formal context relates objects to features. An interrogative agenda is a set of features, read as the questions an agent considers relevant when it categorizes objects. Restricting the context to an agenda gives a concept lattice, so each agenda induces its own categorization, and a coarser agenda gives coarser categories. A Dempster-Shafer mass function over sets of features expresses how much weight an agent gives to each agenda, which turns the family of crisp categorizations into a graded one. Several agents with different agendas can be aggregated, and the papers treat that aggregation as deliberation.

As far as we recall, the papers use agendas to categorize and to compare or aggregate agents. Selecting the next clarifying question in a dialogue from the mass functions would be our own extension. The first task of this line is to establish where that boundary lies.

## What Rasa CALM offers today

This section was checked against Rasa Pro 3.19.2 as installed in the project and against the Rasa documentation on LLM command generators.

CALM has one clarification mechanism. The default command prompt offers the command `disambiguate flows flow_a flow_b ...`, with the instruction to use it in ambiguous cases and to refrain when one flow is clearly more likely. The command starts `pattern_clarification`, which runs `action_clarify_flows` and utters `utter_clarification_options_rasa`: a sentence that lists the candidate flows and asks the user to pick one. The decision to clarify and the list of candidates are both the unexplained output of one LLM call.

CALM has no representation of uncertainty behind that decision. The command generator emits discrete commands without probabilities, flows have no feature description that a question could be about, no component compares candidate questions, and evidence is never combined across turns in an explicit form. Collect steps do ask questions, and they run after the flow has been chosen, so they refine within a route.

This project currently has no clarification at all. The custom prompt in `prompts/command_generator.jinja2` does not list the disambiguate command, and `data/patterns.yml` overrides only `pattern_cancel_flow`, `pattern_completed` and `pattern_search`.

CALM does provide the places to attach a new mechanism. A custom command generator can run before or around the LLM one, a flow with a custom action can utter a question that is chosen at run time and read the answer into a slot, and the evidence sources already exist in the project: the label linker in `experiments/kg/link.py`, flow-retrieval similarity scores, and repeated samples from the command model.

## A first sketch for the bot

The sketch below is a working hypothesis that makes the idea concrete enough to compute with. It will be revised once the paper has been read.

The frame of discernment is the set of routes the bot can take: the graph question shapes, retrieval, and hand-over to a person for questions about the customer's own order. Each source of evidence about a message is a mass function on that frame. A source that cannot tell two routes apart puts its mass on the set that contains both, and a source that knows nothing puts its mass on the whole frame. Dempster's rule combines the sources and reports how much they conflict.

The bot commits to a route when the belief in that route alone reaches a threshold. Belief counts only the mass that is committed to the route, so evidence that merely fails to exclude a route does not count toward it. When no route reaches the threshold, the bot asks.

A question is a feature with a set of possible answers, and each answer is compatible with a set of routes. An answer conditions the mass function on its set, which is Dempster's rule with a certain piece of evidence. The bot scores each available question by the expected drop in the Shannon entropy of the pignistic distribution, with answer probabilities taken from that same distribution, and asks the question with the largest expected drop. The entropy of the pignistic distribution was chosen because it counts both imprecision (mass on large sets) and conflict (mass split over single routes); the module also reports the nonspecificity measure, which counts imprecision only.

This sketch places the mass functions on sets of routes. The papers, as we recall them, place mass on sets of features. How the two relate is the first open question below.

## Toy example

`example.py` works through one invented message, "Ik heb een vraag over mijn Kuyichi jeans", with four routes: `merk` (does the shop carry the brand), `reparatie` (can the shop repair or alter it), `bestelling` (the customer's own order, which needs a person) and `zoeken` (retrieval). All numbers are illustrative and none is estimated from data.

Three sources give evidence. The linker finds a brand, which supports the three brand-related routes with mass 0.7. The possessive wording supports repair or order with mass 0.6. The absence of order vocabulary speaks weakly against the order route, with mass 0.3 on the other three. Each source leaves its remaining mass on the whole frame. The sources do not conflict, and the combination gives the following picture.

| Route | Belief | Plausibility | Pignistic probability |
|---|---|---|---|
| reparatie | 0.180 | 1.000 | 0.530 |
| bestelling | 0.000 | 0.700 | 0.296 |
| merk | 0.000 | 0.400 | 0.140 |
| zoeken | 0.000 | 0.120 | 0.033 |

Repair is the most probable route and nothing excludes it, yet only 0.18 of the evidence is committed to it. At a threshold of 0.6 the bot asks. The three candidate questions score as follows.

| Question | Expected gain (bits) |
|---|---|
| Is er iets stuk aan de jeans, of wil je hem laten vermaken? | 1.031 |
| Gaat het om een bestelling die nog onderweg is of klaarligt? | 0.924 |
| Heb je de jeans bij ons gekocht? | 0.509 |

The first question is asked. The answer "ja" puts all mass on repair and the bot commits. The answer "nee" removes repair, raises the belief in the order route to 0.512, and leaves the bot below the threshold, so a second question follows.

The third question is the one the employees ask in the WhatsApp conversations, and it ranks last here. It decides little between routes and a great deal within the repair route, where the purchase condition determines the answer. This suggests that clarifying questions come in two kinds, those that choose the route and those that complete it, and that the employees ask the second kind early because they have already settled the route by reading the message. Whether the formal method treats the two kinds uniformly is a question for the paper.

## What is in this directory

`ds.py` holds the Dempster-Shafer functions (mass functions, Dempster's rule with the conflict value, conditioning, belief, plausibility, the pignistic transform, nonspecificity and pignistic entropy) and the question-selection functions (`Question`, `rank_questions`, `decide`). The first group is textbook material after Shafer (1976). The second group is our own first design. `example.py` prints the toy example above. `test_ds.py` has eight checks: the validity of mass functions, a textbook case of Dempster's rule, total conflict, the duality of belief and plausibility, the uncertainty measures at their extremes, and the outcome of the toy example. The module depends on the Python standard library only and is not connected to the bot.

## Open questions

The relation between mass on sets of features and mass on sets of routes has to be settled first. If the papers derive a graded categorization of objects from a mass function on agendas, then the route-level mass function used here may be a consequence of the feature-level one, and the question-selection step should be restated in the papers' terms.

The mass functions need a source. The toy numbers were chosen by hand. Candidates are the linker (a match in a class supports the routes that take that class), flow-retrieval similarities, agreement among repeated samples of the command model, and token log-probabilities if the Ollama version in use exposes them. Each of these would need calibration, and the labeled WhatsApp turns proposed for the knowledge-graph line would serve as calibration data.

Dempster's rule assumes independent sources, and evidence derived from the same message by different components is correlated. The conflict value and the alternatives to the rule (Yager's rule, the cautious rule, discounting) need a look once real evidence sources exist.

The set of questions needs a source as well. The graph schema supplies features for the graph routes (channel, purchase origin, brand, product category), and the clarifying questions that employees ask in the WhatsApp conversations supply an empirical set. A census of those questions, with the routes each one separates, is a natural first data product.

The cost of asking is not modeled. A question delays the answer, and a bot that asks on every message is worse than one that sometimes guesses. The threshold stands in for that cost for now.

Evaluation needs ambiguous messages with a known intended route. The held-out routing set planned from the WhatsApp conversations would contain them, with the continuation of the real conversation as evidence of what the customer meant.

## Next steps

1. Read the source paper once it is identified, replace the provisional section above with the definitions from the paper, and state which parts of the sketch follow from it and which are additions.
2. Collect the clarifying questions that employees ask in the WhatsApp conversations, on the server and under the privacy rules agreed for those logs, and tabulate which routes each question separates.
3. Decide where the mechanism attaches in CALM: the built-in disambiguate command with a rewritten response, a pre-routing flow with a custom action, or a custom command generator.
4. Build mass functions from one real evidence source, the linker, and compare the ask-or-commit decisions with the labeled routing set.

## Commands

```
venv/Scripts/python experiments/interrogative_agenda/example.py
venv/Scripts/python -m pytest experiments/interrogative_agenda/test_ds.py -q
```
