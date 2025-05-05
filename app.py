# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, Response
from werkzeug.utils import secure_filename
import requests
import json
import os
import shutil # 用于删除文件夹
import subprocess
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import imaplib
import email
import threading
import time




api_key='W8KN00M-RVA45WX-PVN3WNV-ZWT8JG7'
#默认
MODE='chat'
WB='671b'
PROMPT='HI!AAAA'
NET='online'


#删除全部的文件
def delete_system_files():
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }
    response = requests.get('http://localhost:3001/api/v1/documents', headers=headers)
    data=response.json()
    filenames = extract_filenames(data['localFiles'])
    for filename in filenames:
        json_data = {
            'names': [
                f'custom-documents/{filename}',
            ],
        }
        response = requests.delete('http://localhost:3001/api/v1/system/remove-documents', headers=headers, json=json_data)
        print(f"文件 {filename} 删除状态码: {response.status_code}")

#提取文件名
def extract_filenames(data):
    result = []
    if isinstance(data, dict):
        if data.get('type') == 'file':
            result.append(data['name'])
        elif data.get('type') == 'folder':
            for item in data.get('items', []):
                result.extend(extract_filenames(item))
    elif isinstance(data, list):
        for item in data:
            result.extend(extract_filenames(item))
    return result
#上传uploads文件夹中所有文件到文档存储目录
def upload_all_files():
    upload_dir = './uploads'
    url = 'http://localhost:3001/api/v1/document/upload'  # 替换为实际API地址
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + api_key,
        # requests won't add a boundary if this header is set when you pass files=
        # 'Content-Type': 'multipart/form-data',
    }
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):  # 确保是文件而非子目录
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(url, headers=headers, files=files)
                print(f"文件 {filename} 上传状态码: {response.status_code}")

#所有文件都传入工作区完成嵌入
def upload_workspace():
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }

    response = requests.get('http://localhost:3001/api/v1/documents', headers=headers)
    data=response.json()
    filenames = extract_filenames(data['localFiles'])
    wb_slugs=seek_workspace()

    for filename in filenames:
        json_data = {
            'adds': [
                f'custom-documents/{filename}',
            ],
        }
        for wb in wb_slugs:
            response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb}/update-embeddings', headers=headers, json=json_data)
            print(f"文件 {filename} 上传状态码: {response.status_code}上传到工作区{wb}")
        
app = Flask(__name__)

# 从配置文件中settings加载配置
app.config.from_pyfile('settings.py')


def add_thread(wb):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }

    json_data = {
        'userId': 1,
    }

    response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb}/thread/new', headers=headers, json=json_data)
    print(response.content)


def send_email(sender, sender_password, receiver, subject, body, smtp_server, smtp_port):#发送邮箱函数
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver

    server = None 
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() 
        server.login(sender, sender_password)
        server.sendmail(sender, [receiver], msg.as_string())
        print('邮件发送成功')
    except Exception as e:
        print('邮件发送失败:', e)
    finally:
        if server:
            server.quit()

def sending():#发送邮件
    # 从环境变量中获取敏感信息
    sender = os.environ.get('SENDER_EMAIL')  # 在环境变量中设置发件人邮箱
    sender_password = os.environ.get('SENDER_PASSWORD')  # 在环境变量中设置邮箱密码或应用专用密码

    if not sender or not sender_password:
        print("错误：请设置环境变量 SENDER_EMAIL 和 SENDER_PASSWORD。")
        sys.exit(1)

    # 其它邮件参数
    receiver = '1364075575@qq.com'
    subject = '端云协同大模型智能平台'
    body = '有人在使用端云协同大模型智能平台，请及时查看！'
    smtp_server = 'mails.qust.edu.cn'
    smtp_port = 25
    send_email(sender, sender_password, receiver, subject, body, smtp_server, smtp_port)
    #receiver2='2386429425@qq.com'
    #send_email(sender, sender_password, receiver2, subject, body, smtp_server, smtp_port)


def funccmd():
    # 捕获输出
    subprocess.run(["docker", "start", "admiring_engelbart"])#启动容器
    sending()
@app.route("/", methods=["GET"])
def index():
    funccmd()
    return render_template("chat.html")
#展示所有工作区和分支
def show_workspace():
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }
    response = requests.get('http://localhost:3001/api/v1/workspaces', headers=headers)
    return response.content

