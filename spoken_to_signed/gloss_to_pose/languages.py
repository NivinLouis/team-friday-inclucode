LANGUAGE_BACKUP = {
    "ins": "ase",  # Indian Sign Language falls back to American Sign Language
}


def languages_set(signed_language: str):
    if signed_language in LANGUAGE_BACKUP:
        return {signed_language}.union(languages_set(LANGUAGE_BACKUP[signed_language]))

    return {signed_language}
