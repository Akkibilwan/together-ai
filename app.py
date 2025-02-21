import streamlit as st
import base64
from PIL import Image
import io
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Image Transformation App",
    page_icon="🎨",
    layout="wide"
)

# Initialize API keys
def initialize_api():
    try:
        # First try to get from Streamlit secrets
        TOGETHER_API_KEY = st.secrets["api_keys"]["together_api"]
    except Exception:
        # Fallback to environment variables
        TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
        
    if not TOGETHER_API_KEY:
        st.error("Together AI API key not found. Please set it in your secrets or environment variables.")
        st.stop()
        
    return TOGETHER_API_KEY

# Image processing functions
def preprocess_image(uploaded_file):
    """Preprocess the uploaded image"""
    try:
        image = Image.open(uploaded_file)
        # Ensure image is in RGB mode
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def generate_images(api_key, image, prompt, num_images):
    """Generate image variations using Together AI"""
    try:
        img_base64 = image_to_base64(image)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "black-forest-labs/FLUX.1-canny",
            "prompt": prompt,
            "width": image.width,
            "height": image.height,
            "steps": 28,
            "n": num_images,
            "response_format": "b64_json",
            "input_image": img_base64  # Add the input image if required by the API
        }
        
        with st.spinner("🎨 Generating variations..."):
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
            return response.json().get("data", [])
            
    except Exception as e:
        st.error(f"Error generating images: {str(e)}")
        return None

def main():
    # Initialize API
    api_key = initialize_api()
    
    # App header
    st.title("🎨 Together AI - Image Transformation")
    st.write("Transform your images using AI-powered generation")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        num_images = st.slider("Number of Variations", min_value=1, max_value=5, value=1)
        
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        uploaded_image = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"],
            help="Select a PNG or JPEG image to transform"
        )
        
        prompt = st.text_area(
            "Transformation prompt",
            "Make this image look like a futuristic city",
            help="Describe how you want to transform the image"
        )
    
    with col2:
        if uploaded_image:
            image = preprocess_image(uploaded_image)
            if image:
                st.image(image, caption="Original Image", use_column_width=True)
                
                if st.button("Generate Variations", type="primary"):
                    results = generate_images(api_key, image, prompt, num_images)
                    
                    if results:
                        st.write("### Generated Variations")
                        for idx, img_data in enumerate(results):
                            try:
                                img_bytes = base64.b64decode(img_data["b64_json"])
                                st.image(
                                    img_bytes,
                                    caption=f"Variation {idx+1}",
                                    use_column_width=True
                                )
                            except Exception as e:
                                st.error(f"Error displaying variation {idx+1}: {str(e)}")

if __name__ == "__main__":
    main()