#寻找所有工作区的slug
def seek_workspace():
    # 原始数据（注意需要移除开头的 b' 和结尾的 '）
    data_str = show_workspace()  # 完整数据见问题描述

    # 转换为Python对象
    data = json.loads(data_str)

    # 提取所有工作区slug
    workspace_slugs = [ws["slug"] for ws in data["workspaces"]]
    return workspace_slugs

#寻找特定工作区分支的slug
def seek_thread(wb):
    # 原始数据（已处理字节字符串）
    data_str =show_workspace()   # 完整数据见问题描述
    
    # 解析JSON
    data = json.loads(data_str)

    # 定义目标workspace的slug列表
    target_slugs = {wb}  # 注意这是workspace的slug，不是thread的

    # 提取特定workspace下的thread slugs
    result = {}
    for workspace in data['workspaces']:
        if workspace.get('slug') in target_slugs:
            workspace_slug = workspace['slug']
            result[workspace_slug] = [
                thread['slug'] 
                for thread in workspace.get('threads', []) 
                if 'slug' in thread
            ]

    print("特定workspace下的thread slugs：")
    for ws_slug, slugs in result.items():
        print(f"\nWorkspace '{ws_slug}':")
        print("\n".join(slugs) if slugs else "（无threads）")
        return slugs[0]

def switch1():
    MODE=''
    WB=''
    PROMPT=''

def switch2():
    MODE=''
    WB=''
    PROMPT=''
def switch3():
    MODE=''
    WB=''
    PROMPT=''

def switch4():    
    MODE=''
    WB=''
    PROMPT=''

def switch4():    
    MODE=''
    WB=''
    PROMPT=''

#切换提示词
def promt_new(wb,prompt):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }
    json_data = {
        'openAiPrompt': prompt,
    }
    response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb}/update', headers=headers, json=json_data)
@app.route("/chatmode", methods=["POST"])
def chatmode():
    global MODE
    try:
        MODE='chat'
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route("/querymode", methods=["POST"])
def querymode():
    global MODE
    try:
        MODE='query'
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route("/chat", methods=["POST"])
def chat():
    global MODE
    global WB
    global PROMPT
    global NET
    global api_key
    wb=WB
    mode=MODE
    messages = request.form.get("prompts", None)
    apiKey = request.form.get("apiKey", 'W8KN00M-RVA45WX-PVN3WNV-ZWT8JG7')
    api_key=apiKey
    apiUrl = request.form.get("apiUrl", 'www.deepseek.com')
    model = request.form.get("model", "Auto")
    print(apiKey)
    #提示词
    tem="Given the following conversation, " \
    "relevant context, and a follow up question, " \
    "reply with an answer to the current question the user is asking. " \
    "Return only your response to the question given the above information following the users instructions as needed."
    if (model == "Auto"):
        if(NET=='online'):
            WB='672b'
            promt_new(WB,tem)
        elif(NET=='offline'):
            WB='7b'
            promt_new(WB,tem)
            NET='online'
    elif(model=='NetTurbo'):
        WB='671b'
        promt_new(WB,tem)
    elif(model=='Std'):
        WB='7b'
        promt_new(WB,tem)
    elif(model=='LocalTurbo'):
        WB='2b'
        promt_new(WB,tem)
    elif(model=='SOTA'):
        #需要修改提示词
        WB='671b'
        tem1="Act as a meticulous editor and critical thinker. Analyze the user-provided content (message/document) thoroughly. Follow these steps: \
Error Identification: Check for grammatical, factual, logical, or structural inconsistencies. Highlight ambiguities, redundancies, or unclear phrasing.\
Context Alignment: Assess if the content aligns with its intended purpose (e.g., informational, persuasive, technical). Identify mismatches between context and execution.\
Optimization Framework:\
Clarity: Simplify complex sentences. Replace jargon with accessible terms if needed.\
Accuracy: Verify data/claims against reliable sources (if applicable). Flag unsupported assertions.\
Coherence: Improve flow between ideas using transitional phrases or reordering.\
Impact: Suggest stronger vocabulary, rhetorical devices, or visual aids (e.g., bullet points).\
User-Centric Adjustments: Propose revisions tailored to the target audience’s needs (e.g., formality, cultural sensitivity).\
Alternative Solutions: Offer 1-2 improved versions of critical sections, explaining why they enhance the original.\
Final Summary: Provide a concise report of key issues and optimization strategies.\
Always maintain the original intent while elevating quality.\
"
        promt_new(WB,tem1)
    elif(model=='V3'):
        WB='672b'
        promt_new(WB,tem)
    wb=WB
    if messages is None:
        return jsonify({"error": {"message": "请输入prompts！", "type": "invalid_request_error", "code": ""}})

    # 依次从环境变量、配置文件获取key和代理url
    if apiKey is None:
        apiKey = os.environ.get('OPENAI_API_KEY', app.config["OPENAI_API_KEY"])

    if apiUrl is None:
        apiUrl = os.environ.get("OPENAI_API_URL", app.config["URL"])

    prompts = json.loads(messages)
