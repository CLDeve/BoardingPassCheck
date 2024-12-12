import streamlit as st
import requests

# API Configuration
API_KEY = '56e9c3-1bef36'  # Replace with your Aviation Edge API key
BASE_URL = 'https://aviation-edge.com/v2/public/timetable'

# Initialize session state for barcode input
if "barcode_input" not in st.session_state:
    st.session_state["barcode_input"] = ""

# Streamlit Interface
st.title("Boarding Pass Validator with Flight Checks")

# CSS to disable auto-fill
st.markdown("""
<style>
input[type="text"] {
    autocomplete: off;
}
</style>
""", unsafe_allow_html=True)

# Barcode input
barcode = st.text_input(
    "Scan the barcode here:",
    placeholder="Place the cursor here and scan your boarding pass...",
    key="barcode_input"
)

# Scan and validate button
if st.button("Scan and Validate"):
    if barcode:
        # Simulated validation logic (Replace with your actual logic)
        st.write(f"Validating barcode: {barcode}")
        # Example: Call an API or process barcode data here
        st.success(f"Barcode '{barcode}' has been validated successfully!")
        st.session_state["barcode_input"] = ""  # Reset the barcode field
    else:
        st.error("Please scan a barcode.")
