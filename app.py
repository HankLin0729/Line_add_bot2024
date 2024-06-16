import random
import string
import os
from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for, abort
import sqlite3
import re
import paho.mqtt.client as mqtt
import requests
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import requests


app = Flask(__name__)
# 必須放上自己的Channel Access Token
line_bot_api = LineBotApi('Pm8bbGolkGYBAAg1LPH/XgU6gnT6iUCzK0twyzMt8uLsIoFj4npoZJ95pvCJS/NsxUtKt810RiQBKuVKuq2samIeG4es/3N6A4U4pZ3VFpL7ssJiPLanLXABEoFH0hnMhbMDsotzjy/YoV/oNeRH3gdB04t89/1O/w1cDnyilFU=')
# 必須放上自己的Channel Secret
handler = WebhookHandler('6e0fb968dd0f21768c626fb585496e5c')



app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' 

DATABASE = 'data.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    else:
        try:
            db.execute('SELECT 1')
        except (AttributeError, sqlite3.ProgrammingError):
            db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r', encoding='utf-8') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
@app.before_request
def before_request():
    g.db = get_db()


        
def generate_random_string():
    chars = string.ascii_letters + string.digits.replace('0', '')
    random_string = ''.join(random.choice(chars) for _ in range(10))
    random_string = random_string[:0] + 'R' + random_string[2:5] + 'H' + random_string[6:8] + '0' + random_string[9:]
    return random_string

def fetch_all_line_no():
    conn = get_db()  
    cursor = conn.cursor()
    cursor.execute('SELECT line_no FROM material')  
    line_nos = cursor.fetchall()  
    conn.close()
    return [line_no[0] for line_no in line_nos] 

