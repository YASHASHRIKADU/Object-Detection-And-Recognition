
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session
import sqlite3, subprocess, sys

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_secret_key_if_env_missing")
DB="database.db"

def get_db():
    return sqlite3.connect(DB)

def init_db():
    con=get_db()
    cur=con.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS detections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object_name TEXT,
        confidence REAL,
        detected_time TEXT
    )
    ''')

    con.commit()
    con.close()

init_db()

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/login',methods=['POST'])
def login_post():
    email=request.form['email']
    password=request.form['password']

    con=get_db()
    cur=con.cursor()

    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(email,password))
    user=cur.fetchone()

    if user:
        session['user']=user[1]
        return redirect('/dashboard')
    else:
        return "Invalid Login"

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']

        con=get_db()
        cur=con.cursor()
        cur.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,email,password))
        con.commit()

        return redirect('/')

    return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template("dashboard.html",name=session['user'])

@app.route('/start_detection')
def start_detection():
    # Run detection script separately so Flask is not blocked
    subprocess.Popen([sys.executable,"detection.py"])
    return redirect('/dashboard')

@app.route('/view_predictions')
def view_predictions():
    con=get_db()
    cur=con.cursor()

    cur.execute("SELECT * FROM detections ORDER BY id DESC")
    data=cur.fetchall()

    return render_template("predictions.html",data=data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__=="__main__":
    app.run(debug=True)
