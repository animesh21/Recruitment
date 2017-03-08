from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, Http404 , get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import auth
import json
from .excel_creator import SectionWiseMarks, total_marks
from django.core.exceptions import ObjectDoesNotExist
from .forms import RegistrationForm, QuestionForm, AdminLoginForm, ReviewForm, LoginForm , AddCategory, PythonRegisterForm
from .models import Student, Question, Category, Test, CorrectChoice, MarksOfStudent, ExamStarter, StudentInfo
from .ajax import markCalculate
from datetime import datetime
from django.views.generic import ListView

def check_question_data(request):
    obj = Question.objects.all()
    if len(obj) == 0:
        return HttpResponseRedirect(reverse('Exam_portal:notstarted'))

    return True

class ListQuestion(ListView):
    model = Question
    template_name = 'Exam_portal/Question.html'
    context_object_name = "question"

def custom404(request):
    return render(request, "Exam_portal/404page.html")


def not_started(request):
    return render(request, "Exam_portal/notstarted.html", {})


def timer(request):
    time = Test.objects.all()

    hours = time[0].time.hour
    minutes = time[0].time.minute
    seconds = time[0].time.second

    warn = time[0].warn_time

    data = {'time': [hours, minutes, seconds],
            'warn': warn}

    return HttpResponse(json.dumps(data), content_type='application/json')


def end(request):
    test_obj = Question.objects.all();

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return redirect(reverse("Exam_portal:notstarted"))
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if not obj.flag:
        messages.success(request, " Opps, Looks like the exam is not started yet. Come back later")
        return redirect(reverse("Exam_portal:notstarted"))

    print(request.session.get('student_id'))
    if not request.session.get('student_id'):
        if request.session['python']:
            return redirect(reverse('Exam_portal:python'))
        messages.error(request, "First, Register for the examination here..")
        return redirect(reverse('Exam_portal:register'))
    markCalculate(request)


    #deleting all the created session while the user logged in

    del request.session['student_id']
    del request.session['post_data']
    # del request.session['end']
    del request.session['name']
    del request.session['started']

    #modifies the session variable 
    request.session.modified = True

    return render(request, 'Exam_portal/end.html', {})


def review(request):

    #Review for with the inheritate class of register form with different def clean_StudentNo method
    test_obj = Question.objects.all();

    if request.session['python']:
        return HttpResponseRedirect(reverse("Exam_portal:end"))

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return redirect(reverse("Exam_portal:notstarted"))
    if not request.session.get('student_id'):
        messages.error(request, "First Register for the examination here..")
        return redirect(reverse('Exam_portal:register'))

    form = ReviewForm(request.session.get('post_data') or None)
    print(request.session.get('post_data'))

    if request.method == "POST":
        psd = request.session['post_data'].get('Password')
        cnf_psd = request.session['post_data'].get('Cnf_Password')
        mutable = request.POST._mutable
        request.POST._mutable = True
        request.POST['StudentNo'] = request.session['student_id']
        request.POST['Password'] = psd
        request.POST['Cnf_Password'] = cnf_psd
        form = ReviewForm(request.POST or None)
        request.POST._mutable = mutable

        if form.is_valid():
            print("form is valid")
            print(request.POST)

            student = StudentInfo.objects.get(pk=request.session['student_id'])
            student.name = request.POST.get('Name')
            student.email = request.POST.get('Email')
            studentinfo = student.student_set
            studentinfo.skills = request.POST.get('Skills')
            studentinfo.designer = request.POST.get('Designer')
            studentinfo.contact = request.POST.get('Contact')
            studentinfo.branch = form.cleaned_data['Branch']
            if request.POST.get('Hosteler') == 'y':
                hosteler = True
            else:
                hosteler = False

            studentinfo.hosteler = hosteler
            # studentinfo.save()
            student.save()

            return HttpResponseRedirect(reverse("Exam_portal:end"))

    if not request.session['python']:
        request.session['end'] = True

    context = {
        "title": "Review Exam",
        "heading": "Review your registration details.",
        "form": form,
        "display": True,
    }
    return render(request, 'Exam_portal/register.html', context)


def exam_starter_switch(request):

    #with this exam can be started or not
    context = exam_starter()
    return render(request, "Exam_portal/admin_interface.html", context)


