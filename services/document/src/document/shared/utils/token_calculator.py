from litellm import token_counter

def tokens_calculator(text: str, model: str = "gemini-2.5-flash") -> int:
    """Calculate the number of tokens for a given model and text.

    Args:
        text (str): The text to analyze.
        model (str): The model to use for token calculation.

    Returns:
        int: The number of tokens in the text.
    """
    return token_counter(model=model, text=text)