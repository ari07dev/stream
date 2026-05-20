import streamlit as st
import google.generativeai as genai
import pandas as pd
import tempfile
import os
import time
 
# Configure your API Key (Securely stored in Streamlit secrets)
genai.configure(api_key="AIzaSyCg8YAJ4YXFgw11rbfTVi-xvwby5FTRvT8")
 
st.title("🏭 Industrial Action Sequence Analyzer")
st.write("Upload a workstation video to automatically generate an action sequence report.")
 
uploaded_file = st.file_uploader("Upload Video (MP4)", type=["mp4"])
 
if uploaded_file is not None:
    # Display the video
    st.video(uploaded_file)
    
    if st.button("Analyze Video"):
        with st.spinner("Uploading and analyzing video... this may take a minute."):
            
            # 1. Save uploaded file temporarily for the API to access
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
 
            try:
                # 2. Upload video to Gemini API
                video_file = genai.upload_file(path=temp_file_path)
                
                # Wait for the video to process in Google's servers
                while video_file.state.name == 'PROCESSING':
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
 
                # 3. Call the Model with the hidden system prompt
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = """
                Analyze the video and output the chronological sequence of worker actions.
                STRICT RULES:
                - Use ONLY these exact phrases, adjusting steps where necessary: WALK X-Y STEPS, GET + HOLD OBJECT, HOLD + PUT OBJECT, GRASP + USE TOOL, GRASP + PLACE OBJECT, HOLD + SLIDE OBJECT.
                - Output each action on a new line.
                - NO introductions, NO timestamps, NO markdown, NO concluding remarks.
                """
                
                response = model.generate_content([video_file, prompt])
                
                # 4. Process the output into Pandas
                # Split the text response by new lines and remove any empty strings
                actions = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                
                df = pd.DataFrame(actions, columns=["Action Sequence"])
                
                # 5. Show results and create Excel download
                st.success("Analysis Complete!")
                st.dataframe(df)
                
                # Convert DF to Excel in memory
                excel_buffer = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                df.to_excel(excel_buffer.name, index=False)
                
                with open(excel_buffer.name, "rb") as file:
                    st.download_button(
                        label="📥 Download Excel Sheet",
                        data=file,
                        file_name="action_sequence.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
 
            finally:
                # Clean up temporary files
                os.remove(temp_file_path)
                if 'excel_buffer' in locals():
                    os.remove(excel_buffer.name)