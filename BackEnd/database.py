import re
from pymongo import MongoClient , UpdateOne
from bson import ObjectId
from datetime import datetime
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
import warnings
warnings.filterwarnings("ignore")
import fitz
import json
from openai import OpenAI
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults
import urllib.request
import urllib.parse

client = MongoClient("mongodb://localhost:27017/")

db = client["TeachAI"]

users_collection = db['Users']
schedules_collection = db['Schedules']
notes_collection = db['Notes']
students_collection = db['Students']
exams_collection = db['Exams']
results_collection = db['Results']
videos_collection = db['Videos']
users_videos_collection = db['Users_Videos']
preperation_lessons_collection = db['Preperation_lessons']

users_collection.create_index("email")
schedules_collection.create_index("user_id")
notes_collection.create_index("user_id")
students_collection.create_index("user_id")
exams_collection.create_index("user_id")
results_collection.create_index("user_id")
videos_collection.create_index("user_id")
users_videos_collection.create_index("user_id")
preperation_lessons_collection.create_index("user_id")

# users_collection.drop()
# schedules_collection.drop()
# notes_collection.drop()


password_hash = PasswordHash.recommended()

def is_hash_format(s: str) -> bool:
    if not isinstance(s, str):
        return False
    # Identify standard hash formats to prevent direct hash comparison
    return s.count("$") >= 3 and (s.startswith("$argon2") or s.startswith("$2b$") or s.startswith("$2a$") or s.startswith("$pbkdf2"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Reject hash format string as plain password input for security
    if is_hash_format(plain_password):
        return False

    try:
        return password_hash.verify(plain_password, hashed_password)
    except UnknownHashError:
        return plain_password == hashed_password

######################################################## User ############################################################

# CREATE
def create_user(user_data):
        if "password" in user_data:
            pwd = user_data["password"]
            if not is_hash_format(pwd):
                user_data["password"] = password_hash.hash(pwd)
        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)

# READ ONE
def get_user(email,password):
    user = users_collection.find_one({"email": email})
    if user and verify_password(password, user.get("password", "")):
        return user
    return None

def get_user_by_id(user_id):
    return users_collection.find_one({"_id": ObjectId(user_id)})


# READ ALL
def get_all_users():
    return users_collection.count_documents({})

# UPDATE FROM LOGIN
def update_user_login(email,password):
    user = users_collection.find_one({"email": email})
    if user:
        if verify_password(password, user.get("password", "")):
            return "this is the same of old password"
    
    hashed = password_hash.hash(password)
    result = users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed}}
    )
    return result.modified_count


# UPDATE FROM LOGIN
def update_user_email(oldEmail,newEmail):
    isSame = users_collection.count_documents(
        {"email": newEmail}
    )
    if(isSame):
        return "this is the same of email"
    result = users_collection.update_one(
        {"email": oldEmail},
        {"$set": {"email":newEmail}}
    )
    return result.modified_count

# UPDATE
def update_user(user_id,user_data):
    if "password" in user_data:
        pwd = user_data["password"]
        if not is_hash_format(pwd):
            user_data["password"] = password_hash.hash(pwd)
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user_data}
    )
    return result.modified_count


############################################### SCHEDULE ############################################################


def get_schedule(user_id):
    schedules = list(schedules_collection.find({"user_id": user_id},{"user_id":0}))
    for sch in schedules:
        sch["_id"] = str(sch["_id"])
    return schedules

def add_schedule(schedule_data):
    if(schedules_collection.count_documents({"user_id": schedule_data["user_id"], "day": schedule_data["day"]})) < 10:
        schedule_data["dateInserted"] = str(datetime.now().date())
        schedule_data["user_id"] = ObjectId(schedule_data["user_id"])
        result = schedules_collection.insert_one(schedule_data)
        return result.inserted_id
    return "You have reached the maximum number of schedules allowed of this day"

def delete_schedule(schedule_id):
    schedules_collection.delete_one({"_id": ObjectId(schedule_id)})
    return "Schedule deleted successfully"


################################################ NOTES ############################################################


def get_notes(user_id):
    notes = list(notes_collection.find({"user_id": ObjectId(user_id)},{"user_id":0}))
    for note in notes:
        note["_id"] = str(note["_id"])
    return notes

