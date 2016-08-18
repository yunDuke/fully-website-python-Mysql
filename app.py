#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, session, request, redirect, flash, g, jsonify
from flask_googlemaps import GoogleMaps
from grove_rgb_lcd import *
from grovepi import *
from datetime import datetime
import mysql.connector
import json
import hashlib
import RPi.GPIO as GPIO
import time




sensor = 7

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.IN)
GPIO.setup(18, GPIO.OUT)  

app = Flask(__name__)
app.config['GOOGLEMAPS_KEY'] = "AIzaSyDk-2GwCjFNls84UgwzO2sULjyqhdCUp9I"
GoogleMaps(app, key="AIzaSyDk-2GwCjFNls84UgwzO2sULjyqhdCUp9I")


app.secret_key = '123456'
 
dbConnection = mysql.connector.connect(host='178.62.86.129', password="1234", user='root', database='all')


def get_model(table_name, attributes, sql_override=None):
    def func(id):
        if (id == None): return None

        cursor = dbConnection.cursor()
        cursor.execute(sql_override if sql_override is not None else 'select ' + ','.join(
            attributes) + ' from ' + table_name + ' where id=%s',
                       [id])
        result = cursor.fetchall()
        if len(result) == 0:
            return None
        else:
            ret = {}
            for i in range(0, len(attributes)):
                ret[attributes[i]] = result[0][i]

            return ret

    return func


get_user = get_model('user', ['id', 'name', 'password', 'user_type','carplate','cartype','email'])
get_post = get_model('post', ['id', 'title', 'content', 'time', 'name','price','location','lat','lon','allowingperiod','img1','img2','img3'],
                     'select post.id,title,content,time,user.name,price,location,lat,lon,allowingperiod,img1,img2,img3 from `post` left join user on user.id = user_id where post.id=%s')


def get_authed_user():
    return get_user(session.get('user_id', None))


@app.before_request
def before_request():
    g.authedUser = get_authed_user()
    g.url_path = request.path

@app.route('/')
def homepage():
    return render_template("show.html")

@app.route('/auth/logout')
def page_logout():
    flash(u'登出成功', 'success')
    del session['user_id']
    return redirect('/')



@app.route('/order')
def page_form():
    cursor = dbConnection.cursor()
    cursor.execute('select id,ordername,ordertime,currenttime,period,price from `order` where ordername = %s',[g.authedUser['carplate']])

    list = []

    for (id, ordername,ordertime,currenttime,period,price) in cursor.fetchall():
        list.append({"id": id,"ordername":ordername,"ordertime":ordertime,"currenttime":currenttime,"period":period,"price":price})
    
    return render_template('order.html', list=list)



@app.route('/order',methods=["POST"])
def shanchu():
    if request.form['delete'] != None:
         c = dbConnection.cursor()
         c.execute("DELETE from `order` WHERE `id`=%s",[request.form['delete']])
         c = dbConnection.cursor()
         dbConnection.commit()
         c.close()
         d = dbConnection.cursor()
         d.execute('select id,ordername,ordertime,currenttime,period,price from `order` where ordername = %s',[g.authedUser['carplate']])
         
        
         list = []

    for (id, ordername,ordertime,currenttime,period,price) in d.fetchall():
        list.append({"id": id,"ordername":ordername,"ordertime":ordertime,"currenttime":currenttime,"period":period,"price":price})
        
        
    return render_template('order.html', list=list)



@app.route('/new', methods=['POST'])
def page_form_post():
    if (len(request.form['title']) < 5):
        return redirect('/new')
    cursor = dbConnection.cursor();
    cursor.execute("INSERT into post (title,content,user_id,time) values (%s,%s,%s,now())",
                   [request.form['title'], request.form['content'], session['user_id']])

    return redirect('/')


@app.route('/add',methods=['GET','POST'])
def add():
    if request.method =="POST":
        if request.form.get('submit') == 'submit':
            cursor = dbConnection.cursor()
            list = []
            cursor.execute("select * from product where uniquecode = %s",[request.form['code']])    
            return render_template('add.html', list=cursor.fetchall())
        if request.form.get('submit') == 'bind':
             cursor = dbConnection.cursor()
             cursor.execute("INSERT into post (title,content,user_id,time,location,lat,lon,allowingperiod,polepassword,price,img1,img2,img3) values (%s,%s,%s,now(),%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                   [request.form['title'], request.form['content'], session['user_id'],request.form['location'],request.form['lat'],request.form['lon'],request.form['allowingperiod'],request.form['polepassword'],
                    request.form['price'],request.form['img1'],request.form['img2'],request.form['img3'] ])
             c = dbConnection.cursor()
           
             c.execute('UPDATE product SET name = %s,ownerplate=%s,location=%s WHERE id = %s', [request.form['title'],request.form['content'],request.form['location'],request.form['id']])
             dbConnection.commit()
             c.close()
             return redirect('/manage')
    return render_template('add.html')



@app.route('/list')
def page_list():
    cursor = dbConnection.cursor()
    cursor.execute('select id,title,time,content,location,price,allowingperiod,img1,img2,img3 from `post` order by id desc')

    list = []

    for (id, title, time,content,location,price,allowingperiod,img1,img2,img3) in cursor.fetchall():
        list.append({"id": id, "title": title, "time": time,"content":content,"location":location,"price":price,"allowingperiod":allowingperiod,"img1":img1,"img2":img2,"img3":img3})
      
    return render_template('list.html', list=list)


@app.route('/lists')
def page_lists():
    cursor = dbConnection.cursor()
    cursor.execute('select id,title,time,content,location,price,allowingperiod,img1,img2,img3 from `post` order by id desc')

    list = []

    for (id, title, time,content,location,price,allowingperiod,img1,img2,img3) in cursor.fetchall():
        list.append({"id": id, "title": title, "time": time,"content":content,"location":location,"price":price,"allowingperiod":allowingperiod,"img1":img1,"img2":img2,"img3":img3})
      
    return jsonify(list)


