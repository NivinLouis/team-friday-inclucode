from collections.abc import Iterator

from .common import load_spacy_model
from .types import Gloss, GlossItem

ENGLISH_SPACY_MODELS = ("en_core_web_lg", "en_core_web_md", "en_core_web_sm")

_ARTICLES = {"a", "an", "the"}
_FILLER_LEMMAS = {"well", "so", "like"}
_MODAL_LEMMAS = {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}
_NEGATION_LEMMAS = {"not", "never", "no", "none", "nothing", "nobody", "nowhere"}
_WH_LEMMAS = {"what", "where", "when", "who", "whom", "whose", "why", "which", "how"}
_KEEP_DETERMINER_LEMMAS = {
    "this",
    "that",
    "these",
    "those",
    "my",
    "your",
    "his",
    "her",
    "its",
    "our",
    "their",
}
_TIME_ADVERB_LEMMAS = {
    "yesterday",
    "today",
    "tomorrow",
    "now",
    "later",
    "soon",
    "always",
    "never",
    "usually",
    "often",
    "sometimes",
    "recently",
    "already",
    "ago",
    "before",
    "after",
    "early",
    "late",
    "finally",
}
_TIME_NOUN_LEMMAS = {
    "morning",
    "afternoon",
    "evening",
    "night",
    "week",
    "month",
    "year",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
_TIME_ENTITY_TYPES = {"DATE", "TIME"}


def _safe_upper_lemma(token) -> str:
    lemma = token.lemma_.strip()
    if lemma in {"", "-PRON-"}:
        return token.text.upper()
    return lemma.upper()


def _ordered_unique(tokens) -> list:
    seen = set()
    ordered = []
    for token in tokens:
        token_id = id(token)
        if token_id in seen:
            continue
        seen.add(token_id)
        ordered.append(token)
    return ordered


def _looks_like_question(tokens) -> bool:
    return any(getattr(token, "text", "") == "?" for token in tokens)


def _is_modal(token) -> bool:
    return token.tag_ == "MD" or token.lemma_.lower() in _MODAL_LEMMAS


def _is_aux_not_main(token) -> bool:
    if token.pos_ != "AUX":
        return False
    if token.dep_ == "ROOT":
        return False
    if _is_modal(token):
        return False
    return True


def _is_negation(token) -> bool:
    text_lower = token.text.lower()
    return token.dep_ == "neg" or text_lower.endswith("n't") or token.lemma_.lower() in _NEGATION_LEMMAS


def _is_wh_token(token) -> bool:
    return token.tag_.startswith("W") or token.lemma_.lower() in _WH_LEMMAS


def _is_time_token(token) -> bool:
    lemma_lower = token.lemma_.lower()
    return (
        lemma_lower in _TIME_ADVERB_LEMMAS
        or lemma_lower in _TIME_NOUN_LEMMAS
        or token.ent_type_ in _TIME_ENTITY_TYPES
        or token.dep_ in {"npadvmod", "tmod"}
    )


def _extract_time_tokens(tokens) -> list:
    phrase_tokens = []
    for token in tokens:
        if not _is_time_token(token):
            continue
        root = token.head if token.dep_ in {"pobj", "compound"} and token.head.pos_ == "ADP" else token
        phrase_tokens.extend(list(root.subtree))
    return _ordered_unique([token for token in phrase_tokens if token in tokens])


def _has_predicate_complement(token, tokens) -> bool:
    return any(
        child.head == token and child in tokens and child.dep_ in {"acomp", "attr", "oprd"}
        for child in tokens
    )


def _reorder_nominals(tokens) -> list:
    moved_by_head = {}
    moved_token_ids = set()
    for token in tokens:
        if token.dep_ in {"amod", "nummod"} and token.head in tokens and token.i < token.head.i:
            moved_by_head.setdefault(id(token.head), []).append(token)
            moved_token_ids.add(id(token))

    reordered = []
    for token in tokens:
        if id(token) in moved_token_ids:
            continue
        reordered.append(token)
        if id(token) in moved_by_head:
            reordered.extend(sorted(moved_by_head[id(token)], key=lambda candidate: candidate.i))
    return reordered


def _glossify(tokens) -> Iterator[GlossItem]:
    for token in tokens:
        if token.pos_ in {"PUNCT", "SPACE", "SYM", "X"}:
            continue
        if _is_aux_not_main(token):
            continue

        lemma_lower = token.lemma_.lower()
        if lemma_lower in _FILLER_LEMMAS:
            continue
        if token.pos_ == "DET" and lemma_lower not in _KEEP_DETERMINER_LEMMAS and lemma_lower not in _ARTICLES:
            continue
        if lemma_lower in _ARTICLES or token.text == "'s":
            continue
        if lemma_lower == "be" and token.dep_ == "ROOT" and _has_predicate_complement(token, tokens):
            continue

        if _is_negation(token):
            gloss = "NONE" if lemma_lower in {"none", "nothing", "nobody", "nowhere"} else "NOT"
        elif token.ent_type_ in {"PERSON", "GPE", "LOC", "ORG", "PRODUCT"}:
            gloss = token.text.upper()
        elif token.pos_ in {"PRON", "DET"}:
            gloss = token.text.upper()
        else:
            gloss = _safe_upper_lemma(token)

        yield GlossItem(word=token.text, gloss=gloss)


def _clause_to_gloss_en(clause) -> list[GlossItem]:
    tokens = [token for token in clause if token.pos_ != "SPACE"]

    time_tokens = _extract_time_tokens(tokens)
    wh_tokens = [token for token in tokens if _is_wh_token(token)]
    neg_tokens = [token for token in tokens if _is_negation(token)]
    modal_tokens = [token for token in tokens if _is_modal(token) and not _is_aux_not_main(token)]

    reserved_ids = {id(token) for token in time_tokens + wh_tokens + neg_tokens + modal_tokens}
    main_tokens = [token for token in tokens if id(token) not in reserved_ids]
    main_tokens = _reorder_nominals(main_tokens)

    ordered_tokens = []
    ordered_tokens.extend(time_tokens)
    ordered_tokens.extend(main_tokens)
    ordered_tokens.extend(modal_tokens)
    ordered_tokens.extend(neg_tokens)
    if _looks_like_question(tokens):
        ordered_tokens.extend(wh_tokens)
    else:
        ordered_tokens.extend(wh_tokens)

    return list(_glossify(_ordered_unique(ordered_tokens)))


def text_to_gloss(text: str, language: str = "en", **unused_kwargs) -> list[Gloss]:
    if language != "en":
        raise NotImplementedError("This project only supports English input.")
    if text.strip() == "":
        return [[]]

    spacy_model = load_spacy_model(ENGLISH_SPACY_MODELS)
    doc = spacy_model(text)
    clauses = [list(sentence) for sentence in doc.sents]
    return [_clause_to_gloss_en(clause) for clause in clauses if clause]
