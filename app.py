import streamlit as st
import requests
from PIL import Image, ImageOps
import io
import base64

# -----------------------------
# STREAMLIT PAGE
# -----------------------------
st.set_page_config(page_title="Pin Search", layout="centered")

st.title("📌 Pin Search")

# -----------------------------
# API CONFIGURATION
# -----------------------------
API_URL = "http://34.58.76.140:8000/search"

# -----------------------------
# UI
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload image to search",
    type=["png", "jpg", "jpeg", "webp"],
    key="search_image_uploader"
)

search_btn = st.button(
    "🔍 Search Pin",
    disabled=uploaded_file is None,
    key="search_pin"
)

# -----------------------------
# SEARCH FUNCTIONALITY
# -----------------------------
if search_btn and uploaded_file is not None:
    # Display uploaded image
    image = Image.open(uploaded_file)
    # Apply EXIF orientation correction
    image = ImageOps.exif_transpose(image)
    st.image(image, caption="Uploaded Image", use_container_width=True)
    
    # Prepare file for upload
    uploaded_file.seek(0)  # Reset file pointer
    files = {
        'file': (uploaded_file.name, uploaded_file, uploaded_file.type or 'image/jpeg')
    }
    
    # Send request to API
    with st.spinner("🔍 Searching for similar pins..."):
        try:
            response = requests.post(
                API_URL,
                files=files,
                headers={'accept': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Display results
                st.success("✅ Search completed!")
                
                # Show API link
                st.info(f"🔗 **API Endpoint:** `{API_URL}`")
                
                # Main result info
                if result.get("match"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.success(f"**Match:** ✅ Found")
                    with col2:
                        st.info(f"**Matches:** {result.get('count', 0)}")
                    with col3:
                        confidence_emoji = "🟢" if result.get("confidence") == "high" else "🟡" if result.get("confidence") == "medium" else "🟠"
                        st.info(f"**Confidence:** {confidence_emoji} {result.get('confidence', '').title()}")
                    with col4:
                        st.info(f"**Time:** {result.get('time_taken_sec', 0):.2f}s")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.warning(f"**Match:** ❌ Not Found")
                    with col2:
                        st.info(f"**Threshold:** {result.get('threshold', 'N/A')}")
                    with col3:
                        st.info(f"**Time:** {result.get('time_taken_sec', 0):.2f}s")
                
                # Reason
                if result.get("reason"):
                    st.info(f"**Reason:** {result.get('reason')}")
                
                # Display matches if found
                if result.get("match") and result.get("matches"):
                    st.subheader(f"✅ Found {result.get('count', 0)} Match(es)")
                    matches = result.get("matches", [])
                    for match in matches:
                        with st.expander(f"Pin ID: {match.get('pin_id')} - Similarity: {match.get('similarity', 0):.4f}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                if match.get("name"):
                                    st.write(f"**Name:** {match.get('name')}")
                                if match.get("origin"):
                                    st.write(f"**Origin:** {match.get('origin')}")
                            with col2:
                                st.metric("Similarity", f"{match.get('similarity', 0):.4f}")
                            if match.get("image_link"):
                                st.markdown(f"🔗 **Image Link:** [{match.get('image_link')}]({match.get('image_link')})")
                
                # Display cutout image from API
                if result.get("cutout_image"):
                    try:
                        cutout_data = result.get("cutout_image")
                        # Handle data URL format: data:image/png;base64,{base64_string}
                        if cutout_data.startswith("data:image"):
                            # Extract base64 part after the comma
                            cutout_b64 = cutout_data.split(",")[1]
                        else:
                            cutout_b64 = cutout_data
                        
                        # Decode and display
                        cutout_bytes = base64.b64decode(cutout_b64)
                        cutout_img = Image.open(io.BytesIO(cutout_bytes))
                        # Apply EXIF orientation correction
                        cutout_img = ImageOps.exif_transpose(cutout_img)
                        st.subheader("🖼️ Cutout Image")
                        st.image(cutout_img, caption="Processed Cutout from API", use_container_width=True)
                        
                        # Download button for cutout
                        buf = io.BytesIO()
                        cutout_img.save(buf, format="PNG")
                        buf.seek(0)
                        st.download_button(
                            "⬇️ Download Cutout",
                            data=buf.getvalue(),
                            file_name="pin_cutout.png",
                            mime="image/png",
                            key="download_cutout"
                        )
                    except Exception as e:
                        st.warning(f"Could not decode cutout image: {str(e)}")
                
                # Debug information (similar pins)
                if result.get("debug") and len(result["debug"]) > 0:
                    st.subheader("🔍 Similar Pins")
                    
                    # Create a table for better visualization
                    debug_data = result["debug"]
                    
                    # Display only top 3 similar pins
                    for idx, item in enumerate(debug_data[:3], 1):
                        pin_id = item.get('pin_id')
                        similarity = item.get('similarity', 0)
                        pin_link = f"http://34.58.76.140:8000/pin/{pin_id}"
                        
                        with st.expander(f"Pin ID: {pin_id} - Similarity: {similarity:.4f}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Similarity", f"{similarity:.4f}")
                            with col2:
                                st.metric("Distance", f"{item.get('distance', 0):.4f}")
                            
                            # Show image link if available, otherwise show regular link
                            if item.get("image_link"):
                                st.markdown(f"🔗 **Image Link:** [{item.get('image_link')}]({item.get('image_link')})")
                            else:
                                st.markdown(f"🔗 **Link:** [{pin_link}]({pin_link})")
                
                # Show raw JSON response (collapsible)
                with st.expander("📄 View Raw Response"):
                    st.json(result)
                    
            elif response.status_code == 422:
                st.error("❌ Validation Error")
                st.json(response.json())
            else:
                st.error(f"❌ Error: {response.status_code}")
                st.code(response.text)
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request failed: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
