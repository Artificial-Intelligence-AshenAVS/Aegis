from flask import Flask, request, jsonify, render_template
from safeguard_api import SafeguardAPI
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
safeguard_api = SafeguardAPI(api_url=os.getenv("SAFEGUARD_API_URL"))

# Initialize the LLM (replace this with GROQ once it's available via LangChain)
llm = ChatGroq(
    temperature=0.9, 
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama3-70b-8192"
)

# Configuration flag to toggle safeguard
safeguard_enabled = os.getenv("SAFEGUARD_ENABLED", "true").lower() == "true"

def truncate_text(text, max_length=512):
    tokens = text.split()
    if len(tokens) > max_length:
        return ' '.join(tokens[:max_length])
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query_llm():
    data = request.json
    user_input = data.get('input_text', '')

    # Get response from LLM
    llm_response = llm.invoke("You are a helpful assistant to provide details on climate changes, user data: name:Ashen age:23 gender:male " + user_input)
    
    llm_response_text = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

    truncated_response_text = truncate_text(llm_response_text)

    # Optionally pass LLM response to safeguard API
    if safeguard_enabled:
        moderated_response = safeguard_api.moderate(truncated_response_text)
    else:
        moderated_response = truncated_response_text

    return jsonify({'response': moderated_response})

@app.route('/toggle_safeguard', methods=['POST'])
def toggle_safeguard():
    global safeguard_enabled
    safeguard_enabled = not safeguard_enabled
    status = "enabled" if safeguard_enabled else "disabled"
    return jsonify({'status': status})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
