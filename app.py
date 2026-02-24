import streamlit as st

# Hide the sidebar and set a clean page title
st.set_page_config(page_title="Under Maintenance", page_icon="🛠️", layout="centered")

# Hide Streamlit's default header and footer for a cleaner look
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)

st.title("🛠️ Down for Maintenance")
st.warning("**We are currently upgrading the mathematical engine to make the Financial Freedom calculator 100% bulletproof. Adding the DWZ(Die with zero) model as some may not like to dies with 500 Cr in bank but would like to retire early instead.**")
st.info("The app will be back online shortly. Thank you for your patience!")

# This stops any other code from running
st.stop()