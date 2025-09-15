# services/analysis_service.py
import os
import json
import io
import pdfplumber
from google.generativeai import GenerativeModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, conlist
from typing import List, Dict, Any

class WorkExperience(BaseModel):
    role: str
    company: str
    duration: str
    description: List[str]

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: str

class ResumeAnalysis(BaseModel):
    name: str = "N/A"
    email: str = "N/A"
    phone: str = "N/A"
    linkedin_url: str = "N/A"
    portfolio_url: str = "N/A"
    summary: str = "N/A"
    work_experience: conlist(WorkExperience, min_length=0) = []
    education: conlist(Education, min_length=0) = []
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    projects: List[str] = []
    certifications: List[str] = []
    resume_rating: int = Field(..., ge=1, le=10)
    improvement_areas: str
    upskill_suggestions: List[str] = []

async def extract_text_from_pdf(file_buffer):
    text = ""
    try:
        with pdfplumber.open(file_buffer) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"PDF extraction failed: {e}")
        return ""

async def analyze_resume(resume_text):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "name": "N/A", "email": "N/A", "phone": "N/A", "linkedin_url": "N/A", "portfolio_url": "N/A",
            "summary": "AI parsing not available, using basic fallback.", "work_experience": [],
            "education": [], "technical_skills": [], "soft_skills": [], "projects": [],
            "certifications": [], "resume_rating": None, "improvement_areas": "Set up GOOGLE_API_KEY.",
            "upskill_suggestions": []
        }

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        
        parser = JsonOutputParser(pydantic_object=ResumeAnalysis)

        prompt_template = PromptTemplate(
            template="""
            You are an expert technical recruiter. Analyze the following resume and extract all key information.
            Also, provide constructive feedback on areas for improvement and suggest specific skills for upskilling based on the resume content.
            
            Return the output as a valid JSON object.
            
            {format_instructions}
            
            Resume Text:
            {resume_text}
            """,
            input_variables=["resume_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt_template | llm | parser
        
        # LangChain's async invoke requires an event loop, but for a simple Flask app
        # we can run it synchronously
        result = chain.invoke({"resume_text": resume_text})

        return result
    
    except Exception as e:
        print(f"Gemini analysis failed: {e}")
        return {
            "name": "N/A", "email": "N/A", "phone": "N/A", "linkedin_url": "N/A", "portfolio_url": "N/A",
            "summary": "AI parsing failed, using fallback.", "work_experience": [],
            "education": [], "technical_skills": [], "soft_skills": [], "projects": [],
            "certifications": [], "resume_rating": None, "improvement_areas": "Review Gemini API key or request payload.",
            "upskill_suggestions": []
        }