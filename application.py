from flask import Flask
from flask import request, redirect, render_template
from flask import make_response, render_template
from uuid  import uuid4
from bcrypt import checkpw
import os
import sqlite3

app = Flask(__name__)
app.use("/static", express.static('./static/'));
currentDir = os.path.dirname(os.path.abspath(__file__))
hashed_password = b'$2b$12$YegDi5sS7DB4QCA9/XfEGu4P7VFgKs5qaXjUqW87QI9V2kv3qFJaC'
authenticated_users = {"ba12b970-228b-4d61-b8b8-ee428866b53f" : "bach"}


@app.route("/", methods=["GET", "POST"])
def index():
  
  if "backRegister" in request.form:
    return render_template("register-form.html")

  sid = request.cookies.get("sid")
  
  # wczytywanie sida z bazy danych
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  querySelect = "select name, sid from Users where Sid = '" + str(sid) + "';";
  result = cursor.execute(querySelect)
  received = list(cursor.fetchall())
  connection.commit()
  cursor.close()
  
  if len(received) != 0:
    usernameReceived = received[0][0]
    sidReceived = received[0][1]
    if sid == sidReceived:
      return render_template("homepage.html", username = usernameReceived)
  else:
    return redirect("/authenticate", code=302)
    
    
    

@app.route("/authenticate", methods=["GET", "POST"])
def authenticate():
  if request.method == "GET":
    return render_template("login-form.html")
  
  if "register" in request.form:
    return render_template("register-form.html")
             
  username = request.form.get("username", "")
  password = request.form.get("password", "")

  #logowanie za pomoca bazy danych
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  querySelect = "select name, password from Users where name = '" + username + "' and Password = '" + password + "';";
  result = cursor.execute(querySelect)
  received = list(cursor.fetchall())

  if len(received) != 0:
    usernameReceived = received[0][0]
    passwordReceived = received[0][1]

    if username == usernameReceived and password == passwordReceived:
      sid = str(uuid4())
      queryUpdateSid = "UPDATE Users SET Sid = '" + sid + "' WHERE name = '" + username + "' and Password = '" + password + "';"
      cursor.execute(queryUpdateSid)
      connection.commit()
      cursor.close()
      response = redirect("/", code=302)
      response.set_cookie("sid", sid)
      return response

  else:
    connection.commit()
    cursor.close()
    return render_template("flash.html", msg = "logowania")



@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "GET":
    return render_template("register-form.html")
  
  if "login" in request.form:
    return render_template("login-form.html")

  username = request.form.get("username", "")
  email = request.form.get("email", "")
  password = request.form.get("password", "")
  
  
  #rejestracja za pomoca bazy danych
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  
  #sprawdzenie czy taki użytkownik istnieje w bazie danych
  querySelect = "select name, password from Users where name = '" + username + "' and Password = '" + password + "';";
  print(querySelect + "-----------------------------")
  result = cursor.execute(querySelect)
  received = list(cursor.fetchall())

  if len(received) != 0:
    usernameReceived = received[0][0]
    passwordReceived = received[0][1]
    print("us=", username)
    print("usR=", usernameReceived)
    print("p=", password)
    print("pR=", passwordReceived)
    if username == usernameReceived or password == passwordReceived:
      connection.commit()
      cursor.close()
      return render_template("flash.html", msg = "rejestracji (taki użytkownik istnieje już w bazie danych)")
      
  #mozemy utworzyc nowego uzytkownika (w tym miejscu walidacja danych)
  #return render_template("flash.html", msg = "rejestracji")
  sid = str(uuid4())
  queryInsert = "Insert into users values ('" + username + "', '" + sid + "', '" + password + "');"
  result = cursor.execute(queryInsert)
  connection.commit()
  cursor.close()
  response = redirect("/", code=302)
  response.set_cookie("sid", sid)
  return response


@app.route("/logout", methods=["POST"])
def logout():
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  queryUpdateSid = "UPDATE Users SET Sid = '' WHERE name = '" + request.form['name'] + "';"
  cursor.execute(queryUpdateSid)
  connection.commit()
  cursor.close()
    
  response = redirect("/", code=302)
  return response










if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug="True")