from flask import Flask,request,jsonify
from flask_cors import cross_origin
from flask_mysqldb import MySQL
import json
import random
import histogram
from datetime import datetime as dt

# from flask_httpauth import HTTPBasicAuth
app = Flask(__name__)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'sarptalha'
# app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_DB'] = 'itusis'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route("/create_tables")
@cross_origin()
def create_tables():
    cur = mysql.connection.cursor()
    
    cur.execute('''CREATE TABLE IF NOT EXISTS people (
    person_id INT AUTO_INCREMENT PRIMARY KEY,
    pname VARCHAR(255) NOT NULL,
    psurname VARCHAR(255) NOT NULL,
    mail VARCHAR(255) ,
    major VARCHAR(3) ,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );''')    
    
    cur.execute('''CREATE TABLE IF NOT EXISTS topics (
    class_name VARCHAR(6) PRIMARY KEY,
    class_desc VARCHAR(255),
    credits INT NOT NULL,
    major VARCHAR(3) ,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );''')    
    
    cur.execute('''CREATE TABLE IF NOT EXISTS classes (
    crn INT AUTO_INCREMENT PRIMARY KEY,
    c_teacher_id INT NOT NULL,
    c_class_name VARCHAR(6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY(c_teacher_id)
    REFERENCES people (person_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    FOREIGN KEY(c_class_name)
    REFERENCES topics (class_name)
    ON DELETE CASCADE
    ON UPDATE CASCADE
    );''')   

    cur.execute('''CREATE TABLE IF NOT EXISTS enrollment (
    student_id INT NOT NULL,
    crn INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (student_id,crn),
    FOREIGN KEY(student_id)
    REFERENCES people (person_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    FOREIGN KEY(crn)
    REFERENCES classes (crn)
    ON DELETE CASCADE
    ON UPDATE CASCADE
    );''')   

    cur.execute('''CREATE TABLE IF NOT EXISTS grades (
    student_id INT NOT NULL,
    crn INT NOT NULL,
    grade VARCHAR(2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (student_id,crn),
    FOREIGN KEY(student_id)
    REFERENCES people (person_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    FOREIGN KEY(crn)
    REFERENCES classes (crn)
    ON DELETE CASCADE
    ON UPDATE CASCADE
    );''')       
    
    mysql.connection.commit()  
       
    cur.execute(
    '''
    create or replace view teachers AS
    SELECT distinct people.person_id, people.pname, people.psurname, people.created_at
    FROM people,classes
    WHERE classes.c_teacher_id = people.person_id;
    ''')
    
    cur.execute(
     '''
    create or replace view students AS
    SELECT distinct people.person_id, people.pname, people.psurname, people.created_at
    FROM 
    people left outer join classes
    on
    classes.c_teacher_id = people.person_id
    where crn is null;
    '''
    )    
       
    cur.execute('''CREATE TABLE IF NOT EXISTS semesters (
    semester_year INT NOT NULL,
    semester_season varchar(10) NOT NULL,
    end_date TIMESTAMP,
    start_date TIMESTAMP,
    
    PRIMARY KEY (semester_year,semester_season));
    '''
    )           
    
    mysql.connection.commit()  
    return("success")


add_to_db_querries = {
    "user": '''
                INSERT INTO people (pname,psurname)
                VALUES (%s,%s); 
            ''' ,
    "topic": '''
                INSERT INTO topics (class_name,class_desc,credits)
                VALUES (%s,%s,%s); 
            ''' ,
    "class": '''
                INSERT INTO classes (c_class_name,c_teacher_id)
                VALUES (%s,%s); 
            ''' ,
    "enrollment": '''
                INSERT INTO enrollment (student_id , crn)
                VALUES (%s,%s); 
            ''' ,
    "grade": '''
                INSERT INTO grades (student_id , grade, crn)
                VALUES (%s,%s,%s); 
            ''' ,
    "semester": '''
                INSERT INTO semesters (semester_year , semester_season, end_date, start_date)
                VALUES (%s,%s,%s,%s); 
            ''' ,
}

delete_from_db_querries = {
    "user" : "DELETE FROM people WHERE person_id = %s",
    "topic" : "DELETE FROM topics WHERE class_name = %s",
    "class" : "DELETE FROM people WHERE crn = %s",
    "grades" : "DELETE FROM grades WHERE student_id = %s and crn = %s",
    "enrollment" : "DELETE FROM enrollment WHERE student_id = %s and crn = %s",
    }