@app.route('/users')
def page_users():
    cursor = dbConnection.cursor()
    cursor.execute('select id,name,password,email,cartype,carplate from `user` order by id desc')
    
    user = []
    
    for (id, name,password,email,cartype,carplate) in cursor.fetchall():
        list.append({"id": id, "name": name, "password":password,"email":email,"cartype":cartype,"carplate":carplate})
    
    return jsonify(user)




@app.route('/manage')
def manage():
    cursor = dbConnection.cursor()
    cursor.execute("select id,title,time,content,img1,img2,img3,location,price from `post` where user_id = %s",[g.authedUser['id']])

    list = []

    for (id, title, time,content,img1,img2,img3,location,price) in cursor.fetchall():
        list.append({"id": id, "title": title, "time": time,"content":content,"img1":img1,"img2":img2,"img3":img3,"location":location,"price":price})

    return render_template('manage.html', list=list)

@app.route('/manage',methods=["POST"])
def delete():
    if request.form['delete'] != None:
         cursor = dbConnection.cursor()
         cursor.execute('delete from post where id = %s', [request.form['delete']])
         cursor = dbConnection.cursor()
         cursor.execute("select id,title,time,content,img1,img2,img3 from `post` where user_id = %s",[g.authedUser['id']])

         list = []

         for (id, title, time,content,img1,img2,img3) in cursor.fetchall():
           list.append({"id": id, "title": title, "time": time,"content":content,"img1":img1,"img2":img2,"img3":img3})
    return render_template('manage.html',list=list)






@app.route("/item/<id>")
def page_item(id):
    post = get_post(id)
    cursor = dbConnection.cursor()
    cursor.execute(
        'select content,time,name,reply.id from reply left join user on reply.user_id=user.id where post_id=%s', [id])
    replies = cursor.fetchall()
    return render_template("item.html", post=post, replies=replies)

@app.route("/item/<id>", methods=["POST"])
def page_item_post(id):
    if request.form['action'] == 'delete':
        cursor = dbConnection.cursor()
        cursor.execute('delete from post where id = %s', [id])
        return redirect('/')
    elif request.form['action'].startswith('delete-reply:'):
        cursor = dbConnection.cursor()
        cursor.execute('delete from reply where id = %s', [request.form['action'][13:]])
        return redirect('/item/' + id)

    elif request.form['action'] == 'reply':
        if len(request.form['reply']) < 3:
            flash(u"回复太短！", 'error')
            return redirect('/item/' + id)

        cursor = dbConnection.cursor()
        cursor.execute('INSERT into reply (user_id,post_id,content,time) values (%s,%s,%s,now())',
                       [g.authedUser['id'], id, request.form['reply']])

        flash(u"回复成功！", 'success')
        return redirect('/item/' + id)
    
    elif request.form['action'] == 'order':
        cursor = dbConnection.cursor()
       
       
        s = request.form['period']
        price = float(s)
        c = dbConnection.cursor()
        c.execute(   'select price from post where id=%s', [id])
        cu = c.fetchall()
        print cu
        for r in cu:
              print r[0]
              print time.time()
              strs = g.authedUser['carplate']
              ss=str(time.time())
              cursor.execute('INSERT into `order`( `ordername`,`ordertime`,`period`,`post_id`,`currenttime`,`price`,`aucode`,`orderstate`) VALUES (%s,%s,%s,%s,now(),%s,%s,%s)',
                       [g.authedUser['carplate'],request.form['ordertime'],request.form['period'],id,price*r[0],strs[-5:-1]+ss[2:6],"start"])
        
              dbConnection.commit()
              cursor.close()
              c = dbConnection.cursor()   
              c.execute('UPDATE post SET reserveplate = %s,reservetime=%s WHERE id = %s', [g.authedUser['carplate'],request.form['ordertime'],id])
              dbConnection.commit()
              c.close()
        return redirect('/order')    

    else:
        flash(u"action not supported", 'error')
        return redirect('/item/' + id)


@app.route('/login')
def page_login():
    return render_template("signin.html")


@app.route('/register')
def page_register():
    return render_template("signup.html")


@app.route('/login', methods=["POST"])
def page_login_post():
    username = request.form['username']
    password = request.form['password']
    cursor = dbConnection.cursor()
    cursor.execute('select id,password from `user` where name=%s', [username])

    result = cursor.fetchall()
    if len(result) == 0:
        return redirect('/login')

    if md5Hash(password) != result[0][1]:
        return redirect('/login')

    session['user_id'] = result[0][0]
    
    return redirect('/list')
   


@app.route('/register', methods=["POST"])
def page_register_post():
    if len(request.form['name']) < 3:
        return redirect('/register')

    if len(request.form['password']) < 6:
        return redirect('/register')

    cursor = dbConnection.cursor()

    cursor.execute('select count(1) from `user` where name=%s',
                   [request.form['name']])

    if cursor.fetchall()[0][0] > 0:
        return redirect('/register')

    cursor = dbConnection.cursor()

    cursor.execute('insert into `user` (name,password,email,carplate,cartype) values (%s,%s,%s,%s,%s)',
                   [request.form['name'], md5Hash(request.form['password']),request.form['email'],request.form['carplate'],request.form['cartype']])

    flash("", 'success')

    session['user_id'] = cursor.lastrowid

    return redirect('/login')


def md5Hash(password):
    m = hashlib.md5()
    m.update(password)
    return m.hexdigest()


if __name__ == '__main__':
    app.run(debug=True)
