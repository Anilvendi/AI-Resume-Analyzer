import ollama


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


    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


    return response["message"]["content"]