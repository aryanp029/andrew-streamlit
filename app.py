import streamlit as st
import requests
import base64
import time
from PIL import Image
import io
from dotenv import load_dotenv
import os

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()  # Load .env for local development

ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
API_KEY = os.getenv("RUNPOD_API_KEY")

if not ENDPOINT_ID or not API_KEY:
    st.error("❌ Missing RUNPOD_ENDPOINT_ID or RUNPOD_API_KEY in environment!")
    st.stop()

API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -----------------------------
# STREAMLIT PAGE
# -----------------------------
st.set_page_config(page_title="RunPod Pin Cutout", layout="centered")

st.title("📌 RunPod Pin Cutout")
st.caption("YOLO → BiRefNet / SAM3 → PNG Cutout")

# -----------------------------
# UI
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload pin image",
    type=["png", "jpg", "jpeg", "webp"]
)

model = st.selectbox(
    "Segmentation model",
    ["birefnet", "sam3"]
)

enhance = st.checkbox("Enhance output", value=True)

run_btn = st.button("🚀 Run Cutout", disabled=uploaded_file is None)

# -----------------------------
# RUN
# -----------------------------
if run_btn:
    with st.spinner("Encoding image..."):
        image_bytes = uploaded_file.read()
        image_b64 = base64.b64encode(image_bytes).decode()

    # Submit job
    with st.spinner("Submitting job to RunPod..."):
        resp = requests.post(
            f"{API_URL}/run",
            headers=HEADERS,
            json={
                "input": {
                    "image": image_b64,
                    "model": model,
                    "enhance": enhance
                }
            }
        )

    if resp.status_code != 200:
        st.error(f"Submit failed ({resp.status_code})")
        st.code(resp.text)
        st.stop()

    job_id = resp.json().get("id")
    st.success(f"Job submitted: `{job_id}`")

    # Poll
    status_placeholder = st.empty()
    progress = st.progress(0)
    output = None

    for i in range(60):
        time.sleep(1)
        progress.progress((i + 1) / 60)

        status_resp = requests.get(
            f"{API_URL}/status/{job_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        data = status_resp.json()
        status = data.get("status")

        status_placeholder.info(f"Status: **{status}**")

        if status == "COMPLETED":
            output = data.get("output", {})
            break

        if status == "FAILED":
            st.error("Job failed")
            st.json(data)
            st.stop()

    if output is None:
        st.error("Timed out waiting for result")
        st.stop()

    if "error" in output:
        st.error(output["error"])
        st.stop()

    # Decode output
    result_bytes = base64.b64decode(output["image"])
    result_img = Image.open(io.BytesIO(result_bytes))

    st.success("✅ Cutout ready!")

    st.image(result_img, caption=f"Model: {output.get('model_used')}")

    st.download_button(
        "⬇️ Download PNG",
        data=result_bytes,
        file_name="pin_cutout.png",
        mime="image/png"
    )
