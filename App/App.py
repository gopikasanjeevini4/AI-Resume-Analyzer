import streamlit as st
import pandas as pd
import base64
import random
import datetime
import pymysql
import os
import fitz
import pdfplumber
import numpy as np
from streamlit_tags import st_tags
import easyocr
from pdf2image import convert_from_path
from PIL import Image
import plotly.express as px

from Courses import (
    ds_course,
    web_course,
    android_course,
    ios_course,
    uiux_course,
    resume_videos,
    interview_videos
)

# ADD THIS HERE
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

# =====================================================
# DATABASE
# =====================================================
connection = pymysql.connect(
    host="localhost",
    user="gopika",
    password="gopika479",
    db="resume_analyzer"
)

cursor = connection.cursor()

# =====================================================
# PDF READER (NO OCR VERSION)
# pdfplumber + PyMuPDF hybrid
# =====================================================
def pdf_reader(file):
    try:
        text = ""

        # Method 1: pdfplumber
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + " "

        # Method 2: PyMuPDF fallback
        if len(text.strip()) < 20:
            doc = fitz.open(file)
            for page in doc:
                t = page.get_text()
                if t:
                    text += t + " "
            doc.close()

        # Method 3: OCR fallback
        if len(text.strip()) < 20:
            images = convert_from_path(
                file,
                dpi=250,
                poppler_path=r"C:\Users\gopik\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"
            )
            for img in images:
                img_np = np.array(img)
                result = reader.readtext(img_np, detail=0)
                text += " ".join(result) + " "


        return text.strip()

    except Exception as e:
        st.error(f"PDF Read Error: {e}")
        return ""

# =====================================================
# SHOW PDF
# =====================================================
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="700"
        height="500">
    </iframe>
    """

    st.markdown(pdf_display, unsafe_allow_html=True)

# =====================================================
# COURSE RECOMMENDER
# =====================================================
def course_recommender(course_list):
    st.subheader(" Recommended Courses")

    random.shuffle(course_list)

    for i, (name, link) in enumerate(course_list[:5], 1):
        st.markdown(f"{i}. [{name}]({link})")

# =====================================================
# INSERT DATA
# =====================================================
def insert_data(name, email, score, timestamp, pages, field, skills, courses):
    sql = """
    INSERT INTO user_data
    (name,email,resume_score,timestamp,page_no,predicted_field,skills,recommended_courses)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        name,
        email,
        score,
        timestamp,
        pages,
        field,
        skills,
        courses
    )

    cursor.execute(sql, values)
    connection.commit()

