import wikipedia


def get_wikipedia_summary(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary

    except wikipedia.exceptions.DisambiguationError as e:
        return f"Your search is too broad. Try something more specific like {e.options[0]}."

    except wikipedia.exceptions.PageError:
        return "Sorry, I could not find anything on Wikipedia."

    except Exception as e:
        return f"Something went wrong: {e}"