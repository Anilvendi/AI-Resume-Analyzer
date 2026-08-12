import ast
import io
import streamlit as st
import time

from authentication.database import create_database, get_user
from authentication.auth import signup, login
from resume_analyzer.pdf_reader import extract_text
from resume_analyzer.resume_analysis import analyze_resume  # kept for compatibility, not used in flow
from resume_analyzer.groq_ai import get_ai_analysis
from aws.dynamodb_services import save_resume_analysis, get_resume_history, delete_resume_analysis


# ==============================
# Reusable UI helper functions
# ==============================

def render_skill_badges(skills, badge_type="green"):
    """
    Render a list of skills as colored badges.
    badge_type: "green" for matched skills, "red" for missing skills.
    """
    css_class = "skill-badge-green" if badge_type == "green" else "skill-badge-red"

    if skills:
        badges_html = "".join(
            f'<span class="skill-badge {css_class}">{skill}</span>'
            for skill in skills
        )
        st.markdown(badges_html, unsafe_allow_html=True)
    else:
        if badge_type == "green":
            st.warning("No matched skills detected.")
        else:
            st.success("Excellent! No important skills are missing.")


def score_color(score):
    """Return (bar_color, label_color, label_bg) based on ATS score band."""
    if score >= 80:
        return "#10b981", "#065f46", "#d1fae5"   # green
    elif score >= 50:
        return "#f59e0b", "#92400e", "#fef3c7"   # amber
    else:
        return "#ef4444", "#991b1b", "#fee2e2"   # red


def render_score_card(score):
    """
    Renders the ATS score as a circular (donut) progress indicator
    instead of a horizontal bar.
    """
    bar_color, label_color, label_bg = score_color(score)
    pct = min(max(score, 0), 100)

    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-card-top">
                <span class="score-card-title">📈 ATS Compatibility Score</span>
                <span class="score-pill" style="background:{label_bg}; color:{label_color};">
                    {score} / 100
                </span>
            </div>
            <div class="score-circle-wrap">
                <div class="score-circle-outer" style="background:conic-gradient({bar_color} {pct}%, #e2e8f0 0);">
                    <div class="score-circle-inner">
                        <span class="score-circle-value" style="color:{label_color};">{score}</span>
                        <span class="score-circle-suffix">/ 100</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def build_history_summary(result):
    """
    Trim the full AI result down to the fields shown in the history
    section: ATS score, matched/missing skills, improvement
    suggestions, recommended job roles, and the learning roadmap.
    Strengths / weaknesses are intentionally not kept in history.
    Full raw AI output is only shown right after analysis, not stored.
    """
    return {
        "ats_score": result.get("ats_score", 0),
        "skills_matched": result.get("skills_matched", []),
        "missing_skills": result.get("missing_skills", []),
        "improvement_suggestions": result.get("improvement_suggestions", []),
        "recommended_job_roles": result.get("recommended_job_roles", []),
        "learning_roadmap": result.get("learning_roadmap", []),
    }


def section_header(icon, title):
    st.markdown(
        f"""<div class="section-box-header">{icon} {title}</div>""",
        unsafe_allow_html=True
    )


def render_resume_analysis_box(result):
    """
    Renders the "Resume Analysis" box: ATS score, skills matched/missing,
    and resume improvement suggestions. Shows a placeholder blurb before
    any analysis has run.
    """
    with st.container(border=True):
        section_header("📄", "Resume Analysis")

        if not result:
            st.info(
                """
                Upload your resume and get:

                • ATS Score

                • Skill Matched

                • Skill Missing

                • Resume Improvement Suggestions

                """
            )
            return

        render_score_card(result.get("ats_score", 0))

        # Only show the most important reasons behind the score
        # (max 4 points) instead of a long list.
        ats_explanation = result.get("ats_score_explanation")
        if ats_explanation:
            st.markdown("**ℹ️ Why this score?**")
            for point in ats_explanation[:4]:
                st.info(point)

        st.write("")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ Skills Matched**")
            render_skill_badges(result.get("skills_matched"), badge_type="green")
        with col2:
            st.markdown("**❌ Missing Skills**")
            render_skill_badges(result.get("missing_skills"), badge_type="red")

        st.write("")
        st.markdown("**💡 Resume Improvement Suggestions**")
        suggestions = result.get("improvement_suggestions")
        if suggestions:
            for suggestion in suggestions:
                st.markdown(f"<div class='suggestion-item'>• {suggestion}</div>", unsafe_allow_html=True)
        else:
            st.caption("No improvement suggestions available.")


