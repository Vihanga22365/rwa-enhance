"""Prompt for the issue-classification agent (app/agents/classifier.py).

The issue type list is NOT hardcoded here - it is built at call time from
whichever issue types the currently-loaded decision-tree workbook defines
(app/data/decision_trees.py:list_issue_types()), so swapping in a different
workbook never requires touching this file.
"""

ISSUE_CLASSIFICATION_PROMPT = """
Think step by step very carefully.
Classify the issue type based on the given input text.

Available Issue Types:
{issue_type_list}

Match the input text to the issue type whose name best fits the intent of the
email content, even if the exact wording differs - use synonyms, partial
matches, and related financial/risk concepts. Base the match only on the
issue type names listed above; do not invent or use any other category.

Please return only the matched issue type exactly as written above, or
'No Issue Matched' if none apply. Do not print any other text/numbers or
explanation.

Input Text: {input_text}
"""
