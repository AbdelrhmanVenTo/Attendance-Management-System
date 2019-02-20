import os
from flask import *
from datetime import datetime
import urllib
import base64
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import sqla
#import generatingqrcode
#import imageprocessing


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.secret_key = 'super secret key'
db = SQLAlchemy(app)
admin = Admin(app, name='AMS')

# Create M2M table
course_student_table = db.Table('course_student', 
                           db.Column('cid', db.String(30), db.ForeignKey('course.cid')),
                           db.Column('sid', db.Integer, db.ForeignKey('student.sid'))
                           )

report_student_table = db.Table('report_student', 
                           db.Column('report_id', db.String(30), db.ForeignKey('report.id')),
                           db.Column('sid', db.Integer, db.ForeignKey('student.sid'))
                           )

class Course(db.Model):
    cid = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(30))
    students = db.relationship('Student', secondary=course_student_table, backref=db.backref('courses', lazy='dynamic'))
    pid = db.Column(db.Integer(), db.ForeignKey('professor.pid'))
    professor = db.relationship('Professor', backref='course')

    def __repr__(self):
        return self.name

class Report(db.Model):
    id = db.Column(db.String(30), primary_key=True)
    date = db.Column(db.String(30))
    cid = db.Column(db.String(30), db.ForeignKey('course.cid'))
    course = db.relationship('Course', backref='report')
    pid = db.Column(db.Integer(), db.ForeignKey('professor.pid'))
    professor = db.relationship('Professor', backref='report')
    students = db.relationship('Student', secondary=report_student_table, backref=db.backref('reports', lazy='dynamic'))
    
    def __init__(self, id, date, course, students, professor):
        self.id = id
        self.date = date
        self.course = course
        self.students = students
        self.professor = professor

    def __repr__(self):
        return self.date
	
class Professor(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(30), unique=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))

    def __repr__(self):
        return self.name

class Student(db.Model):
    sid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))

    def __repr__(self):
        return self.name

class ReportAdmin(sqla.ModelView):
    column_display_pk = True
    can_create = False
    can_edit = True
    # can_delete = False
    # can_view_details = True
    form_columns = ['id', 'date', 'course', 'professor', 'students']

class CourseAdmin(sqla.ModelView):
    column_display_pk = True
    form_columns = ['cid', 'name', 'students', 'professor']

class ProfessorAmin(sqla.ModelView):
    column_display_pk = True
    form_columns = ['pid', 'name', 'email', 'username', 'password']
    
class StudentAdmin(sqla.ModelView):
    #to display primary key 3shan hwa fl framework de msh bydisplay el pk
    column_display_pk = True
    form_columns = ['sid', 'name']


#init el view
admin.add_view(CourseAdmin(Course, db.session))
admin.add_view(ProfessorAmin(Professor, db.session))
admin.add_view(StudentAdmin(Student, db.session))
admin.add_view(ReportAdmin(Report, db.session))

def professor_json(professor):
    courses = Course.query.filter_by(professor = professor)
    course_array = []
    for course in courses:
        course_array.append({"cid": course.cid, "name": course.name})
    return jsonify({'name': professor.name, 'pid': professor.pid, 'courses': course_array})

@app.route('/')
@app.route('/index')
def index():
    return redirect("/admin", code=302)

@app.route('/API/auth', methods=['GET'])
def authentication():
    password = request.args.get('password')
    username = request.args.get('username')
    if password and username:
        if type(password) is str and type(username) is str:
            prof = Professor.query.filter_by(username = username).first()
            if prof is None:
                return jsonify({'status':'failed', 'message':'Wrong Username'})
            if prof.password != password:
                return jsonify({'status':'failed', 'message':'Wrong Password'})
            return professor_json(prof)
        else:
            return error_type_mismatch()
    else:
        return error_empty()     
    
@app.route('/API/get_dates', methods=['GET'])
def get_dates():
    cid = request.args.get('cid')
    if  cid:
        if type(cid) is str:
            course = Course.query.get(cid)
            reports = Report.query.filter_by(course = course)
            dates = []
            for report in reports:
                dates.append(report.date)
            return jsonify({'dates': dates})
        else: 
            return error_type_mismatch()
    else:
         return error_empty()
         