def render_career_assistant_box(result):
    """
    Renders the "Career Assistant" box: recommended job roles,
    strengths/weaknesses, and the learning roadmap. Shows a placeholder
    blurb before any analysis has run.
    """
    with st.container(border=True):
        section_header("🎯", "Career Assistant")

        if not result:
            st.info(
                """
                Get:

                • Job Role Suggestions

                • Strengths

                • Weaknesses

                • Learning Roadmap
                """
            )
            return

        st.markdown("**🚀 Recommended Job Roles**")
        recommended_roles = result.get("recommended_job_roles")
        if recommended_roles:
            # Each role on its own line instead of side-by-side.
            roles_html = "".join(
                f'<div class="role-badge">{idx}. {role}</div>'
                for idx, role in enumerate(recommended_roles, start=1)
            )
            st.markdown(roles_html, unsafe_allow_html=True)
        else:
            st.caption("No job role recommendations available.")

        st.write("")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**💪 Strengths**")
            strengths = result.get("strengths")
            if strengths:
                for strength in strengths:
                    st.success(f"✅ {strength}")
            else:
                st.caption("No strengths identified.")
        with col2:
            st.markdown("**⚠️ Weaknesses**")
            weaknesses = result.get("weaknesses")
            if weaknesses:
                for weakness in weaknesses:
                    st.warning(f"⚠️ {weakness}")
            else:
                st.caption("No weaknesses identified.")

        st.write("")
        st.markdown("**🗺️ Learning Roadmap**")
        roadmap = result.get("learning_roadmap")
        if roadmap:
            for step_num, step in enumerate(roadmap, start=1):
                st.markdown(f"**Step {step_num}:** {step}")
        else:
            st.caption("No learning roadmap available.")


def display_history_summary(result):
    """
    Renders the trimmed summary stored per history record.
    Resume Analysis: ATS score, skills matched, skills missing,
    improvement suggestions.
    Career Assistant: recommended job roles and learning roadmap only
    (strengths / weaknesses are not shown in history).
    """

    with st.container(border=True):
        section_header("📄", "Resume Analysis")

        render_score_card(result.get("ats_score", 0))

        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ Skills Matched**")
            render_skill_badges(result.get("skills_matched"), badge_type="green")
        with col2:
            st.markdown("**❌ Missing Skills**")
            render_skill_badges(result.get("missing_skills"), badge_type="red")

        suggestions = result.get("improvement_suggestions")
        if suggestions:
            st.write("")
            st.markdown("**💡 Resume Improvement Suggestions**")
            for suggestion in suggestions:
                st.markdown(f"<div class='suggestion-item'>• {suggestion}</div>", unsafe_allow_html=True)

    recommended_roles = result.get("recommended_job_roles")
    roadmap = result.get("learning_roadmap")

    if recommended_roles or roadmap:
        st.write("")
        with st.container(border=True):
            section_header("🎯", "Career Assistant")

            if recommended_roles:
                st.markdown("**🚀 Recommended Job Roles**")
                roles_html = "".join(
                    f'<div class="role-badge">{idx}. {role}</div>'
                    for idx, role in enumerate(recommended_roles, start=1)
                )
                st.markdown(roles_html, unsafe_allow_html=True)
                st.write("")

            if roadmap:
                st.markdown("**🗺️ Learning Roadmap**")
                for step_num, step in enumerate(roadmap, start=1):
                    st.markdown(f"**Step {step_num}:** {step}")


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🚀",
    layout="wide"
)

create_database()

# ---------------- CSS ----------------

