import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle


st.set_page_config(
    page_title="Smart Chef App",
    layout="wide",
    page_icon="🍳"
)

st.markdown("""
<style>

/* Background utama */
.stApp {
    background-color: #F5EFE6;
}

/* Sidebar lebih elegan */
section[data-testid="stSidebar"] {
    background: #2F3E2E;
    padding-top: 20px;
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: #F1F5F1;
}

/* Sidebar title */
section[data-testid="stSidebar"] h1 {
    color: #FFFFFF;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton>button {
    background-color: #3F5F45;
    border-radius: 10px;
    border: none;
    padding: 12px;
    font-weight: 500;
}

section[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #4F7A57;
}

/* INPUT BOX */
.stTextInput input {
    border: 2px solid #D6D3D1 !important;
    border-radius: 8px !important;
    padding: 10px !important;
}

.stTextInput input:focus {
    border: 2px solid #F97316 !important;
}

/* Selectbox */
.stSelectbox div[data-baseweb="select"] {
    border: 2px solid #D6D3D1 !important;
    border-radius: 8px !important;
}

/* Button utama */
.stButton>button {
    background-color: #16A34A;
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
    border: none;
    font-weight: 600;
}

.stButton>button:hover {
    background-color: #15803D;
}

/* Recipe card */
.recipe-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    border-left: 6px solid #F97316;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Title */
h1, h2, h3 {
    color: #7C2D12;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align:center; font-size:43px;'>🍳 Smart Chef Recommendation System</h1>
<p style='text-align:center; font-size:18px; color:#7C2D12;'>
Discover delicious recipes from ingredients you already have
</p>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("resep_masakan.csv")
    df['ingredient_list'] = df['bahan'].apply(
        lambda x: [i.strip().lower() for i in x.split(',')]
    )
    return df

@st.cache_resource
def load_model():
    with open("apriori_model.pkl", "rb") as f:
        return pickle.load(f)

try:
    df = load_data()
    loaded_model = load_model()

    rules_per_country = loaded_model["rules_per_country"]
    frequent_itemsets_per_country = loaded_model["frequent_itemsets_per_country"]

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# RECOMMENDATION FUNCTION
def get_recommendations(country_input, user_ingredients):
    user_ingredients = set(
        [i.lower().strip() for i in user_ingredients if i]
    )

    rules = rules_per_country.get(country_input, pd.DataFrame())
    additional = set()

    if not rules.empty:
        for _, row in rules.iterrows():
            if row["antecedents"].issubset(user_ingredients):
                additional.update(row["consequents"])

    total_ingredients = user_ingredients.union(additional)
    df_country = df[df["negara"] == country_input]
    results = []

    for _, row in df_country.iterrows():
        recipe_ingredients = set(row["ingredient_list"])
        matched = recipe_ingredients.intersection(total_ingredients)
        score = len(matched) / len(recipe_ingredients)

        if score > 0.10:
            results.append({
                "Recipe": row["masakan"],
                "Match Score": score,
                "Matched": ", ".join(matched),
                "Missing": ", ".join(recipe_ingredients - total_ingredients)
            })
    return pd.DataFrame(results).sort_values("Match Score", ascending=False)


# SIDEBAR MENU
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

with st.sidebar:
    st.markdown("## 👨‍🍳 Smart Chef")
    if st.button("📊 Popular Ingredients", use_container_width=True):
        st.session_state.menu = "Dashboard"
        st.rerun()
    if st.button("🔍 Recommendation Recipe", use_container_width=True):
        st.session_state.menu = "RecipeFinder"
        st.rerun()
    if st.button("➕ Add Recipe", use_container_width=True):
        st.session_state.menu = "AddRecipe"
        st.rerun()

# DASHBOARD PAGE
if st.session_state.menu == "Dashboard":
    st.title("📊 Popular Ingredients Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Recipes", len(df))
    col2.metric("Countries", df["negara"].nunique())
    col3.metric("Unique Ingredients",
                df["ingredient_list"].explode().nunique())
    st.markdown("---")

    country = st.selectbox(
        "Select Country",
        df["negara"].unique()
    )

    frequent_itemsets = frequent_itemsets_per_country.get(country)
    if frequent_itemsets is not None:

        one_itemsets = frequent_itemsets[
            frequent_itemsets["itemset_length"] == 1
        ].copy()

        one_itemsets["ingredient"] = one_itemsets["itemsets"].apply(
            lambda x: list(x)[0]
        )

        one_itemsets = one_itemsets.sort_values(
            "support",
            ascending=False
        ).head(10)

        fig, ax = plt.subplots(figsize=(10,5))

        sns.barplot(
            x="support",
            y="ingredient",
            data=one_itemsets,
            palette="Greens_r",
            ax=ax
        )

        ax.set_title(f"Top Ingredients in {country}")
        st.pyplot(fig)

    else:
        st.info("No data available")

# RECIPE FINDER PAGE
elif st.session_state.menu == "RecipeFinder":
    st.title("🔍 Recommendation Recipe")
    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox(
            "Select Country",
            df["negara"].unique()
        )

    ing1 = st.text_input("Ingredient 1")
    ing2 = st.text_input("Ingredient 2")
    ing3 = st.text_input("Ingredient 3")

    if st.button("🔍 Get Recommendation"):
        ingredients = [i for i in [ing1, ing2, ing3] if i]
        if len(ingredients) == 0:

            st.warning("Please input at least one ingredient")
        else:
            result = get_recommendations(country, ingredients)
            if not result.empty:
                st.success("Recommended Recipes")
                for _, row in result.head(5).iterrows():

                    st.markdown(f"""
                    <div class="recipe-card">
                    <h3>🍽 {row['Recipe']}</h3>
                    <p><b>Match Score:</b> {row['Match Score']*100:.1f}%</p>
                    <p><b>Missing Ingredients:</b> {row['Missing']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.progress(row["Match Score"])
            else:
                st.info("No recipes found.")


# ADD RECIPE PAGE
elif st.session_state.menu == "AddRecipe":
    st.title("➕ Add New Recipe")

    with st.form("recipe_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        new_country = col1.text_input("Country")
        new_name = col2.text_input("Recipe Name")
        new_ingredients = st.text_area("Ingredients (comma separated)")
        submit = st.form_submit_button("Save Recipe")

        if submit:
            if new_country and new_name and new_ingredients:

                new_row = {
                    "negara": new_country.strip(),
                    "masakan": new_name.strip(),
                    "bahan": new_ingredients.strip()
                }
                try:
                    df_update = pd.read_csv("update_dataset.csv")
                except FileNotFoundError:
                    df_update = pd.DataFrame(columns=["negara", "masakan", "bahan"])

                df_update = pd.concat([df_update, pd.DataFrame([new_row])], ignore_index=True)
                df_update.to_csv("update_dataset.csv", index=False)
                st.success("Recipe saved successfully🎉")
            else:
                st.error("Please fill all fields")