@app.route('/add_<entry>',methods = ["POST"])
@cross_origin()
def add_to_db(entry):
    if request.method == "POST" and entry in add_to_db_querries:
        cur = mysql.connection.cursor()
        cur.execute(add_to_db_querries[entry],(tuple(request.json.values())))
        mysql.connection.commit()
        return "added "+entry

@app.route('/remove_<entry>/<id_num>',methods = ["DELETE"])
@cross_origin()
def remove_from_db(entry,id_num):
    if request.method == "DELETE" and entry in ["user","topic","class"]:
        cur = mysql.connection.cursor()
        cur.execute(delete_from_db_querries[entry],(id_num))
        mysql.connection.commit()
        return "removed "+str(id_num)

@app.route('/student_remove_<entry>/<id_num>/<crn>',methods = ["DELETE"])
@cross_origin()
def remove_from_db_two_args(entry,id_num,crn):
    if request.method == "DELETE" and entry in ["grades","enrollment"]:
        cur = mysql.connection.cursor()
        cur.execute(delete_from_db_querries[entry],(id_num,crn))
        mysql.connection.commit()
        return "removed "+str(id_num)

@app.route("/clear_all_tables")
@cross_origin()
def clear_all_tables():
    cur = mysql.connection.cursor()
    cur.execute( '''
            SET FOREIGN_KEY_CHECKS = 0;
            truncate people;
            truncate topics;
            truncate classes;
            truncate enrollment;
            truncate grades;
            SET FOREIGN_KEY_CHECKS = 1;
              ''')
    # mysql.connection.commit()
    return ("successfully cleared all the tables")

@app.route("/deneme")
@cross_origin()
def deneme():
    
    with open('./seeddata.json') as json_file:
        cur = mysql.connection.cursor()
        data = json.load(json_file)
        
        cur.execute(add_to_db_querries["semester"],(2021,"spring","2021-01-28 20:53:41","2021-07-28 20:53:41"))
        
        for i in data['people']:
            cur.execute('''  INSERT INTO people (pname,psurname) VALUES (%s,%s); ''',(i.split(" ")[0],i.split(" ")[1]))
        
        for i in data['topics']:
            cur.execute('''INSERT INTO topics (class_name,class_desc,credits) VALUES (%s,%s,%s); ''',(i,"Temporary description",random.randint(2,4)))
        
        for i in range(20):
            cur.execute(''' INSERT INTO classes (c_class_name,c_teacher_id) VALUES (%s,%s); ''',(data['topics'][i%15],i%9+1))

        crn_dict = dict()
        for i in range(9,50):
            num = random.randint(1,16)
            crn_dict[i] = [num,(num+1)%15+1,(num+2)%15+1,(num+3)%15+1]
            for j in crn_dict[i]:
                cur.execute('''INSERT INTO enrollment (student_id , crn)VALUES (%s,%s); ''',(i,j))
    
        for enrol in crn_dict:
            for crn_num in crn_dict[enrol]:
                cur.execute('''INSERT INTO grades (student_id , grade, crn) VALUES (%s,%s,%s);''',(enrol,list(grade_translation.keys())[random.randint(0,7)],crn_num))

        mysql.connection.commit()
        return ("success1")

grade_translation={"AA":4,"BA":3.5,"BB":3,"CB":2.5,"CC":2,"DC":1.5,"DD":1,"FF":0}
def get_avg_grade(grades, is_class=False):
    if not grades: return 0
    
    if is_class: 
        return sum([grade_translation[grade] for grade in [student["grade"] for student in grades]])/len(grades)
    
    quality_credits=0
    total_credits=0
    for entry in grades:
        quality_credits += grade_translation[entry["grade"]] * entry["credits"]
        total_credits += entry["credits"]
    return quality_credits/total_credits
    
    
@app.route('/ranking',methods = ["GET"])
@cross_origin()
def get_ranking():
    cur = mysql.connection.cursor()
    
    cur.execute("select * from students")
    
    people = cur.fetchall()
    GPA_LIST=[]
    for person in people:
        person_name = person["pname"] + " " + person["psurname"]
        person_gpa = get_student_info(person["person_id"])["GPA"]
        GPA_LIST.append((person_name,person_gpa))
        
    GPA_LIST.sort(key = lambda x: x[1],reverse=True)
    response = jsonify({i:GPA_LIST[i-1] for i in range(1,len(GPA_LIST)+1)})
    return response
    
