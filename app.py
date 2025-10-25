import streamlit as st
from supabase import create_client
from datetime import datetime
import os

# ===============================
# 🔐 Supabase Setup
# ===============================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================
# 🗃️ Database Functions
# ===============================

def init_db():
    """Ensure the projects table exists."""
    ddl = """
    create table if not exists projects (
        id serial primary key,
        project_name text not null,
        description text not null,
        date_added timestamp default current_timestamp
    );
    """
    try:
        # Execute raw SQL
        supabase.rpc("execute_sql", {"sql": ddl}).execute()
    except Exception:
        # If rpc doesn't exist yet, just skip silently (Supabase default table might already exist)
        pass

def add_project(name, desc):
    supabase.table("projects").insert(
        {"project_name": name, "description": desc}
    ).execute()

def update_project(project_id, name, desc):
    supabase.table("projects").update(
        {"project_name": name, "description": desc}
    ).eq("id", project_id).execute()

def delete_project(project_id):
    supabase.table("projects").delete().eq("id", project_id).execute()

def get_projects(keyword=None):
    query = supabase.table("projects").select("*").order("date_added", desc=True)
    if keyword:
        query = query.or_(
            f"project_name.ilike.%{keyword}%,description.ilike.%{keyword}%"
        )
    res = query.execute()
    return res.data or []

# ===============================
# 🧩 Utility
# ===============================
def copy_to_clipboard(text):
    js_code = f"""
    <script>
        navigator.clipboard.writeText(`{text}`).then(() => {{
            alert("Copied to clipboard!");
        }});
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

# ===============================
# 🎨 Streamlit UI
# ===============================
st.set_page_config(page_title="Project Manager", page_icon="📂", layout="wide")
st.title("📂 My Project Manager (Supabase Edition)")

# Initialize DB (safe to call multiple times)
try:
    init_db()
except Exception as e:
    st.warning(f"⚠️ Couldn't verify DB schema: {e}")

menu = st.sidebar.radio("Navigation", ["➕ Add New Project", "📋 Dashboard"])

if menu == "➕ Add New Project":
    st.subheader("Add a New Project")
    with st.form("add_project_form"):
        name = st.text_input("Project Name")
        desc = st.text_area("Project Description (can include live links, tech stack, etc.)", height=200)
        submitted = st.form_submit_button("Save Project")
        if submitted:
            if name.strip() and desc.strip():
                add_project(name, desc)
                st.success(f"✅ Project '{name}' added successfully!")
            else:
                st.warning("⚠️ Please fill in all fields.")

elif menu == "📋 Dashboard":
    st.subheader("Projects Dashboard")
    keyword = st.text_input("🔍 Search by keyword", placeholder="Enter keyword (e.g., Python, chatbot, API)")
    projects = get_projects(keyword)

    if projects:
        for p in projects:
            with st.expander(f"📌 {p['project_name']}"):
                st.markdown(p['description'], unsafe_allow_html=True)
                date_added = p.get("date_added")
                if date_added:
                    if isinstance(date_added, str):
                        try:
                            date_added = datetime.fromisoformat(date_added.replace("Z", ""))
                        except:
                            pass
                    st.markdown(f"*Added on: {date_added.strftime('%Y-%m-%d')}*")

                col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
                with col1:
                    if st.button("📋 Copy", key=f"copy_{p['id']}"):
                        copy_to_clipboard(p['description'])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{p['id']}"):
                        with st.form(f"edit_form_{p['id']}"):
                            new_name = st.text_input("Project Name", value=p['project_name'])
                            new_desc = st.text_area("Description", value=p['description'], height=200)
                            if st.form_submit_button("Update"):
                                update_project(p['id'], new_name, new_desc)
                                st.success("✅ Project updated successfully!")
                                st.experimental_rerun()
                with col3:
                    if st.button("🗑 Delete", key=f"delete_{p['id']}"):
                        delete_project(p['id'])
                        st.warning("🗑 Project deleted!")
                        st.experimental_rerun()
                st.markdown("---")
    else:
        st.info("No projects found. Try a different keyword or add a new one.")
