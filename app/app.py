import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os

# -------------------------
# Load Model
# -------------------------

model = joblib.load("repo_success_model.pkl")
scaler = joblib.load("scaler.pkl")

st.set_page_config(page_title="GitHub AI Repository Analyzer", layout="wide")

# -------------------------
# Sidebar Inputs
# -------------------------

st.sidebar.title("Repository Metrics")

forks = st.sidebar.number_input("Forks Count", min_value=0.0, value=2.0)
watchers = st.sidebar.number_input("Watchers", min_value=0.0, value=1.5)
prs = st.sidebar.number_input("Pull Requests", min_value=0.0, value=2.0)
commits = st.sidebar.number_input("Commit Count", min_value=0.0, value=3.0)
engagement = st.sidebar.number_input("Engagement Score", min_value=0.0, value=5.0)
language = st.sidebar.number_input("Primary Language Code", min_value=0.0, value=5.0)

st.sidebar.markdown("### Feature Guide")

st.sidebar.info("""
Forks → number of repository forks  
Watchers → repo followers  
PRs → pull requests activity  
Commits → development activity  
Engagement → community interaction  
Language → encoded language
""")

# -------------------------
# GitHub Repo Analyzer
# -------------------------

st.sidebar.markdown("### Analyze GitHub Repository")

repo_url = st.sidebar.text_input("Paste GitHub Repo URL")

if repo_url:

    try:

        repo_name = repo_url.replace("https://github.com/", "")

        api_url = f"https://api.github.com/repos/{repo_name}"

        response = requests.get(api_url)

        if response.status_code == 200:

            data = response.json()

            forks = data["forks_count"]
            watchers = data["watchers_count"]

            prs = data["open_issues_count"]
            commits = forks * 2
            engagement = watchers + forks

            st.sidebar.success("Repository data loaded")

            st.sidebar.write("Forks:", forks)
            st.sidebar.write("Watchers:", watchers)

        else:
            st.sidebar.error("Repository not found")

    except:
        st.sidebar.error("Invalid GitHub URL")

# -------------------------
# Tabs
# -------------------------

tab1, tab2 = st.tabs(["Analyzer", "Model Details"])

# -------------------------
# Analyzer Tab
# -------------------------

with tab1:

    st.title("GitHub AI Repository Analyzer")

    st.write("Predict repository success and analyze project health.")

    st.divider()

    if st.button("Analyze Repository"):

        query = np.array([[forks, watchers, prs, commits, engagement, language]])

        query = np.log1p(query)
        query = scaler.transform(query)

        prediction = model.predict(query)
        probability = model.predict_proba(query)[0][1]

        st.subheader("Success Prediction")

        if prediction[0] == 1:
            st.success("Repository likely SUCCESSFUL")
        else:
            st.error("Repository likely NOT successful")

        st.metric("Success Probability", f"{probability*100:.1f}%")

        # -------------------------
        # Probability Gauge
        # -------------------------

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=probability*100,
            title={'text': "Success Probability"},
            gauge={
                'axis': {'range':[0,100]},
                'bar': {'color':"green"},
                'steps':[
                    {'range':[0,40],'color':"red"},
                    {'range':[40,70],'color':"orange"},
                    {'range':[70,100],'color':"lightgreen"}
                ]
            }
        ))

        st.plotly_chart(fig_gauge, use_container_width=True)

        st.divider()

        # -------------------------
        # Repository Health Scores
        # -------------------------

        community_score = watchers + forks + prs
        activity_score = commits + prs
        growth_score = forks * watchers

        col1, col2, col3 = st.columns(3)

        col1.metric("Community Strength", community_score)
        col2.metric("Developer Activity", activity_score)
        col3.metric("Growth Potential", growth_score)

        # -------------------------
        # Health Analytics Chart
        # -------------------------

        scores = pd.DataFrame({
            "Metric":[
                "Community Strength",
                "Developer Activity",
                "Growth Potential"
            ],
            "Score":[
                community_score,
                activity_score,
                growth_score
            ]
        })

        fig_scores = px.bar(
            scores,
            x="Metric",
            y="Score",
            color="Metric",
            title="Repository Health Analytics"
        )

        st.plotly_chart(fig_scores, use_container_width=True)

        st.divider()

        # -------------------------
        # Save Prediction
        # -------------------------

        record = {
            "Forks": forks,
            "Watchers": watchers,
            "Pull Requests": prs,
            "Commits": commits,
            "Engagement": engagement,
            "Language": language,
            "Success Probability": round(probability,3)
        }

        df = pd.DataFrame([record])

        if os.path.exists("prediction_history.csv"):
            df.to_csv("prediction_history.csv", mode="a", header=False, index=False)
        else:
            df.to_csv("prediction_history.csv", index=False)

        st.download_button(
            "Download Prediction",
            df.to_csv(index=False),
            file_name="prediction.csv"
        )

        st.divider()

        # -------------------------
        # Prediction History
        # -------------------------

        st.subheader("Prediction History")

        if os.path.exists("prediction_history.csv"):

            history = pd.read_csv("prediction_history.csv")

            st.dataframe(history)

            if "Success Probability" in history.columns:

                fig_trend = px.line(
                    history,
                    y="Success Probability",
                    markers=True,
                    title="Prediction Trend"
                )

                st.plotly_chart(fig_trend, use_container_width=True)

        st.divider()

        # -------------------------
        # Input Metrics Chart
        # -------------------------

        st.subheader("Repository Metrics")

        df_metrics = pd.DataFrame({
            "Metric":["Forks","Watchers","PRs","Commits","Engagement"],
            "Value":[forks,watchers,prs,commits,engagement]
        })

        fig_metrics = px.bar(
            df_metrics,
            x="Metric",
            y="Value",
            color="Metric"
        )

        st.plotly_chart(fig_metrics, use_container_width=True)

        st.divider()

        # -------------------------
        # Model Explanation
        # -------------------------

        st.subheader("Factors Affecting Prediction")

        coeff = model.coef_[0]

        features = [
            "forks",
            "watchers",
            "pull_requests",
            "commits",
            "engagement",
            "language"
        ]

        impact = coeff * query[0]

        df_explain = pd.DataFrame({
            "Feature":features,
            "Impact":impact
        }).sort_values("Impact")

        fig_exp = px.bar(
            df_explain,
            x="Impact",
            y="Feature",
            orientation="h",
            color="Impact"
        )

        st.plotly_chart(fig_exp, use_container_width=True)

# -------------------------
# Model Details Tab
# -------------------------

with tab2:

    st.header("Model Details")

    st.write("""
Machine Learning Model: Logistic Regression

Pipeline:
Raw Data → Log Transformation → Scaling → Logistic Regression

Evaluation Metrics:
Accuracy ≈ 0.83
ROC-AUC ≈ 0.90
""")

    st.subheader("Feature Importance")

    features = [
        "forks",
        "watchers",
        "pull_requests",
        "commits",
        "engagement",
        "language"
    ]

    importance = abs(model.coef_[0])

    df_imp = pd.DataFrame({
        "Feature":features,
        "Importance":importance
    })

    fig_imp = px.bar(
        df_imp,
        x="Importance",
        y="Feature",
        orientation="h"
    )

    st.plotly_chart(fig_imp, use_container_width=True)