def send_line_notify(notify_token, message):
    headers = {
        'Authorization': f'Bearer {notify_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'message': message}
    response = requests.post('https://notify-api.line.me/api/notify', headers=headers, data=data)
    return response.status_code


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

 
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

#訊息傳遞區塊
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type == 'group':
        group_id = event.source.group_id  
        print("Received a message from Group ID:", group_id)
        
    message_text = event.message.text  
    
    line_nos = fetch_all_line_no()
    
    if message_text in line_nos:
        print("正確")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="設定完成")
        )
        db = get_db()
        cursor = db.cursor()
        
        safe_table_name = "".join([c for c in message_text if c.isalnum()])  
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {safe_table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            dollars TEXT NOT NULL
        )''')
        db.commit()

        if event.source.type == 'group':  
            cursor.execute('''UPDATE material SET line_id = ? WHERE line_no = ?''', (group_id, message_text))
            db.commit()

    if event.source.type == 'group' and event.message.text == '到':
        group_id = event.source.group_id 
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT line_no FROM material WHERE line_id = ?', (group_id,))
        result = cursor.fetchone()
        
        if result:
            line_no = result[0]
            safe_table_name = "".join([c for c in line_no if c.isalnum() or c == '_'])
            sql_delete_contents = f'''DELETE FROM "{safe_table_name}"'''
            cursor.execute(sql_delete_contents)
            db.commit()
            print(f"已清空{line_no}。")
        else:
            print(f"没有找到{group_id}")
            
    if event.source.type == 'group':
        group_id = event.source.group_id  
        print("Received a message from Group ID:", group_id)
        
    message_text = event.message.text  

    keywords = message_text.split('+')

    db = get_db()
    cursor = db.cursor()

    if group_id:
        cursor.execute('SELECT line_no FROM material WHERE line_id = ?', (group_id,))
        result = cursor.fetchone()
        
        if result:
            line_no = result[0]
            safe_table_name = "".join([c for c in line_no if c.isalnum() or c == '_'])
        else:
            print(f"沒有紀錄。")
            return

    for keyword in keywords:
        cursor.execute('SELECT keyword, dollors FROM keyword WHERE keyword = ?', (keyword.strip(),))
        result = cursor.fetchone()
        
        if result:
            item_name, amount = result
            
            sql_insert_item = f'''INSERT INTO "{safe_table_name}" (keyword, dollars) VALUES (?, ?)'''
            cursor.execute(sql_insert_item, (item_name, amount))
            db.commit()
            print(f"已向{line_no}表添加項目{item_name}和金額{amount}。")
        else:
            print(f"ERROR: No data for keyword '{keyword.strip()}'")

        
    if event.source.type == 'group':
        group_id = event.source.group_id
        print("Received a message from Group ID:", group_id)
        
    message_text = event.message.text

    if message_text == '結帳':
        db = get_db()
        cursor = db.cursor()
    
        cursor.execute('SELECT line_no, notify FROM material WHERE line_id = ?', (group_id,))
        result = cursor.fetchone()
    
        if result:
            line_no, notify_token = result
            safe_table_name = "".join([c for c in line_no if c.isalnum() or c == '_'])
    
            try:
                cursor.execute(f'SELECT SUM(CAST(dollars AS INTEGER)) FROM "{safe_table_name}"')
                total_amount = cursor.fetchone()[0] or 0
                message = f"總金額: {total_amount}"
                print(message)
                if notify_token: 
                    notify_status = send_line_notify(notify_token, message)
                    print(f"Line Notify 狀態碼: {notify_status}")
                
                cursor.execute(f'DELETE FROM "{safe_table_name}"')
                db.commit()
                print(f"已清空{line_no}的資料表。")
    
            except Exception as e:
                error_msg = f"計算錯誤: {e}"
                print(error_msg)
        else:
            no_record_msg = "沒有紀錄。"
            print(no_record_msg)
    
    if event.source.type == 'group':
        group_id = event.source.group_id
        print("Received a message from Group ID:", group_id)

    message_text = event.message.text
    db = get_db()
    cursor = db.cursor()

    if '收回' in message_text:
        try:
            delete_count = int(message_text.split('*')[1])
        except (IndexError, ValueError):
            delete_count = 1  
        print(f"Preparing to delete the last {delete_count} entries.")

        cursor.execute('SELECT line_no FROM material WHERE line_id = ?', (group_id,))
        result = cursor.fetchone()
        if result:
            line_no = result[0]
            safe_table_name = "".join([c for c in line_no if c.isalnum() or c == '_'])
            print(f"Table for deletion: {safe_table_name}")

            cursor.execute(f'SELECT id FROM "{safe_table_name}" ORDER BY id DESC LIMIT ?', (delete_count,))
            last_ids = cursor.fetchall()
            if last_ids:
                ids_to_delete = [id_tuple[0] for id_tuple in last_ids]
                print(f"IDs to delete: {ids_to_delete}")

                cursor.executemany(f'DELETE FROM "{safe_table_name}" WHERE id = ?', [(id,) for id in ids_to_delete])
                db.commit()
                print(f"Deleted the last {delete_count} records from {line_no}.")
            else:
                print("No records to delete.")
        else:
            print("No line_no found for this group ID.")
    return 'OK'




@app.route('/register', methods=['GET', 'POST'])
def register():
    auth_code = ""  
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        auth_code = request.form.get('auth_code', '') 

        if auth_code != "ReAO1Hos0m":
            flash('Invalid auth code')
            
        db = get_db()
        try:
            db.execute('INSERT INTO user (username, password_hash) VALUES (?, ?)', [username, password])  
            db.commit()
        except sqlite3.IntegrityError:
            flash('Username already taken. Please choose another one.')
            return render_template('register.html')

        return redirect(url_for('success'))
    else:
        return render_template('register.html')


@app.route('/')
def index():
    return render_template('sign.html')
    
@app.route('/submit-your-login-form', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM user WHERE username = ? AND password_hash = ?', (username, password))
    user = cursor.fetchone()
    if user:
        return redirect(url_for('main', a='a'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('index'))


@app.route('/settinguser')
def settinguser():
    db = get_db()
    cursor = db.execute('SELECT * FROM material')
    materials = cursor.fetchall()
    return render_template('settinguser.html', materials=materials)

@app.route('/index/<string:a>')
def main(a):
    return render_template('index.html')

@app.route('/success')
def success():
    flash('Registered successfully!')
    return redirect(url_for('index'))

@app.route('/add-employee', methods=['POST'])
def add_employee():
    db = get_db()
    data = request.get_json()
    notify = data['notify']
    name_line = data['name_line']
    key = generate_random_string()
    try:
        db.execute('INSERT INTO material (notify, name_line, line_no, line_id) VALUES (?, ?, ?, ?)', (notify, name_line, key, '?'))
        db.commit()
        return jsonify({"status": "success", "message": "Employee group added successfully."})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/materials')
def get_materials():
    query_parameters = request.args
    location = query_parameters.get('location')

    query = 'SELECT * FROM material'
    to_filter = []

    if location:
        query += ' WHERE location = ?'
        to_filter.append(location)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, to_filter)
    data = cursor.fetchall()

    results = [{'id':row[0], 'notify': row[1], 'name_line': row[2], 'key' : row[4], 'line_id' : row[3]} for row in data]
    return jsonify(results)

@app.route('/edit-material', methods=['POST'])
def edit_material():
    data = request.get_json()
    material_id = data['id']
    new_value = data['new_value']
    field = data['field']  

    db = get_db()
    cursor = db.cursor()
    if field == 'name_line':
        cursor.execute('UPDATE material SET name_line = ? WHERE id = ?', (new_value, material_id))
    elif field == 'notify':
        cursor.execute('UPDATE material SET notify = ? WHERE id = ?', (new_value, material_id))
    db.commit()
    
    return jsonify({"status": "success", "message": "Material updated successfully."})



@app.route('/delete-material', methods=['POST'])
def delete_material():
    data = request.get_json()
    material_id = data['id']
    
    db = get_db()
    db.execute('DELETE FROM material WHERE id = ?', (material_id,))
    db.commit()
    
    return jsonify({"status": "success", "message": "Material deleted successfully."})

@app.route('/settingkey')
def setkey():
    return render_template('settingkey.html')

@app.route('/add-keyword', methods=['POST'])
def add_keyword():
    data = request.get_json()  
    keyword = data.get('keyword')
    dollors = data.get('dollors')
    
    if not keyword or dollors is None:
        return jsonify({"status": "error", "message": "Missing keyword or dollors"}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO keyword (keyword, dollors) VALUES (?, ?)', (keyword, int(dollors)))
        db.commit()
        return jsonify({"status": "success", "message": "Keyword added successfully."})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid dollors value"}), 400


@app.route('/keywords')
def get_keywords():
    db = get_db()
    cursor = db.execute('SELECT id, keyword, dollors FROM keyword')
    keywords = cursor.fetchall()
    print(keywords)  
    return jsonify([{'id': row[0], 'keyword': row[1], 'dollors': row[2]} for row in keywords])


@app.route('/edit-keyword', methods=['POST'])
def edit_keyword():
    data = request.get_json()
    keyword_id = data['id']
    field = data['field']
    new_value = data['newValue']
    db = get_db()
    try:
        if field == 'keyword':
            db.execute('UPDATE keyword SET keyword = ? WHERE id = ?', (new_value, keyword_id))
        elif field == 'dollors':
            db.execute('UPDATE keyword SET dollors = ? WHERE id = ?', (new_value, keyword_id))
        db.commit()
        return jsonify({"status": "success", "message": "Keyword updated successfully."})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/delete-keyword', methods=['POST'])
def delete_keyword():
    data = request.get_json()
    keyword_id = data['id']
    db = get_db()
    try:
        db.execute('DELETE FROM keyword WHERE id = ?', (keyword_id,))
        db.commit()
        return jsonify({"status": "success", "message": "Keyword deleted successfully."})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/get-all-line-no')
def get_all_line_no():
    line_nos = fetch_all_line_no()
    return jsonify(line_nos)  


    
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5011))
    app.run(host='0.0.0.0', port=port)
