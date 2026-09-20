print("🔥 USING THIS GROQ_AI.PY FILE")
print("🔥 FILE PATH:", __file__)
print("MODEL BEING USED:", "openai/gpt-oss-20b")
import os
import json
from groq import Groq


def get_ai_analysis(resume_text, job_role):

    prompt = f"""
You are an expert ATS (Applicant Tracking System) Resume Analyzer, Technical Recruiter, and Career Advisor.

Your task is to analyze a candidate resume STRICTLY against ONE selected job role.
The ATS score must measure how well this specific resume fits this specific job role
— NOT how well-written the resume is in general.

Selected Job Role:
{job_role}


Candidate Resume:
----------------
{resume_text}
----------------


FOLLOW THIS EXACT STEP-BY-STEP METHOD BEFORE SCORING:

STEP 1 — Build the role's requirement profile:
Internally list the 10-15 core skills, tools, and competencies that a real employer
would expect for the "{job_role}" role (e.g. for "Frontend Developer" that would be
HTML, CSS, JavaScript, a UI framework like React/Vue/Angular, responsive design,
browser dev tools, etc. For "AI Engineer" that would be Python, ML/DL frameworks,
model training, data pipelines, etc. Build this list yourself based on the role name
— do not reuse the same list for a different role).

STEP 2 — Compare the resume against that requirement profile:
Count how many of those core skills/competencies actually appear (directly or through
equivalent project/experience evidence) in the resume. Compute a rough match ratio:
matched_core_skills / total_core_skills_for_role.

STEP 3 — Score each weighted component using that match ratio as the primary driver
(not general resume polish):

- Technical Skills (40%): score proportional to how many role-required technical
  skills are present in the resume. If almost none of the role's core skills are
  present, this component must be LOW (below 10 out of 40), even if the candidate
  has strong skills in a completely different domain.
- Projects (20%): score based on how relevant the candidate's projects are to THIS
  role's day-to-day work, not just project quality in general.
- Internship / Experience (15%): score based on how relevant the experience is to
  THIS role.
- Education (10%): score based on how well the degree/coursework supports THIS role.
- Certifications (5%): only count certifications relevant to THIS role.
- Resume Quality (10%): formatting, clarity, structure — this is the ONLY component
  that should stay roughly stable across different job roles for the same resume.

STEP 4 — Add the five weighted components together for the final ats_score (0-100).

HARD RULE: If the resume's actual background (skills/projects/experience) belongs to
a clearly different domain than the selected job role (e.g. a Data Science/AI resume
evaluated for "Frontend Developer", or a Backend resume evaluated for "Data Analyst"),
the final ats_score MUST fall below 40, regardless of how strong or well-formatted the
resume is. A resume that is a strong match for the selected role should score 70+.
A partial/adjacent match (e.g. Python Developer resume for "Backend Developer") should
land roughly in the 45-70 range depending on overlap. Do not default to a "generic
quality" score — the role match ratio from Step 2 must visibly drive the score.

The same resume evaluated against different job roles in separate calls MUST produce
noticeably different ats_score values reflecting the actual fit for each role, and the
ats_score_explanation must reference the specific role's requirements, not generic
resume praise.


Also generate the following, all still specific to the selected job role:

1. ats_score_explanation:
Explain the score using the Step 1-4 reasoning above — mention which core role-required
skills were found, which were missing, and how that drove the score. 3-4 concise,
specific points only.

2. skills_matched:
- Only skills actually present in the resume.
- Prioritize the ones relevant to the selected job role's requirement profile.

3. missing_skills:
- Important skills from the role's requirement profile (Step 1) that are absent from
  the resume.
- Do not include skills already present in the resume.

4. strengths:
Strongest points of the resume specifically in relation to this job role.

5. weaknesses:
Gaps specifically in relation to this job role.

6. recommended_job_roles:
Suggest roles that best fit the candidate's ACTUAL skills/projects/education/experience
as found in the resume (these may differ from the selected job role if the resume
doesn't match it well).

7. improvement_suggestions:
Practical resume improvement suggestions, focused on better positioning the candidate
for the selected job role where possible.

8. learning_roadmap:
Next learning steps to close the gap between the candidate's current profile and the
selected job role's requirement profile.


IMPORTANT RULES:

- Analyze every resume differently.
- Do not copy example values.
- Do not always return the same skills or the same score across different job roles.
- Generate results only from the provided resume text — do not invent experience.
- The ats_score must clearly reflect fit with the selected job role, following Steps 1-4.
- Keep suggestions realistic.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not include ```json.
- Do not add explanations outside JSON.


Return JSON in exactly this structure:


{{
    "ats_score": 0,

    "ats_score_explanation": [
        "reason 1",
        "reason 2",
        "reason 3"
    ],

    "skills_matched": [
        "skill found in resume"
    ],

    "missing_skills": [
        "skill required for selected job role but missing"
    ],

    "strengths": [
        "candidate strength"
    ],

    "weaknesses": [
        "candidate weakness"
    ],

    "recommended_job_roles": [
        "recommended role 1",
        "recommended role 2"
    ],

    "improvement_suggestions": [
        "suggestion 1",
        "suggestion 2"
    ],

    "learning_roadmap": [
        "learning step 1",
        "learning step 2"
    ]
}}

"""


    client = Groq(
        api_key=os.getenv("GROQ_API_KEY")
    )

    print("MODEL BEING USED:", "openai/gpt-oss-20b")
    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.3
    )


    ai_response = response.choices[0].message.content.strip()


    # Remove markdown if AI returns it
    ai_response = ai_response.replace("```json", "")
    ai_response = ai_response.replace("```", "")

    ai_response = ai_response.strip()


    try:

        result = json.loads(ai_response)

        return result


    except json.JSONDecodeError:

        return {

            "ats_score": 0,

            "ats_score_explanation": [
                "Unable to generate ATS explanation"
            ],

            "skills_matched": [],

            "missing_skills": [],

            "strengths": [],

            "weaknesses": [],

            "recommended_job_roles": [],

            "improvement_suggestions": [
                "AI response could not be processed"
            ],

            "learning_roadmap": []

        }