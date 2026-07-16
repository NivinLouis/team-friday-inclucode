from types import SimpleNamespace

from spoken_to_signed.text_to_gloss.rules import _clause_to_gloss_en


def _make_token(i, text, lemma, pos, dep, tag="", ent_type=""):
    token = SimpleNamespace(
        i=i,
        text=text,
        lemma_=lemma,
        pos_=pos,
        dep_=dep,
        tag_=tag,
        ent_type_=ent_type,
        head=None,
        subtree=[],
    )
    token.morph = ""
    return token


def _finalize(tokens, heads):
    for token, head_index in zip(tokens, heads):
        token.head = token if head_index is None else tokens[head_index]
    for token in tokens:
        token.subtree = [token]
    return tokens


def test_clause_to_gloss_en_moves_time_and_modal():
    tokens = _finalize(
        [
            _make_token(0, "Tomorrow", "tomorrow", "NOUN", "npadvmod"),
            _make_token(1, "I", "I", "PRON", "nsubj"),
            _make_token(2, "can", "can", "AUX", "aux", tag="MD"),
            _make_token(3, "go", "go", "VERB", "ROOT"),
            _make_token(4, ".", ".", "PUNCT", "punct"),
        ],
        [3, 3, 3, None, 3],
    )

    output = _clause_to_gloss_en(tokens)

    assert [item.gloss for item in output] == ["TOMORROW", "I", "GO", "CAN"]


def test_clause_to_gloss_en_keeps_possessive_and_moves_adjective_after_noun():
    tokens = _finalize(
        [
            _make_token(0, "My", "my", "DET", "poss"),
            _make_token(1, "big", "big", "ADJ", "amod"),
            _make_token(2, "dog", "dog", "NOUN", "nsubj"),
            _make_token(3, "runs", "run", "VERB", "ROOT"),
            _make_token(4, ".", ".", "PUNCT", "punct"),
        ],
        [2, 2, 3, None, 3],
    )

    output = _clause_to_gloss_en(tokens)

    assert [item.gloss for item in output] == ["MY", "DOG", "BIG", "RUN"]


def test_clause_to_gloss_en_moves_negation_and_wh_to_end():
    tokens = _finalize(
        [
            _make_token(0, "Why", "why", "ADV", "advmod", tag="WRB"),
            _make_token(1, "is", "be", "AUX", "ROOT"),
            _make_token(2, "John", "John", "PROPN", "nsubj", ent_type="PERSON"),
            _make_token(3, "not", "not", "PART", "neg"),
            _make_token(4, "home", "home", "ADJ", "acomp"),
            _make_token(5, "?", "?", "PUNCT", "punct"),
        ],
        [1, None, 1, 4, 1, 1],
    )

    output = _clause_to_gloss_en(tokens)

    assert [item.gloss for item in output] == ["JOHN", "HOME", "NOT", "WHY"]
