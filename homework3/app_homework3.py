import personal_info, uuid
from flask import( Flask, abort, flash, get_flashed_messages,
                   redirect, render_template, request, session, url_for )
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = ''

@app.route( '/login', methods=['GET', 'POST'] )
def login():
  username = request.form.get( 'username', '' )
  password = request.form.get( 'password', '' )
  if request.method == 'POST':
    db = personal_info.open_database()
    if personal_info.has_account( db, username, password ):
      session['username'] = username
      session['csrf_token'] = uuid.uuid4().hex
      db.close()
      return redirect( url_for( 'index' ) )
  return render_template( 'login.html', username=username )

@app.route( '/logout' )
def logout():
  session.pop( 'username', None )
  return redirect( url_for( 'login' ) )

@app.route( '/' )
def index():
  db = personal_info.open_database()
  username = session.get( 'username' )
  if not username:
    return redirect( url_for( 'login' ) )
  info = personal_info.get_information( db, username )
  birth_date = datetime.strptime( info[0].birth, "%Y-%m-%d" ).date()
  db.close()
  return render_template( 'index.html', account = info[0].account, birth = birth_date,
                          introduction = info[0].introduction,
                          flash_messages=get_flashed_messages() )

@app.route( '/edit', methods=['GET', 'POST'] )
def edit():
  username = session.get( 'username' )
  if not username:
    return redirect( url_for( 'login' ) )
  account = username
  birth = request.form.get( 'birth', '' ).strip()
  password = request.form.get( 'password', '' ).strip()
  introduction = request.form.get( 'introduction', '' ).strip()

  complaint = None
  if request.method == 'POST':
    if request.form.get( 'csrf_token' ) != session['csrf_token']:
      abort(403)
    if password and password.isalnum():
      db = personal_info.open_database()
      personal_info.update_information( db, account, password, birth, introduction )
      db.commit()
      db.close()
      flash( 'Update successful' )
      return redirect( url_for( 'index' ) )
    complaint = ( 'Password must be an alphanumeric' )

  db = personal_info.open_database()
  info = personal_info.get_information( db, username )
  db.close()
  return render_template( 'edit.html', complaint=complaint, username=info[0].account,
                          password=info[0].password, birth=info[0].birth,
                          introduction=info[0].introduction, csrf_token=session['csrf_token'] )

@app.route( '/register', methods=['GET', 'POST'] )
def register():
  account = request.form.get( 'account', '' ).strip()
  birth = request.form.get( 'birth', '' ).strip()
  password = request.form.get( 'password', '' ).strip()
  introduction = request.form.get( 'introduction', '' ).strip()
  print( account + "+++++++++++++++" )
  complaint = None
  if request.method == 'POST':
    if password and password.isalnum() and account and account.isalnum():
      print( account )
      db = personal_info.open_database()
      personal_info.add_information( db, account, password, birth, introduction )
      db.commit()
      db.close()
      flash( 'Register successful!' )
      return redirect( url_for( 'login' ) )
    complaint = ( 'Password and account must be an alphanumeric' )

  return render_template( 'register.html' )

if __name__ == '__main__':
  app.debug = True
  f = open( 'secretkey', 'r' )
  app.secret_key = f.read()

  app.run(ssl_context=( 'server.crt', 'server.key' ) )
