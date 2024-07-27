from flask import Flask, request, jsonify, render_template, redirect, url_for
from model_training import LLMGuard

app = Flask(__name__, static_folder='static')
llm_guard = LLMGuard()

# Admin interface routes
@app.route('/')
def index():
    banned_words = llm_guard.get_banned_words()
    sensitive_patterns = llm_guard.get_sensitive_patterns()
    system_prompt_patterns = llm_guard.get_system_prompt_patterns()
    return render_template('index.html', banned_words=banned_words, sensitive_patterns=sensitive_patterns, system_prompt_patterns=system_prompt_patterns)

@app.route('/add_banned_word', methods=['POST'])
def add_banned_word():
    word = request.form['word']
    llm_guard.add_banned_word(word)
    return redirect(url_for('index'))

@app.route('/delete_banned_word', methods=['POST'])
def delete_banned_word():
    words_to_delete = request.form.getlist('banned_words')
    for word in words_to_delete:
        llm_guard.delete_banned_word(word)
    return redirect(url_for('index'))

@app.route('/add_sensitive_pattern', methods=['POST'])
def add_sensitive_pattern():
    pattern = request.form['pattern']
    llm_guard.add_sensitive_pattern(pattern)
    return redirect(url_for('index'))

@app.route('/delete_sensitive_pattern', methods=['POST'])
def delete_sensitive_pattern():
    patterns_to_delete = request.form.getlist('sensitive_patterns')
    for pattern in patterns_to_delete:
        llm_guard.delete_sensitive_pattern(pattern)
    return redirect(url_for('index'))

@app.route('/add_system_prompt_pattern', methods=['POST'])
def add_system_prompt_pattern():
    pattern = request.form['pattern']
    llm_guard.add_system_prompt_pattern(pattern)
    return redirect(url_for('index'))

@app.route('/delete_system_prompt_pattern', methods=['POST'])
def delete_system_prompt_pattern():
    patterns_to_delete = request.form.getlist('system_prompt_patterns')
    for pattern in patterns_to_delete:
        llm_guard.delete_system_prompt_pattern(pattern)
    return redirect(url_for('index'))

# Moderation API route
@app.route('/moderate', methods=['POST'])
def moderate():
    data = request.json
    input_text = data.get('input_text', '')
    moderated_text = llm_guard.moderate(input_text)
    return jsonify({'result': moderated_text})

if __name__ == '__main__':
    app.run(debug=True, port=5003)