def add_notes(notes_data):
    if(notes_collection.count_documents({"user_id": ObjectId(notes_data["user_id"])})) < 20:
        notes_data["user_id"] = ObjectId(notes_data["user_id"])
        notes_data["dateInserted"] = str(datetime.now().date())
        result = notes_collection.insert_one(notes_data)
        return result.inserted_id
    return "You have reached the maximum number of notes allowed"

def update_notes(note_data):
    note_id = note_data.pop("id",None)
    note_data["user_id"] = ObjectId(note_data["user_id"])
    result = notes_collection.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": note_data}
    )
    if result.matched_count == 0:
        return "Note not found"
    return note_id

def delete_notes(note_id):
    notes_collection.delete_one({"_id": ObjectId(note_id)})

######################################################## Students ############################################################

def get_students(user_id, indexPage):
    students = list(students_collection.find({"user_id": ObjectId(user_id)}).skip(indexPage * 10).limit(10))
    for student in students:
        student["_id"] = str(student["_id"])
    return students

def add_student(student_data):
    student_data["dateInserted"] = str(datetime.now().date())
    student_data["user_id"] = ObjectId(student_data["user_id"])
    result = students_collection.insert_one(student_data)
    return str(result.inserted_id)


def update_student(student_data):
    student_id = student_data.pop("id",None)
    student_data["dateInserted"] = str(datetime.now().date())
    student_data["user_id"] = ObjectId(student_data["user_id"])

    result =students_collection.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": student_data}
    )
    return result.modified_count

def delete_student(student_id):
    students_collection.delete_one({"_id": ObjectId(student_id)})

def search_about_students(user_id: str, student_name: str):
    q = re.escape(student_name.strip())

    results = list(
        students_collection.find(
            {
                "user_id": ObjectId(user_id),
                "name": {
                    "$regex": q,
                    "$options": "i"  # case insensitive
                }
            }
        ).limit(10)
    )

    for student in results:
        student["_id"] = str(student["_id"])
        student["user_id"] = str(student["user_id"])

    return results

######################################################## Evaluation ############################################################
OPENAI_API_KEY = ""
MAX_LESSON_CONTEXT_CHARS = 5000
MAX_SECTION_CONTEXT_CHARS = 12000
SUBJECTS= {
    "اللغة العربية (الصفوف 1-6 الابتدائي)": {
        "key": "arabic",
        "label": "Arabic Language",
        "label_ar": "اللغة العربية (الصفوف 1-6 الابتدائي)",
        "marker": "تقييم معلم اللغة العربية"
    },
    "الرياضيات (الصفوف 1-3 الابتدائي)": {
        "key": "math",
        "label": "Mathematics (Grades 1-3 priamry)",
        "label_ar": "الرياضيات (الصفوف 1-3 الابتدائي)",
        "marker": "Knowledge Delivery"
    },
    "الرياضيات (الصفوف 4-6 الابتدائي)": {
        "key": "math",
        "label": "Mathematics (Grades 4-6 primary)",
        "label_ar": "الرياضيات (الصفوف 4-6 الابتدائي)",
        "marker": "تقييم معلمين الرياضيات"
    },
    "الدراسات الاجتماعية (الصفوف 4-6 الابتدائي)": {
        "key": "social_studies",
        "label": "Social Studies (Grades 4-6 primary)",
        "label_ar": "الدراسات الاجتماعية (الصفوف 4-6 الابتدائي)",
        "marker": "تقييم معلم الدراسات الاجتماعية"
    },
    "العلوم (الصفوف 4-6 الابتدائي)": {
        "key": "science",
        "label": "Science (Grades 4-6 primary)",
        "label_ar": "العلوم (الصفوف 4-6 الابتدائي)",
        "marker": "تقييم معلمي العلوم"
    },
    "التربية الدينية (الصفوف 1-6 الابتدائي)": {
        "key": "religion",
        "label": "Islamic / Religious Education (Grades 1-6 primary)",
        "label_ar": "التربية الدينية (الصفوف 1-6 الابتدائي)",
        "marker": "المجال الأول: المعرفي"
    }
}

