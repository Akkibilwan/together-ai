import streamlit as st
import requests
import base64
from googleapiclient.discovery import build
from together import Together

# Load API keys from Streamlit secrets
YOUTUBE_API_KEY = st.secrets["api_keys"]["youtube_api"]
TOGETHER_API_KEY = st.secrets["api_keys"]["together_api"]

# Initialize Together API client
together_client = Together(api_key=TOGETHER_API_KEY)

# Function to fetch YouTube videos based on a keyword
@st.cache_data(ttl=300)
def get_youtube_videos(keyword, max_results):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Search for videos related to the keyword
    search_response = youtube.search().list(
        q=keyword, part="snippet", type="video", maxResults=max_results
    ).execute()

    videos = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["medium"]["url"]
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["channelTitle"]

        # Get video stats
        video_response = youtube.videos().list(
            part="statistics", id=video_id
        ).execute()

        if video_response["items"]:
            views = int(video_response["items"][0]["statistics"].get("viewCount", 0))

            # Get channel's average views
            channel_stats = youtube.channels().list(
                part="statistics", id=channel_id
            ).execute()

            if channel_stats["items"]:
                total_views = int(channel_stats["items"][0]["statistics"]["viewCount"])
                total_videos = int(channel_stats["items"][0]["statistics"].get("videoCount", 1))
                avg_views = total_views / max(total_videos, 1)  # Avoid division by zero

                # Calculate outlier score
                outlier_score = round(views / avg_views, 2)

                videos.append({
                    "video_id": video_id,
                    "title": title,
                    "thumbnail": thumbnail,
                    "channel": channel_title,
                    "views": views,
                    "outlier_score": outlier_score
                })

    # Sort by highest outlier score
    videos.sort(key=lambda x: x["outlier_score"], reverse=True)
    return videos

# Function to generate an image with Together API
def generate_image(prompt, model, num_outputs):
    response = together_client.images.generate(
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
st.title("🔍 YouTube Search & AI Image Generator")

# User input for keyword search
keyword = st.text_input("Enter a keyword to search YouTube videos", "")
num_results = st.number_input("Max results (1-15)", min_value=1, max_value=15, value=10, step=1)

if st.button("Search"):
    if keyword:
        videos = get_youtube_videos(keyword, num_results)
        if videos:
            st.write(f"### Top {len(videos)} YouTube Videos Related to '{keyword}'")
            for video in videos:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(video["thumbnail"], width=180)
                with col2:
                    st.markdown(f"**[{video['title']}](https://www.youtube.com/watch?v={video['video_id']})**")
                    st.write(f"📺 **Channel:** {video['channel']}")
                    st.write(f"👀 **Views:** {video['views']:,}")
                    st.write(f"📈 **Outlier Score:** {video['outlier_score']}x")

            st.write("### Click a thumbnail to generate a similar AI image")
            selected_video = st.selectbox("Select a video", videos, format_func=lambda v: v["title"])

            # Ask model selection before generating image
            st.write("#### Select AI Model for Image Generation")
            model_option = st.selectbox(
                "Choose a model",
                ["black-forest-labs/FLUX.1-canny", "stabilityai/stable-diffusion-2"]
            )
            num_outputs = st.number_input("Number of Images (1-5)", min_value=1, max_value=5, value=1)

            if st.button("Generate AI Image"):
                st.write(f"Generating AI images based on `{selected_video['title']}` thumbnail...")
                with st.spinner("Generating... Please wait!"):
                    generated_images = generate_image(
                        prompt=f"Generate a similar image to this YouTube thumbnail: {selected_video['title']}",
                        model=model_option,
                        num_outputs=num_outputs
                    )

                # Display the generated images
                st.write("### AI Generated Images")
                for img_data in generated_images:
                    st.image(img_data, use_column_width=True)

    else:
        st.warning("Please enter a keyword to search.")