def exam_starter():
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        ExamStarter.objects.create(flag=False)
        obj = ExamStarter.objects.first()

    if obj.flag:
        context = {
            "button": "Exam is Stopped"
        }
        obj.flag = False
        obj.save()
    else:
        context = {
            "button": "Exam is Started"
        }
        obj.flag = True
        obj.save()

    return context


def show(request):

    #The main page of exam where the question shows up
    test_obj = Question.objects.all()

    if request.session.get('end'):
        return HttpResponseRedirect(reverse('Exam_portal:review'))

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return redirect(reverse("Exam_portal:notstarted"))
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if obj.flag:
        print("exam has started")

    else:
        messages.success(request, "Opps, Looks like the exam is not started yet. Come back later")
        return redirect(reverse("Exam_portal:notstarted"))

    if request.session.get('student_id') is None:
        messages.error(request, "First Register for the examination here..")
        return redirect(reverse('Exam_portal:register'))

    category1 = Category.objects.all().order_by('order')

    print (category1)
    if len(category1) == 0:
        messages.error(request, "Oops look like the exam is not created yet. Try after some time")
        return redirect(reverse('Exam_portal:register'))

    question = category1[0].question_set.all().order_by('id')
    choice = question[0].questionchoice_set.all().order_by('id')

    category_first_data = []
    question_key = []
    print(len(category1))

    time = Test.objects.all()

    if len(time) == 0:
        messages.error(request, "Oops Time of exam is not specified yet Try after some time")
        return redirect(reverse('Exam_portal:register'))

    for i in range(0, len(category1)):
        print(i)
        print(category1[i])

        qs = category1[i].question_set.all().order_by('id')
        try:
            data = (qs[0].id, category1[i].category, category1[i].id)
            category_first_data.append(data)
        except IndexError:
            print("skipping")
        for j in range(0, len(qs)):
            question_key.append(qs[j].id)

    choice_data = []

    for i in range(0, len(choice)):
        data = (choice[i].get_marked_choice(), choice[i].id)
        choice_data.append(data)

    query_set = {
        "question_no": "1",
        "question": question[0].get_marked_down(),
        "negative": question[0].negative,
        "choice_data": choice_data,
        "category": category_first_data
    }

    request.session['key_list'] = question_key
    request.session['current'] = question[0].id

    time = time[0]
    if len(str(time.time.minute)) == 1:
        time_string = '0' + str(time.time.minute)
    else:
        time_string = str(time.time.minute)

    if len(str(time.time.hour)) == 1:
        time_string = '0' + str(time.time.hour) + ':' + time_string
    else:
        time_string = str(time.time.hour) + ':' + time_string

    context_variable = {
        "keys": question_key,
        "Number": range(1, len(question) + 1),
        "instance": query_set,
        "time": time_string,
        "warn": time.warn_time,
    }

    if request.session['python']:
        context_variable['title'] = "Python Quiz"

    return render(request, 'Exam_portal/ajax.html', context_variable)


def login(request):

    #view for login
    if request.session.get('started'):
        return HttpResponseRedirect(reverse("Exam_portal:ajaxshow"))

    test_obj = Question.objects.all()

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return redirect(reverse("Exam_portal:notstarted"))
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if obj.flag is True:
        print("exam is started")

    else:
        messages.success(request, "Opps, Looks like the exam is not started yet. Come back later")
        return redirect(reverse("Exam_portal:notstarted"))

    form = LoginForm()
    if request.session.get('student_id'):
        return redirect(reverse('Exam_portal:instruction'))

    if request.method == "POST":
        form = LoginForm(request.POST or None)

        if form.is_valid():
            user = form.cleaned_data.get('student_no')
            password = form.cleaned_data.get('password')

            try:
                student = Student.objects.get(student_no=user)
            except ObjectDoesNotExist:
                messages.success(request, "Invalid Student Number")
                return HttpResponseRedirect(reverse("Exam_portal:login"))

            if student.hosteler:
                hst = 'y'
            else:
                hst = 'n'

            review_data = {
                'Name': student.name,
                "Contact": student.contact,
                "Email": student.email,
                "Password": student.password,
                "Cnf_Password": student.cnf_password,
                "StudentNo": student.student_no,
                "Branch": student.branch,
                "Hosteler": hst,
                "Designer": student.designer,
                "Skills": student.skills,
            }
            print(review_data)

            if password == student.password:
                request.session['name'] = review_data.get('Name')
                request.session['student_id'] = user
                request.session['post_data'] = review_data
                return HttpResponseRedirect(reverse("Exam_portal:instruction"))
            else:
                messages.success(request, "Password Does not match")
                return HttpResponseRedirect(reverse("Exam_portal:login"))

    context = {
        'form': form,
    }

    return render(request, "Exam_portal/login.html", context)


