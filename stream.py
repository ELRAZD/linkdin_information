import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from main import Data_Mining

CSV_PATH = r"C:\Users\Elyar\Desktop\test\job_data.csv"
SEARCH_DATA_PATH = r"C:\Users\Elyar\Desktop\test\linkedin_search_data_large.csv"

st.set_page_config(page_title="LinkedIn Job Scraper", layout="wide")
st.title("🔍 Live LinkedIn Job Scraper")

with st.form("job_form"):
    job_title = st.text_input("🔤 Job Title", value="java")
    location = st.text_input("📍 Location", value="germany")
    count = st.number_input("📦 Number of Jobs to Scrape", min_value=1, value=50)
    submitted = st.form_submit_button("🚀 Start Scraping")

if submitted:
    scraper = Data_Mining()
    try:
        with st.spinner("🧭 Launching browser..."):
            scraper.setup_driver()

        with st.expander("🔐 LinkedIn Login", expanded=True):
            st.markdown("✅ Please log into your LinkedIn account in the browser and solve the CAPTCHA if prompted.")
            st.code("⏳ Wait until you're redirected to LinkedIn's homepage...")

        scraper.login()

        with st.spinner("🔎 Searching jobs..."):
            scraper.jobs(job_title, location)

        with st.spinner("📥 Scraping job data..."):
            scraper.job_scraper(count)

        st.success("✅ Scraping completed successfully!")
           
        st.subheader("📄 Suggested Resume for You")

        resume_dir = "resumes"
        resume_file_name = f"{job_title.lower().strip().replace(' ', '_')}.txt"
        resume_file_path = os.path.join(resume_dir, resume_file_name)

        if os.path.exists(resume_file_path):
            with open(resume_file_path, "r", encoding="utf-8") as file:
                resume_text = file.read()
                st.code(resume_text, language="text")

            with open(resume_file_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download Suggested Resume",
                    data=file,
                    file_name=resume_file_name,
                    mime="text/plain"
                )
        else:
            st.warning("⚠️ No suggested resume found for this job title.")


    except Exception as e:
        st.error(f"❌ Error during scraping: {e}")

    finally:
        try:
            scraper.driver.quit()
        except:
            pass


if os.path.exists(CSV_PATH):
    st.subheader("📋 Extracted Job Results:")
    df = pd.read_csv(CSV_PATH)

    with st.expander("🔧 Filter Results"):
        location_filter = st.multiselect("🌍 Filter by Location", df["Location"].dropna().unique())
        company_filter = st.multiselect("🏢 Filter by Company", df["Company"].dropna().unique())
        title_search = st.text_input("🔎 Search by Job Title")

    filtered_df = df.copy()
    if location_filter:
        filtered_df = filtered_df[filtered_df["Location"].isin(location_filter)]
    if company_filter:
        filtered_df = filtered_df[filtered_df["Company"].isin(company_filter)]
    if title_search:
        filtered_df = filtered_df[filtered_df["Title"].str.contains(title_search, case=False, na=False)]

    st.metric("📊 Number of Jobs After Filtering", len(filtered_df))

    
    with st.expander("📊 Location Distribution"):
        location_count = filtered_df['Location'].value_counts().head(10)

        fig, ax = plt.subplots(figsize=(10, 6), facecolor='black')
        bars = ax.bar(location_count.index, location_count.values, color='deepskyblue', edgecolor='white')

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, color='white')

        ax.set_facecolor('black')
        ax.set_title("📍 Job Count by Location", fontsize=14, color='white')
        ax.set_xlabel("Location", fontsize=12, color='white')
        ax.set_ylabel("Number of Jobs", fontsize=12, color='white')
        ax.tick_params(colors='white')
        plt.xticks(rotation=45, ha='right', color='white')
        plt.tight_layout()
        st.pyplot(fig)

    
    def make_clickable(link):
        return f'<a href="{link}" target="_blank">View on LinkedIn</a>'

    filtered_df['Link_View'] = filtered_df['Link'].apply(make_clickable)

    
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df.insert(0, "No", filtered_df.index + 1)

    st.write("### 📄 Job Listings")
    st.write(
        filtered_df[['No', 'Title', 'Company', 'Location', 'Salary', 'Link_View']].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    
    st.download_button(
        label="⬇️ Download Filtered Results",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_jobs.csv",
        mime="text/csv"
    )


st.markdown("---")
if os.path.exists(SEARCH_DATA_PATH):
    search_df = pd.read_csv(SEARCH_DATA_PATH)
    job_demand = search_df.groupby("job_title")["search_count"].sum().sort_values(ascending=False)

    st.subheader("📊 Job Demand Comparison")

    job_options = list(job_demand.index)
    default_jobs = [job for job in ["java", "python"] if job in job_options]
    selected_jobs = st.multiselect("🔎 Select Job Titles to Compare", options=job_options, default=default_jobs)

    if selected_jobs:
        selected_demand = job_demand[selected_jobs]

        col1, col2 = st.columns(2)

        
        with col1:
            fig1, ax1 = plt.subplots(figsize=(8, 5), facecolor="black")
            sns.set_style("white")
            sns.barplot(x=selected_demand.values, y=selected_demand.index, ax=ax1, palette="plasma")
            ax1.set_title("💼 Job Demand", fontsize=16, color='white')
            ax1.set_xlabel("Search Count", fontsize=12, color='white')
            ax1.set_ylabel("Job Title", fontsize=12, color='white')
            ax1.set_facecolor("black")
            ax1.tick_params(colors='white')
            for spine in ax1.spines.values():
                spine.set_edgecolor('white')
            plt.tight_layout()
            st.pyplot(fig1)

        
        with col2:
            fig2, ax2 = plt.subplots(figsize=(6, 6), facecolor='black', subplot_kw=dict(aspect="equal"))

            def func(pct, allvals):
                absolute = int(np.round(pct/100.*np.sum(allvals)))
                return f"{pct:.1f}%\n({absolute})"

            wedges, texts, autotexts = ax2.pie(
                selected_demand.values,
                labels=selected_demand.index,
                autopct=lambda pct: func(pct, selected_demand.values),
                textprops=dict(color="white"),
                colors=plt.cm.tab20.colors
            )

            plt.setp(autotexts, size=8, weight="bold")
            ax2.set_title("🔍 Search Share by Job Title", fontsize=14, color='white')
            ax2.legend(wedges, selected_demand.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), labelcolor='white')
            st.pyplot(fig2)
else:
    st.error("❌ Search data file not found.")