import os
from groq import Groq


def get_ai_analysis(resume_text):

    prompt = f"""
You are an expert AI resume reviewer.

Analyze the following resume:

----------------
{resume_text}
----------------


Give the response in this format:

1. Resume Strengths:
-

2. Missing Skills:
-

3. Improvement Suggestions:
-

4. Recommended Job Roles:
-
"""

    client = Groq(
        api_key=os.getenv("GROQ_API_KEY")
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content