@app.route('/student_info/<student_id>',methods = ["GET"])
@cross_origin()
def student_info(student_id):
    if request.method == "GET":
        response = jsonify(get_student_info(student_id))
        return response    
    
def get_student_info(student_id):
    cur = mysql.connection.cursor()   
    
    cur.execute(
    '''
    select classes.crn,c_class_name,topics.credits from classes 
    inner join enrollment on 
    classes.crn = enrollment.crn
    inner join topics on
    classes.c_class_name = topics.class_name
    inner join students on 
    students.person_id = enrollment.student_id
    inner join semesters on 
    (classes.created_at between end_date and start_date) and
    (current_timestamp() between end_date and start_date)
    where students.person_id = %s;
    ''',(student_id,))
    
    ongoing_classes = cur.fetchall()
    
    cur.execute(
    '''
    select classes.crn,c_class_name from classes 
    inner join enrollment on 
    classes.crn = enrollment.crn
    inner join topics on
    classes.c_class_name = topics.class_name
    inner join students on 
    students.person_id = enrollment.student_id
    where students.person_id = %s;
    ''',(student_id,))
    
    classes = cur.fetchall()
    
    cur.execute(
    '''
    select grades.crn,topics.class_name,grade,topics.credits from students
    inner join grades on 
    grades.student_id = students.person_id
    inner join enrollment on 
    grades.crn = enrollment.crn and students.person_id = enrollment.student_id
    inner join classes on 
    enrollment.crn = classes.crn
    inner join topics on 
    topics.class_name = classes.c_class_name
    where students.person_id = %s;
    ''',(student_id,))

    grades = cur.fetchall()
    
    cur.execute(
    '''
    select pname,psurname from students where person_id = %s
    ''',(student_id,))       
    
    info= cur.fetchone()
    
    return {"classes":classes,"ongoing_classes":ongoing_classes,"grades":grades,"GPA":get_avg_grade(grades),"personal information":info}
        
@app.route('/crn_info/<crn>',methods = ["GET"])
@cross_origin()
def crn_info(crn):
    if request.method == "GET":
        cur = mysql.connection.cursor()
        
        cur.execute(
        '''
        select pname as teacher_name,psurname as teacher_surname,person_id,c_class_name,class_desc,classes.crn from classes 
        inner join people on 
        classes.c_teacher_id = people.person_id
        inner join topics on
        classes.c_class_name = topics.class_name
        where classes.crn = %s;
        ''',(crn,))
        
        info = cur.fetchone()
        
        cur.execute(
        '''
        select student_id,grade from grades
        inner join people on 
        grades.student_id = people.person_id
        where grades.crn = %s;
        ''',(crn,))

        grades = cur.fetchall()
        
        cur.execute(
        '''
        select person_id,pname,psurname from classes 
        inner join enrollment on 
        classes.crn = enrollment.crn
        inner join topics on
        classes.c_class_name = topics.class_name
        inner join people on 
        people.person_id = enrollment.student_id
        where classes.crn = %s;
        ''',(crn,))

        students = cur.fetchall()
                
        response= jsonify({"info": info,"students":students,"grades": grades,"class_average":get_avg_grade(grades, is_class=True)})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
  
@app.route('/reset')
@cross_origin()
def reset_db():
    clear_all_tables()
    create_tables()
    deneme()
    return ("reseted database")
    
@app.route('/crn_histogram/<crn>',methods = ["GET"])
@cross_origin()
def crn_histogram(crn): 
    return histogram.get_crn_histogram(crn)

@app.route('/class_histogram/<class_name>',methods = ["GET"])
@cross_origin()
def class_histogram(class_name):
    return histogram.get_class_histogram(class_name)

@app.route('/teacher_histogram/<person_id>',methods = ["GET"]) 
@cross_origin()
def teacher_histogram(person_id): 
    return histogram.get_teacher_histogram(person_id)

@app.route('/teacher_class_histogram/<person_id>/<class_id>',methods = ["GET"])
@cross_origin()
def teacher_class_histogram(person_id,class_id):
    return histogram.get_teacher_class_histogram(person_id,class_id)

@app.route('/')
@cross_origin()
def index():
    cur = mysql.connection.cursor()

    cur.execute('''
        SELECT * FROM PEOPLE
    ''')

    results = cur.fetchall()
    resultarr=[]
    for i in results:
        resultarr.append(i['pname'] + ' ' + i['psurname'])
    print(resultarr)
    return str(resultarr)

if __name__ == '__main__':
    app.run(debug=True, port=1999)
