import ast
import io
import streamlit as st
import time

from authentication.database import create_database, get_user
from authentication.auth import signup, login
from resume_analyzer.pdf_reader import extract_text
from resume_analyzer.resume_analysis import analyze_resume
from resume_analyzer.groq_ai import get_ai_analysis
from aws.s3_services import upload_resume
from aws.dynamodb_services import save_resume_analysis, get_resume_history, delete_resume_analysis

create_database()

st.set_page_config(
    page_title="AI Resume Analyzer",
    layout="wide"
)

# ---------------- CSS ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg,
        #ede9fe,
        #ddd6fe
    );
}
.main-title {
    font-size: 55px;
    font-weight: 800;
    color: #1f2937;
    text-align: center;
    margin-top: 50px;
}

.subtitle {
    font-size: 22px;
    color: #4b5563;
    text-align: center;
    margin-bottom: 40px;
}

.card {
    background-color: #ffffff;
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
}
.upload-success {
    background-color: #e8f5e9;
    color: #2e7d32;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    margin: 20px auto;
    width: 60%;
}
.success-message {
    background-color: #e8f5e9;
    color: #2e7d32;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    width: 60%;
    margin: 20px auto;
}
.error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    width: 60%;
    margin: 20px auto;
}
.skill-badge {
    display: inline-block;
    padding: 6px 14px;
    margin: 5px;
    border-radius: 20px;
    font-size: 15px;
    font-weight: 600;
}
.skill-badge-green {
    background-color: #d1fae5;
    color: #065f46;
}
.skill-badge-red {
    background-color: #fee2e2;
    color: #991b1b;
}
div.stButton > button[kind="primary"] {
    background-color: #22c55e;
    color: white;
    border: none;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #16a34a;
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

if "show_ai_loading" not in st.session_state:
    st.session_state.show_ai_loading = False

if "uploaded_resume" not in st.session_state:
    st.session_state.uploaded_resume = False


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

if st.session_state.show_signup and not st.session_state.logged_in:

    st.subheader("Create Account")

    name = st.text_input("Username *", key="signup_name")
    email = st.text_input("Email *", key="signup_email")
    password = st.text_input("Password *", type="password", key="signup_password")

    if st.button("Create Account"):

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

if st.session_state.show_login and not st.session_state.logged_in:

    st.subheader("Login")

    email = st.text_input("Email *", key="login_email")
    password = st.text_input("Password *", type="password", key="login_password")

    if st.button("Login Now"):

        if login(email, password):

            user = get_user(email)

            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.username = user["email"]
            st.session_state.uploaded_resume = False

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

    # user_id is needed everywhere below (upload, analysis, history)
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
            st.session_state.uploaded_resume = False
            st.rerun()

    st.write("")

    # ---------------- Welcome Card ----------------

    st.markdown(
        f"""
        <div class="custom-message">
        <b>👋 Welcome, <span style="color:#1f2937;">{st.session_state.username}</span></b>
        <br>
        <h3><b>Start improving your resume with AI-powered analysis.</b></h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # ---------------- Dashboard Feature Cards ----------------

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Resume Analysis")
        st.info(
            """
            Upload your resume and get:

            • ATS Score

            • Skill Analysis
            """
        )

    with col2:
        st.subheader("🎯 Career Assistant")
        st.info(
            """
            Get:

            • Job Role Suggestions

            • Missing Skills
            """
        )

    st.write("")

    # ---------------- Resume Upload Section ----------------

    st.subheader("📤 Upload Resume")

    uploaded_file = st.file_uploader(
        "Choose your resume PDF",
        type=["pdf"]
    )

    if uploaded_file:

        # Read the file content ONCE into memory, so we can reuse it
        # safely for both S3 upload and text extraction without relying
        # on the original file object's seek/close state.
        file_bytes = uploaded_file.getvalue()

        # Upload to S3 only once per session
        if not st.session_state.uploaded_resume:

            # upload_resume() reads file.name to build the S3 key, so a
            # plain BytesIO won't work — attach the original filename to it.
            file_for_upload = io.BytesIO(file_bytes)
            file_for_upload.name = uploaded_file.name

            upload_status = upload_resume(file_for_upload, user_id)

            if upload_status:
                st.session_state.uploaded_resume = True

                st.markdown(
                    """
                    <div class="upload-success">
                        ✅ Resume Uploaded Successfully
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="error-message">
                        ❌ Resume Upload Failed. Please try again.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown(
            """
            <h2 style="font-size:28px; color:#1f2937;">
                🎯 Select Your Target Job Role
            </h2>
            """,
            unsafe_allow_html=True
        )

        job_role = st.selectbox(
            "",
            [
                "AWS Cloud Engineer",
                "Python Developer",
                "AI Engineer",
                "Data Analyst",
                "Frontend Developer",
                "Backend Developer",
                "Full Stack Developer"
            ],
            index=None,
            placeholder="Choose Job Role"
        )

        # Use a fresh BytesIO copy for text extraction — don't reuse
        # uploaded_file directly since upload_resume() may have consumed it.
        resume_text = extract_text(io.BytesIO(file_bytes))

        # ---------------- Resume Analysis Section ----------------

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            analyze_clicked = st.button(
                "📊 Analyze Resume",
                use_container_width=True,
                type="primary"
            )

        if analyze_clicked:

            if job_role is None:
                st.warning("Please select a job role")

            else:
                with st.spinner("🔍 Analyzing your resume..."):

                    result = analyze_resume(resume_text, job_role)

                    save_resume_analysis(
                        user_id,
                        uploaded_file.name,
                        job_role,
                        result["score"],
                        result
                    )

                st.success("✅ Resume analyzed successfully!")

                # ATS Score
                st.subheader("📈 Resume Score")
                st.metric(
                    label="ATS Compatibility Score",
                    value=f"{result['score']}%"
                )

                st.divider()

                # Skills Section
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("✅ Skills Found")

                    if result["skills"]:
                        skills_html = "".join(
                            f'<span class="skill-badge skill-badge-green">{skill}</span>'
                            for skill in result["skills"]
                        )
                        st.markdown(skills_html, unsafe_allow_html=True)
                    else:
                        st.warning("No skills detected.")

                with col2:
                    st.subheader("❌ Missing Skills")

                    if result["missing_skills"]:
                        missing_html = "".join(
                            f'<span class="skill-badge skill-badge-red">{skill}</span>'
                            for skill in result["missing_skills"]
                        )
                        st.markdown(missing_html, unsafe_allow_html=True)
                    else:
                        st.success("Excellent! No important skills are missing.")

                st.divider()

                st.subheader("💡 Resume Improvement Suggestions")

                for suggestion in result["suggestions"]:
                    st.write(f"✅ {suggestion}")

        # ---------------- AI Analysis ----------------

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            ai_clicked = st.button(
                "🤖 Generate AI Analysis",
                use_container_width=True
            )

        if ai_clicked:

            with st.spinner("🤖 AI is analyzing your resume..."):
                ai_result = get_ai_analysis(resume_text)

            st.success("AI Analysis Completed!")
            st.subheader("🤖 AI Career Suggestions")
            st.info(ai_result)

    else:
        st.info("📄 Please upload your resume PDF to continue.")

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

                # Old records were saved with str(dict) — parse those back;
                # new records are already a native dict, so this is skipped.
                if isinstance(result, str):
                    try:
                        result = ast.literal_eval(result)
                    except (ValueError, SyntaxError):
                        result = {}

                st.metric("ATS Compatibility Score", f"{record['ats_score']}%")
                st.divider()

                hist_col1, hist_col2 = st.columns(2)

                with hist_col1:
                    st.markdown("**✅ Skills Found**")
                    skills = result.get("skills") if isinstance(result, dict) else None

                    if skills:
                        skills_html = "".join(
                            f'<span class="skill-badge skill-badge-green">{skill}</span>'
                            for skill in skills
                        )
                        st.markdown(skills_html, unsafe_allow_html=True)
                    else:
                        st.caption("No skills detected.")

                with hist_col2:
                    st.markdown("**❌ Missing Skills**")
                    missing_skills = result.get("missing_skills") if isinstance(result, dict) else None

                    if missing_skills:
                        missing_html = "".join(
                            f'<span class="skill-badge skill-badge-red">{skill}</span>'
                            for skill in missing_skills
                        )
                        st.markdown(missing_html, unsafe_allow_html=True)
                    else:
                        st.caption("No important skills missing.")

                suggestions = result.get("suggestions") if isinstance(result, dict) else None

                if suggestions:
                    st.divider()
                    st.markdown("**💡 Suggestions**")
                    for suggestion in suggestions:
                        st.write(f"✅ {suggestion}")

                st.divider()

                if st.button(
                    "🗑️ Delete this analysis",
                    key=f"delete_{record['analysis_id']}"
                ):
                    delete_resume_analysis(user_id, record["analysis_id"])
                    st.success("Deleted.")
                    st.rerun()
    else:
        st.info("No previous analyses yet. Upload a resume above to get started.")