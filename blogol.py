from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

app= Flask(__name__)

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]= "kblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
app.secret_key="kblog"

mysql=MySQL(app)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Sayfayı görüntülemek için giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function


#Giriş Yapma
class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")

@app.route("/login", methods= ["GET","POST"])
def login():
    log_form=LoginForm(request.form)
    if request.method== "POST":
        username=log_form.username.data
        password_entered=log_form.password.data

        cursor=mysql.connection.cursor()
        sorgu="Select * from users where username=(%s)"
        result=cursor.execute(sorgu,(username,))
        
        if result>0:
            data=cursor.fetchone()
            real_password= data["password"]
            if sha256_crypt.verify(password_entered, real_password):

                flash(message="Hoşgeldiniz..",category="success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("first"))
            else:
                flash(message="Hatalı Parola",category="danger")
            return redirect(url_for("login"))

        elif result==0:
            flash(message="Böyle Bir Kullanıcı Yok",category="danger")
        return redirect(url_for("login"))

    else:
        return render_template("login.html",form=log_form)

#Kayıt Olma
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min=6 , max=25),validators.DataRequired(message="Lütfen İsminizi Girin.")])
    username=StringField("Kullanıcı Adı",validators=[validators.Length(min=6 , max=25),validators.DataRequired(message="Lütfen Kullanıcı Adı Girin.")])
    email=StringField("E-Mail",validators=[validators.Email(message="Lütfen geçerli bir mail adresi giriniz."),validators.DataRequired(message="Lütfen Mailinizi Girin")])
    password=PasswordField("Parola",validators=[validators.DataRequired(message="Lütfen Parola Belirleyiniz"), validators.EqualTo(fieldname="confirm", message="Parolalar uyuşmuyor.")])
    confirm=PasswordField("Parola Tekrar")
@app.route("/register",methods=["GET", "POST"])
def register():
    form=RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        cursor=mysql.connection.cursor()
        sorgu= "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash(message="Başarıyla Kayıt Oldunuz",category="success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

#To Do kısmı
@login_required
@app.route("/todo",methods=["GET","POST"])
def todo():

    return render_template("todo.html")
#Makale Ekleme
class Addarticle(Form):
    title=StringField("Makale Adı",validators=[validators.Length(min=5, max=40)])
    content=TextAreaField("Makaleniz")
@app.route("/addarticle", methods= ["GET", "POST"])
def addarticle():
    form=Addarticle(request.form)
    if request.method=="POST":
        title=form.title.data
        content=form.content.data
        cursor=mysql.connection.cursor()
        sorgu= "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()
        cursor.close()
        flash(message="Makaleniz başarıyla eklendi",category="success")
        return redirect(url_for("dashb"))
    else:
        return render_template("addarticle.html", form=form)

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles"
    sorgu=cursor.execute(sorgu)
    if sorgu>0:

        articles= cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")
    cursor.close()

#Makale Silme 
@app.route("/delete/<string:id>")
@login_required
def delet(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where author=%s and id=%s "
    result= cursor.execute(sorgu, (session["username"],id))
    if result>0:
        sorgu2="Delete From articles where id=(%s)"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashb"))
    else:
        flash("Bu işleme izin yok.","danger")
        return redirect(url_for("first"))


#Anasayfa
@app.route("/")
def first(): 
    return render_template("index.html" )

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard")
@login_required
def dashb():
    cursor=mysql.connect.cursor()
    sorgu="Select * From articles where author=(%s)"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        data=cursor.fetchall()
        return render_template("dashboard.html",articles=data)
    else:
        return render_template("dashboard.html")

@app.route("/article/<string:id>")
def articles1(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where id=(%s)"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        data=cursor.fetchone()
        return render_template("article.html", article=data)
    else: 
        return render_template("article.html")


#Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()

        sorgu="Select * from articles where id= %s and author = %s"
        result=cursor.execute(sorgu, (id, session["username"]))
        if result==0:
            flash("Böyle bir makale yok ya da bu makaleyi güncellemeye iznin yok","warning")
            return redirect(url_for("dashb"))
        else:
            article=cursor.fetchone()
            form= Addarticle()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)

            
    else:
        form= Addarticle(request.form)
        cursor=mysql.connection.cursor()

        new_title=form.title.data
        new_content=form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s "
        cursor.execute(sorgu2,(new_title,new_content,id,))
        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashb"))

#Makale Arama
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("articles"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%" + keyword +"%'"
        result=cursor.execute(sorgu)
        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles")) 
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)







@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("first"))



if __name__== "__main__":
    app.run(debug=True)