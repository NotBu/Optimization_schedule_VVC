"""Functions for creating, transforming, and adding prefixes to strings."""


def add_prefix_un(word):
    """Take the given word and add the 'un' prefix."""
    return "un" + word


def make_word_groups(vocab_words):
    """Transform a list containing a prefix and words."""
    prefix = vocab_words[0]
    result = [prefix]
    for word in vocab_words[1:]:
        result.append(prefix + word)
    return ' :: '.join(result)

def remove_suffix_ness(word):
    """Remove the suffix from the word while keeping spelling in mind.

    Parameters:
        word (str): Word to remove suffix from.

    Returns:
        str: Word with suffix removed & spelling adjusted.

    Examples:
        >>> remove_suffix_ness('heaviness')
        'heavy'

        >>> remove_suffix_ness('sadness')
        'sad'

    """
    word_out_ness= word[:-4]
    if word_out_ness[-1] == 'i':
        return word_out_ness[:-1] + 'y'
    return word[:-4]

def adjective_to_verb(sentence, index):
    """Change the adjective within the sentence to a verb.

    Parameters:
        sentence (str): The word used in a sentence as an adjective.
        index (int): Index of the adjective to remove and transform.

    Returns:
        str: The extracted adjective in verb form.

    Examples:
        >>> adjective_to_verb('It got dark as the sun set.', 2)
        'darken'

        >>> adjective_to_verb('The ink stains her fingers black.', -1)
        'blacken'

    """

    words = sentence.split()
    a_word = words[index]
    clean = a_word.strip('.')
    return clean + "en"