import streamlit as st
import sqlite3
import json
import socket
from datetime import datetime
from streamlit_extras.authenticator import login

# Set up the database
conn = sqlite3.connect('quiz_app.db', check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, question TEXT, options TEXT, answer TEXT, info TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, user TEXT, ip TEXT, score INTEGER, timestamp TEXT)''')
conn.commit()

# Function to get user IP
def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "Unknown"

# Authentication system using Streamlit login
user = login(fields=["username", "password"], title="Login", form_key="login_form")
if user:
    st.session_state['user'] = user
    st.sidebar.success(f"Logged in as {user['username']}")

# Show leaderboard
def show_leaderboard():
    st.subheader("Leaderboard")
    c.execute("SELECT user, MAX(score) FROM attempts GROUP BY user ORDER BY MAX(score) DESC")
    data = c.fetchall()
    for rank, (user, score) in enumerate(data, 1):
        st.write(f"{rank}. {user} - {score} points")

# Admin Panel
def admin_panel():
    st.title("Admin Panel")
    show_leaderboard()
    if st.button("Add Question"):
        q = st.text_input("Question")
        options = st.text_area("Options (comma-separated)")
        answer = st.text_input("Correct Answer")
        info = st.text_area("Additional Info")
        if st.button("Submit Question"):
            c.execute("INSERT INTO questions (question, options, answer, info) VALUES (?, ?, ?, ?)", (q, options, answer, info))
            conn.commit()
            st.success("Question Added!")

# Student Quiz
def student_quiz():
    st.title("Live Quiz")
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    if 'quiz_progress' not in st.session_state:
        st.session_state['quiz_progress'] = {'index': 0, 'score': 0}

    if st.session_state['quiz_progress']['index'] < len(questions):
        q_id, question, options, answer, info = questions[st.session_state['quiz_progress']['index']]
        st.subheader(f"Q{st.session_state['quiz_progress']['index'] + 1}: {question}")
        options = options.split(",")
        choice = st.radio("Select an option:", options)
        if st.button("Submit"):
            if choice == answer:
                st.success("Correct!")
                st.session_state['quiz_progress']['score'] += 10
            else:
                st.error("Incorrect!")
            st.session_state['quiz_progress']['index'] += 1
    else:
        st.write(f"Quiz completed! Final Score: {st.session_state['quiz_progress']['score']}")
        c.execute("INSERT INTO attempts (user, ip, score, timestamp) VALUES (?, ?, ?, ?)", (st.session_state['user']['username'], get_ip(), st.session_state['quiz_progress']['score'], str(datetime.now())))
        conn.commit()
        st.session_state['quiz_progress'] = {'index': 0, 'score': 0}

# Main App Logic
if 'user' in st.session_state:
    user = st.session_state['user']
    if user['role'] == "Admin":
        admin_panel()
    else:
        student_quiz()
