from resume_analyzer.job_roles import JOB_ROLES

def analyze_resume(resume_text, job_role):

    text = resume_text.lower()


    # Get required skills based on selected job role
    required_skills = JOB_ROLES.get(job_role, [])


    found_skills = []
    missing_skills = []


    # Compare resume skills with job role skills
    for skill in required_skills:

        if skill.lower() in text:
            found_skills.append(skill)

        else:
            missing_skills.append(skill)



    # ---------------- ATS Score Calculation ----------------

    score = 0


    # Email check
    if "@" in text:
        score += 10


    # Phone number check
    if sum(c.isdigit() for c in text) >= 10:
        score += 10


    # Skills match score
    if found_skills:

        skill_score = min(len(found_skills) * 5, 30)

        score += skill_score



    # Education check
    if "education" in text or "b.tech" in text or "bachelor" in text:
        score += 15


    # Project check
    if "project" in text or "projects" in text:
        score += 15


    # Experience check
    if "experience" in text or "internship" in text:
        score += 20



    # Maximum score should be 100
    score = min(score, 100)



    # ---------------- Suggestions ----------------

    suggestions = []


    if not found_skills:

        suggestions.append(
            f"Add technical skills related to {job_role}."
        )


    if missing_skills:

        suggestions.append(
            "Consider learning missing skills: "
            + ", ".join(missing_skills[:5])
        )


    if "project" not in text:

        suggestions.append(
            "Add projects with technologies used and measurable results."
        )


    if "experience" not in text and "internship" not in text:

        suggestions.append(
            "Add internships or practical experience."
        )



    return {

        "job_role": job_role,

        "score": score,

        "skills": found_skills,

        "missing_skills": missing_skills,

        "suggestions": suggestions

    }