from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from sentence_transformers import SentenceTransformer, util
import re
import pymongo
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    temperature=0.9, 
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama3-70b-8192"
)

class LLMGuard:
    def __init__(self):
        # Load a pre-trained model for vulnerability detection
        self.model_name = "distilbert-base-uncased"
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.pipeline = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer)

        # Load a model for semantic similarity
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize MongoDB connection
        mongo_client = pymongo.MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
        self.db = mongo_client["llm_guard"]
        self.banned_words_collection = self.db["banned_words"]
        self.sensitive_patterns_collection = self.db["sensitive_patterns"]
        self.system_prompt_patterns_collection = self.db["system_prompt_patterns"]

        # Load patterns from MongoDB
        self.banned_words = [word["value"] for word in self.banned_words_collection.find()]
        self.sensitive_patterns = [pattern["value"] for pattern in self.sensitive_patterns_collection.find()]
        self.system_prompt_patterns = [pattern["value"] for pattern in self.system_prompt_patterns_collection.find()]

        # Compute embeddings for banned words
        self.banned_word_embeddings = self.embedding_model.encode(self.banned_words, convert_to_tensor=True)

    def is_vulnerable(self, text):
        results = self.pipeline(text, truncation=True, padding=True, max_length=512)
        for result in results:
            if result['label'] in ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate'] and result['score'] > 0.5:
                return True
        return False

    def contains_sensitive_data(self, text):
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def contains_system_prompts(self, text):
        for pattern in self.system_prompt_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def moderate(self, text):
        for word in self.banned_words:
            if word in text.lower():
                llm_response = llm.invoke("You are a helpful assistant. The user has asked a question with banned words so kindly and professionally reject it by informing the reason.")
                llm_response_text = llm_response.content
                return llm_response_text

        if self.contains_sensitive_data(text):
            llm_response = llm.invoke("You are a helpful assistant. The user has asked a question related to sensitive data so kindly and professionally reject it by informing the reason.")
            llm_response_text = llm_response.content
            return llm_response_text

        if self.contains_system_prompts(text):
            llm_response = llm.invoke("You are a helpful assistant. The user has asked a question related to system prompt reveal so kindly and professionally reject it by informing the reason.")
            llm_response_text = llm_response.content
            return llm_response_text

        if self.is_vulnerable(text):
            llm_response = llm.invoke("You are a helpful assistant. The user has asked a question related to system vulnerability reveal so kindly and professionally reject it by informing the reason.")
            llm_response_text = llm_response.content
            return llm_response_text

        # Check for semantic similarity with banned words
        text_embedding = self.embedding_model.encode(text, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(text_embedding, self.banned_word_embeddings)

        if cosine_scores.max().item() > 0.3:  # Adjust the threshold as needed
            llm_response = llm.invoke("You are a helpful assistant. The user has asked a question with words similar to banned words so kindly and professionally reject it by informing the reason.")
            llm_response_text = llm_response.content
            return llm_response_text

        return text

    def add_banned_word(self, word):
        self.banned_words_collection.insert_one({"value": word})
        self.banned_words.append(word)
        # Update embeddings
        new_embedding = self.embedding_model.encode([word], convert_to_tensor=True)
        self.banned_word_embeddings = torch.cat((self.banned_word_embeddings, new_embedding), dim=0)

    def add_sensitive_pattern(self, pattern):
        self.sensitive_patterns_collection.insert_one({"value": pattern})
        self.sensitive_patterns.append(pattern)

    def add_system_prompt_pattern(self, pattern):
        self.system_prompt_patterns_collection.insert_one({"value": pattern})
        self.system_prompt_patterns.append(pattern)

    def delete_banned_word(self, word):
        self.banned_words_collection.delete_one({"value": word})
        self.banned_words = [w for w in self.banned_words if w != word]
        # Recompute embeddings
        self.banned_word_embeddings = self.embedding_model.encode(self.banned_words, convert_to_tensor=True)

    def delete_sensitive_pattern(self, pattern):
        self.sensitive_patterns_collection.delete_one({"value": pattern})
        self.sensitive_patterns = [p for p in self.sensitive_patterns if p != pattern]

    def delete_system_prompt_pattern(self, pattern):
        self.system_prompt_patterns_collection.delete_one({"value": pattern})
        self.system_prompt_patterns = [p for p in self.system_prompt_patterns if p != pattern]

    def get_banned_words(self):
        return [word["value"] for word in self.banned_words_collection.find()]

    def get_sensitive_patterns(self):
        return [pattern["value"] for pattern in self.sensitive_patterns_collection.find()]

    def get_system_prompt_patterns(self):
        return [pattern["value"] for pattern in self.system_prompt_patterns_collection.find()]
