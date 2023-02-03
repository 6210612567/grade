from django.shortcuts import render
import json
import pandas as pd
from .models import CustomGradeField, Grade, GradeTable
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
from rest_framework import status

# def handle_uploaded_file(f):
#     with open('path/to/save/file', 'wb+') as destination:
#         for chunk in f.chunks():
#             destination.write(chunk)
from django.conf import settings
from django.db import connection


HOST = "https://restapi.engr.tu.ac.th"

# Create your views here.


def index(request):
    try:
        if request.session['user_id']:
            return HttpResponseRedirect(reverse("grade:grade"))
    except:
        return render(request, "grade/login.html")


# Login page
def login_view(request):
    try:
        if request.session['user_id']:
            return HttpResponseRedirect(reverse("grade:grade"))
    except:
        if request.method == "POST":
            username = request.POST["username"]
            password = request.POST["password"]
            data = {
                'username': username,
                'password': password
            }
            response = requests.post(
                HOST+'/api/v1/authentication/', data=data)
            if response.status_code == status.HTTP_200_OK:
                request.session['user_id'] = username
                # print(request.session['user_id'])
                # print("render policy page")
                request.session['login_status'] = username
                request.session.modified = True
                # return render(request, "web/policy.html")
                return HttpResponseRedirect(reverse("grade:grade"))
            else:
                return render(request, "grade/login.html")
        return render(request, "grade/login.html")


# Load grade data
def get_grade_data(choice, request):
    output = []
    grade_table_list = GradeTable.objects.filter(
        user=request.session['user_id'])
    for grade_table in grade_table_list:
        header_list = []
        table_name = grade_table.subject_id+'_'+grade_table.section+'_'+grade_table.year + \
            '_'+grade_table.semestre+'_'+grade_table.course + \
            '_'+request.session['user_id']
        # get cloumn name
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_NAME`=\'"+table_name+"\';")
            products = cursor.fetchall()
            # Column name to list
            for column_name in products:
                header_list.append(column_name[0])
            # print(header_list)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name};")
            products = cursor.fetchall()
            output.append({'grade_list': products, 'header_list': header_list,
                          'table_name': table_name, 'grade_table_id': grade_table.id})
    return output


# Manage_grade Page
def manage_grade_view(request):
    try:
        request.session['user_id']
        # Upload Excel file and create db to store data
        if request.method == 'POST':
            try:
                # Read exel file to json
                subject_id = request.POST["sid"]  # รหัสวิชา
                subject_name = request.POST["sname"]  # ชื่อวิชา
                section = request.POST["section"]  # SECTION
                year = request.POST["year"]  # ปีการศึกษา
                semestre = request.POST["semestre"]  # ภาคการศึกษา
                department = request.POST["department"]  # ภาควิชา
                course = request.POST["course"]  # โครงการ / หลักสูตร
                desc = request.POST["desc"]  # หมายเหตุ
                df = pd.read_excel(request.FILES['file'])
                data = df.to_json(orient='records')
                student_list = json.loads(data)

                # Set table name
                grade_table = subject_id+'_'+section+'_'+year+'_' + \
                    semestre+'_'+course+'_'+request.session['user_id']
                if len(GradeTable.objects.filter(grade_table=grade_table)) != 0:
                    return render(request, "grade/manage_grade.html", {'message': 'Table is already exist,Please delete old table'})
                # Create GradeTable Object that store table's data
                grade = GradeTable.objects.create(subject_id=subject_id, subject_name=subject_name, section=section, year=year, semestre=semestre,
                                                  department=department, course=course, desc=desc, grade_table=grade_table, user=request.session['user_id'])
                # Get header for create table field
                create_table_sql = f"CREATE TABLE {grade_table} ("
                header = []
                for key in student_list[0]:
                    if create_table_sql[-1] != "(":
                        create_table_sql += ","
                    create_table_sql += f"{key} varchar(255)"
                    header.append(key)
                # Create table
                create_table_sql += ');'
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(create_table_sql)
                except:
                    return render(request, "grade/manage_grade.html", {'message': 'table is already exist,Please delete old table'})

                # Upload exel to table
                for student in student_list:
                    # Get header for create table field
                    insert_data_sql = f"INSERT INTO {grade_table} VALUES ("
                    for key in header:
                        if insert_data_sql[-1] != "(":
                            insert_data_sql += ","
                        insert_data_sql += "\'"+str(student[key])+"\'"
                    insert_data_sql += ');'
                    # Insert each row of student data
                    with connection.cursor() as cursor:
                        cursor.execute(insert_data_sql)
                return HttpResponseRedirect(reverse("grade:courese_list"))
            # If upload file error
            except Exception as e:
                output = get_grade_data(0, request)
                return render(request, "grade/manage_grade.html", {'output': output, 'message': f'Exel File Error : {e}'})
        # Load data to manage_grade page
        else:
            output = get_grade_data(0, request)
            return render(request, "grade/manage_grade.html", {'output': output, 'message': 'Loaded'})
    # If cause Exception
    except Exception as e:
        return render(request, "grade/manage_grade.html", {'message': f'Error : {e}'})


def delete_table_view(request, grade_table_id):
    try:
        grade_table = GradeTable.objects.get(
            id=grade_table_id, user=request.session['user_id'])
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE {grade_table.grade_table}")
        grade_table.delete()
        output = get_grade_data(0, request)
        return render(request, "grade/manage_grade.html", {'output': output, 'message': 'Delete Success'})
    except Exception as e:
        output = get_grade_data(0, request)
        return render(request, "grade/manage_grade.html", {'output': output, 'message': f'Delete Error : {e}'})


# Grade Page
def grade_view(request):
    try:
        request.session['user_id']
        # subject = 'cn203'
        grade_table_list = GradeTable.objects.filter(status=True)
        return render(request, "grade/grade.html", {'grade_table_list': grade_table_list})
    except:
        return HttpResponseRedirect(reverse("grade:login"))


def courese_list(request):
    grade_table_list = GradeTable.objects.filter(
        user=request.session['user_id'])
    return render(request, "grade/courese_list.html", {'grade_table_list': grade_table_list})


def logout_view(request):
    del request.session['user_id']
    return HttpResponseRedirect(reverse("grade:login"))


def show_grade_view(request, grade_table_id):
    grade_table = ""
    try:
        grade_table_data = GradeTable.objects.get(id=grade_table_id)
        header_list = []
        # get cloumn name
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_NAME`=\'"+grade_table_data.grade_table+"\';")
            products = cursor.fetchall()
            # Column name to list
            for column_name in products:
                header_list.append(column_name[0])
            # print(header_list)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM {grade_table_data.grade_table} WHERE `std_id`=\'"+request.session['user_id']+"\';")
            grade_table = cursor.fetchall()

    except:
        pass
    if grade_table == ():
        grade_table = "None"
        output = {'grade_list': grade_table}
    else:
        output = {'grade_list': grade_table, 'header_list': header_list,
                  'table_name': grade_table_data.grade_table, 'grade_table_id': grade_table_data.id}
    return render(request, "grade/show_grade.html", {'grade_table': output})


def change_status_view(request, grade_table_id):
    try:
        grade_table = GradeTable.objects.get(
            id=grade_table_id, user=request.session['user_id'])
        grade_table.status = grade_table.status == False
        grade_table.save()
        return HttpResponseRedirect(reverse("grade:courese_list"))
    except Exception as e:
        return HttpResponseRedirect(reverse("grade:courese_list"))


def course_info(request):
    return render(request, "grade/course_info.html")