def register(request):
    #Registration view
    test_obj = Question.objects.all()

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return redirect(reverse("Exam_portal:notstarted"))
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if obj.flag is True:
        print("exam is started")

    else:
        messages.success(request, "Opps, Looks like the exam is not started yet. Come back later")
        return redirect(reverse("Exam_portal:notstarted"))

    if request.session.get('student_id'):
        return redirect(reverse('Exam_portal:instruction'))

    form = RegistrationForm()


    if request.method == "POST":
        form = RegistrationForm(request.POST or None)

        if form.is_valid():
            password = form.cleaned_data.get("Password")
            cnf_password = form.cleaned_data.get("Cnf_Password")
            name = form.cleaned_data['Name']
            email = form.cleaned_data['Email']
            contact = form.cleaned_data['Contact']
            studentno = form.cleaned_data['StudentNo']
            branch = form.cleaned_data['Branch']
            if form.cleaned_data['Hosteler'] == 'y':
                hosteler = True
            else:
                hosteler = False
            skills = form.cleaned_data['Skills']
            designer = form.cleaned_data['Designer']

            data = StudentInfo.objects.create(name=name,student_no=studentno,email=email)
            info = data.student_set.create(branch=branch, contact=contact,
                                          skills=skills,
                                          hosteler=hosteler, designer=designer, password=password,
                                          cnf_password=cnf_password)
            if data:
                request.session['name'] = name
                request.session['student_id'] = data.student_no
                request.session['post_data'] = request.POST
                return HttpResponseRedirect(reverse('Exam_portal:instruction'))

    context = {
        'title': 'SI recruitment',
        "heading": "Registration",
        'form': form,
    }

    return render(request, 'Exam_portal/register.html', context)


def instruction(request):
    #next milestone for Instructiton won't be hard coded 

    if request.session.get('started'):
        return HttpResponseRedirect(reverse("Exam_portal:ajaxshow"))

    check_question_data(request)

    test_obj = Question.objects.all()

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return HttpResponseRedirect(reverse("Exam_portal:notstarted"))

    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if not obj.flag:
        messages.success(request, " Opps, Looks like the exam is not started yet. Come back later")
        return redirect(reverse("Exam_portal:notstarted"))

    if request.session.get('student_id') is None:
        messages.success(request, "First Register For the exam here")
        return redirect(reverse('Exam_portal:register'))

    request.session['started'] = True
    if not request.session['python']:
        return render(request, "Exam_portal/instruction.html", context={})
    else:
        return render(request, "Exam_portal/python_instruction.html", context={"title":"Python Quiz"})


#detect the refresh on show page
def refresh(request):
    s = Student.objects.filter(refresh_flag=0)

    for a in s:
        print (a)

    context = {
        "title": "Students who refreshed ",
        "students": s,
    }

    return render(request, "Exam_portal/refresh_check.html", context)

def add_category(request):
    if request.method == "POST":
        form = AddCategory(request.POST)
        if form.is_valid():
            form.save()


    return HttpResponseRedirect(reverse('Exam_portal:admin'))




#View for the admin panel
def admin(request):
    if not request.user.is_authenticated():
        messages.error(request, "Opps You're not an admin ")
        return HttpResponseRedirect(reverse("Exam_portal:admin_auth"))

    category = Category.objects.all().order_by('id')
    if request.method == "POST":
        form = QuestionForm(request.POST or None)
        category_form = AddCategory()

        if form.is_valid():
            print(request.POST)

            if create_question(request.POST):
                messages.success(request, "Question have been Added into the data base")
            return HttpResponseRedirect(reverse("Exam_portal:admin"))

    else:
        form = QuestionForm()
        category_form = AddCategory()

    if category is None:
        category = "No category yet"
        category_flag = False
    else:
        category_flag = True

    query_set = {
        "category_flag": category_flag,
        'c_form':category_form,
        "category": category,
        "form": form,
        'display_not': True,
    }

    return render(request, "Exam_portal/Question.html", query_set)

