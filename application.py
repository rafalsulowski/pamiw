from flask import Flask
from flask import request, redirect, render_template
from flask import make_response, render_template
from uuid  import uuid4
from bcrypt import checkpw
from datetime import datetime
import os
import sqlite3
import queue



class MessageAnnouncer:

    def __init__(self):
        self.listeners = []

    def listen(self):
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]


def format_sse(data: str, event=None) -> str:
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg

def sql(strSQL):
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  cursor.execute(strSQL)
  connection.commit()
  cursor.close()


app = Flask(__name__)
currentDir = os.path.dirname(os.path.abspath(__file__))
hashed_password = b'$2b$12$YegDi5sS7DB4QCA9/XfEGu4P7VFgKs5qaXjUqW87QI9V2kv3qFJaC'
announcer = MessageAnnouncer()


@app.route("/sse", methods=["GET"])
def sse():
  messages = announcer.listen()  # returns a queue.Queue
  while True:
    msg = messages.get()  # blocks until a new message arrives
    yield msg
  return Flask.Response(stream(), mimetype='text/event-stream')

@app.route("/", methods=["GET", "POST"])
def index():
  
  msg = format_sse(data='pong')
  announcer.announce(msg=msg)

  sid = request.cookies.get("sid")
  
  # wczytywanie sida z bazy danych
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  querySelect = "select name, sid from Users where Sid = '" + str(sid) + "';";
  result = cursor.execute(querySelect)
  received = list(cursor.fetchall())
  
  if len(received) != 0:
    usernameReceived = received[0][0]
    sidReceived = received[0][1]
    if sid == sidReceived:
      
      #pobranie Paczek z bazy danych
      querySelectPackage = "select * from Package";
      result = cursor.execute(querySelectPackage)
      received = list(cursor.fetchall())
      connection.commit()
      cursor.close()
      
      return render_template("homepage.html", username = usernameReceived, len = len(received), Packages = received)
  else:
    connection.commit()
    cursor.close()
    return redirect("/authenticate", code=302)
 
@app.route("/add", methods=["GET","POST"])
def add():
  if request.method == "GET":
    return render_template("add.html")
    
  id = request.form.get("id")
  status = request.form.get("status") or "w przygotowaniu u nadawcy"
  date = request.form.get("date") or  datetime.now().strftime("%d-%m-%Y")
  
  if len(id) != 19:
    return render_template("flash.html", msg = "nowej paczki")

  sql("INSERT INTO Package (id, status, data) VALUES ('" + id + "', '" + status + "', '" + date + "');")
  return redirect("/", code=302)
  
@app.route("/delete", methods=["POST"])
def delete():
  id = request.form.get("id")
  
  sql("DELETE FROM Package WHERE id = '" + id + "';")
  return redirect("/", code=302)

@app.route("/stricteModify", methods=["POST"])
def stricteModify():
  number = request.form["number"]
  id = request.form["id"]
  status = request.form["status"]
  date = request.form["date"]
  return render_template("modifyPackageWindow.html", number = number, id = id, status = status, date = date)
    
@app.route("/stricteModifyDefinitive", methods=["POST"])
def stricteModifyDefinitive():
  number = request.form["number"]
  oldId = request.form["oldId"]
  id = request.form["id"]
  status = request.form["status"]
  date = request.form["date"]

  sql("UPDATE Package SET id = '" + id + "', status = '" + status + "', data = '" + date + "' WHERE id = '" + oldId + "';")
  return render_template("modify.html", number = number, id = id, status = status, date = date)

@app.route("/packageMoreInfo", methods=["GET", "POST"])
def packageMoreInfo():
  id = request.form["id"]
  number = request.form["number"]

  #pobranie Paczek z bazy danych
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  querySelectPackage = "select * from Package WHERE Id = '" + id + "';";
  result = cursor.execute(querySelectPackage)
  received = list(cursor.fetchall())  
  connection.commit()
  cursor.close()

  return render_template("modify.html", number = number, id = received[0][0], status = received[0][1], date = received[0][2])

@app.route("/authenticate", methods=["GET", "POST"])
def authenticate():
  if request.method == "GET":
    return render_template("login-form.html")
               
  username = request.form.get("username", "")
  password = request.form.get("password", "")

  #logowanie za pomoca bazy danych
  connection = sqlite3.connect(currentDir + "./db/context.db")
  cursor = connection.cursor()
  querySelect = "select name, password from Users where name = '" + username + "' and Password = '" + password + "';";
  result = cursor.execute(querySelect)
  received = list(cursor.fetchall())
  connection.commit()
  cursor.close()

  if len(received) != 0:
    usernameReceived = received[0][0]
    passwordReceived = received[0][1]

    if username == usernameReceived and password == passwordReceived:
      sid = str(uuid4())
      sql("UPDATE Users SET Sid = '" + sid + "' WHERE name = '" + username + "' and Password = '" + password + "';")
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
  connection.commit()
  cursor.close()

  if len(received) != 0:
    usernameReceived = received[0][0]
    passwordReceived = received[0][1]
    if username == usernameReceived or password == passwordReceived:
      connection.commit()
      cursor.close()
      return render_template("flash.html", msg = "rejestracji (taki użytkownik istnieje już w bazie danych)")
      
  #mozemy utworzyc nowego uzytkownika (w tym miejscu walidacja danych)
  #return render_template("flash.html", msg = "rejestracji")
  sid = str(uuid4())
  sql("Insert into users values ('" + username + "', '" + sid + "', '" + password + "');")
  response = redirect("/", code=302)
  response.set_cookie("sid", sid)
  return response

@app.route("/logout", methods=["POST"])
def logout():
  sql("UPDATE Users SET Sid = '' WHERE name = '" + request.form['name'] + "';")    
  return redirect("/", code=302)

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug="True")