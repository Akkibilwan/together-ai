import streamlit as st
import together
import base64
import requests
from PIL import Image
import io

# Load Together AI API Key from Streamlit secrets
TOGETHER_API_KEY = st.secrets["api_keys"]["together_api"]

# Set Together AI API Key
together.api_key = TOGETHER_API_KEY

# Streamlit UI
st.title("🎨 Together AI - Image Transformation")

# Upload an image
uploaded_image = st.file_uploader("Upload an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

# User input fields
prompt = st.text_area("Enter a prompt for AI transformation", "Make this image look like a futuristic city")
num_images = st.number_input("Number of Variations (1-5)", min_value=1, max_value=5, value=1)

if uploaded_image and st.button("Generate Variations"):
    st.write("🖌️ Generating AI images... Please wait!")

    with st.spinner("Generating images..."):
        try:
            # Convert uploaded image to base64
            image = Image.open(uploaded_image)
            img_buffer = io.BytesIO()
            image.save(img_buffer, format="PNG")
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

            # Call Together AI API
            response = together.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-canny",
                width=image.width,
                height=image.height,
                steps=28,
                n=num_images,
                input_image=img_base64,  # ✅ Passing uploaded image
                response_format="b64_json"
            )

            # Display generated images
            st.write("### Generated Variations")
            for idx, img in enumerate(response["data"]):
                img_data = base64.b64decode(img["b64_json"])
                st.image(img_data, caption=f"Variation {idx+1}", use_column_width=True)

        except Exception as e:
            st.error(f"Error generating images: {str(e)}")
