import streamlit as st
import requests
import base64
from helpers import parse_cv, extract_keywords

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

st.set_page_config(page_title="AutoHire", layout="centered")

# bg setting css used in martdown
def set_bg_from_local(image_file):
    with open(image_file, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
    background = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: black;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}
    </style>
    """
    st.markdown(background, unsafe_allow_html=True)

set_bg_from_local("img7.jpg")

st.markdown("""
    <style>
    /* Default: all text black */
    body, .stApp, .css-1d391kg, .css-ffhzg2, .css-10trblm, .css-1cpxqw2 {
        color: black !important;
    }

    /* File uploader label */
    .stFileUploader label {
        color: black !important;
        font-weight: bold;
    }

    /* Button: white text if dark background */
    .stButton>button {
        color: white !important;
        background-color: black !important;
        border: 1px solid white;
    }

    /* Expander: white title if dark background */
    .stExpander>summary {
        color: white !important;
        background-color: black !important;
    }

    /* Text area: white text inside dark box */
    textarea {
        color: white !important;
        background-color: #111 !important;
    }

    /* Download button */
    .stDownloadButton>button {
        color: white !important;
        background-color: black !important;
        border: 1px solid white;
    }
    </style>
""", unsafe_allow_html=True)


#fethicg jobs form the api arbritnow

def fetch_remotive_jobs(keywords, limit=10):
    jobs = []
    url = "https://www.arbeitnow.com/api/job-board-api"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for job in data.get("data", []):
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()

            if any(keyword.lower() in title or keyword.lower() in description for keyword in keywords):
                jobs.append({
                    "title": job.get("title"),
                    "company": job.get("company_name"),
                    "location": job.get("location"),
                    "description": job.get("description"),
                    "link": job.get("url")
                })

            if len(jobs) >= limit:
                break

    except requests.RequestException as e:
        st.warning(f"Uh-oh! Couldn't fetch jobs: {e}")
    except ValueError:
        st.warning("Received invalid JSON response from Arbeitnow API.")

    return jobs

def generate_cover_letter(name, job_title, experience, skills, job_description):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourappname.streamlit.app",
        "X-Title": "AutoHire App"
    }

    prompt = f"""
    Write a personalized cover letter for a job application.

    Name: {name}
    Job Title: {job_title}
    Experience: {experience}
    Skills: {skills}
    Job Description: {job_description}

    The tone should be professional, enthusiastic, and tailored to the job.
    """

    body = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=body)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"❌ Error: {response.status_code} - {response.text}"

def main():
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style="
            font-size: 3.5em;
            color: black;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            text-shadow: 1px 1px 2px #CCCCCC;
            animation: fadeIn 2s;
        ">
              AutoHire
        </h1>
        <p style='font-size: 1.2em; color: black;'>Your AI-powered bestie for job hunting</p>
    </div>

    <style>
    @keyframes fadeIn {
      from {opacity: 0;}
      to {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

    st.markdown("### Upload Your CV", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop your CV here 👇", type=["pdf"])

    if uploaded_file:
        cv_path = "uploaded_cv.pdf"
        with open(cv_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success("CV uploaded successfully!")

        cv_text = parse_cv(cv_path)

        # name being taken from the first line of the cv
        cv_lines = cv_text.strip().split("\n")
        name = cv_lines[0] if cv_lines else ""
        name = " ".join([word.capitalize() for word in name.split()]) if name else ""


        keywords = extract_keywords(cv_text)

        st.markdown("###  Remote Jobs Just for You", unsafe_allow_html=True)
        jobs = fetch_remotive_jobs(keywords)

        if jobs:
            for idx, job in enumerate(jobs):
                with st.expander(f"{job['title']} at {job['company']}"):
                    st.write(f"Location: {job['location']}")
                    st.markdown(f"[🔗 View Job Posting]({job['link']})", unsafe_allow_html=True)
                    
                    if st.button(f"Generate Cover Letter for {job['title']} ({idx})"):
                        if not name:
                            st.warning("Please upload a valid CV to auto-detect your name.")
                        else:
                            with st.spinner("Generating your awesome cover letter..."):
                                cover_letter = generate_cover_letter(
                                    name=name,
                                    job_title=job['title'],
                                    experience="Based on my CV and past experience.",
                                    skills=", ".join(keywords),
                                    job_description=job['description']
                                )
                                st.subheader("Your AI-Generated Cover Letter")
                                st.text_area("Cover Letter", cover_letter, height=300)
                                st.download_button("Download Cover Letter", cover_letter, file_name=f"{job['title']}_cover_letter.txt")
        else:
            st.info(" No jobs matched. Try uploading a different CV or updating your skills!")

    else:
        st.info("📎 Upload your CV above to get started!")


if __name__ == "__main__":
    main()