#View for the admin panel
def question_edit(request,pk):

    question = get_object_or_404(Question,id=pk)
    choices = question.questionchoice_set.all()
    correctchoice = question.correctchoice_set.all()

    correct = correctchoice[0].correct_choice.choice
#     print(correct)
    choice = []
    for c in choices:
        choice.append(c.choice)

    question_data = {
        'category':question.type.category,
        'question':question.question_text,
        'marks':question.marks,
        'negative':question.negative,
        'negative_marks':question.negative_marks,
        'choice1':choice[0],
        'choice2':choice[1],
        'choice3':choice[2],
        'choice4':choice[3],
        'correct_choice':choice.index(correct) + 1,
    }

    print(question_data.get('correct_choice'))

    form = QuestionForm(question_data)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            if edit_again(pk=pk,data = form.cleaned_data):
                print("updated")

    context_varaible = {
        'form':form,
        'question_id':pk,
        'category_show':False,
    }



    return  render(request,"Exam_portal/Question.html",context_varaible)

def question_list(request):
    try:
        question = Question.objects.all().order_by('type')
    except Question.DoesNotExist:
        pass

    query_set = {
        'question':question,
    }

    return render(request,"Exam_portal/QuestionList.html",query_set)


def create_question(question_data):
    try:
        if question_data['negative'] is False and question_data['negative_marks'] is None:
            negative_marks = 0
            negative = False
        elif question_data['negative'] is False and question_data['negative_marks'] is not None:
            negative_marks = 0
            negative = False
        else:
            negative_marks = question_data['negative_marks']
            negative = True
    except Exception,e:
        negative_marks = 0
        negative = False


    try:
        category = Category.objects.get(category=question_data['category'])
    except ObjectDoesNotExist:
        category = Category.objects.create(category=question_data['category'])

    question = category.question_set.create(
        question_text=question_data['question'],
        negative=negative,
        negative_marks=negative_marks,
        marks=question_data['marks'])

    choice = question.questionchoice_set
    # choice_data = question_data['choice']
    for i in range(1,5):
        choice.create(choice=question_data['choice'+str(i)])
        # print (choice_data[i])

    CorrectChoice.objects.create(question_id=question,
                                 correct_choice=choice.get(
                                     choice=question_data['choice'+question_data['correct_choice']]))
    return True


def edit_again(pk,data):

    try:
        if data['negative'] is False and data['negative_marks'] is None:
            negative_marks = 0
            negative = False
        elif data['negative'] is False and data['negative_marks'] is not None:
            negative_marks = 0
            negative = False
        else:
            negative_marks = data['negative_marks']
            negative = True
    except Exception,e:
        negative_marks = 0
        negative = False

    question = get_object_or_404(Question,pk=pk)
    question.type = Category.objects.get(category = data['category'])

    question.question_text = data['question']
    question.marks = data['marks']
    question.negative = negative
    question.negative_marks = negative_marks

    choices = question.questionchoice_set.all().order_by('id')

    count = 1
    for choice in choices:
        choice.choice = data['choice'+str(count)]
        count += 1
        choice.save()

    correct_query_set = question.correctchoice_set.all()[0]

    correct_query_set.correct_choice.choice = data['choice'+str(data['correct_choice'])]

    question.save()
    return True


#admin panel view
def edittime(request):
    if not request.user.is_authenticated():
        messages.error(request, "Opps You're not an admin ")
        return HttpResponseRedirect(reverse("Exam_portal:admin_auth"))

    try:
        time_test = Test.objects.all()[0]
    except Exception:
        time_test = None

    if request.method == "POST":

        time = int(request.POST.get("minutes"))
        warn = int(request.POST.get("warn"))
        if time != 0:
            hour = int(time / 60)
            min = time % 60
            time_str = "{}:{}:00".format(hour, min)
            # print(time_str)
            if time_test is None:
                Test.objects.create(name=request.POST.get('name'), time=time_str)
            else:
                time_test.time = time_str
                time_test.name = request.POST.get('name')
                time_test.warn_time = warn
                time_test.save()
            messages.success(request, "Time have been changed ! ")
            return HttpResponseRedirect(reverse('Exam_portal:edittime'))

    return render(request, "Exam_portal/time.html", {"time": time_test})