############################################################################################################
#对接docker
    headers = {
        'accept': 'text/event-stream',
        'Authorization': 'Bearer '+api_key,
        'Content-Type': 'application/json'
    }
    content=prompts[0]['content']
    #str=content.encode('utf-8')
   # print(str)
    data={
        'message':content,
        'mode':mode,
        'userId': 1,
    }
    thread=seek_thread(wb)
    resp = requests.post(f'http://localhost:3001/api/v1/workspace/{wb}/thread/{thread}/stream-chat', headers=headers, json=data,stream=True)
    #迭代器实现流式响应
    def generate():
        
        for chunk in resp.iter_lines():
            print(chunk)
            if chunk:
                streamStr=chunk.decode("utf-8").replace("data: ", "")
                print("[Decoded Stream]",streamStr)
                streamDict=json.loads(streamStr)
                respStr = streamDict.get("textResponse", "")  # 默认空字符串
                if(respStr=="<think>"):
                    yield respStr.encode("utf-8")+b'\n\n'
                elif (respStr=="</think>"):
                    yield respStr.encode("utf-8")+b'\n\n'
                else:
                    yield respStr.encode("utf-8")
                print("数据块:"+respStr)
    return Response(generate(), content_type='text/event-stream')

    
#新上传文件代码
app.config['UPLOAD_FOLDER'] = './uploads'  # 存储目录[3](@ref)
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024  # 限制128MB[3](@ref)

# 创建上传目录
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '空文件名'}), 400
    
    try:
        # 获取原始文件名并安全处理
        raw_filename = file.filename
        
        # 安全过滤（代替secure_filename）
        filename = os.path.basename(raw_filename)  # 移除路径信息
        filename = filename.replace(' ', '_')  # 替换空格[可选]
        
        # 防止特殊字符
        if any(c in filename for c in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']):
            return jsonify({'error': '文件名包含非法字符'}), 400
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(save_path)
        return jsonify({
            'message': '上传成功',
            'original_filename': raw_filename,
            'saved_filename': filename,
            'path': save_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#删除分支，同时新建分支    
@app.route('/delete', methods=['POST'])
def delete_thread():
    wb=WB
    thread=seek_thread(wb)
    try:
        headers = {
            'accept': '*/*',
            'Authorization': 'Bearer '+api_key,
        }
        response = requests.delete(f'http://localhost:3001/api/v1/workspace/{wb}/thread/{thread}', headers=headers)
        add_thread(wb)
        print(response.content)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

#监听网络延迟
@app.route('/network', methods=['POST'])
def network_offline():
    try:
        global NET
        NET='offline'
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# 新增文件列表接口
@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        files = []
        upload_dir = app.config['UPLOAD_FOLDER']= './uploads'
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            files.append({
                "name": filename,
                "size": os.path.getsize(file_path),
                "type": "file" if os.path.isfile(file_path) else "folder"
            })
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增文件删除接口
@app.route('/delete_file', methods=['POST'])
def delete_file():
    try:
        data = request.json
        filename = data['filename']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "文件不存在"}), 404
            
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            shutil.rmtree(file_path)
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


#刷新按钮触发清空工作区和文档存储目录，再重新上传到文档存储目录和工作区
@app.route('/refresh', methods=['POST'])
def refresh():
    delete_system_files()
    upload_all_files()
    upload_workspace()
    return jsonify({'status': 'success'})


def restart_action():
    print("60分钟已到，执行重启前操作...")
    # 在此处添加你需要执行的操作，比如调用funccmd()或其它函数
    # funccmd()
    subprocess.run(["docker", "stop", "admiring_engelbart"])#关闭容器

def scheduled_restart():

    interval = 3600  # 设置间隔时间，单位为秒；实际场景下可改为3600秒
    while True:
        time.sleep(interval)
        restart_action()


    # 重启当前 Python 程序
    # python = sys.executable
    # os.execl(python, python, *sys.argv)

if __name__ == '__main__':
     # 启动定时关闭docker
    restart_thread = threading.Thread(target=scheduled_restart, daemon=True)
    restart_thread.start()
    app.run(port=5000, debug=False)

#小小测试