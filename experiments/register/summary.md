# Register mirroring in the study answers

Source: `C:/Users/juria/git/prototypeDRW/experiments/contrastive/results_study/answers.csv`, 47120 case results, 37109 with an answer text.

The question register is the bot's own classification (`detect_register` in `actions/actions.py`, informal unless formal markers dominate). The answer register comes from second-person markers in the answer text; neutral answers have none and are excluded from the mirroring rate.

## The suite's questions

124 distinct questions: 0 classified formal, 124 informal (the default). 0 contain an explicit *u*/*uw*. The suite was written for retrieval and, despite the plan, contains no formal paraphrases, so the study answers can only show the informal direction; the formal direction is measured with `tests/test_register.yml` (sections below).

Formal questions:


## Mirroring per answer model, k0 condition

| answer model | n answered | formal Q: answered formal | formal Q: answered informal | informal Q: answered informal | informal Q: answered formal | neutral answers | mixed |
|---|---|---|---|---|---|---|---|
| gemma3:12b | 361 | n/a (0) | n/a | 100.0% (342) |   0.0% |   5.3% |   0.0% |
| gemma3:27b | 396 | n/a (0) | n/a | 100.0% (363) |   0.0% |   8.3% |   0.0% |
| gemma3:4b | 620 | n/a (0) | n/a | 100.0% (520) |   0.0% |  16.1% |   0.0% |
| GEITje-7B-ultra-GGUF:Q4_K_M | 607 | n/a (0) | n/a |  92.6% (542) |   7.4% |   9.7% |   1.0% |
| fietje-2-chat-GGUF:Q4_K_M | 620 | n/a (0) | n/a |  70.0% (213) |  30.0% |  61.9% |   3.7% |
| EuroLLM-9B-Instruct-GGUF:Q4_K_M | 620 | n/a (0) | n/a | 100.0% (478) |   0.0% |  22.9% |   0.0% |
| llama3.3:70b | 577 | n/a (0) | n/a | 100.0% (564) |   0.0% |   2.3% |   0.0% |
| mistral-small3.2 | 304 | n/a (0) | n/a | 100.0% (238) |   0.0% |  21.7% |   0.0% |
| qwen3.5:27b | 369 | n/a (0) | n/a | 100.0% (319) |   0.0% |  13.6% |   0.0% |
| qwen3.5:9b | 577 | n/a (0) | n/a | 100.0% (418) |   0.0% |  27.6% |   0.0% |

## Mirroring per answer model, all conditions pooled

| answer model | n answered | formal Q: answered formal | formal Q: answered informal | informal Q: answered informal | informal Q: answered formal | neutral answers | mixed |
|---|---|---|---|---|---|---|---|
| gemma3:12b | 5484 | n/a (0) | n/a | 100.0% (5163) |   0.0% |   5.9% |   0.0% |
| gemma3:27b | 3248 | n/a (0) | n/a | 100.0% (2966) |   0.0% |   8.7% |   0.0% |
| gemma3:4b | 4960 | n/a (0) | n/a | 100.0% (4285) |   0.0% |  13.6% |   0.0% |
| GEITje-7B-ultra-GGUF:Q4_K_M | 4877 | n/a (0) | n/a |  93.2% (4393) |   6.8% |   7.9% |   2.1% |
| fietje-2-chat-GGUF:Q4_K_M | 3091 | n/a (0) | n/a |  71.9% (1028) |  28.1% |  63.5% |   3.3% |
| EuroLLM-9B-Instruct-GGUF:Q4_K_M | 4960 | n/a (0) | n/a |  99.9% (3768) |   0.1% |  24.0% |   0.0% |
| llama3.3:70b | 577 | n/a (0) | n/a | 100.0% (564) |   0.0% |   2.3% |   0.0% |
| mistral-small3.2 | 2395 | n/a (0) | n/a | 100.0% (1778) |   0.0% |  25.8% |   0.0% |
| qwen3.5:27b | 2990 | n/a (0) | n/a | 100.0% (2557) |   0.0% |  14.5% |   0.0% |
| qwen3.5:9b | 4527 | n/a (0) | n/a | 100.0% (3171) |   0.0% |  30.0% |   0.0% |

## gemma3:12b per condition

| condition | formal Q answered formal | informal Q answered informal | neutral |
|---|---|---|---|
| k0 | n/a (0) | 100.0% (342) |   5.3% |
| topk2 | n/a (0) | 100.0% (332) |   6.7% |
| bottom_k1 | n/a (0) | 100.0% (356) |   5.3% |
| bottom_k2 | n/a (0) | 100.0% (346) |   6.7% |
| bottom_k3 | n/a (0) | 100.0% (378) |   5.3% |
| bottom_k4 | n/a (0) | 100.0% (383) |   4.7% |
| random_k1 | n/a (0) | 100.0% (355) |   6.8% |
| random_k2 | n/a (0) | 100.0% (363) |   8.3% |
| random_k3 | n/a (0) | 100.0% (378) |   6.9% |
| random_k4 | n/a (0) | 100.0% (392) |   6.2% |
| next_k1 | n/a (0) | 100.0% (353) |   6.6% |
| next_k2 | n/a (0) | 100.0% (375) |   4.3% |
| next_k3 | n/a (0) | 100.0% (394) |   3.9% |
| next_k4 | n/a (0) | 100.0% (416) |   5.0% |

## Paraphrase pairs whose two versions differ in register

0 of the answerable questions have one formal and one informal paraphrase. For each pair and model (k0, all repeats), the share of answers whose register follows the question:

| answer model | formal version answered formal | informal version answered informal |
|---|---|---|
| gemma3:12b | n/a (0) | n/a (0) |
| gemma3:27b | n/a (0) | n/a (0) |
| gemma3:4b | n/a (0) | n/a (0) |
| GEITje-7B-ultra-GGUF:Q4_K_M | n/a (0) | n/a (0) |
| fietje-2-chat-GGUF:Q4_K_M | n/a (0) | n/a (0) |
| EuroLLM-9B-Instruct-GGUF:Q4_K_M | n/a (0) | n/a (0) |
| llama3.3:70b | n/a (0) | n/a (0) |
| mistral-small3.2 | n/a (0) | n/a (0) |
| qwen3.5:27b | n/a (0) | n/a (0) |
| qwen3.5:9b | n/a (0) | n/a (0) |

Pairs:


## Examples: formal question answered informally (k0)


## Register suite run: `experiments/register/results/gemma3-12b_default`

Read from the e2e transcripts. `slot` is the value of `klant_register` after the turn; `answer` is the register of the enterprise-search answer text (neutral = no second-person marker); `Rasa` is whether the case's own assertions passed (the never-matching capture assertion excluded).

| case | turn | user message | slot | answer register | Rasa |
|---|---|---|---|---|---|
| F | retouren - terugsturen kosten | 1 | Kunt u mij vertellen wat de kosten zijn als ik een artikel w | formeel | neutral | ok |
| F | retouren - online aankoop in winkel terugbrengen | 1 | Ik heb online besteld. Kan ik het artikel in uw winkel in Ut | formeel | formeel | ok |
| F | retouren - wanneer geld terug | 1 | Wanneer ontvang ik mijn geld terug nadat u mijn retour heeft | formeel | formeel | ok |
| F | verzending - verzendkosten en drempel | 1 | Wat zijn uw verzendkosten, en vanaf welk bedrag verzendt u g | formeel | neutral | ok |
| F | verzending - bezorging Belgie | 1 | Bezorgt u ook in België? | formeel | formeel | ok |
| F | verzending - levertijd | 1 | Hoe lang duurt de levering bij u? | formeel | formeel | ok |
| F | bestellen - account verplicht | 1 | Moet ik een account aanmaken om bij u te kunnen bestellen? | formeel | formeel | ok |
| F | producten - maat uitverkocht | 1 | Mijn maat is online uitverkocht. Kunt u deze voor mij nabest | formeel | formeel | ok |
| F | betalen - achteraf betalen | 1 | Is het mogelijk om achteraf te betalen bij u? | formeel | formeel | ok |
| F | betalen - PayPal toeslag | 1 | Rekent u extra kosten als ik met PayPal betaal? | formeel | formeel | ok |
| F | betalen - Klarna (negative answer) | 1 | Accepteert u Klarna? | formeel | formeel | ok |
| F | kortingscode - studentenkorting | 1 | Geeft u korting aan studenten? | formeel | formeel | ok |
| F | cadeaukaart - cadeaubon online gebruiken | 1 | Ik heb een cadeaubon ontvangen. Kan ik deze in uw webshop ge | formeel | formeel | ok |
| F | maatadvies - afspraak om te passen | 1 | Kan ik bij u een afspraak maken om rustig te komen passen? | formeel | formeel | ok |
| F | fysieke winkel - openingstijd donderdag | 1 | Tot hoe laat bent u op donderdag geopend? | formeel | formeel | ok |
| F | fysieke winkel - zondag open | 1 | Bent u op zondag geopend? | formeel | formeel | ok |
| F | fysieke winkel - vestiging Amsterdam (negative answer) | 1 | Heeft u ook een vestiging in Amsterdam? | formeel | - | FAIL |
| F | garantie - broek stuk na 3 maanden | 1 | Mijn broek is na drie maanden kapot. Wat kunt u voor mij doe | formeel | formeel | ok |
| F | garantie - Nudie jeans elders gekocht repareren | 1 | Repareert u ook Nudie Jeans die ik elders heb gekocht? | formeel | formeel | ok |
| F | loyaliteitspunten - waarde gespaarde punten | 1 | Hoeveel korting leveren mijn gespaarde punten bij u op? | formeel | formeel | ok |
| F | bedrijfsgegevens - contact | 1 | Op welk telefoonnummer kan ik u bereiken? | formeel | formeel | ok |
| F | assortiment - kinderkleding | 1 | Verkoopt u ook kinderkleding? | formeel | formeel | ok |
| F | assortiment - schoenen (negative answer) | 1 | Heeft u ook schoenen in uw assortiment? | formeel | formeel | ok |
| F | verzending - niet thuis bij bezorging | 1 | Wat gebeurt er als ik niet thuis ben wanneer u het pakket be | formeel | formeel | ok |
| I | retouren - terugsturen kosten | 1 | Hoi, wat kost het als ik iets naar jullie terugstuur? | informeel | informeel | ok |
| I | verzending - bezorging Belgie | 1 | Bezorgen jullie ook in België? | informeel | informeel | ok |
| I | betalen - PayPal toeslag | 1 | Betaal ik extra als ik met PayPal betaal bij jullie? | informeel | informeel | ok |
| I | fysieke winkel - zondag open | 1 | Zijn jullie op zondag open? | informeel | informeel | ok |
| I | garantie - broek stuk na 3 maanden | 1 | M'n broek is na drie maanden alweer stuk, wat nu? | informeel | informeel | ok |
| I | assortiment - kinderkleding | 1 | Hebben jullie ook iets voor kinderen? | informeel | informeel | ok |
| M | informal then formal | 1 | Wat kost het om iets terug te sturen? | informeel | informeel | ok |
| M | informal then formal | 2 | Kunt u mij ook vertellen hoe lang de levering duurt? | formeel | formeel | ok |
| M | formal then informal | 1 | Kunt u mij vertellen wat de verzendkosten zijn? | formeel | neutral | ok |
| M | formal then informal | 2 | En bezorgen jullie ook in België? | informeel | neutral | ok |
| M | formal then neutral follow-up keeps formal | 1 | Tot hoe laat bent u op donderdag geopend? | formeel | formeel | ok |
| M | formal then neutral follow-up keeps formal | 2 | En op zondag? | formeel | formeel | ok |
| M | informal then neutral follow-up keeps informal | 1 | Hoi! Tot hoe laat zijn jullie donderdag open? | informeel | informeel | ok |
| M | informal then neutral follow-up keeps informal | 2 | En op zondag? | informeel | informeel | ok |
| M | formal greeting | 1 | Goedemiddag, kunt u mij helpen? | formeel | formeel | FAIL |
| M | informal greeting | 1 | Hoi! Kun je me helpen? | informeel | informeel | FAIL |

Formal single-turn: 21 of 21 answers with a marker are formal (100.0%), 2 neutral. Informal single-turn: 6 of 6 informal (100.0%), 0 neutral. Multi-turn formal turns: 4 of 4 formal, 1 neutral. Rasa assertion failures: 3 of 36 cases.

Failed assertions:

- F | fysieke winkel - vestiging Amsterdam (negative answer): {'utter_name': 'utter_no_relevant_answer_found', 'text_matches': None, 'buttons': [], 'line': 27, 'type': 'bot_did_not_utter'}
- M | formal greeting: {'utter_name': 'utter_begroeting', 'text_matches': 'Goedendag', 'buttons': [], 'line': 241, 'type': 'bot_uttered'}
- M | informal greeting: {'utter_name': 'utter_begroeting', 'text_matches': 'Hallo', 'buttons': [], 'line': 250, 'type': 'bot_uttered'}

## Register suite run: `experiments/register/results/gemma3-12b_k0`

Read from the e2e transcripts. `slot` is the value of `klant_register` after the turn; `answer` is the register of the enterprise-search answer text (neutral = no second-person marker); `Rasa` is whether the case's own assertions passed (the never-matching capture assertion excluded).

| case | turn | user message | slot | answer register | Rasa |
|---|---|---|---|---|---|
| F | retouren - terugsturen kosten | 1 | Kunt u mij vertellen wat de kosten zijn als ik een artikel w | formeel | neutral | ok |
| F | retouren - online aankoop in winkel terugbrengen | 1 | Ik heb online besteld. Kan ik het artikel in uw winkel in Ut | formeel | formeel | ok |
| F | retouren - wanneer geld terug | 1 | Wanneer ontvang ik mijn geld terug nadat u mijn retour heeft | formeel | formeel | ok |
| F | verzending - verzendkosten en drempel | 1 | Wat zijn uw verzendkosten, en vanaf welk bedrag verzendt u g | formeel | neutral | ok |
| F | verzending - bezorging Belgie | 1 | Bezorgt u ook in België? | formeel | formeel | ok |
| F | verzending - levertijd | 1 | Hoe lang duurt de levering bij u? | formeel | formeel | ok |
| F | bestellen - account verplicht | 1 | Moet ik een account aanmaken om bij u te kunnen bestellen? | formeel | formeel | ok |
| F | producten - maat uitverkocht | 1 | Mijn maat is online uitverkocht. Kunt u deze voor mij nabest | formeel | formeel | ok |
| F | betalen - achteraf betalen | 1 | Is het mogelijk om achteraf te betalen bij u? | formeel | formeel | ok |
| F | betalen - PayPal toeslag | 1 | Rekent u extra kosten als ik met PayPal betaal? | formeel | formeel | ok |
| F | betalen - Klarna (negative answer) | 1 | Accepteert u Klarna? | formeel | formeel | ok |
| F | kortingscode - studentenkorting | 1 | Geeft u korting aan studenten? | formeel | formeel | ok |
| F | cadeaukaart - cadeaubon online gebruiken | 1 | Ik heb een cadeaubon ontvangen. Kan ik deze in uw webshop ge | formeel | formeel | ok |
| F | maatadvies - afspraak om te passen | 1 | Kan ik bij u een afspraak maken om rustig te komen passen? | formeel | formeel | ok |
| F | fysieke winkel - openingstijd donderdag | 1 | Tot hoe laat bent u op donderdag geopend? | formeel | formeel | ok |
| F | fysieke winkel - zondag open | 1 | Bent u op zondag geopend? | formeel | formeel | ok |
| F | fysieke winkel - vestiging Amsterdam (negative answer) | 1 | Heeft u ook een vestiging in Amsterdam? | formeel | - | FAIL |
| F | garantie - broek stuk na 3 maanden | 1 | Mijn broek is na drie maanden kapot. Wat kunt u voor mij doe | formeel | formeel | ok |
| F | garantie - Nudie jeans elders gekocht repareren | 1 | Repareert u ook Nudie Jeans die ik elders heb gekocht? | formeel | formeel | ok |
| F | loyaliteitspunten - waarde gespaarde punten | 1 | Hoeveel korting leveren mijn gespaarde punten bij u op? | formeel | formeel | ok |
| F | bedrijfsgegevens - contact | 1 | Op welk telefoonnummer kan ik u bereiken? | formeel | formeel | ok |
| F | assortiment - kinderkleding | 1 | Verkoopt u ook kinderkleding? | formeel | formeel | ok |
| F | assortiment - schoenen (negative answer) | 1 | Heeft u ook schoenen in uw assortiment? | formeel | formeel | ok |
| F | verzending - niet thuis bij bezorging | 1 | Wat gebeurt er als ik niet thuis ben wanneer u het pakket be | formeel | formeel | ok |
| I | retouren - terugsturen kosten | 1 | Hoi, wat kost het als ik iets naar jullie terugstuur? | informeel | informeel | ok |
| I | verzending - bezorging Belgie | 1 | Bezorgen jullie ook in België? | informeel | informeel | ok |
| I | betalen - PayPal toeslag | 1 | Betaal ik extra als ik met PayPal betaal bij jullie? | informeel | informeel | ok |
| I | fysieke winkel - zondag open | 1 | Zijn jullie op zondag open? | informeel | informeel | ok |
| I | garantie - broek stuk na 3 maanden | 1 | M'n broek is na drie maanden alweer stuk, wat nu? | informeel | informeel | ok |
| I | assortiment - kinderkleding | 1 | Hebben jullie ook iets voor kinderen? | informeel | informeel | ok |
| M | informal then formal | 1 | Wat kost het om iets terug te sturen? | informeel | neutral | ok |
| M | informal then formal | 2 | Kunt u mij ook vertellen hoe lang de levering duurt? | formeel | formeel | ok |
| M | formal then informal | 1 | Kunt u mij vertellen wat de verzendkosten zijn? | formeel | neutral | ok |
| M | formal then informal | 2 | En bezorgen jullie ook in België? | informeel | neutral | ok |
| M | formal then neutral follow-up keeps formal | 1 | Tot hoe laat bent u op donderdag geopend? | formeel | formeel | ok |
| M | formal then neutral follow-up keeps formal | 2 | En op zondag? | formeel | formeel | ok |
| M | informal then neutral follow-up keeps informal | 1 | Hoi! Tot hoe laat zijn jullie donderdag open? | informeel | informeel | ok |
| M | informal then neutral follow-up keeps informal | 2 | En op zondag? | informeel | informeel | ok |
| M | formal greeting | 1 | Goedemiddag, kunt u mij helpen? | formeel | formeel | FAIL |
| M | informal greeting | 1 | Hoi! Kun je me helpen? | informeel | informeel | FAIL |

Formal single-turn: 21 of 21 answers with a marker are formal (100.0%), 2 neutral. Informal single-turn: 6 of 6 informal (100.0%), 0 neutral. Multi-turn formal turns: 4 of 4 formal, 1 neutral. Rasa assertion failures: 3 of 36 cases.

Failed assertions:

- F | fysieke winkel - vestiging Amsterdam (negative answer): {'utter_name': 'utter_no_relevant_answer_found', 'text_matches': None, 'buttons': [], 'line': 27, 'type': 'bot_did_not_utter'}
- M | formal greeting: {'utter_name': 'utter_begroeting', 'text_matches': 'Goedendag', 'buttons': [], 'line': 241, 'type': 'bot_uttered'}
- M | informal greeting: {'utter_name': 'utter_begroeting', 'text_matches': 'Hallo', 'buttons': [], 'line': 250, 'type': 'bot_uttered'}
