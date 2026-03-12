#!/usr/bin/env python3
"""
PDF to Markdown converter for HR resumes
Extracts structured data from PDF resumes and converts to Markdown format
"""

import sys
import json
from pathlib import Path
import PyPDF2
import re


def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return None


def parse_resume_sections(text):
    """Parse resume text into sections"""
    # Define common resume section headers
    section_patterns = {
        'contact': [
            r'phone[:\s]*([^\n\r]+)',
            r'tel[:\s]*([^\n\r]+)', 
            r'mobile[:\s]*([^\n\r]+)',
            r'email[:\s]*([^\n\r]+)',
            r'address[:\s]*([^\n\r]+)',
            r'linkedin[:\s]*([^\n\r]+)',
            r'github[:\s]*([^\n\r]+)'
        ],
        'education': [
            r'(education|educazione)[\s\S]*?(?=experience|work|skills|competenze|\n\s*\n|$)',
            r'(school|university|degree|diploma)[\s\S]*?(?=experience|work|skills|competenze|\n\s*\n|$)'
        ],
        'experience': [
            r'(experience|esperienza|work experience|employment)[\s\S]*?(?=education|skills|competenze|\n\s*\n|$)',
            r'(professional experience|work history)[\s\S]*?(?=education|skills|competenze|\n\s*\n|$)'
        ],
        'skills': [
            r'(skills|competenze|technologies|technical skills)[\s\S]*?(?=education|experience|about|\n\s*\n|$)'
        ],
        'summary': [
            r'(summary|profilo|objective|about me)[\s\S]*?(?=education|experience|skills|\n\s*\n|$)'
        ]
    }

    sections = {}
    lower_text = text.lower()

    for section_name, patterns in section_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, lower_text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Get the original text for this section
                start_pos = match.start()
                end_pos = match.end()
                
                # Extract the section text
                if section_name == 'education':
                    # Find next section to determine end of education section
                    exp_match = re.search(r'(experience|work|skills)', text[end_pos:], re.IGNORECASE)
                    summary_match = re.search(r'(summary|about)', text[end_pos:], re.IGNORECASE)
                    
                    next_section_pos = len(text)
                    if exp_match:
                        next_section_pos = min(next_section_pos, end_pos + exp_match.start())
                    if summary_match:
                        next_section_pos = min(next_section_pos, end_pos + summary_match.start())
                    
                    section_text = text[start_pos:next_section_pos].strip()
                elif section_name == 'experience':
                    # Find next section to determine end of experience section
                    edu_match = re.search(r'(education|skills)', text[end_pos:], re.IGNORECASE)
                    summary_match = re.search(r'(summary|about)', text[end_pos:], re.IGNORECASE)
                    
                    next_section_pos = len(text)
                    if edu_match:
                        next_section_pos = min(next_section_pos, end_pos + edu_match.start())
                    if summary_match:
                        next_section_pos = min(next_section_pos, end_pos + summary_match.start())
                    
                    section_text = text[start_pos:next_section_pos].strip()
                else:
                    section_text = text[start_pos:start_pos+min(len(text)-start_pos, 1000)].strip()
                
                if section_text and len(section_text.strip()) > 10:
                    sections[section_name] = section_text
                    break

    # Extract basic info
    contact_patterns = {
        'name': r'^([A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',
        'phone': r'(?:phone|tel|mobile)[:\s]*([^\n\r]+)',
        'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        'address': r'(?:address|location)[:\s]*([^\n\r]+)'
    }
    
    basic_info = {}
    for field, pattern in contact_patterns.items():
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            basic_info[field] = match.group(1).strip()
    
    # If we couldn't extract a name from contact info, try to find it at the beginning of the resume
    if 'name' not in basic_info:
        # Look for potential name at the start of the document
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) < 50:  # Names are usually not very long
                # Check if it looks like a name (starts with capital letters)
                if re.match(r'^[A-Z][a-z]+\s[A-Z][a-z]+', line):
                    basic_info['name'] = line
                    break
    
    return {
        'basic_info': basic_info,
        'sections': sections,
        'raw_text': text
    }


def extract_work_experience(text):
    """Extract work experience details"""
    # Pattern to match work experience entries
    exp_pattern = r'([A-Z][A-Za-z\s]+)\s*(?:[-–—]\s*|\n)([A-Z][A-Za-z\s,]+?)\s*(?:[-–—]\s*|\n)\s*([A-Z][A-Z\s/\-,\d]+)\s*(?:\n\s*\n|(?=\n[A-Z]))'
    
    experiences = []
    matches = re.findall(exp_pattern, text, re.MULTILINE)
    
    for match in matches:
        company, position, duration = match
        experiences.append({
            'company': company.strip(),
            'position': position.strip(), 
            'duration': duration.strip()
        })
    
    return experiences