# Ordered list of markers as they appear in the document, used to find
# the boundaries between sections.
_ORDERED_MARKERS= [
    "تقييم معلم اللغة العربية",
    "Knowledge Delivery",
    "تقييم معلمين الرياضيات"
    "تقييم معلم الدراسات الاجتماعية",
    "تقييم معلمي العلوم",
    "المجال الأول: المعرفي"
]


openai_client = OpenAI(api_key=OPENAI_API_KEY)
search_tool = DuckDuckGoSearchResults()
def extract_pdf_text(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    text = text.replace("\n", " ")
    return text

pdf_path_sound = "mergedd_output.pdf"

pdf_text = extract_pdf_text(pdf_path_sound)

def extract_pdf_text_uploaded(pdf_file):
    pdf_bytes = pdf_file.file.read()
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    return text.replace("\n", " ")

def choose_subject(subject:str,pdf_text,acadmicLevels:list):
    """
    Displays the subject menu, asks the user to choose, and returns the
    selected subject info dict along with the extracted PDF context for
    that subject.
    """
    subject_context = ""
    specialCase = False

    if((subject == "اللغة العربية" or "التربية الدينية") and (acadmicLevels[0] == "Primary 1-3" or acadmicLevels[0] == "Primary 4-6")):
        subjectKey = " (الصفوف 1-6 الابتدائي)"
        print(subjectKey)
        specialCase = True
        if(len(acadmicLevels)>1 and acadmicLevels[0] == "Primary 1-3" and acadmicLevels[1] == "Primary 4-6"):
            acadmicLevels.pop(0)

    for acadmicLevel in acadmicLevels:
        if(acadmicLevel == "Primary 1-3" and not specialCase):
            subjectKey = " (الصفوف 1-3 الابتدائي)"
        elif(acadmicLevel == "Primary 4-6" and not specialCase):
            subjectKey = " (الصفوف 4-6 الابتدائي)"
        elif(acadmicLevel == "Preparatory"):
            subjectKey = " (الصفوف الاعدادية)"
        elif(acadmicLevel == "Secondary"):
            subjectKey = " (الصفوف الثانوية)"
        subject_info = SUBJECTS[subject+subjectKey]
        subject_context += extract_subject_context(pdf_text, subject_info , len(acadmicLevels))

    return subject_info, subject_context


def extract_subject_context(full_text, subject_info , numberOfAcadmicLevels:int):
    """
    Extracts the portion of the PDF text that corresponds to the given
    subject, based on marker positions. Falls back to the first
    MAX_SECTION_CONTEXT_CHARS characters of the full text if the marker
    is not found.
    """
    marker = subject_info["marker"]
    start = full_text.find(marker)

    if start == -1:
        return full_text[:(MAX_SECTION_CONTEXT_CHARS // numberOfAcadmicLevels)]

    # Find the next marker (different from the current one) that appears
    # after the current marker's position, to determine where this
    # subject's section ends.

    end = len(full_text)
    for other_marker in _ORDERED_MARKERS:
        if other_marker == marker:
            continue
        pos = full_text.find(other_marker, start + len(marker))
        if pos != -1 and pos < end:
            end = pos

    section_text = full_text[start:end]
    return section_text[:(MAX_SECTION_CONTEXT_CHARS // numberOfAcadmicLevels)]

def sessionExam(user_id:str):
    user_id = ObjectId(user_id)
    result = exams_collection.insert_one({"user_id":user_id,"questions": None})
    return str(result.inserted_id)

def examDetails(exam_id:str):
    exam = exams_collection.find_one({"_id":ObjectId(exam_id)})
    if not exam:
        return {"status": "exam not found"}
    elif exam["questions"] != None:
        exams_collection.delete_one({"_id":ObjectId(exam_id)})
        return {"status":exam["questions"]}
    return {"status":"not reached yet"}

def generate_all_questions(exam_id:str,subject:str,grades:list):
    if("انجليزي" in subject):
        language = "English"
    elif(subject == "اللغة الفرنسية"):
        language = "French"
    elif(subject == "اللغة الايطالية"):
        language = "Italian"
    else:
        language = "Arabic"

    subject_info, subject_context = choose_subject(subject,pdf_text,grades)
    prompt = f"""You are an educational expert specialized in evaluating teacher performance
in the subject: {subject_info['label_ar']} ({subject_info['label']}).

Here is the relevant evaluation reference material for this subject from the PDF:
---
{subject_context}
---

Based on this reference material, generate distinctive and challenging questions
for each of the following aspects, written in {language}, and clearly related to
teaching {subject_info['label_ar']}:

1. Knowledge Delivery
2. Knowledge Transfer
3. Pedagogical Aspect

Generate 1 question for "Knowledge Delivery" and 1 question for "Knowledge Transfer",
and 1 questions for "Pedagogical Aspect and it's acceptable answer to MCQ Make Sure that Questions it's very very hard and all question can be right in MCQ",

and Generate 1 question for "Knowledge Delivery" and 1 question for "Knowledge Transfer",
and 1 questions for "Pedagogical Aspect and it's acceptable answer to sound Make Sure that Questions it's very very hard".

All questions must be thoughtful, specific, measurable, written in {language},
and relevant to teaching {subject_info['label']}.

Return the answer as JSON only in the following format (no extra text or backticks).
The "type" values must stay in English exactly as shown, but the "question" , "options" and "explanation" values must be in {language},
but only correct_index value must be integer number from 0 to 3:
Write explanation at a professional teacher level, focusing on educational reasoning and subject-matter understanding rather than student-level simplifications.
example for a JSON response :
{{
  "questions": {{
    "MCQ_questions":[
    {{"type": "Knowledge Delivery", "question": "..." , "options": ["...", "...", "...", "..."], "correct_index": 0 ,"explanation": "..."}},
    {{"type": "Knowledge Transfer", "question": "...", "options": ["...", "...", "...", "..."], "correct_index": 2 , "explanation": "..."}},
    {{"type": "Pedagogical Aspect", "question": "...", "options": ["...", "...", "...", "..."], "correct_index": 3 , "explanation": "..."}}
    ], 

    "sound_questions":[
    {{"type": "Knowledge Delivery", "question": "..."}},
    {{"type": "Knowledge Transfer", "question": "..."}},
    {{"type": "Pedagogical Aspect", "question": "..."}}
    ]
  }}
}}"""
    # ADDED IN MCQ
    #answerIndex :0 , score: 0 , feedback: "no feed back"
    # ADDED IN SOUND
    #audio_name: ""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an educational expert. Return JSON only, with no extra text or backticks. All 'question' values must be written in {language} and relevant to the given subject."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        exams_collection.update_one({"_id":ObjectId(exam_id)},{"$set":{"questions":data["questions"]}})
        return data.get("questions", {})

    except Exception as e:
        return []
    
def sessionEvaluation(user_id:str):
    user_id = ObjectId(user_id)
    result = results_collection.insert_one({"user_id":user_id,"questions": None ,"scores":None})
    return str(result.inserted_id)

def EvaluationDetails(result_id:str):
    results = results_collection.find_one({"_id":ObjectId(result_id)})
    if not results:
        return {"status": "exam not found"}
    elif results["questions"] != None:
        return {"status":results["questions"]+results["scores"]}
    return {"status":"not reached yet"}

def evaulate_prepare(exam_id:str,subject:str, grades:list ,questions_details:map, audios):

    subject_info, subject_context = choose_subject(subject,pdf_text,grades)
    for i,q in enumerate(questions_details["sound_questions"]):
        for audio in audios:
            if audio.filename == q["audio_name"]:
                teacher_answer, tone_analysis = record_and_analyze_voice(audio)
                if teacher_answer:
                    evaluate_details = evaluate_answer(
                    q["question"],
                    teacher_answer,
                    tone_analysis,
                    subject_info,
                    subject_context
                )

                    score    = evaluate_details.get("Score", 0)
                    judgment = evaluate_details.get("Final_Judgment", "Unknown")
                    feedback = evaluate_details.get("Feedback", "")
                    print(score)
                    questions_details["sound_questions"][i]["score"]          = score
                    questions_details["sound_questions"][i]["judgment"]       = judgment
                    questions_details["sound_questions"][i]["feedback"]       = feedback
                    questions_details["sound_questions"][i]["teacher_answer"] = teacher_answer
                    questions_details["sound_questions"][i]["tone_analysis"]  = tone_analysis
                else:
                    questions_details["sound_questions"][i]["score"]          = 0
                    questions_details["sound_questions"][i]["judgment"]       = "Needs Improvement"
                    questions_details["sound_questions"][i]["feedback"]       = f"لم يستطع الاجابه علي هذا السؤال : {questions_details['sound_questions'][i]['question']}"
                    questions_details["sound_questions"][i]["teacher_answer"] = ""
                    questions_details["sound_questions"][i]["tone_analysis"]  = "لم يجب علي السؤال و بالتالي لم يتم تحديد النبره"
        # {
        #     "Total Score" : 30,
        #     "knowledge Delivery Score" : 10,
        #     "Knowledge Transfer Score" : 10,
        #     "Pedagogical Aspects Score" : 10,
        # }

    scoreRecord = 0
    by_type = {}
    questions_details = questions_details["sound_questions"] + questions_details["MCQ_questions"]
    for q in questions_details:
        q_type = q.get("type", "Unknown")
        score = q.get("score", 0)
        scoreRecord += score
        print(f"scoreRecord : {scoreRecord}")
        print(f"questions_details Length : {len(questions_details)}")
        if q_type not in by_type:
            by_type[q_type] = {"scores": []}
        by_type[q_type]["scores"].append(score)
    avg_scores = {
    f"{qt} Score": sum(v["scores"]) / len(v["scores"])
    for qt, v in by_type.items()
} | {"Total Score" : scoreRecord / len(questions_details)}
    print(f"avg_scores : {avg_scores}")
    results_collection.update_one({"_id":ObjectId(exam_id)},{"$set":{"questions":questions_details , "scores" : avg_scores}})
    suggest_youtube_videos(questions_details, subject_info)

def smart_search_if_needed(question, pdf_chunk):
    """
    Asks the LLM whether the PDF contains enough information to answer the question.
    If not, runs a DuckDuckGo search and returns the result.
    If yes, returns None (PDF content is sufficient).
    """
    check_prompt = f"""Based on the following text from a PDF:
---
{pdf_chunk[:3000]}
---

Does this text contain enough information to answer the following question?
Question: {question}

Answer with YES or NO only."""

    try:
        check_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": check_prompt}],
            temperature=0,
            max_tokens=5
        )
        answer = check_response.choices[0].message.content.strip().upper()

        if answer == "NO":
            search_results = search_tool.run(question)
            return search_results
        else:
            return None

    except Exception as e:
        return None

def evaluate_answer(question, teacher_answer, tone_analysis, subject_info, subject_context):
    """
    Evaluates the teacher's answer using the subject-specific section of
    the PDF as reference (criteria, levels, and example scenarios for
    this subject). If that section is not sufficient, fetches information
    from the internet and adds it as an additional reference.
    """

    extra_context = smart_search_if_needed(question, subject_context)

    extra_section = ""
    if extra_context:
        extra_section = f"""
Additional information from the internet (use as an extra reference):
{extra_context[:2000]}
"""

    prompt = f"""You are a smart evaluator of teacher performance in the subject: {subject_info['label_ar']} ({subject_info['label']}).

Evaluation criteria and reference scenarios for this subject (from the PDF):
{subject_context}
{extra_section}

Question: {question}
Teacher's answer: {teacher_answer}

Voice tone analysis: {tone_analysis}

Evaluate the teacher's answer based on:
1. Accuracy and depth of content, judged against the evaluation criteria and performance
   levels (Excellent, Very good , good, Need Improvement) provided above for this subject (60%)
2. Clarity and presentation style (20%)
3. Voice tone and confidence (20%)

Return the answer as JSON only in the following format (no extra text or backticks).
The "Final_Judgment" value must stay in English exactly as shown ("Acceptable" or "Needs Improvement"),
but the "Feedback" value must be written in Arabic:
{{
  "Score": <number from 0 to 100>,
  "Final_Judgment": "<Acceptable or Needs Improvement>",
  "Feedback": "<brief feedback in Arabic>"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an educational evaluator. Return JSON only, with no extra text or backticks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    except Exception as e:
        return {"Score": 0, "Final_Judgment": "Error", "Feedback": str(e)}

def record_and_analyze_voice(audio_file):
    try:
        # with open(audio_path, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio_file.filename, audio_file.file.read()),
                language="ar"
            )

        text = transcript.text

        tone_prompt = f"""Analyze the following text in terms of:
    1. Tone (confident, hesitant, enthusiastic, neutral)
    2. Clarity and fluency
    3. Sentiment (positive, neutral, negative)
    4. Confidence level in the answer

    Text: {text}

    Give a brief analysis in 2-3 sentences only in Arabic ."""

        response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": tone_prompt}]
            )

        tone_analysis = response.choices[0].message.content

        return text, tone_analysis

    except Exception:
        return "", ""
    
######################################################## Videos ############################################################
YOUTUBE_API_KEY = "AIzaSyDqx3NkHQPlmmIvq8gGnIb2AkjZ3wlde-8"

def suggest_youtube_videos(questions_details, subject_info):
    queries = get_youtube_search_queries(questions_details, subject_info)

    if not queries:
        return None

    for q_info in queries:
        query = q_info.get("query", "")
        if not query:
            continue

        suggest_videos = search_youtube_videos(query, max_results=2)
        unique_videos = list({
    video["video_id"]: video
    for video in suggest_videos
}.values())
        
    operations = [
    UpdateOne(
        {"video_id": video["video_id"]},
        {"$setOnInsert": video},
        upsert=True
    )
    for video in unique_videos
]

    videos_collection.bulk_write(operations)
    users_videos_collection.insert_many(suggest_videos)
    return unique_videos

def get_youtube_search_queries(questions_details, subject_info):
    """
    GPT-4o analyzes weaknesses and generates appropriate English search queries
    for each aspect, taking into account the subject being taught.
    If the score is above 80, generates a query for advanced/professional content.
    If the score is below 80, generates a query targeting the specific weakness.
    """
    by_type = {}
    for q in questions_details:
        q_type = q.get("type", "Unknown")
        score = q.get("score", 0)
        feedback = q.get("feedback", "")
        if q_type not in by_type:
            by_type[q_type] = {"scores": [], "feedbacks": []}
        by_type[q_type]["scores"].append(score)
        by_type[q_type]["feedbacks"].append(feedback)

    avg_scores = {
        qt: sum(v["scores"]) / len(v["scores"])
        for qt, v in by_type.items()
    }

    prompt = f"""You are an educational expert. Based on the following teacher evaluation
for a teacher of {subject_info['label_ar']} ({subject_info['label']}):

Average scores per aspect:
{json.dumps(avg_scores, ensure_ascii=False, indent=2)}

Detailed feedback per aspect:
{json.dumps({qt: v["feedbacks"] for qt, v in by_type.items()}, ensure_ascii=False, indent=2)}

For each aspect:
- If the score is below 80: create a precise and specific English search query to find an educational YouTube video addressing the main weakness in this aspect, based on the feedback, ideally related to teaching {subject_info['label']}.
- If the score is 80 or above: create a search query for advanced/expert-level content in this aspect, related to teaching {subject_info['label']}.

The queries must be:
1. Arabic only
2. Specific and targeted (e.g., "scaffolding techniques for math teachers" not just "teaching")
3. Suitable for a teacher who wants to develop themselves

Return JSON only with no backticks:
{{
  "queries": [
    {{"query": "effective knowledge delivery techniques for teachers step by step"}},
    {{"query": "advanced knowledge transfer strategies expert teachers"}},
    {{"query": "classroom management and student engagement techniques"}}
  ]
}}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an educational expert. Return JSON only, with no extra text or backticks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=700
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return data.get("queries", [])

    except Exception as e:
        return []


def search_youtube_videos(query, max_results=2):
    """
    Searches YouTube using the YouTube Data API v3 and returns a list of videos.
    Each video includes: title, channel, and a direct URL that opens the video.
    """
    video_ids = []
    params = urllib.parse.urlencode({
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "relevanceLanguage": "ar",
        "videoEmbeddable": "true",
        "videoDuration": "medium",
        "key": YOUTUBE_API_KEY
    })

    url = f"https://www.googleapis.com/youtube/v3/search?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        videos = []
        for item in data.get("items", []):
            video_id = item["id"].get("videoId", "")
            video_ids.append(video_id)
            title = item["snippet"].get("title", "No title")
            if video_id:
                videos.append({
                    "title": title,
                    "video_id": video_id
                })
        params2 = urllib.parse.urlencode({
        "part": "contentDetails",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    })
        url2 = f"https://www.googleapis.com/youtube/v3/videos?{params2}"

        with urllib.request.urlopen(url2, timeout=10) as response:
            data2 = json.loads(response.read().decode())

        for item_index in range(len(data2["items"])):
            durationCode = data2["items"][item_index]["contentDetails"]["duration"]
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, durationCode)

            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            seconds = int(match.group(3)) if match.group(3) else 0

            duration = {"duration": {"hours": hours, "minutes": minutes, "seconds":seconds}}
            videos[item_index] = videos[item_index] | duration

        return videos

    except urllib.error.HTTPError:
        return []
    except Exception:
        return []


def get_recommended_videos(indexPage):
    videos = list(videos_collection.find().skip(indexPage * 10).limit(10))
    for video in videos:
        video["_id"] = str(video["_id"])
    return videos

def get_all_videos(user_id, indexPage):
    videos = list(users_videos_collection.find({"user_id": ObjectId(user_id)}).skip(indexPage * 10).limit(10))
    for video in videos:
        video["_id"] = str(video["_id"])
        video["user_id"] = str(video["user_id"])
    return videos

################################################ PREPERATION LESSONS ############################################################


def get_preperation(user_id):
    lessons = list(preperation_lessons_collection.find({"user_id": user_id},{"user_id":0}))
    for lesson in lessons:
        lesson["_id"] = str(lesson["_id"])
    return lessons

def search_preperation_lesson(user_id: str, lesson_name: str):
    q = re.escape(lesson_name.strip())

    results = list(
        preperation_lessons_collection.find(
            {
                "user_id": ObjectId(user_id),
                "name": {
                    "$regex": q,
                    "$options": "i"  # case insensitive
                }
            }
        ).limit(10)
    )

    for lesson in results:
        lesson["_id"] = str(lesson["_id"])
        lesson["user_id"] = str(lesson["user_id"])

    return results

def add_preperation_lesson(lesson_data):
    lesson_data["dateInserted"] = str(datetime.now().date())
    result = preperation_lessons_collection.insert_one(lesson_data)
    return str(result.inserted_id) 

def update_preperation_lesson(lesson_data):
    lesson_id = lesson_data.pop("id", None)
    result = preperation_lessons_collection.update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": lesson_data}
    )
    if result.matched_count == 0:
        return "Preparation lesson not found"
    return lesson_id

def delete_preperation_lesson(lesson_id):
    preperation_lessons_collection.delete_one({"_id": ObjectId(lesson_id)})
    return "Preparation lesson deleted successfully"

def prepare_lesson_content(grade_level, lesson_pdf):
    """
    Reads a lesson PDF provided by the teacher and prepares the lesson content
    for the given grade level.

    Inputs:
        grade_level: the grade/year level of the students (e.g. "First Primary")
        lesson_pdf_path: path to the PDF file the teacher wants to prepare

    Output:
        A dict with either:
            {"lesson_content": "<prepared lesson text>"}
        or
            {"error": "<error message>"}
    """
    # try:

    lesson_text = extract_pdf_text_uploaded(lesson_pdf)
    context = lesson_text[:MAX_LESSON_CONTEXT_CHARS]

    if not context.strip():
        return {"error": "No text could be extracted from the provided PDF."}

    prompt = f"""You are an expert teacher preparing lesson content.

Lesson content (from the provided PDF):
---
{context}
---

Task: Prepare this content for explanation to students at the following grade level: {grade_level}.

The prepared lesson must be:
- Suitable for the language level and comprehension of students at this grade level
- Organized progressively (introduction, main explanation, examples/application, conclusion)
- Includes examples and analogies appropriate for this age group
- Written entirely in same lanugage of Lesson content (from the provided PDF)

Return only the final lesson preparation text in Lesson content (from the provided PDF), with no extra commentary."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert teacher who prepares and simplifies lesson content for students."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=2000
    )

    lesson_content = response.choices[0].message.content.strip()
    return {"lesson_content": lesson_content.replace("\n"," ")}

################################################ RESULTS & DASHBOARD ################################################

def get_user_results(user_id):
    results = list(results_collection.find({"user_id": user_id}))
    for r in results:
        r["_id"] = str(r["_id"])
        r["user_id"] = str(r["user_id"])
    return results