st.markdown("""
<style>
:root {
    --primary: #4f46e5;
    --primary-dark: #4338ca;
    --accent: #0d9488;
    --text-dark: #1e293b;
    --text-muted: #64748b;
    --card-bg: #ffffff;
    --card-border: #e5e7eb;
}

.stApp {
    background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 50%, #ddd6fe 100%);
}
.main-title {
    font-size: 52px;
    font-weight: 800;
    text-align: center;
    margin-top: 40px;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    font-size: 20px;
    color: var(--text-muted);
    text-align: center;
    margin-bottom: 40px;
}

.card {
    background-color: var(--card-bg);
    padding: 26px;
    border-radius: 16px;
    text-align: center;
    border: 1px solid var(--card-border);
    box-shadow: 0px 6px 18px rgba(79, 70, 229, 0.08);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0px 10px 24px rgba(79, 70, 229, 0.14);
}

.upload-success, .success-message {
    background-color: #ecfdf5;
    color: #047857;
    padding: 14px;
    border-radius: 12px;
    text-align: center;
    font-size: 17px;
    font-weight: 600;
    margin: 18px auto;
    width: 60%;
    border: 1px solid #a7f3d0;
}

/* Compact "ready to analyze" pill — sized to match the Analyze Resume
   button's column instead of the wide 60%-page-width message above. */
.ready-message {
    background-color: #ecfdf5;
    color: #047857;
    padding: 10px 14px;
    border-radius: 8px;
    text-align: center;
    font-size: 15px;
    font-weight: 600;
    width: 100%;
    margin: 10px 0;
    border: 1px solid #a7f3d0;
}

.error-message {
    background-color: #fef2f2;
    color: #b91c1c;
    padding: 14px;
    border-radius: 12px;
    text-align: center;
    font-size: 17px;
    font-weight: 600;
    width: 60%;
    margin: 18px auto;
    border: 1px solid #fecaca;
}

.custom-message {
    background-color: var(--card-bg);
    padding: 20px 24px;
    border-radius: 14px;
    border: 1px solid var(--card-border);
    box-shadow: 0px 4px 14px rgba(15, 23, 42, 0.05);
}

.skill-badge {
    display: inline-block;
    padding: 6px 14px;
    margin: 4px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
}
.skill-badge-green {
    background-color: #d1fae5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}
.skill-badge-red {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
}

/* Recommended job roles now stack one per line instead of inline. */
.role-badge {
    display: block;
    width: fit-content;
    padding: 8px 16px;
    margin: 0 0 8px 0;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    background-color: #eef2ff;
    color: var(--primary-dark);
    border: 1px solid #c7d2fe;
}

.suggestion-item {
    padding: 8px 4px;
    color: var(--text-dark);
    font-size: 15px;
    border-bottom: 1px dashed #e2e8f0;
}

.score-card {
    background-color: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0px 4px 14px rgba(15, 23, 42, 0.05);
}
.score-card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.score-card-title {
    font-size: 17px;
    font-weight: 700;
    color: var(--text-dark);
}
.score-pill {
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 15px;
}

/* Circular ATS score indicator (donut) */
.score-circle-wrap {
    display: flex;
    justify-content: center;
    padding: 10px 0 4px 0;
}
.score-circle-outer {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.score-circle-inner {
    width: 112px;
    height: 112px;
    border-radius: 50%;
    background-color: var(--card-bg);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.score-circle-value {
    font-size: 32px;
    font-weight: 800;
    line-height: 1.1;
}
.score-circle-suffix {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
}

.section-box-header {
    font-size: 20px;
    font-weight: 700;
    color: var(--text-dark);
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid #ede9fe;
}

.auth-title {
    font-size: 26px;
    font-weight: 800;
    text-align: center;
    color: var(--text-dark);
    margin-bottom: 4px;
}
.auth-subtitle {
    font-size: 14px;
    color: var(--text-muted);
    text-align: center;
    margin-bottom: 18px;
}

div.stButton > button[kind="primary"] {
    background-color: var(--primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}
div.stButton > button[kind="primary"]:hover {
    background-color: var(--primary-dark);
    color: white;
}
div.stButton > button:not([kind="primary"]) {
    border-radius: 8px;
}

/* ---- Analyze Resume button: green only ----
   Scoped to the button's own wrapper via its Streamlit `key`
   (Streamlit auto-adds a "st-key-<key>" class to that wrapper), so
   this ONLY affects the Analyze Resume button and leaves every other
   button (Login, Signup, Logout, Delete, etc.) untouched. */
.st-key-analyze_resume_btn button[kind="primary"] {
    background-color: #16a34a;
    border-color: #16a34a;
}
.st-key-analyze_resume_btn button[kind="primary"]:hover {
    background-color: #15803d;
    border-color: #15803d;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ---------------- Session State ----------------

if "show_signup" not in st.session_state:
    st.session_state.show_signup = False

if "show_login" not in st.session_state:
    st.session_state.show_login = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "resume"

if "login_success" not in st.session_state:
    st.session_state.login_success = False

if "last_analysis_result" not in st.session_state:
    st.session_state.last_analysis_result = None

# Tracks which uploaded file we've already shown the "ready" pill for,
# so it only appears once right after upload — not on every rerun
# triggered by picking a job role or clicking Analyze.
if "ready_pill_shown_for" not in st.session_state:
    st.session_state.ready_pill_shown_for = None

# Tracks the last selected job role so we can detect a *change* and
# clear any previously displayed analysis result.
if "last_job_role" not in st.session_state:
    st.session_state.last_job_role = None


# ---------------- Header ----------------

if not st.session_state.logged_in:

    col1, col2, col3 = st.columns([7, 0.8, 0.8])

    with col2:
        if st.button("Signup"):
            st.session_state.show_signup = True
            st.session_state.show_login = False

    with col3:
        if st.button("Login"):
            st.session_state.show_login = True
            st.session_state.show_signup = False


# ---------------- Home Page ----------------

if (not st.session_state.logged_in
        and not st.session_state.show_signup
        and not st.session_state.show_login):

    st.markdown(
        '<h1 class="main-title">AI Resume Analyzer</h1>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p class="subtitle">
        Analyze your resume using Artificial Intelligence and
        improve your chances of getting hired.
        </p>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="card">
            <h3>📄 Resume Analysis</h3>
            <p>Upload your resume and get AI-based feedback.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="card">
            <h3>🎯 Skill Matching</h3>
            <p>Find missing skills according to job requirements.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="card">
            <h3>🚀 Career Growth</h3>
            <p>Improve your resume and increase opportunities.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")
    st.info("Login or Signup to start analyzing your resume.")


# ---------------- Signup ----------------
# Centered, compact card — narrow middle column keeps the fields small
# instead of stretching full page width.

if st.session_state.show_signup and not st.session_state.logged_in:

    left, mid, right = st.columns([1.3, 1, 1.3])

    with mid:
        with st.container(border=True):
            st.markdown('<div class="auth-title">Create Account</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subtitle">Join to start analyzing your resume</div>', unsafe_allow_html=True)

            name = st.text_input("Username *", key="signup_name")
            email = st.text_input("Email *", key="signup_email")
            password = st.text_input("Password *", type="password", key="signup_password")

            if st.button("Create Account", type="primary", use_container_width=True):

                success, message = signup(name, email, password)

                if success:
                    st.session_state.show_signup = False
                    st.session_state.show_login = True
                    st.session_state.signup_success = True
                    st.rerun()
                else:
                    st.error(message)


# ---------------- Signup Success Message ----------------

if st.session_state.get("signup_success"):

    st.markdown(
        """
        <div class="success-message">
            🎉 Account Created Successfully<br>
            Please Login to Continue
        </div>
        """,
        unsafe_allow_html=True
    )

    st.session_state.signup_success = False


# ---------------- Login ----------------
# Wider centered card than Signup so the "Login Successful" message has
# room to sit on one line instead of wrapping.

if st.session_state.show_login and not st.session_state.logged_in:

    left, mid, right = st.columns([1.3, 1, 1.3])

    with mid:
        with st.container(border=True):
            st.markdown('<div class="auth-title">Welcome Back</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subtitle">Login to continue</div>', unsafe_allow_html=True)

            email = st.text_input("Email *", key="login_email")
            password = st.text_input("Password *", type="password", key="login_password")

            if st.button("Login Now", type="primary", use_container_width=True):

                if login(email, password):

                    user = get_user(email)

                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.username = user["email"]

                    st.markdown(
                        """<div class="success-message">✅ Login Successful</div>""",
                        unsafe_allow_html=True
                    )

                    time.sleep(1)

                    st.session_state.show_login = False
                    st.session_state.show_signup = False
                    st.session_state.login_success = False

                    st.rerun()

                else:
                    st.error("Invalid Email or Password")


# ==============================
# Dashboard
# ==============================

if st.session_state.logged_in:

    # user_id is needed everywhere below (analysis, history)
    user_id = st.session_state.user["user_id"]

    # ---------------- Dashboard Header ----------------

    col1, col2 = st.columns([9, 0.8], vertical_alignment="center")

    with col1:
        st.markdown(
            """
            <h1 style="text-align:center;">
                 Welcome to Your AI Career Assistant 🚀
            </h1>
            """,
            unsafe_allow_html=True
        )

    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user = None
            st.session_state.show_login = False
            st.session_state.show_signup = False
            st.session_state.last_analysis_result = None
            st.session_state.ready_pill_shown_for = None
            st.session_state.last_job_role = None
            st.rerun()

    st.write("")

    # ---------------- Welcome Card ----------------

    st.markdown(
        f"""
        <div class="custom-message">
        <b>👋 Welcome, <span style="color:var(--primary-dark);">{st.session_state.username}</span></b>
        <br>
        <h3 style="margin-top:6px;"><b>Start improving your resume with AI-powered analysis.</b></h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # ---------------- Resume Analysis / Career Assistant boxes ----------------
    # Static placeholder boxes right below the welcome card. The real
    # results are shown further down, below the Analyze Resume button.

    col1, col2 = st.columns(2)

    with col1:
        render_resume_analysis_box(None)

    with col2:
        render_career_assistant_box(None)

    st.write("")

    # ---------------- Resume Upload Section ----------------
    # Heading stays left-aligned; the actual upload widget, job-role
    # picker, and analyze button are centered in a narrow middle column.

    st.subheader("📤 Upload Resume")

    up_col, _ = st.columns([2, 3])
    with up_col:
        uploaded_file = st.file_uploader(
            "Choose your resume PDF",
            type=["pdf"]
        )

    if uploaded_file:
        # Check resume file size (Maximum 1 MB)
        max_size = 1 * 1024 * 1024  # 1 MB
        if uploaded_file.size > max_size:
            st.markdown("""<div class="error-message">
                ❌ Resume size should be less than 1 MB.
                </div>
                """,
                unsafe_allow_html=True
            )
            st.stop()

        # Read the file content once into memory. No S3 upload — the
        # resume is only used in-memory for text extraction, then
        # discarded once analysis is done.
        file_bytes = uploaded_file.getvalue()

        # Show the "ready to analyze" pill ONLY the first time this
        # specific file is seen. Picking a job role or clicking
        # Analyze triggers a rerun with the same file_id, so the pill
        # is skipped on those reruns.
        if st.session_state.ready_pill_shown_for != uploaded_file.file_id:
            st.session_state.ready_pill_shown_for = uploaded_file.file_id

            ready_col1, ready_col2, ready_col3 = st.columns([1, 2, 1])
            with ready_col2:
                ready_placeholder = st.empty()
                ready_placeholder.markdown(
                    '<div class="ready-message">✅ Resume Loaded — ready to analyze</div>',
                    unsafe_allow_html=True
                )
            time.sleep(2)
            ready_placeholder.empty()

        st.markdown(
            """
            <h3 style="color:var(--text-dark);">
                🎯 Select Your Target Job Role
            </h3>
            """,
            unsafe_allow_html=True
        )

        # Preset roles + an "Other" option that reveals a free-text
        # field, so the user can either pick from the list or type
        # their own job role — either way it flows into `job_role`.
        PRESET_JOB_ROLES = [
            "AWS Cloud Engineer",
            "Python Developer",
            "AI Engineer",
            "Data Analyst",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
        ]
        OTHER_ROLE_OPTION = "✏️ Other (type your own)"

        role_col, _ = st.columns([2, 3])
        with role_col:
            selected_option = st.selectbox(
                "",
                PRESET_JOB_ROLES + [OTHER_ROLE_OPTION],
                index=None,
                placeholder="Choose Job Role or select 'Other' to type your own"
            )

            job_role = selected_option

            if selected_option == OTHER_ROLE_OPTION:
                custom_role = st.text_input(
                    "Enter your target job role",
                    key="custom_job_role",
                    placeholder="e.g. DevOps Engineer"
                )
                # Use the typed value as the actual job role once the
                # user has entered something; otherwise leave it
                # unset so the "please select a job role" check below
                # still applies.
                job_role = custom_role.strip() if custom_role.strip() else None

        # Changing the job role invalidates any previously displayed
        # analysis result, so stale results don't linger on screen.
        if job_role != st.session_state.last_job_role:
            st.session_state.last_job_role = job_role
            st.session_state.last_analysis_result = None

        resume_text = extract_text(io.BytesIO(file_bytes))

        # ---------------- Resume Analysis Section ----------------

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            analyze_clicked = st.button(
                "📊 Analyze Resume",
                use_container_width=True,
                type="primary",
                key="analyze_resume_btn"
            )

        if analyze_clicked:

            if not job_role:
                st.warning("Please select or enter a job role")

            else:
                try:
                    with st.spinner("🔍 Analyzing your resume..."):
                        result = get_ai_analysis(resume_text, job_role)
                except Exception as exc:
                    # Groq/network errors land here instead of crashing
                    # the whole page with a raw traceback.
                    st.markdown(
                        f"""<div class="error-message">
                        ❌ Couldn't reach the AI service. Please check your
                        internet connection and try again.<br>
                        <span style="font-size:13px; font-weight:400;">({exc})</span>
                        </div>""",
                        unsafe_allow_html=True
                    )
                    st.stop()

                # Only store the trimmed summary that's actually useful
                # for tracking progress in history — not the full
                # raw AI response.
                history_summary = build_history_summary(result)

                save_resume_analysis(
                    user_id,
                    uploaded_file.name,
                    job_role,
                    result.get("ats_score", 0),
                    history_summary
                )

                # Keep the full result in session_state so it stays
                # visible below the button on later reruns too (e.g.
                # expanding/deleting history).
                st.session_state.last_analysis_result = result

                st.success("✅ Resume analyzed successfully! See your results below.")

        # Results are shown directly below the Analyze Resume button.
        if st.session_state.last_analysis_result:
            st.write("")
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                render_resume_analysis_box(st.session_state.last_analysis_result)
            with res_col2:
                render_career_assistant_box(st.session_state.last_analysis_result)

    # ---------------- Resume History ----------------

    st.divider()
    st.subheader("📜 Your Analysis History")

    history = get_resume_history(user_id)

    if history:
        for record in history:
            with st.expander(
                f"📄 {record['file_name']} — {record['job_role']} — {record['uploaded_date']}"
            ):
                result = record["analysis_result"]

                # Old records saved before this change may still have
                # str(dict) or the full raw result — handle both.
                if isinstance(result, str):
                    try:
                        result = ast.literal_eval(result)
                    except (ValueError, SyntaxError):
                        result = {}

                if not isinstance(result, dict):
                    result = {}

                display_history_summary(result)

                st.write("")

                if st.button(
                    "🗑️ Delete this analysis",
                    key=f"delete_{record['analysis_id']}"
                ):
                    delete_resume_analysis(user_id, record["analysis_id"])
                    st.success("Deleted.")
                    st.rerun()
    else:
        st.info("No previous analyses yet. Upload a resume above to get started.")