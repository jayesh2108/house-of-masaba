import streamlit as st
import pandas as pd
import openai
import re
from datetime import datetime
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="House of Masaba AEO Insights", layout="wide", page_icon="🎨")

st.title("🎨 House of Masaba: Luxury AEO Analyzer")
st.markdown("Track visibility for **India's Queen of Prints** across luxury ethnic and fusion AI searches.")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("1. Brand & Market Settings")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    
    brand_name = st.text_input("Brand Name", value="House of Masaba")
    brand_domain = st.text_input("Brand Domain", value="houseofmasaba.com")
    
    # Mode Selection
    input_mode = st.radio("Category Mode", ["Designer Signature", "Manual Entry"])
    
    # Masaba-specific luxury categories
    masaba_categories = (
        "designer print sarees, luxury silk kaftans, quirky bridal lehengas, "
        "fusion pret wear for women, gold foil print anarkalis, luxury resort wear India, "
        "designer fine jewellery, celebrity-inspired ethnic wear"
    )
    
    if input_mode == "Manual Entry":
        categories_input = st.text_area("Type custom categories (comma separated)", 
                                       placeholder="e.g. wedding guest outfits, floral capes, organza sarees")
    else:
        categories_input = st.text_area("Signature Brand Categories", value=masaba_categories)
    
    num_queries_per_cat = st.slider("Queries per Category", 2, 5, 3)
    
    if api_key:
        openai.api_key = api_key

# --- CORE LOGIC ---

def discover_luxury_prompts(categories, n):
    client = openai.OpenAI(api_key=api_key)
    cat_list = [c.strip() for c in categories.split(",") if c.strip()]
    all_q = []
    for cat in cat_list:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI luxury fashion consultant for the Indian market. Focus on high-end, designer-seeking shoppers."},
                {"role": "user", "content": f"Find {n} realistic non-branded queries a luxury shopper in India would ask for: '{cat}'. One per line."}
            ]
        )
        all_q.extend(resp.choices[0].message.content.strip().splitlines())
    return [q.strip("-•1234567890. ") for q in all_q if q.strip()]

def check_designer_presence(query, brand_name, brand_domain):
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Rank the top 10 luxury designer brands for the query in India. Format: Rank | Brand | USP. Provide AEO advice for {brand_name} to win this query."},
                {"role": "user", "content": f"Query: {query}"}
            ]
        )
        output = resp.choices[0].message.content.strip()
        # Broad check for "Masaba" or domain
        present = "Yes" if "masaba" in output.lower() else "No"
        return {"Query": query, "Brand Present": present, "AI Context": output}
    except Exception as e:
        return {"Query": query, "Brand Present": "Error", "AI Context": str(e)}

# --- APP INTERFACE ---

if st.button("🚀 Analyze Designer Visibility"):
    if not api_key:
        st.error("Please enter your OpenAI API Key.")
    else:
        st.session_state['masaba_results'] = None
        with st.status("Analyzing Designer Landscape...", expanded=True) as status:
            st.write("💎 Curating luxury shopping prompts...")
            queries = discover_luxury_prompts(categories_input, num_queries_per_cat)
            
            results = []
            progress = st.progress(0)
            for i, q in enumerate(queries):
                st.write(f"Evaluating: **{q}**")
                results.append(check_designer_presence(q, brand_name, brand_domain))
                progress.progress((i + 1) / len(queries))
            
            df = pd.DataFrame(results)
            st.session_state['masaba_results'] = df
            status.update(label="Analysis Complete!", state="complete")

# --- DASHBOARD DISPLAY ---

if 'masaba_results' in st.session_state and st.session_state['masaba_results'] is not None:
    df = st.session_state['masaba_results']
    
    st.divider()
    
    # High-level Metrics
    col1, col2 = st.columns(2)
    with col1:
        sov = (df[df['Brand Present'] == "Yes"].shape[0] / len(df)) * 100
        st.metric("Masaba Share of Voice (SOV)", f"{sov:.1f}%")
        
    with col2:
        fig = px.pie(df, names="Brand Present", title="Presence in Designer Search Results",
                     color="Brand Present", color_discrete_map={"Yes":"#D4AF37", "No":"#2C3E50"}) # Gold & Navy
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Designer Market Intelligence")
    st.dataframe(df, use_container_width=True)
    
    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Luxury Report", data=csv, file_name="masaba_aeo_report.csv")