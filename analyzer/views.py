from django.shortcuts import render
import PyPDF2
import docx
import os
from httpx import request
from openai import OpenAI
from .models import ResumeRecord

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def login_page(request):
    return render(request, "login.html")

def register_page(request):
    return render(request, "register.html")

def read_image(file):
    print("IMAGE FUNCTION CALLED")   # for testing
    image = Image.open(file).convert("L")
    text = pytesseract.image_to_string(image)
    print("TEXT:", text[:100])       # preview
    return text.strip()

# ==========================================
# OPENAI CLIENT
# ==========================================
def get_openai_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ==========================================
# SKILLS DATABASE
# ==========================================
skills_db = [
    "python", "java", "html", "css", "javascript", "sql", "django",
    "communication", "leadership", "teamwork",
    "machine learning", "data science", "pandas", "numpy",
    "scikit-learn", "tensorflow", "tableau", "power bi",
    "mechanical", "diesel mechanics", "operator",
    "pump house", "maintenance", "problem-solving",
    "creativity", "hindi", "kannada", "iti"
]


# ==========================================
# PAGES
# ==========================================
def home(request):
    return render(request, "home.html")


def history_page(request):
    records = ResumeRecord.objects.all().order_by("-id")
    return render(request, "history.html", {"records": records})


# ==========================================
# FILE READERS
# ==========================================
def read_pdf(file):
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text.strip()


def read_docx(file):
    text = ""
    doc = docx.Document(file)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text.strip()


def read_txt(file):
    return file.read().decode("utf-8").strip()


# ==========================================
# HELPERS
# ==========================================
def find_skills(text):
    found = []
    lower = text.lower()

    for skill in skills_db:
        if skill in lower:
            found.append(skill)

    return sorted(list(set(found)))


# ✅ AI SUMMARY
def generate_summary(skills, score, match_score):
    skill_text = ", ".join(skills) if skills else "limited relevant skills"

    return f"""
This candidate has an ATS score of {score}% with a job match score of {match_score}%.

The resume demonstrates proficiency in {skill_text}. The profile shows a moderate alignment with industry requirements.

The candidate has potential but needs improvement in advanced skills, project experience, and keyword optimization.

Overall, the profile is suitable for entry-level or intermediate roles depending on further development.
"""


# ✅ JOB RECOMMENDATION
def recommend_jobs(skills):
    jobs = []

    if {"python","django"} & set(skills):
        jobs.append("Backend Developer")

    if {"html","css","javascript"} & set(skills):
        jobs.append("Frontend Developer")

    if {"machine learning","data science","pandas"} & set(skills):
        jobs.append("Data Analyst / ML Engineer")

    if {"communication","leadership"} & set(skills):
        jobs.append("Business / HR Roles")

    if {"mechanical","maintenance"} & set(skills):
        jobs.append("Mechanical Technician")

    if not jobs:
        jobs = ["Fresher Role", "Trainee"]

    return jobs[:5]


# ✅ SKILL RELEVANCE
def skill_relevance(skills, jobdesc):
    if not jobdesc:
        return {}

    job_words = set(jobdesc.lower().split())
    relevance = {}

    for skill in skills:
        relevance[skill] = "High" if skill in job_words else "Medium"

    return relevance


# ✅ STRUCTURED INSIGHTS
def generate_insights(skills, score, match_score):
    return {
        "strength": "Good skill foundation" if score > 50 else "Basic skill level",
        "risk": "Low job match" if match_score < 40 else "Moderate match",
        "improvement": "Add projects, certifications, and role-specific skills"
    }


# ✅ MATCH SCORE
def calculate_match_score(resume_text, job_text):
    resume_words = set(resume_text.lower().split())
    job_words = set(job_text.lower().split())

    if not job_words:
        return 0

    matched = resume_words.intersection(job_words)
    return int((len(matched) / len(job_words)) * 100)

# ==========================================
# FALLBACK ANALYSIS
# ==========================================
def fallback_analysis(resume_text, target_role):
    return f"""
<h3>Basic Resume Analysis</h3>
<p>AI service is currently unavailable.</p>

<h3>Suggestion</h3>
<p>Improve skills, add projects, and align resume with {target_role} role.</p>
"""

# ==========================================
# AI ANALYSIS
# ==========================================
def ai_resume_analysis(resume_text, target_role):
    try:
        client = get_openai_client()

        prompt = f"""
You are an expert ATS Resume Reviewer.

Analyze resume for: {target_role}

Provide a professional structured report in HTML format:

<h3>Strengths</h3>
<h3>Weaknesses</h3>
<h3>Improvements</h3>
<h3>ATS Score</h3>

Resume:
{resume_text}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",   # 🔥 safer model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1000
        )

        result = response.choices[0].message.content

        print("AI SUCCESS")   # debug

        return result

    except Exception as e:
        print("AI ERROR:", e)   # 🔥 VERY IMPORTANT
        return fallback_analysis(resume_text, target_role)

# ==========================================
# MAIN VIEW
# ==========================================
def upload_resume(request):
    context = {
        "show_result": False,
        "text": "",
        "skills": [],
        "score": 0,
        "summary": "",
        "jobs": [],
        "match_score": 0,
        "ai_report": "",
        "target_role": "",
        "relevance": {},
        "insights": {}
    }

    if request.method == "POST" and request.FILES.get("resume"):
        uploaded_file = request.FILES["resume"]
        filename = uploaded_file.name.lower()

        try:
            if filename.endswith(".pdf"):
                text = read_pdf(uploaded_file)
            elif filename.endswith(".docx"):
                text = read_docx(uploaded_file)
            elif filename.endswith(".txt"):
                text = read_txt(uploaded_file)
            else:
                context["summary"] = "Unsupported file format."
                return render(request, "upload.html", context)

        except Exception:
            context["summary"] = "Error reading file."
            return render(request, "upload.html", context)

        skills = find_skills(text)
        score = min(len(skills) * 10, 100)

        jobdesc = request.POST.get("jobdesc", "").strip()
        target_role = request.POST.get("target_role") or "General Role"

        match_score = calculate_match_score(text, jobdesc) if jobdesc else 0

        summary = generate_summary(skills, score, match_score)
        jobs = recommend_jobs(skills)
        relevance = skill_relevance(skills, jobdesc)
        insights = generate_insights(skills, score, match_score)
        ai_report = ai_resume_analysis(text, target_role)

        ResumeRecord.objects.create(
            filename=uploaded_file.name,
            target_role=target_role,
            skills=", ".join(skills),
            score=score,
            match_score=match_score,
            summary=summary,
            jobs=", ".join(jobs),
            ai_report=ai_report
        )

        context = {
            "show_result": True,
            "text": text,
            "skills": skills,
            "score": score,
            "summary": summary,
            "jobs": jobs,
            "match_score": match_score,
            "ai_report": ai_report,
            "target_role": target_role,
            "relevance": relevance,
            "insights": insights
        }

        # ✅ REDIRECT TO RESULT PAGE
        return render(request, "result.html", context)

    # ✅ DEFAULT PAGE
    return render(request, "upload.html")