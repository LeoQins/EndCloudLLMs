
import requests
import json
import os
import shutil
api_key='W8KN00M-RVA45WX-PVN3WNV-ZWT8JG7'

#验证API密钥
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer ' + api_key,
#     'accept': 'application/json',
# }

# response = requests.get('http://localhost:3001/api/v1/auth', headers=headers)
# print(response.text)
# print(response.status_code)
# print(response.headers)


# #上传文件到文档存储目录
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer ' + api_key,
#     # requests won't add a boundary if this header is set when you pass files=
#     # 'Content-Type': 'multipart/form-data',
# }

# files = {
#     'file': open('./uploads/AAA.txt', 'rb'),
# }

# response = requests.post('http://localhost:3001/api/v1/document/upload', headers=headers, files=files)
# print(response.text)
# print(response.status_code)



# #创建新的工作区
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer '+api_key,
#     # Already added when you pass json= but not when you pass data=
#     # 'Content-Type': 'application/json',
# }

# json_data = {
#     'name': 'My New Workspace',
# }

# response = requests.post('http://localhost:3001/api/v1/workspace/new', headers=headers, json=json_data)
# print(response.status_code)

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{\n  "name": "My New Workspace"\n}'
#response = requests.post('http://服务器IP:3001/api/v1/workspace/new', headers=headers, data=data)


# #列出所有工作区
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer '+api_key
# }

# response = requests.get('http://localhost:3001/api/v1/workspaces', headers=headers)
# print(response.content)


# #文档存储目录中列表
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer '+api_key,
# }

# response = requests.get('http://localhost:3001/api/v1/documents', headers=headers)
# print(response.content)


# #更新工作区设置
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer '+api_key,
#     # Already added when you pass json= but not when you pass data=
#     # 'Content-Type': 'application/json',
# }

# json_data = {
#     'name': 'OOO',
#     'openAiTemp': 0.2,
#     'openAiHistory': 10,
#     'openAiPrompt': 'Respond to all inquires and questions in binary - do not respond in any other format.',
# }

# response = requests.post('http://localhost:3001/api/v1/workspace/oooo/update', headers=headers, json=json_data)
# print(response.content)


# #添加或删除文件到工作区
# headers = {
#     'accept': 'application/json',
#     'Authorization': 'Bearer '+api_key,
#     # Already added when you pass json= but not when you pass data=
#     # 'Content-Type': 'application/json',
# }
# json_data = {
#     'adds': [
#         'custom-documents/AAA.txt-2c410bc2-7f37-4ff1-85bf-5d93c8682a34.json',
#     ],
#     # 'deletes': [
#     #     'custom-documents/anythingllm.txt-hash.json',
#     # ],
# }

# response = requests.post('http://localhost:3001/api/v1/workspace/oooo/update-embeddings', headers=headers, json=json_data)
# print(response.status_code)
# print(response.content)



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


#清空uploads目录
def clear_uploads():
    if os.path.exists('./uploads'):
        shutil.rmtree('./uploads')  # 递归删除目录及内容
        os.makedirs('./uploads')    # 重建空目录
        print('已清空uploads目录')


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

#所有文件都传入工作区
def upload_workspace():
    wb1='wb1'
    wb2='wb2'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }

    response = requests.get('http://localhost:3001/api/v1/documents', headers=headers)
    data=response.json()
    filenames = extract_filenames(data['localFiles'])

    for filename in filenames:
        json_data = {
            'adds': [
                f'custom-documents/{filename}',
            ],
        }
        response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb1}/update-embeddings', headers=headers, json=json_data)
        response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb2}/update-embeddings', headers=headers, json=json_data)
        print(f"文件 {filename} 上传状态码: {response.status_code}上传到工作区{wb1}和{wb2}")

#所有文件从工作区删除
def delete_workspace():
    wb1='671b'
    wb2='7b'
    wb3='2b'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }

    response = requests.get('http://localhost:3001/api/v1/documents', headers=headers)
    data=response.json()
    filenames = extract_filenames(data['localFiles'])

    for filename in filenames:
        json_data = {
            'deletes': [
                f'custom-documents/{filename}',
            ],
        }
        response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb1}/update-embeddings', headers=headers, json=json_data)
        response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb2}/update-embeddings', headers=headers, json=json_data)
        response=requests.post(f'http://localhost:3001/api/v1/workspace/{wb3}/update-embeddings', headers=headers, json=json_data)
        print(f"文件 {filename} 上传状态码: {response.status_code}移除工作区{wb1}和{wb2}和{wb3}")

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


#默认对话窗口流式对话

def chat():
    wb1='671b'
    wb2='7b'
    wb3='2b'
    headers = {
        'accept': 'text/event-stream',
        'Authorization': 'Bearer '+api_key,
        'Content-Type': 'application/json',
    }
    json_data = {
        'message': 'Hello, how are you?',
        'mode': 'chat',
        'userId': 1,
    }

    resp = requests.post(f'http://localhost:3001/api/v1/workspace/{wb1}/stream-chat', headers=headers, json=json_data)
    
    
    for chunk in resp.iter_lines(chunk_size=None):
        if chunk:
            streamStr=chunk.decode("utf-8").replace("data: ", "")
            #print("[Decoded Stream]",streamStr)
            streamDict=json.loads(streamStr)
            respStr=streamDict.get("textResponse")
            print("[Response]",respStr)
            #yield respStr

    #return Response(generate(), content_type='text/event-stream')    
        



#特定工作区换成精心设计的提示词
def prompt_new(wb,prompt):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }
    json_data = {
        'openAiPrompt': prompt,
    }
    response = requests.post(f'http://localhost:3001/api/v1/workspace/{wb}/update', headers=headers, json=json_data)
    print(response.content)

#展示所有工作区和分支
def show_workspace():
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }
    response = requests.get('http://localhost:3001/api/v1/workspaces', headers=headers)
    return response.content

#添加新分支
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
#删除某分支
def delete_thread(wb,thread):
    headers = {
        'accept': '*/*',
        'Authorization': 'Bearer '+api_key,
    }

    response = requests.delete(f'http://localhost:3001/api/v1/workspace/{wb}/thread/{thread}', headers=headers)
    print(response.content)

# 删除则新建分支，不删除则保留对话。
#对话历史按钮扣下，默认开启


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

#寻找所有工作区的slug
def seek_workspace():
    # 原始数据（注意需要移除开头的 b' 和结尾的 '）
    data_str = show_workspace()  # 完整数据见问题描述

    # 转换为Python对象
    data = json.loads(data_str)

    # 提取所有工作区slug
    workspace_slugs = [ws["slug"] for ws in data["workspaces"]]
    return workspace_slugs
#展示文档存储目录所有文件
def show_ducutment():
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+api_key,
    }

    response = requests.get('http://localhost:3001/api/v1/documents', headers=headers)
    print(response.content)


#特定工作区，特定分支，流式对话
def chat_thread(wb,thread):
    headers = {
        'accept': 'text/event-stream',
        'Authorization': 'Bearer '+api_key,
    }

    json_data = {
        'message': '分享会什么时候开始?',
        'mode': 'chat',
        'userId': 1,
    }

    response = requests.post(f'http://locahost:3001/api/v1/workspace/{wb}/thread/{thread}/stream-chat', headers=headers, json=json_data)
    print(response.content)

if __name__ == '__main__':
    
    


  