@app.route('/API/get_record', methods=['GET'])
def get_record():
    date = request.args.get('date')
    cid = request.args.get('cid')
    pid = request.args.get('pid')
    if  cid and  pid and date:
        pid = int(pid)
        if type(cid) is str and type(pid) is int and type(date) is str:
            course = Course.query.get(cid)
            report = Report.query.filter(and_(Report.date == date, Report.course == course)).first()
            students_array = []
            for student in report.students:
                students_array.append({'name': student.name, 'sid': student.sid})
            courses = Course.query.filter_by(professor = report.professor)
            course_array = []
            for course in courses:
                course_array.append({"cid": course.cid, "name": course.name})
            return jsonify({'professor': {'name': report.professor.name, 'pid': report.professor.pid, 'courses': course_array}, 'course': {'cid': report.course.cid, 'name': report.course.name},'date': report.date , 'students': students_array})
        else:
            return error_type_mismatch()
    else:
        return error_empty()
        
@app.route('/API/post_record', methods=['POST'])
def post_record():
    data = request.json
    pid = data["pid"]
    lng = data["lng"]
    cid = data["cid"]
    date = data["date"]
    lat = data["lat"]
    time = data["time"]
    attendance = data["attendance"]
    if  cid and  pid and  date and  time and lat and lng:
        date = urllib.parse.unquote_plus(date)
        time = urllib.parse.unquote_plus(time)
        cid = urllib.parse.unquote_plus(cid)
        pid = int(pid)
        lat = float(lat)
        lng = float(lng)
        attendance = list(attendance)
        if type(cid) is str and type(time) is str and type(pid) is int and type(date) is str and type(lat) is float and type(lng) is float:
            course = Course.query.get(cid)
            professor = Professor.query.get(pid)
            reports_count = Report.query.count()
            students = []
            for sid in attendance:
                students.append(Student.query.get(sid))
            reports_count = reports_count + 1
            report = Report('%d'%reports_count, date, course, students, professor)
            db.session.add(report)
            db.session.commit()
            return jsonify({'status':'success', 'message':'request is received successfully'}), 200
        else:
            return error_type_mismatch()
    else:
        return error_empty() 

@app.route('/API/post_edit_record', methods=['PUT', 'DELETE'])
def post_edit_record():
    prams = request.json
    date = prams['date']
    cid = prams['cid']
    sid = prams['sid']
    if  cid and date and sid:
        date = urllib.parse.unquote_plus(date)
        cid = urllib.parse.unquote_plus(cid)
        sid = int(sid)
        if type(cid) is str and type(date) is str and type(sid) is int:
            course = Course.query.get(cid)
            report = Report.query.filter(and_(Report.date == date, Report.course == course)).first()

            student = Student.query.get(sid)
            if student is None:
                return jsonify({'status':'failed', 'message':'Student Not Found'})

            if request.method == 'PUT':
                report.students.append(student)
                db.session.commit()
                return jsonify({'status':'success', 'message':'request is received successfully'}), 200
            else:
                report.students.remove(student)
                db.session.commit()
                return jsonify({'status':'success', 'message':'request is received successfully'}), 200
        else:
            return error_type_mismatch()
    else:
        return error_empty()
        
def error_empty():
    return jsonify({'status':'failed', 'message':'Requested parameters are empty'})

def error_type_mismatch():
     return jsonify({'status':'failed', 'message':'Requested parameters\' type mismatch'})
    
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'status':'failed', 'message':'bad request'}), 400

@app.errorhandler(401)
def unauthorized(error):              
    return jsonify({'status':'failed', 'message':'authentication is required and has failed or has not yet been provided'}), 401

@app.errorhandler(403)
def forbidden(error):              
    return jsonify({'status':'failed', 'message':'The request was valid, but the server is refusing action'}), 403

@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'status':'failed', 'message':'This URL does not exist'}), 404

@app.errorhandler(405)
def mathod_not_allowed(error):              
    return jsonify({'status':'failed', 'message':'The method is not allowed for the requested URL'}), 405

@app.errorhandler(406)
def not_acceptable(error):              
    return jsonify({'status':'failed', 'message':'The requested resource is capable of generating only content not acceptable'}), 406

@app.errorhandler(408)
def request_timeout(error):              
    return jsonify({'status':'failed', 'message':'The server timed out waiting for the request'}), 408

@app.errorhandler(409)
def conflict(error):              
    return jsonify({'status':'failed', 'message':'Indicates that the request could not be processed because of conflict in the request'}), 409

@app.errorhandler(410)
def gone(error):              
    return jsonify({'status':'failed', 'message':'Indicates that the resource requested is no longer available and will not be available again'}), 410

@app.errorhandler(414)
def urltolong(error):              
    return jsonify({'status':'failed', 'message':'The URI provided was too long for the server to process'}), 414



if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True )
