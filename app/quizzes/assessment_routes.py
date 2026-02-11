from flask import Blueprint, render_template, request, jsonify
import google.generativeai as genai
import random
import json
import os

assessment_bp = Blueprint('assessment', __name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash-lite')

@assessment_bp.route('/quiz/assessment')
def show_assessment_quiz():
    subject = request.args.get('subject')
    if not subject:
        return 'Subject is required', 400
    return render_template('assessment_quiz.html')

@assessment_bp.route('/quiz/generate-assessment', methods=['POST'])
def generate_assessment():
    data = request.get_json()
    subject = data.get('subject')
    num_questions = data.get('num_questions', 25)  # Default to 25 questions
    
    try:
        # Create the prompt for Gemini
        prompt = f"""
        Generate {num_questions} multiple choice quiz questions about {subject}. Each question should:
        1. Be appropriate for a student learning this subject
        2. Have exactly 4 options (A, B, C, D)
        3. Have one correct answer
        
        Return the result in this exact JSON format:
        [
            {{
                "question": "Question text here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "The exact correct option text"
            }}
        ]
        """
        
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Parse the response
        try:
            # First try to parse the response text directly
            questions = json.loads(response.text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response
            response_text = response.text
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                questions = json.loads(json_str)
            else:
                raise ValueError("Could not extract valid JSON from response")
        
        # Validate and clean the questions
        cleaned_questions = []
        for q in questions[:num_questions]:  # Limit to requested number of questions
            # Validate required fields
            if all(key in q for key in ['question', 'options', 'correct_answer']):
                # Ensure correct_answer is in options
                if q['correct_answer'] not in q['options']:
                    q['correct_answer'] = q['options'][0]  # Default to first option
                cleaned_questions.append(q)

        # Shuffle the questions
        random.shuffle(cleaned_questions)
        
        return jsonify(cleaned_questions)

    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        return jsonify({"error": "Failed to generate quiz"}), 500