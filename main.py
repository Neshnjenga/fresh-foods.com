from flask import Flask,flash,render_template,redirect,session,url_for,request
from flask_mail import Message,Mail
from random import *
import re
import pymysql
import secrets
import bcrypt
import time
import base64

app=Flask(__name__)
app.secret_key='ccxdrdrxcderfatftftyxs'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='chegenelson641@gmail.com'
app.config['MAIL_USE_TSL']=False
app.config['MAIL_USE_SSL']=True

mail=Mail(app)

connection=pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='flask_fresh'
)

cur=connection.cursor()
def sendmail(subject,email,body):
    
        msg=Message(subject=subject,sender='chegenelson641@gmail.com',recipients=[email],body=body)
        mail.send(msg)
   

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        phone=request.form['phone']
        address=request.form['address']
        password=request.form['password']
        confirm=request.form['confirm']
        cur.execute('SELECT * FROM user WHERE username=%s',(username))
        connection.commit()
        data=cur.fetchone()
        cur.execute('SELECT * FROM user WHERE  email=%s',(email))
        connection.commit()
        main=cur.fetchone()
        if username=='' or email=='' or phone=='' or password=='' or address=='' or confirm=='':
            flash('All fields are required','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        elif data is not None:
            flash('Username already created create new one','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        elif main is not None:
            flash('Create new email','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        elif username==password:
            flash('Username and password should not be simillar','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        elif password != confirm:
            flash('Incorrect passwords','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        elif not re.search('[A-Z]',password):
            flash('Password should have capital letters','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        elif not re.search('[a-z]',password):
            flash('Password should have small letters','warning')
            return render_template('register.html',username=username,email=email,phone=phone,address=address,password=password,confirm=confirm)
        else:
            hashed=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
            sendAtTime=int(time.time())
            otp=randint(0000,9999)
            cur.execute('INSERT INTO user(username,email,phone,address,password,otp,sendAtTime)VALUES(%s,%s,%s,%s,%s,%s,%s)',(username,email,phone,address,hashed,otp,sendAtTime))
            connection.commit()
            subject='Account creation'
            body=f'Thank you for creating an account with us.\nPlease verify your accont using this otp {otp} .'
            sendmail(subject,email,body)
            flash('Account created successfully','success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/otp',methods=['POST','GET'])
def otp():
    if request.method=='POST':
        id=session['user_id']
        otp=request.form['otp']
        cur.execute('SELECT * FROM user WHERE id=%s',(id,))
        connection.commit()
        data=cur.fetchone()
        if data is not None:
            if data[8]==int(otp):
                current_At_Time=int(time.time())
                expiryTime=int(1*60)
                sendAtTime=int(data[11])
                if current_At_Time - sendAtTime > expiryTime:
                    flash('Otp has expired','warning')
                    return redirect(url_for('otp'))
                else:
                    cur.execute('UPDATE user SET is_verified=1 WHERE otp=%s',(otp))
                    connection.commit()
                    flash('Account has been verified successfully','success')
                    return redirect(url_for('otp'))
                
            else:
                flash('Otp does not Match','warning')
                return redirect(url_for('otp'))
            
    cur.execute('SELECT * FROM user WHERE id=%s',(session['user_id']))
    connection.commit()
    data=cur.fetchone()
    Time=int(time.time())-int(data[11])
    remainingTime=int(1*60)-Time
    print(remainingTime)
    return render_template('otp.html',remainingTime=remainingTime)

@app.route('/resend')
def resend():
    if 'username' in session:
        id=session['user_id']
        cur.execute('SELECT * FROM user WHERE id=%s',(id))
        connection.commit()
        data=cur.fetchone()
        otp=randint(000000,999999)
        sendAtTime=int(time.time())
        cur.execute('UPDATE user SET otp=%s,sendAtTime=%s WHERE id=%s',(otp,sendAtTime,id))
        connection.commit()
        subject='New otp'
        body=f'New otp has been sent to account {otp}'
        sendmail(subject,data[2],body)
        flash('A new otp has been sent to email ','success')
        return redirect(url_for('otp'))
    else:
        flash('PLease login','warning')
        return redirect(url_for('login'))
    



@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        if username=='' or password=='':
            flash('All fields are required','warning')
            return render_template('login.html',username=username,password=password)
        else:
            cur.execute('SELECT * FROM user WHERE username=%s',(username))
            connection.commit()
            data=cur.fetchone()
            if data is not None:
                if bcrypt.checkpw(password.encode('utf-8'),data[5].encode('utf-8')):
                    session['username']=data[1]
                    session['user_id']=data[0]
                    session['role']=data[6]
                    if data[9]==1:
                        if session['role']=='user':
                            return redirect(url_for('home'))
                        else:
                            return redirect(url_for('home'))
                    else:
                        flash('Please verify you account','warning')
                        return redirect(url_for('otp'))
                else:
                    flash('Incorrect password','warning')
                    return render_template('login.html',username=username,password=password)
            else:
                flash('Incorrect username','warning')
                return render_template('login.html',username=username,password=password)
    return render_template('login.html')

@app.route('/forgot',methods=['POST','GET'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        cur.execute('SELECT * FROM user WHERE email=%s',(email))
        connection.commit()
        data=cur.fetchone()
        if data is not None:
            send_at_time=int(time.time())
            token=secrets.token_hex(50)
            reset_link=url_for('reset',token=token,_external=True)
            cur.execute('UPDATE user SET token=%s,tokenSendTime=%s WHERE email=%s',(token,send_at_time,email))
            connection.commit()
            subject='Forgot password'
            body=f'Use this link to change password {reset_link}'
            sendmail(subject,email,body)
            flash('Reset link has been sent to your email','success')
            return redirect(url_for('forgot'))
        else:
            flash('Incorrect email','warning')
            return redirect(url_for('forgot'))
    return render_template('forgot.html')

@app.route('/reset',methods=['POST','GET'])
def reset():
    token=request.args.get('token')
    if request.method=='POST':
        username=session['username']
        password=request.form['password']
        confirm=request.form['confirm']
        if password=='' or confirm=='':
            flash('All fields are required','warning')
            return render_template('reset.html',password=password,confirm=confirm)
        elif username==password:
            flash('Username and password should not be simillar','warning')
            return render_template('reset.html',password=password,confirm=confirm)
        elif password != confirm:
            flash('Incorrect passwords','warning')
            return render_template('reset.html',password=password,confirm=confirm)
        elif not re.search('[A-Z]',password):
            flash('Password should have capital letters','warning')
            return render_template('reset.html',password=password,confirm=confirm)
        elif not re.search('[a-z]',password):
            flash('Password should have small letters','warning')
            return render_template('reset.html',password=password,confirm=confirm)
        else:
            cur.execute('SELECT * FROM user WHERE token=%s',(token))
            connection.commit()
            data=cur.fetchone()
            if data is not None:
                currentTime=int(time.time())
                expiryTime=int(1 * 60)
                send_at_Time=data[10]
                if currentTime - send_at_Time > expiryTime:
                    flash('Token has expired create new one','warning')
                    return redirect(url_for('forgot'))
                else:
                    hashed=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
                    cur.execute('UPDATE user SET token="token",password=%s WHERE token=%s',(hashed,token))
                    connection.commit()
                    flash('Password changed successfully','success')
                    return redirect(url_for('login'))
            else:
                flash('Token already used generate new one by forgetting password','warning')
                return redirect(url_for('forgot'))
    return render_template('reset.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/addDrink',methods=['POST','GET'])
def addDrink():
    if 'username' in session:
        if session['role']=='admin':
            if request.method=='POST':
                name=request.form['name']
                price=request.form['price']
                image=request.files['image'].read()
                cur.execute('INSERT INTO drink(name,price,image)VALUES(%s,%s,%s)',(name,price,image))
                connection.commit()
                return redirect(url_for('home'))
            return render_template('drink.html')
        else:
            return 'Not allowed in this zone'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/viewDrink')
def viewDrink():
    cur.execute('SELECT * FROM drink')
    connection.commit()
    data=cur.fetchall()
    fetch=[]
    for user in data:
        image=user[3]
        decoded=base64.b64encode(image).decode('utf-8')
        upload=list(user)
        upload[3]=decoded
        fetch.append(upload)
    return render_template('viewDrink.html',fetch=fetch)

@app.route('/addFood',methods=['POST','GET'])
def addFood():
    if 'username' in session:
        if session['role']=='admin':

            if request.method=='POST':
                name=request.form['name']
                price=request.form['price']
                image=request.files['image'].read()
                cur.execute('INSERT INTO food(name,price,image)VALUES(%s,%s,%s)',(name,price,image))
                connection.commit()
                return redirect(url_for('home'))
            return render_template('food.html')
        else:
            return 'Not allowed in this zone'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/viewFood')
def viewFood():
    cur.execute('SELECT * FROM food')
    connection.commit()
    data=cur.fetchall()
    fetch=[]
    for user in data:
        image=user[3]
        decoded=base64.b64encode(image).decode('utf-8')
        upload=list(user)
        upload[3]=decoded
        fetch.append(upload)
    return render_template('viewFood.html',fetch=fetch)

@app.route('/order/<table>/<id>',methods=['POST','GET'])
def order(table,id):
    if 'username' in session:  
        if request.method=='POST':
            user_id=session['user_id']
            username=session['username']
            address=request.form['address']
            phone=request.form['phone']
            food=request.form['food']
            price=request.form['price']
            cur.execute('INSERT INTO orders(user_id,username,address,phone,food,price)VALUES(%s,%s,%s,%s,%s,%s)',(user_id,username,address,phone,food,price))
            connection.commit()
            return redirect(url_for('home'))
        else:
            if table =='food':
                user_id=session['user_id']
                cur.execute('SELECT * FROM user WHERE id=%s',(user_id))
                connection.commit()
                data=cur.fetchone()
                cur.execute('SELECT * FROM food WHERE id=%s',(id))
                connection.commit()
                user=cur.fetchone()
               
            else:
                user_id=session['user_id']
                cur.execute('SELECT * FROM user WHERE id=%s',(user_id))
                connection.commit()
                data=cur.fetchone()
                cur.execute('SELECT * FROM drink WHERE id=%s',(id))
                connection.commit()
                user=cur.fetchone()
                
        return render_template('order.html',data=data,user=user)
        
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))
    
@app.route('/viewOrder')
def viewOrder():
    if 'username' in session:
        user_id=session['user_id']
        cur.execute('SELECT * FROM orders WHERE user_id=%s',(user_id))
        connection.commit()
        data=cur.fetchall()
        return render_template('viewOrder.html',data=data)
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/manageOrders')
def manageOrders():
    if 'username' in session:
        if session['role']=='admin':
            cur.execute('SELECT * FROM orders')
            connection.commit()
            data=cur.fetchall()
            return render_template('manageOrders.html',data=data)
        else:
            return 'You are not allowed'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/authorize/<id>',methods=['POST','GET'])
def authorize(id):
    if 'username' in session:
        if session['role']=='admin':
            if request.method=='POST':
                action=request.form['action']
                cur.execute('UPDATE orders SET action=%s WHERE id=%s',(action,id))
                connection.commit()
                return redirect(url_for('manageOrders'))
            return render_template('authorize.html')
        else:
            return 'You are not allowed'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))


@app.route('/mailSend')
def mailSend():
    if 'username' in session:
        if session['role']=='admin':
            return render_template('mail.html')
        else:
            return 'You are not allowed at this point'
    else:
        flash('Please login to your account','warning')
        return redirect(url_for('login'))

@app.route('/typeMail',methods=['POST','GET'])
def typeMail():
    if 'username' in session:
        if session['role']=='admin':
            if request.method=='POST':
                subject=request.form['subject']
                body=request.form['body']
                file=request.files['file']
                recipient=getUsers()
                html_content=render_template('mailContent.html',body=body)
                msg=Message(subject=subject,sender='chegenelson641@gmail.com',recipients=recipient)
                msg.html=html_content
                msg.attach(
                    filename='Offers',
                    content_type='application/pdf',
                    data=file.read(),
                    disposition='attachement'
                )
                mail.send(msg)
                return redirect(url_for('mailSend'))
            return render_template('sendmail.html')
        else:
            return 'You are not allowed at this point'
    else:
        flash('Please login to your account','warning')
        return redirect(url_for('login'))

def getUsers():
    cur.execute('SELECT * FROM user')
    connection.commit()
    users=cur.fetchall()
    return [user[2] for user in users]





@app.route('/manage')
def manage():
    if 'username' in session:
        if session['role']=='admin':
            cur.execute('SELECT * FROM food')
            connection.commit()
            data=cur.fetchall()
            fetch=[]
            for user in data:
                image=user[3]
                decoded=base64.b64encode(image).decode('utf-8')
                upload=list(user)
                upload[3]=decoded
                fetch.append(upload)
            return render_template('manage.html',fetch=fetch)
        else:
            return 'You are not allowed at this point'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/delete/<id>')
def delete(id):
    if 'username' in session:
        if session['role']=='admin':
            cur.execute('DELETE FROM food WHERE id=%s',(id))
            connection.commit()
            return redirect(url_for('home'))
        else:
            return 'You are not allowed at this point'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/update/<id>',methods=['POST','GET'])
def update(id):
    if 'username' in session:
        if session['role']=='admin':
            cur.execute('SELECT * FROM food WHERE id=%s',(id))
            connection.commit()
            data=cur.fetchone()
            image=data[3]
            decoded=base64.b64encode(image).decode('utf-8')
            if request.method=='POST':
                name=request.form['name']
                price=request.form['price']
                image=request.files['image'].read()
                cur.execute('UPDATE food SET name=%s,price=%s,image=%s WHERE id=%s',(name,price,image,id))
                connection.commit()
                return redirect(url_for('manage'))
            return render_template('update.html',data=data,decoded=decoded)
        else:
            return 'You are not allowed at this point'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))

@app.route('/updates/<id>',methods=['POST','GET'])
def updates(id):
    if 'username' in session:
        if session['role']=='admin':
            cur.execute('SELECT * FROM drink WHERE id=%s',(id))
            connection.commit()
            data=cur.fetchone()
            image=data[3]
            decoded=base64.b64encode(image).decode('utf-8')
            if request.method=='POST':
                name=request.form['name']
                price=request.form['price']
                image=request.files['image'].read()
                cur.execute('UPDATE drink SET name=%s,price=%s,image=%s WHERE id=%s',(name,price,image,id))
                connection.commit()
            return render_template('updates.html',decoded=decoded,data=data)
        else:
            return 'You are not allowed at this point'
    else:
        flash('Please login','warning')
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__=='__main__':
    app.run(debug=True)