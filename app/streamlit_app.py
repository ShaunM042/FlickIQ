import os
import psycopg2
import requests
import streamlit as st


DATABASE_URL = os.environ.get("DATABASE_URL")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender")

# --- User selection ---
st.subheader("Select User")
user_options: list[int] = []
if DATABASE_URL:
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 100")
            user_options = [int(r[0]) for r in cur.fetchall()]
    except Exception:
        pass

if user_options:
    user_id = st.selectbox("User", options=user_options, index=0)
else:
    user_id = st.number_input("User ID", min_value=1, value=1, step=1)

limit = st.slider("How many recommendations?", min_value=1, max_value=50, value=10)

if st.button("Get Recommendations"):
    # Fetch recommendations from FastAPI
    try:
        resp = requests.get(f"{API_BASE_URL}/recommendations/{user_id}", params={"limit": limit}, timeout=15)
        if resp.status_code != 200:
            st.error(f"API error: {resp.status_code} {resp.text}")
        else:
            data = resp.json()
            items = data.get("items", [])
            if not items:
                st.info("No recommendations available. Train the model and save embeddings first.")
            else:
                cols = st.columns(5)
                for idx, item in enumerate(items):
                    movie_id = int(item.get("movie_id"))
                    title = item.get("title")
                    year = item.get("year")
                    poster = item.get("poster_path")
                    overview = item.get("overview")
                    with cols[idx % 5]:
                        if poster:
                            st.image(f"https://image.tmdb.org/t/p/w342{poster}", use_column_width=True)
                        st.markdown(f"**{title}** ({year or 'N/A'})")
                        if overview:
                            st.caption(overview[:160] + ("…" if len(overview) > 160 else ""))

                        # Rating controls: 1–5 buttons
                        st.write("")
                        btn_cols = st.columns(5)
                        for r in [1, 2, 3, 4, 5]:
                            with btn_cols[r - 1]:
                                if st.button(str(r), key=f"rate_{user_id}_{movie_id}_{r}"):
                                    try:
                                        r_resp = requests.post(
                                            f"{API_BASE_URL}/interact",
                                            json={"user_id": user_id, "movie_id": movie_id, "rating": r},
                                            timeout=10,
                                        )
                                        if r_resp.status_code == 200:
                                            st.success("Feedback recorded")
                                        else:
                                            st.error(f"Failed: {r_resp.status_code}")
                                    except Exception as ex:
                                        st.error(f"Request failed: {ex}")
    except Exception as e:
        st.error(f"Failed to fetch recommendations: {e}")


