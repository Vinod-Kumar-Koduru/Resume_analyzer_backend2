# routes.py
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.analysis_service import analyze_resume, extract_text_from_pdf
from db.database import get_db_connection

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    try:
        # File buffer is used for direct processing
        file_buffer = file.read()
        resume_text = extract_text_from_pdf(file_buffer)
        analysis = analyze_resume(resume_text)

        # Store in database
        conn = get_db_connection()
        cur = conn.cursor()

        query = """
            INSERT INTO resumes (
                file_name, name, email, phone, linkedin_url, portfolio_url, summary,
                work_experience, education, technical_skills, soft_skills, projects, certifications,
                resume_rating, improvement_areas, upskill_suggestions
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """
        values = (
            secure_filename(file.filename),
            analysis.get("name"),
            analysis.get("email"),
            analysis.get("phone"),
            analysis.get("linkedin_url"),
            analysis.get("portfolio_url"),
            analysis.get("summary"),
            json.dumps(analysis.get("work_experience", [])),
            json.dumps(analysis.get("education", [])),
            json.dumps(analysis.get("technical_skills", [])),
            json.dumps(analysis.get("soft_skills", [])),
            json.dumps(analysis.get("projects", [])),
            json.dumps(analysis.get("certifications", [])),
            analysis.get("resume_rating"),
            analysis.get("improvement_areas"),
            json.dumps(analysis.get("upskill_suggestions", []))
        )
        
        cur.execute(query, values)
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        # Convert the tuple result to a dictionary for a better JSON response
        columns = [desc[0] for desc in cur.description]
        response_data = dict(zip(columns, result))
        return jsonify(response_data)

    except Exception as e:
        print(f"upload_resume error: {e}")
        return jsonify({"error": "Server error"}), 500

@resume_bp.route('/', methods=['GET'])
def get_all_resumes():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, file_name, uploaded_at, name, email, resume_rating FROM resumes ORDER BY uploaded_at DESC")
        resumes = cur.fetchall()
        cur.close()
        conn.close()

        # Convert list of tuples to list of dictionaries
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in resumes]
        return jsonify(result)

    except Exception as e:
        print(f"getAllResumes error: {e}")
        return jsonify({"error": "Server error"}), 500

@resume_bp.route('/<int:id>', methods=['GET'])
def get_resume_by_id(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM resumes WHERE id = %s", (id,))
        resume = cur.fetchone()
        cur.close()
        conn.close()

        if not resume:
            return jsonify({"error": "Resume not found"}), 404

        columns = [desc[0] for desc in cur.description]
        result = dict(zip(columns, resume))
        return jsonify(result)
        
    except Exception as e:
        print(f"getResumeById error: {e}")
        return jsonify({"error": "Server error"}), 500