def extract_education(text):
    """Extract education details"""
    edu_pattern = r'([A-Z][A-Za-z\s]+)\s*(?:[-–—]\s*|\n)([A-Z][A-Za-z\s,]+?)\s*(?:[-–—]\s*|\n)\s*([A-Z][A-Z\s/\-,\d]+)'
    
    educations = []
    matches = re.findall(edu_pattern, text, re.MULTILINE)
    
    for match in matches:
        school, degree, duration = match
        educations.append({
            'school': school.strip(),
            'degree': degree.strip(),
            'duration': duration.strip()
        })
    
    return educations


def extract_skills(text):
    """Extract skills from text"""
    # Look for skills section in various formats
    skills = []
    
    # Common skill separators
    separators = [',', ';', r'\s*,\s*', r'\s*;\s*', r'\s*\|\s*', r'\s*/\s*']
    
    # Split by common skill sections
    skill_sections = re.findall(r'(skills|competenze|technologies|technical skills):\s*([^\n\r]+)', text, re.IGNORECASE)
    
    for _, section in skill_sections:
        for sep in separators:
            if re.search(sep, section):
                skills.extend(re.split(sep, section))
                break
        else:
            skills.append(section)
    
    # Clean up skills
    cleaned_skills = []
    for skill in skills:
        skill = skill.strip().strip('•').strip('-').strip()
        if skill and len(skill) < 50:  # Filter out long text that's likely not a skill
            cleaned_skills.append(skill)
    
    return list(set(cleaned_skills))  # Remove duplicates


def convert_to_markdown(parsed_data):
    """Convert parsed resume data to Markdown format"""
    md_content = []
    
    # Basic Information
    basic_info = parsed_data['basic_info']
    md_content.append("# 候选人简历\n")
    
    if 'name' in basic_info:
        md_content.append(f"## 基本信息\n- **姓名**: {basic_info['name']}")
    
    if 'phone' in basic_info:
        md_content.append(f"- **电话**: {basic_info['phone']}")
        
    if 'email' in basic_info:
        md_content.append(f"- **邮箱**: {basic_info['email']}")
        
    if 'address' in basic_info:
        md_content.append(f"- **地址**: {basic_info['address']}")
    
    md_content.append("")
    
    # Summary/Profile
    if 'summary' in parsed_data['sections']:
        md_content.append("## 个人简介\n")
        md_content.append(f"{parsed_data['sections']['summary']}\n")
    
    # Work Experience
    if 'experience' in parsed_data['sections']:
        md_content.append("## 工作经历\n")
        experiences = extract_work_experience(parsed_data['sections']['experience'])
        if experiences:
            for exp in experiences:
                md_content.append(f"### {exp['position']} - {exp['company']}")
                md_content.append(f"**时间**: {exp['duration']}")
                md_content.append("")  # Empty line
        else:
            # If extraction didn't work, just add the raw section
            md_content.append(f"{parsed_data['sections']['experience']}\n")
    
    # Education
    if 'education' in parsed_data['sections']:
        md_content.append("## 教育背景\n")
        educations = extract_education(parsed_data['sections']['education'])
        if educations:
            for edu in educations:
                md_content.append(f"### {edu['degree']} - {edu['school']}")
                md_content.append(f"**时间**: {edu['duration']}")
                md_content.append("")
        else:
            # If extraction didn't work, just add the raw section
            md_content.append(f"{parsed_data['sections']['education']}\n")
    
    # Skills
    if 'skills' in parsed_data['sections']:
        md_content.append("## 技能\n")
        skills = extract_skills(parsed_data['sections']['skills'])
        if skills:
            for skill in skills:
                md_content.append(f"- {skill}")
        else:
            # If extraction didn't work, just add the raw section
            md_content.append(f"{parsed_data['sections']['skills']}\n")
    
    # Additional sections
    for section_name, content in parsed_data['sections'].items():
        if section_name not in ['summary', 'experience', 'education', 'skills']:
            md_content.append(f"## {section_name.title()}\n")
            md_content.append(f"{content}\n")
    
    return "\n".join(md_content)


def main():
    if len(sys.argv) != 2:
        print("Usage: python pdf_to_markdown.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    # Extract text from PDF
    text = extract_pdf_text(pdf_path)
    if not text:
        sys.exit(1)
    
    # Parse resume sections
    parsed_data = parse_resume_sections(text)
    
    # Convert to Markdown
    markdown_output = convert_to_markdown(parsed_data)
    
    # Print the result
    print(markdown_output)
    
    # Also save to file
    output_path = Path(pdf_path).with_suffix('.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    print(f"\nConverted Markdown saved to: {output_path}")


if __name__ == "__main__":
    main()