#admin panel view
def student_section(request):
    if not request.user.is_authenticated():
        messages.error(request, "Opps You're not an admin ")
        return HttpResponseRedirect(reverse("Exam_portal:admin_auth"))
    try:
        student_marks = MarksOfStudent.objects.all().order_by('-marks')
    except ObjectDoesNotExist:
        student_marks = "No student have given the exams yet !"

    return render(request, "Exam_portal/student_section.html", {"students": student_marks})

#admin authenctication
def admin_auth(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse("Exam_portal:adminchoice"))

    error = False
    if request.method == "POST":
        form = AdminLoginForm(request.POST or None)

        if form.is_valid():
            username = form.cleaned_data.get('username', '')
            password = form.cleaned_data.get('password', '')
            user = auth.authenticate(username=username, password=password)

            print(user)
            if user is not None:
                auth.login(request, user)
                return HttpResponseRedirect("/exam/adminchoice")
            else:
                messages.error(request, "Invalid user. Please enter a valid username")
                error = True
                return HttpResponseRedirect(reverse("Exam_portal:admin_auth"))
    else:
        error = False
        form = AdminLoginForm()

    context_variable = {
        "form": form,
        "error": error,
    }

    return render(request, "Exam_portal/admin_login.html", context_variable)

#admin
def logout_admin(request):
    print("logout")
    auth.logout(request)
    return HttpResponseRedirect(reverse("Exam_portal:admin_auth"))

#Admin
def adminchoice(request):
    print("adminchoice")
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if obj.flag:
        context = {
            "button": "Exam is Started",
        }
    else:
        context = {
            "button": "Exam is Stopped",
        }

    if not request.user.is_authenticated():
        messages.error(request, "Opps You're not an admin ")
        return HttpResponseRedirect(reverse("Exam_portal:admin_auth"))
    return render(request, 'Exam_portal/admin_interface.html', context)

def graph(request,id):
    # student = get_object_or_404(Student,student_no=id)
    marks = SectionWiseMarks(id)
    categories = Category.objects.all()
    category_marks = list()
    for category in categories:
        question = category.question_set.all()
        total_mark = 0
        for q in question:
            total_mark += q.marks
        category_marks.append((category.category ,total_mark))



    context_variable ={
        "marks":marks,
        "total":total_marks(),
        'category':category_marks,
    }
    return render(request,'Exam_portal/graph.html',context_variable)


def python_class(request):

    test_obj = Question.objects.all()

    if len(test_obj) == 0:
        messages.success(request, " Exam is not Created")
        return redirect(reverse("Exam_portal:notstarted"))
    try:
        obj = ExamStarter.objects.get(pk=1)
    except ObjectDoesNotExist:
        obj = ExamStarter.objects.create(flag=False)

    if obj.flag is True:
        print("exam is started")

    else:
        messages.success(request, "Opps, Looks like the exam is not started yet. Come back later")
        return redirect(reverse("Exam_portal:notstarted"))

    if request.session.get('student_id'):
        return redirect(reverse('Exam_portal:instruction'))



    if(len(Question.objects.all())==0):
        messages.warning(request,"Exam not created")
        return HttpResponseRedirect(reverse('Exam_portal:notstarted'))
    form = PythonRegisterForm(request.POST or None)
    context_variable = {
        'title':"Python Quiz",
        'form':form
    }

    request.session['python'] = True

    if request.method == "POST":
        form = PythonRegisterForm(request.POST or None)
        print(request.POST)
        print("ercercer")
        if form.is_valid():
            print('jbjktrtbtrbg')
            form.save()
            request.session['name'] = form.cleaned_data.get('name')
            request.session['student_id'] = form.cleaned_data.get('student_no')
            request.session['post_data'] = request.POST
            return HttpResponseRedirect(reverse('Exam_portal:instruction'))


    return render(request,"Exam_portal/python_register.html",context_variable)
