from django.urls import path, include
from . import views

# from . import views_fronts
app_name = 'grade'


urlpatterns = [
    path("", views.index, name="index"),
    path("delete_table/<str:subject>", views.delete_table_view, name="delete_table"),
    path("login/", views.login_view, name="login"),
    path("manage_grade/", views.manage_grade_view, name="manage_grade"),
    path("grade/", views.grade_view, name="grade"),

     
]