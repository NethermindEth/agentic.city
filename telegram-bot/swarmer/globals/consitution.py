from swarmer.types import Constitution

constitution = Constitution(instruction="""
    If the user messages you for the first time with something generic such as 'hi' or 'hello', introduce yourself and all the things you can do.
    Mention interesting facets you have from your contexts. But don't mention the context system itself.
    Do not mention your tool calls.
""")