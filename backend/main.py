from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, hashlib, secrets, os
from datetime import datetime
DB = os.path.join(os.path.dirname(__file__), 'studymate.db')
app = FastAPI(title='StudyMate API', version='1.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = db()
    c.executescript('\n    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT,student_id TEXT);\n    CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY,name TEXT,student_id TEXT UNIQUE,section TEXT,semester INTEGER,attendance REAL,risk REAL,health REAL,class_rank INTEGER,email TEXT);\n    CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY,student_id INTEGER,name TEXT,score REAL);\n    CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY,student_id INTEGER,title TEXT,status TEXT,due TEXT);\n    CREATE TABLE IF NOT EXISTS interventions(id INTEGER PRIMARY KEY,student_id INTEGER,title TEXT,priority TEXT,status TEXT,description TEXT,progress REAL,created_at TEXT);\n    CREATE TABLE IF NOT EXISTS resources(id INTEGER PRIMARY KEY,title TEXT,subject TEXT,type TEXT,duration TEXT,url TEXT);\n    CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY,user_role TEXT,user_id INTEGER,title TEXT,message TEXT,level TEXT,is_read INTEGER DEFAULT 0);\n    CREATE TABLE IF NOT EXISTS followups(id INTEGER PRIMARY KEY,student_id INTEGER,title TEXT,due TEXT,status TEXT);\n    ')
    if c.execute('SELECT COUNT(*) n FROM users').fetchone()['n'] == 0:
        hp = lambda x: hashlib.sha256(x.encode()).hexdigest()
        c.executemany('INSERT INTO users(name,email,password,role,student_id) VALUES(?,?,?,?,?)', [('Prof. Arjun Sharma', 'faculty@studymate.demo', hp('Demo123!'), 'faculty', None), ('Rahul Kumar', 'student@studymate.demo', hp('Demo123!'), 'student', 'BCA-2A'), ('Admin', 'admin@studymate.demo', hp('Demo123!'), 'admin', None)])
        data = [('Rahul Kumar', 'BCA-2A', 'A', 2, 72, 78, 64, 28), ('Anjali Singh', 'BCA-2B', 'B', 2, 58, 82, 59, 12), ('Mohit Patel', 'BCA-2A', 'A', 2, 69, 78, 63, 19), ('Neha Gupta', 'BCA-2C', 'C', 2, 64, 76, 61, 22), ('Vivek Kumar', 'BCA-2B', 'B', 2, 61, 74, 60, 25), ('Priya Nair', 'BCA-2A', 'A', 2, 88, 31, 86, 4), ('Karan Mehta', 'BCA-2C', 'C', 2, 81, 45, 76, 7), ('Sneha Rao', 'BCA-2B', 'B', 2, 93, 22, 91, 2)]
        c.executemany('INSERT INTO students(name,student_id,section,semester,attendance,risk,health,class_rank) VALUES(?,?,?,?,?,?,?,?)', data)
        names = ['Java Programming', 'Operating Systems', 'Data Structures', 'English', 'Constitutional Values']
        for sid in range(1, 9):
            scores = [42, 48, 65, 78, 85] if sid == 1 else [55 + sid * 3 % 35, 60 + sid * 5 % 30, 68 + sid * 4 % 25, 76, 82]
            c.executemany('INSERT INTO subjects(student_id,name,score) VALUES(?,?,?)', [(sid, n, s) for n, s in zip(names, scores)])
        c.executemany('INSERT INTO assignments(student_id,title,status,due) VALUES(?,?,?,?)', [(1, 'Java Lab 4', 'Pending', 'This week'), (1, 'OS Assignment — Scheduling', 'Pending', 'This week'), (1, 'DSA Worksheet 3', 'Pending', 'This week'), (1, 'English Reflection', 'Completed', 'Next week')])
        c.executemany('INSERT INTO resources(title,subject,type,duration,url) VALUES(?,?,?,?,?)', [('Java OOPs — Complete Revision', 'Java', 'Video', '32 min', '#'), ('Operating Systems — Process Scheduling', 'Operating Systems', 'Video', '39 min', '#'), ('Data Structures — Practice Set', 'Data Structures', 'Worksheet', '20 questions', '#'), ('Java Exception Handling', 'Java', 'Video', '44 min', '#')])
        c.executemany('INSERT INTO notifications(user_role,user_id,title,message,level) VALUES(?,?,?,?,?)', [('faculty', 1, 'High-risk student detected', 'Rahul Kumar risk increased to 78%.', 'high'), ('faculty', 1, 'Attendance warning', 'Neha Gupta attendance is below 65%.', 'medium'), ('student', 2, 'Your plan is ready', 'Your personalised 7-day intervention plan is available.', 'info')])
        c.commit()
    c.close()
init()

class Login(BaseModel):
    email: str
    password: str

class StudentIn(BaseModel):
    name: str
    student_id: str
    section: str = 'A'
    semester: int = 2
    attendance: float = 75

class PlanIn(BaseModel):
    student_id: int
    title: str
    priority: str = 'Medium'
    description: str = ''
    progress: float = 0

class AssignmentIn(BaseModel):
    student_id: int
    title: str
    due: str

class ResourceIn(BaseModel):
    title: str
    subject: str
    type: str
    duration: str = ''
    url: str = '#'

class FollowupIn(BaseModel):
    student_id: int
    title: str
    due: str

class SimIn(BaseModel):
    attendance: float = 72
    subject_score: float = 42
    trend: float = 55
    pending: int = 1

@app.get('/api/health')
def health():
    return {'ok': True}

@app.post('/api/auth/login')
def login(x: Login):
    c = db()
    row = c.execute('SELECT * FROM users WHERE email=? AND password=?', (x.email, hashlib.sha256(x.password.encode()).hexdigest())).fetchone()
    c.close()
    if not row:
        raise HTTPException(401, 'Invalid email or password')
    return {'token': secrets.token_urlsafe(24), 'user': {'id': row['id'], 'name': row['name'], 'role': row['role'], 'student_id': row['student_id']}}

@app.get('/api/dashboard')
def dashboard():
    c = db()
    total = c.execute('SELECT COUNT(*) n FROM students').fetchone()['n']
    high = c.execute('SELECT COUNT(*) n FROM students WHERE risk>=70').fetchone()['n']
    med = c.execute('SELECT COUNT(*) n FROM students WHERE risk>=40 AND risk<70').fetchone()['n']
    avg = c.execute('SELECT ROUND(AVG(risk),1) n FROM students').fetchone()['n']
    c.close()
    return {'totalStudents': total, 'highRisk': high, 'mediumRisk': med, 'lowRisk': total - high - med, 'avgRisk': avg}

@app.get('/api/students')
def students():
    c = db()
    rows = [dict(x) for x in c.execute('SELECT * FROM students ORDER BY risk DESC')]
    c.close()
    return rows

@app.post('/api/students')
def create_student(x: StudentIn):
    c = db()
    try:
        risk = max(10, min(95, round(120 - x.attendance)))
        cur = c.execute('INSERT INTO students(name,student_id,section,semester,attendance,risk,health,class_rank) VALUES(?,?,?,?,?,?,?,?)', (x.name, x.student_id, x.section, x.semester, x.attendance, risk, 100 - risk, 999))
        c.commit()
        row = dict(c.execute('SELECT * FROM students WHERE id=?', (cur.lastrowid,)).fetchone())
        return row
    except sqlite3.IntegrityError:
        raise HTTPException(400, 'Student ID already exists')
    finally:
        c.close()

@app.get('/api/students/{sid}')
def student(sid: int):
    c = db()
    s = c.execute('SELECT * FROM students WHERE id=?', (sid,)).fetchone()
    if not s:
        c.close()
        raise HTTPException(404, 'Student not found')
    d = dict(s)
    d['subjects'] = [dict(x) for x in c.execute('SELECT name,score FROM subjects WHERE student_id=?', (sid,))]
    d['assignments'] = [dict(x) for x in c.execute('SELECT * FROM assignments WHERE student_id=?', (sid,))]
    c.close()
    return d

@app.get('/api/plans')
def plans():
    c = db()
    x = [dict(r) for r in c.execute('SELECT * FROM interventions ORDER BY id DESC')]
    c.close()
    return x

@app.post('/api/plans')
def create_plan(x: PlanIn):
    c = db()
    cur = c.execute('INSERT INTO interventions(student_id,title,priority,status,description,progress,created_at) VALUES(?,?,?,?,?,?,?)', (x.student_id, x.title, x.priority, 'In Progress', x.description, x.progress, datetime.now().isoformat()))
    c.commit()
    r = dict(c.execute('SELECT * FROM interventions WHERE id=?', (cur.lastrowid,)).fetchone())
    c.close()
    return r

@app.get('/api/assignments')
def assignments():
    c = db()
    x = [dict(r) for r in c.execute('SELECT * FROM assignments ORDER BY id DESC')]
    c.close()
    return x

@app.post('/api/assignments')
def create_assignment(x: AssignmentIn):
    c = db()
    cur = c.execute('INSERT INTO assignments(student_id,title,status,due) VALUES(?,?,?,?)', (x.student_id, x.title, 'Pending', x.due))
    c.commit()
    r = dict(c.execute('SELECT * FROM assignments WHERE id=?', (cur.lastrowid,)).fetchone())
    c.close()
    return r

@app.put('/api/assignments/{aid}')
def complete_assignment(aid: int):
    c = db()
    c.execute("UPDATE assignments SET status='Completed' WHERE id=?", (aid,))
    c.commit()
    r = c.execute('SELECT * FROM assignments WHERE id=?', (aid,)).fetchone()
    c.close()
    return dict(r)

@app.get('/api/resources')
def resources():
    c = db()
    x = [dict(r) for r in c.execute('SELECT * FROM resources ORDER BY id DESC')]
    c.close()
    return x

@app.post('/api/resources')
def create_resource(x: ResourceIn):
    c = db()
    cur = c.execute('INSERT INTO resources(title,subject,type,duration,url) VALUES(?,?,?,?,?)', (x.title, x.subject, x.type, x.duration, x.url))
    c.commit()
    r = dict(c.execute('SELECT * FROM resources WHERE id=?', (cur.lastrowid,)).fetchone())
    c.close()
    return r

@app.get('/api/notifications')
def notifications():
    c = db()
    x = [dict(r) for r in c.execute('SELECT * FROM notifications ORDER BY id DESC')]
    c.close()
    return x

@app.post('/api/notifications/read-all')
def read_all():
    c = db()
    c.execute('UPDATE notifications SET is_read=1')
    c.commit()
    c.close()
    return {'ok': True}

@app.get('/api/followups')
def followups():
    c = db()
    x = [dict(r) for r in c.execute('SELECT * FROM followups ORDER BY id DESC')]
    c.close()
    return x

@app.post('/api/followups')
def create_followup(x: FollowupIn):
    c = db()
    cur = c.execute("INSERT INTO followups(student_id,title,due,status) VALUES(?,?,?,'Pending')", (x.student_id, x.title, x.due))
    c.commit()
    r = dict(c.execute('SELECT * FROM followups WHERE id=?', (cur.lastrowid,)).fetchone())
    c.close()
    return r

@app.put('/api/followups/{fid}')
def complete_followup(fid: int):
    c = db()
    c.execute("UPDATE followups SET status='Completed' WHERE id=?", (fid,))
    c.commit()
    r = c.execute('SELECT * FROM followups WHERE id=?', (fid,)).fetchone()
    c.close()
    return dict(r)

@app.post('/api/simulate')
def simulate(x: SimIn):
    risk = max(5, min(95, round(120 - x.attendance * 0.45 - x.subject_score * 0.35 - x.trend * 0.12 + x.pending * 3)))
    return {'risk': risk, 'band': 'High' if risk >= 70 else 'Medium' if risk >= 40 else 'Low'}

@app.post('/api/reports/generate')
def report():
    c = db()
    total = c.execute('SELECT COUNT(*) n FROM students').fetchone()['n']
    high = c.execute('SELECT COUNT(*) n FROM students WHERE risk>=70').fetchone()['n']
    med = c.execute('SELECT COUNT(*) n FROM students WHERE risk>=40 AND risk<70').fetchone()['n']
    c.close()
    return {'generatedAt': datetime.now().isoformat(), 'total': total, 'high': high, 'medium': med, 'low': total - high - med}
