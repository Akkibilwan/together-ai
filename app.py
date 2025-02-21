import streamlit as st
import together
import base64
from PIL import Image
import io

# Load API keys from Streamlit secrets
TOGETHER_API_KEY = st.secrets["api_keys"]["together_api"]
USER_KEY = st.secrets["api_keys"]["user_key"]

# Set the Together AI API key
together.api_key = TOGETHER_API_KEY

# Streamlit UI
st.title("🎨 Together AI - Image Transformation")

# Upload an image
uploaded_image = st.file_uploader("Upload an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

# User input fields
prompt = st.text_area("Enter a prompt for AI transformation", "Make this image look like a futuristic city")
num_images = st.number_input("Number of Variations (1-5)", min_value=1, max_value=5, value=1)

# Function to generate images using Together AI
def generate_images(image, prompt, num_images):
    try:
        # Convert uploaded image to base64
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

        # Call Together AI API to generate image variations
        response = together.images.generate(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-canny",
            width=image.width,
            height=image.height,
            steps=28,
            n=num_images,
            input_image=img_base64,  # Pass the uploaded image in base64 format
            response_format="b64_json"
        )

        # Display generated images
        st.write("### Generated Variations")
        for idx, img in enumerate(response["data"]):
            img_data = base64.b64decode(img["b64_json"])
            st.image(img_data, caption=f"Variation {idx+1}", use_column_width=True)

    except Exception as e:
        st.error(f"Error generating images: {str(e)}")

# Check if image is uploaded and button is clicked
if uploaded_image and st.button("Generate Variations"):
    st.write("🖌️ Generating AI images... Please wait!")
    with st.spinner("Generating images..."):
        image = Image.open(uploaded_image)  # Open the uploaded image
        generate_images(image, prompt, num_images)  # Call the function to generate images
