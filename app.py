import streamlit as st
import requests
import base64
import together
import re
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

# Load API keys from Streamlit secrets
YOUTUBE_API_KEY = st.secrets["api_keys"]["youtube_api"]
TOGETHER_API_KEY = st.secrets["api_keys"]["together_api"]

# Set Together API key
together.api_key = TOGETHER_API_KEY

# Function to extract video ID from YouTube URL
def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif parsed_url.hostname in ["youtu.be"]:
        return parsed_url.path.lstrip("/")
    return None

# Function to fetch video details
@st.cache_data(ttl=300)
def get_video_details(video_id):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Fetch video details
    video_response = youtube.videos().list(
        part="snippet,statistics", id=video_id
    ).execute()

    if not video_response["items"]:
        return None

    video_data = video_response["items"][0]
    title = video_data["snippet"]["title"]
    thumbnail = video_data["snippet"]["thumbnails"]["high"]["url"]
    views = int(video_data["statistics"].get("viewCount", 0))
    likes = int(video_data["statistics"].get("likeCount", 0))

    # Fetch channel statistics
    channel_id = video_data["snippet"]["channelId"]
    channel_response = youtube.channels().list(
        part="statistics", id=channel_id
    ).execute()

    if not channel_response["items"]:
        avg_views = 0
    else:
        total_views = int(channel_response["items"][0]["statistics"]["viewCount"])
        total_videos = int(channel_response["items"][0]["statistics"].get("videoCount", 1))
        avg_views = total_views / max(total_videos, 1)

    # Calculate outlier score
    outlier_score = round(views / avg_views, 2) if avg_views > 0 else 0

    return {
        "title": title,
        "thumbnail": thumbnail,
        "views": views,
        "likes": likes,
        "avg_views": avg_views,
        "outlier_score": outlier_score
    }

# Function to generate AI images with variations
def generate_images(prompt, model, num_outputs):
    response = together.Images.generate(
        prompt=prompt,
        model=model,
        width=1024,
        height=768,
        steps=28,
        n=num_outputs,
        response_format="b64_json"
    )
    return [base64.b64decode(img["b64_json"]) for img in response["data"]]

# Streamlit UI
st.title("🎥 YouTube Thumbnail AI Variations")

# User input for video URL
video_url = st.text_input("Enter YouTube Video URL", "")

# User input for number of AI-generated images
num_images = st.number_input("Number of Images (1-5)", min_value=1, max_value=5, value=3)

# User selects model for AI image generation
model_option = st.selectbox(
    "Choose an AI Model",
    ["black-forest-labs/FLUX.1-canny", "stabilityai/stable-diffusion-2"]
)

if st.button("Generate"):
    video_id = extract_video_id(video_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please enter a valid video link.")
    else:
        st.write("### Video Details")
        video_details = get_video_details(video_id)

        if not video_details:
            st.error("Could not fetch video details. Please check the URL and try again.")
        else:
            # Display video details
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(video_details["thumbnail"], width=200)
            with col2:
                st.write(f"**Title:** {video_details['title']}")
                st.write(f"👀 **Views:** {video_details['views']:,}")
                st.write(f"👍 **Likes:** {video_details['likes']:,}")
                st.write(f"📈 **Avg Views on Channel:** {video_details['avg_views']:,}")
                st.write(f"🔥 **Outlier Score:** {video_details['outlier_score']}x")

            # Generate AI images
            st.write("### AI Generated Variations of the Thumbnail")
            with st.spinner("Generating AI images... Please wait!"):
                generated_images = generate_images(
                    prompt=f"Create a unique but similar variation of this YouTube video thumbnail: {video_details['title']}",
                    model=model_option,
                    num_outputs=num_images
                )

            # Display generated images
            for img_data in generated_images:
                st.image(img_data, use_column_width=True)
