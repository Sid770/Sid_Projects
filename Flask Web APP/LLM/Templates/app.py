from flask import Flask, render_template, request, jsonify
from langchain.prompts import PromptTemplate
from weather import get_weather_data
import os
import logging
import pandas as pd
import googleapiclient.discovery
import speech_recognition as sr
from whisper import load_model
from tweets_DD import tweets_DD
from tweets_agriGoi import tweets_Agri
from dotenv import load_dotenv
from together import Together  # Import the Together API client

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Whisper model for speech-to-text
whisper_model = load_model("base")

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load IMD tweets CSV path
IMD_CSV_PATH = "B:\\OneDrive - Amity University\\Desktop\\Destop\\CSVs\\fetched_tweets_IMD.csv"

# Define QUERY_PROMPT
QUERY_PROMPT = PromptTemplate(
    input_variables=["question", "temp", "humidity", "city", "state", "language", "tweet", "image", "youtube_links"],
    template="""
    You are an AI assistant specializing in Agriculture Disease Management for crops.
    The current weather in {city}, {state} is {temp}°C with a humidity level of {humidity}%. Based on this weather, your task is to:

    1. Preventive Measures: Provide clear, actionable preventive measures the farmer can take to protect crops from potential diseases.
    2. Disease Prediction: Predict potential disease outbreaks in the farmer's area based on the current temperature and humidity.
    3. Crop Management Advice: Offer practical tips on effective crop management to reduce risks.
    4. Include relevant YouTube Videos : {youtube_links}.

    Provide the response in {language}.

    Original question: {question}
    """
)

def load_imd_data():
    """Load IMD data from a CSV file."""
    try:
        df = pd.read_csv(IMD_CSV_PATH)
        return df[['Tweet', 'Images']]
    except Exception as e:
        logging.error(f"Error reading IMD CSV: {e}")
        return pd.DataFrame(columns=['Tweet', 'Images'])

def get_youtube_links(query, max_results=3):
    """
    Fetch YouTube video links based on a query using YouTube API v3.
    """
    try:
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if not youtube_api_key:
            raise ValueError("YouTube API key not found. Please set it in the environment variables.")

        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=youtube_api_key)
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            order="relevance"
        )
        response = request.execute()

        videos = [
            {"title": item["snippet"]["title"], "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"}
            for item in response.get('items', [])
        ]
        return videos
    except Exception as e:
        logging.error(f"Error fetching YouTube links: {e}")
        return []

def extract_disease(text):
    """Extract a disease name from user input."""
    diseases = ["Bacterial Spot", "Early Blight", "Powdery Mildew", "Late Blight", "Scab"]
    for disease in diseases:
        if disease.lower() in text.lower():
            return disease
    return "crop disease prevention"

def detect_language(text):
    """Detect language based on user input keywords."""
    keywords = {
        "Hindi": ["कृपया", "हेलो", "धन्यवाद"],
        "Marathi": ["नमस्कार", "धन्यवाद", "कृपया"],
        "Gujarati": ["સ્વાગત", "શુભ", "કૃપા"],
        "Bengali": ["স্বাগতম", "ধন্যবাদ", "অনুগ্রহ"],
        "Odia": ["ସ୍ଵାଗତ", "ଧନ୍ୟବାଦ", "କୃପାୟା"],
    }
    for language, lang_keywords in keywords.items():
        if any(keyword in text for keyword in lang_keywords):
            return language
    return "English"

def format_response_html(response_text):
    """Format AI response text for HTML rendering."""
    formatted_text = response_text.replace("**", "<strong>").replace("\n\n", "<br><br>").replace("\n", "<br>")
    return formatted_text

# Together API integration
TOGETHER_API_KEY = "90c790f822552c8d116f7f93ecce1316a27ab4b147b597485ca0aafd825eda71"
together_client = Together(api_key=TOGETHER_API_KEY)

def get_together_response(prompt):
    """
    Fetch a response from the Together API.
    """
    try:
        response = together_client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error fetching response from Together API: {e}")
        return "Error fetching response from the AI model. Please try again later."

@app.route("/", methods=["GET", "POST"])
def index():
    response = ""
    if request.method == "POST":
        user_question = request.form.get("question", "")
        city = request.form.get("city", "")
        state = request.form.get("state", "")
        language = detect_language(user_question)

        weather_data = get_weather_data(city, state)
        if not weather_data:
            response = "Error fetching weather data. Please try again."
        else:
            temp = weather_data["temp"]
            humidity = weather_data["humidity"]
            imd_data = load_imd_data()
            tweet = imd_data.iloc[0]['Tweet'] if not imd_data.empty else "No tweet available"
            image = imd_data.iloc[0]['Images'] if not imd_data.empty else "No image available"

            disease = extract_disease(user_question)
            youtube_links = get_youtube_links(disease)

            youtube_links_str = ", ".join(f"<a href='{link['url']}' target='_blank'>{link['title']}</a>" for link in youtube_links)

            # Prepare the prompt for Together API
            prompt = QUERY_PROMPT.format(
                question=user_question,
                temp=temp,
                humidity=humidity,
                city=city,
                state=state,
                language=language,
                tweet=tweet,
                image=image,
                youtube_links=youtube_links_str
            )

            try:
                ai_response = get_together_response(prompt)
                response = format_response_html(ai_response)
            except Exception as e:
                logging.error(f"Error in Together API integration: {e}")
                response = "An error occurred while processing your query. Please try again."

    return render_template("index.html", response=response, tweet_list=tweets_DD, agri_tweet_list=tweets_Agri)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