# =====================================================
# MAIN APP
# =====================================================
def run():

    img = Image.open("./Logo/logo1.png")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image(img, width=400)

    st.title("AI Resume Analyzer")

    choice = st.sidebar.selectbox(
        "Select Role",
        ["User", "Admin"]
    )

    st.sidebar.markdown(
        "<a href='https://www.linkedin.com/in/gopika-sanjeevini-29b826293/' target='_blank'>Developed by Gopika</a>",
        unsafe_allow_html=True
    )

    # =====================================================
    # USER PANEL
    # =====================================================
    if choice == "User":

        pdf_file = st.file_uploader(
            "Upload Resume",
            type=["pdf"]
        )

        if pdf_file:

            os.makedirs("Uploaded_Resumes", exist_ok=True)

            save_path = os.path.join(
                "Uploaded_Resumes",
                pdf_file.name
            )

            with open(save_path, "wb") as f:
                f.write(pdf_file.getbuffer())

            show_pdf(save_path)

            resume_text = pdf_reader(save_path)

            if not resume_text or len(resume_text) < 10:
                st.error("No readable text found in this PDF.")
                return

            text_lower = resume_text.lower().replace("\n", " ")

            name = "User"
            email = "Not Found"
            pages = len(resume_text.split())

            # =====================================================
            # SKILLS LIST
            # =====================================================
            skills_list = [

                # Programming
                'python', 'java', 'c++', 'c', 'sql',

                # Data Science
                'machine learning',
                'data science',
                'pandas',
                'numpy',
                'tensorflow',
                'deep learning',
                'apache spark',
                'spark',
                'hadoop',
                'tableau',
                'power bi',

                # Web Development
                'html',
                'css',
                'javascript',
                'react',
                'redux',
                'angular',
                'jquery',
                'node',
                'node.js',
                'express',
                'mongodb',
                'mysql',
                'php',
                'bootstrap',
                'next.js',

                # UI/UX
                'figma',
                'ui',
                'ux',
                'adobe xd',

                # Mobile
                'android',
                'ios',
                'flutter',
                'swift',
                'kotlin'
            ]

            found_skills = []

            for skill in skills_list:
                if skill in text_lower:
                    found_skills.append(skill.title())

            found_skills = list(set(found_skills))
            found_skills.sort()

            st.subheader("Your Skills")

            if found_skills:
                st_tags(
                    label="Skills",
                    value=found_skills
                )
            else:
                st.warning("No skills detected.")

            # =====================================================
            # FIELD PREDICTION
            # =====================================================
            ds_score = 0
            web_score = 0
            uiux_score = 0
            mobile_score = 0

            ds_keywords = [
                'machine learning',
                'data science',
                'pandas',
                'numpy',
                'tensorflow',
                'spark',
                'hadoop'
            ]

            web_keywords = [
                'html',
                'css',
                'javascript',
                'react',
                'redux',
                'angular',
                'jquery',
                'node',
                'express',
                'mongodb',
                'bootstrap',
                'php'
            ]

            uiux_keywords = [
                'figma',
                'ui',
                'ux',
                'adobe xd'
            ]

            mobile_keywords = [
                'android',
                'ios',
                'flutter',
                'swift',
                'kotlin'
            ]

            for skill in found_skills:

                s = skill.lower()

                if s in ds_keywords:
                    ds_score += 3

                if s in web_keywords:
                    web_score += 3

                if s in uiux_keywords:
                    uiux_score += 3

                if s in mobile_keywords:
                    mobile_score += 3

            if "python" in text_lower:
                ds_score += 2

            if "sql" in text_lower:
                ds_score += 1
                web_score += 1

            if "java" in text_lower:
                mobile_score += 1

            scores = {
                "Data Science": ds_score,
                "Web Development": web_score,
                "UI/UX": uiux_score,
                "Android / iOS": mobile_score
            }

            field = max(scores, key=scores.get)

            if scores[field] == 0:
                field = "General"

            # =====================================================
            # COURSE DATA
            # =====================================================
            if field == "Data Science":
                course_data = ds_course

            elif field == "Web Development":
                course_data = web_course

            elif field == "UI/UX":
                course_data = uiux_course

            elif field == "Android / iOS":
                course_data = android_course + ios_course

            else:
                course_data = []

            st.success(f"Predicted Field: {field}")

            # =====================================================
            # RECOMMENDED SKILLS
            # =====================================================
            if field == "Data Science":
                recommended_skills = [
                    "Python",
                    "TensorFlow",
                    "Machine Learning",
                    "Power BI"
                ]

            elif field == "Web Development":
                recommended_skills = [
                    "HTML",
                    "CSS",
                    "JavaScript",
                    "React",
                    "Node.js"
                ]

            elif field == "UI/UX":
                recommended_skills = [
                    "Figma",
                    "Wireframing",
                    "Adobe XD"
                ]

            elif field == "Android / iOS":
                recommended_skills = [
                    "Flutter",
                    "Firebase",
                    "Swift",
                    "Kotlin"
                ]

            else:
                recommended_skills = [
                    "Communication",
                    "Leadership",
                    "Problem Solving"
                ]

            st.header("Recommended Skills")

            st_tags(
                label="Skills You Should Add",
                text="Improve your resume with these skills",
                value=recommended_skills
            )

            # =====================================================
            # COURSES
            # =====================================================
            if course_data:
                course_recommender(course_data)

            # =====================================================
            # RESUME SCORE
            # =====================================================
            score = 0

            if "project" in text_lower:
                score += 20

            if "skill" in text_lower:
                score += 20

            if "education" in text_lower:
                score += 20

            if "experience" in text_lower:
                score += 20

            if "certification" in text_lower:
                score += 20

            if score > 100:
                score = 100

            st.subheader(f"Resume Score: {score}/100")

            # =====================================================
            # SAVE DATA
            # =====================================================
            timestamp = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            insert_data(
                name,
                email,
                score,
                timestamp,
                pages,
                field,
                str(found_skills),
                str([c[0] for c in course_data[:5]])
            )

            st.success("Data Saved to Database")

            # =====================================================
            # VIDEOS
            # =====================================================
            st.header(" Resume Tips")
            st.video(random.choice(resume_videos))

            st.header(" Interview Tips")
            st.video(random.choice(interview_videos))

    # =====================================================
    # ADMIN PANEL
    # =====================================================
    else:

        st.subheader("Admin Login")

        user = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            if user == "admin" and password == "admin123":

                st.success("Welcome Admin Gopika")

                cursor.execute("SELECT * FROM user_data")
                data = cursor.fetchall()

                df = pd.DataFrame(data, columns=[
                    "ID",
                    "Name",
                    "Email",
                    "Score",
                    "Timestamp",
                    "Pages",
                    "Field",
                    "Skills",
                    "Courses"
                ])

                st.dataframe(df)

                fig = px.pie(
                    df,
                    names="Field",
                    title="Field Distribution"
                )

                st.plotly_chart(fig)

            else:
                st.error("Wrong Credentials")

# =====================================================
# RUN
# =====================================================
run()
