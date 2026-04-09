import os
import re
import json
from flask import Flask, render_template, request, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__name__))
PYTHON_DIR = os.path.join(BASE_DIR, 'python')
ANSWERS_FILE = os.path.join(BASE_DIR, 'Answers.txt')
PROBLEMS_JSON = os.path.join(BASE_DIR, 'problems_data.json')

def load_problem_statements():
    if os.path.exists(PROBLEMS_JSON):
        with open(PROBLEMS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_answers():
    answers = {}
    if not os.path.exists(ANSWERS_FILE):
        return answers
    with open(ANSWERS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(r'^Problem\s+(\d+):\s+(.+)$', line.strip())
            if match:
                prob_id = int(match.group(1))
                answers[prob_id] = match.group(2)
    return answers


def get_problems():
    problems = {}
    if not os.path.exists(PYTHON_DIR):
        return problems
    
    for filename in os.listdir(PYTHON_DIR):
        if not filename.endswith('.py'):
            continue
            
        # Extract problem ID from filename like 'p001.py' or 'pe00001 - xxx.py'
        match = re.search(r'(?:p|pe)0*(\d+)', filename.lower())
        if match:
            prob_id = int(match.group(1))
            if prob_id not in problems:
                problems[prob_id] = []
            problems[prob_id].append(filename)
            
    # Sort files inside each problem
    for p_id in problems:
        problems[p_id].sort()
        
    return problems

@app.route('/')
def index():
    answers = get_answers()
    problems = get_problems()
    statements = load_problem_statements()
    
    # Sort problem IDs
    sorted_pids = sorted(problems.keys())
    
    return render_template('index.html', problems=problems, sorted_pids=sorted_pids, answers=answers, statements=statements)

@app.route('/problem/<int:prob_id>')
def problem_detail(prob_id):
    answers = get_answers()
    problems = get_problems()
    statements = load_problem_statements()
    
    if prob_id not in problems:
        abort(404)
        
    solution_files = problems[prob_id]
    sources = []
    
    for sfile in solution_files:
        path = os.path.join(PYTHON_DIR, sfile)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = "Erreur de lecture du fichier."
        sources.append({
            'filename': sfile,
            'content': content
        })
        
    answer = answers.get(prob_id, 'Réponse inconnue')
    # Get problem info from JSON
    prob_info = statements.get(str(prob_id), {})
    
    return render_template('problem.html', prob_id=prob_id, sources=sources, answer=answer, prob_info=prob_info)

if __name__ == '__main__':
    # Use PORT from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # In production, host must be 0.0.0.0
    app.run(host='0.0.0.0', port=port, debug=False)
