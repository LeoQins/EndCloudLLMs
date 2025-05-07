// 功能
$(document).ready(function() {
  var chatBtn = $('#chatBtn');
  var chatInput = $('#chatInput');
  var chatWindow = $('#chatWindow');
  
  // 全局变量,存储对话信息
  var messages = [];

  // 创建自定义渲染器
  const renderer = new marked.Renderer();

  // 重写list方法
  renderer.list = function(body, ordered, start) {
    const type = ordered ? 'ol' : 'ul';
    const startAttr = (ordered && start) ? ` start="${start}"` : '';
    return `<${type}${startAttr}>\n${body}</${type}>\n`;
  };

  // 设置marked选项
  marked.setOptions({
    renderer: renderer,
    highlight: function (code, language) {
      const validLanguage = hljs.getLanguage(language) ? language : 'javascript';
      return hljs.highlight(code, { language: validLanguage }).value;
    }
  });

  // 转义html代码(对应字符转移为html实体)，防止在浏览器渲染
  function escapeHtml(html) {
    let text = document.createTextNode(html);
    let div = document.createElement('div');
    div.appendChild(text);
    return div.innerHTML;
  }

  
  // 添加请求消息到窗口
  function addRequestMessage(message) {
    $(".answer .tips").css({"display":"none"});    // 打赏卡隐藏
    chatInput.val('');
    let escapedMessage = escapeHtml(message);  // 对请求message进行转义，防止输入的是html而被浏览器渲染
    let requestMessageElement = $('<div class="message-bubble"><span class="chat-icon request-icon"></span><div class="message-text request"><p>' +  escapedMessage + '</p></div></div>');
    chatWindow.append(requestMessageElement);
    let responseMessageElement = $('<div class="message-bubble"><span class="chat-icon response-icon"></span><div class="message-text response"><span class="loading-icon"><i class="fa fa-spinner fa-pulse fa-2x"></i></span></div></div>');
    chatWindow.append(responseMessageElement);
    chatWindow.scrollTop(chatWindow.prop('scrollHeight'));
  }
  

  // 添加响应消息到窗口,流式响应此方法会执行多次
  function addResponseMessage(message) {
    let lastResponseElement = $(".message-bubble .response").last();
    lastResponseElement.empty();
    if ($(".answer .others .center").css("display") === "none") {
      $(".answer .others .center").css("display", "flex");
    }
    let escapedMessage;
    // 处理流式消息中的代码块
    let codeMarkCount = 0;
    let index = message.indexOf('```');
    while (index !== -1) {
      codeMarkCount ++ ;
      index = message.indexOf('```', index + 3);
    }
    if(codeMarkCount % 2 == 1  ){  // 有未闭合的 code
      escapedMessage = marked.parse(message + '\n\n```'); 
    }else if(codeMarkCount % 2 == 0 && codeMarkCount != 0){
      escapedMessage = marked.parse(message);  // 响应消息markdown实时转换为html
    }else if(codeMarkCount == 0){  // 输出的代码没有markdown代码块
      if (message.includes('`')){
        escapedMessage = marked.parse(message);  // 没有markdown代码块，但有代码段，依旧是markdown格式
      }else{
        escapedMessage = marked.parse(escapeHtml(message)); // 有可能不是markdown格式，都用escapeHtml处理后再转换，防止非markdown格式html紊乱页面
      }
    }
    lastResponseElement.append(escapedMessage);
    chatWindow.scrollTop(chatWindow.prop('scrollHeight'));
  }

  // 添加失败信息到窗口
  function addFailMessage(message) {
    let lastResponseElement = $(".message-bubble .response").last();
    lastResponseElement.empty();
    lastResponseElement.append('<p class="error">' + message + '</p>');
    chatWindow.scrollTop(chatWindow.prop('scrollHeight'));
    messages.pop() // 失败就让用户输入信息从数组删除
  }

  // 定义一个变量保存ajax请求对象
  let ajaxRequest = null;
  
  // 处理用户输入
  chatBtn.click(function() {
    // 解绑键盘事件
    chatInput.off("keydown",handleEnter);
    
    // ajax上传数据
    let data = {};
    data.model = $(".settings-common .model").val();

    // 判断消息是否是正常的标志变量
    let resFlag = true;

    // 判断是否使用中转代理api
    let apiUrl = localStorage.getItem('apiUrl');
    if (apiUrl){
      data.apiUrl = apiUrl;
    }
   
    // 判断是否使用自己的api key
    let apiKey = localStorage.getItem('apiKey');
    if (apiKey){
      data.apiKey = apiKey;
    }

    // 接收输入信息变量
    let message = chatInput.val();
    if (message.length == 0){
      // 重新绑定键盘事件
      chatInput.on("keydown",handleEnter);
      return ;
    }

    addRequestMessage(message);
    // 将用户消息保存到数组
    messages.push({"role": "user", "content": message})
    // 收到回复前让按钮不可点击
    chatBtn.attr('disabled',true)

    if(messages.length>40){
      addFailMessage("此次对话长度过长，请点击下方删除按钮清除对话内容！");
      // 重新绑定键盘事件
      chatInput.on("keydown",handleEnter);
      chatBtn.attr('disabled',false) // 让按钮可点击
      return ;
    }
    
    // 判读是否已开启连续对话
    data.prompts = messages.slice();  // 拷贝一份全局messages赋值给data.prompts,然后对data.prompts处理
    if(localStorage.getItem('continuousDialogue') == 'true'){
    }else{
      //后端操作
      $.ajax({
        url: '/delete',
        method: 'POST',
        success: function() {
            console.log('服务器数据已清除');
        },
        error: function(xhr) {
            console.error('删除失败:', xhr.responseText);
        }
      });
    }
    data.prompts.splice(0, data.prompts.length - 1); //取最后一条
    data.prompts = JSON.stringify(data.prompts);
    
    let res;
    // 发送信息到后台
    ajaxRequest = $.ajax({
      url: '/chat',
      method: 'POST',
      data: data,
      xhrFields: {
        onprogress: function(e) {
          res = e.target.responseText;//获取回复信息
          let resJsonObj;
          try{
            resJsonObj = JSON.parse(res);  // 只有错误信息是json类型字符串,且一次返回
            if(resJsonObj.hasOwnProperty("error")){
              addFailMessage(resJsonObj.error.type + " : " + resJsonObj.error.message + " " + resJsonObj.error.code);
              resFlag = false;
            }else{
              addResponseMessage(res);
            }
          }catch(e){
            addResponseMessage(res);
          }
        }
      },
      success:function(result){
        // 判断是否是回复正确信息
        if(resFlag){
          messages.push({"role": "assistant", "content": result});
          // 判断是否本地存储历史会话
          if(localStorage.getItem('archiveSession')=="true"){
            localStorage.setItem("session",JSON.stringify(messages));
          }
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        if (textStatus === 'abort') {
          messages.push({"role": "assistant", "content": res});
          if(localStorage.getItem('archiveSession')=="true"){
            localStorage.setItem("session",JSON.stringify(messages));
          }
        } else {
          addFailMessage('出错啦！请稍后再试!');
        }
      },
      complete : function(XMLHttpRequest,status){
        // 收到回复，让按钮可点击
        chatBtn.attr('disabled',false)
        // 重新绑定键盘事件
        chatInput.on("keydown",handleEnter); 
        ajaxRequest = null;
        $(".answer .others .center").css("display","none");
        // 添加复制
        copy();
      }
    });
  });

  // 停止输出
  $('.stop a').click(function() {
    if(ajaxRequest){
      ajaxRequest.abort();
    }
  })

  // Enter键盘事件
  function handleEnter(e){
    if (e.keyCode==13){
      chatBtn.click();
      e.preventDefault();  //避免回车换行
    }
  }

  // 绑定Enter键盘事件
  chatInput.on("keydown",handleEnter);

  // 设置栏宽度自适应
  let width = $('.function .others').width();
  $('.function .settings .dropdown-menu').css('width', width);
  
  $(window).resize(function() {
    width = $('.function .others').width();
    $('.function .settings .dropdown-menu').css('width', width);
  });

  
  // 主题
  function setBgColor(theme){
    $(':root').attr('bg-theme', theme);
    $('.settings-common .theme').val(theme);
    // 定位在文档外的元素也同步主题色
    $('.settings-common').css('background-color', 'var(--bg-color)');
  }
  
  let theme = localStorage.getItem('theme');
  // 如果之前选择了主题，则将其应用到网站中
  if (theme) {
    setBgColor(theme);
  }else{
    localStorage.setItem('theme', "light"); //默认的主题
    theme = localStorage.getItem('theme');
    setBgColor(theme);
  }

  // 监听主题选择的变化
  $('.settings-common .theme').change(function() {
    const selectedTheme = $(this).val();
    localStorage.setItem('theme', selectedTheme);
    $(':root').attr('bg-theme', selectedTheme);
    // 定位在文档外的元素也同步主题色
    $('.settings-common').css('background-color', 'var(--bg-color)');
  });

  // 读取模型配置
  const model = localStorage.getItem('model');
  if (model) {
    $(".settings-common .model").val(model);
  }

  // 监听模型选择的变化
  $('.settings-common .model').change(function() {
    const model = $(this).val();
    localStorage.setItem('model', model);
    //模型切换需要清除历史对话，删除和新建分支
    $.ajax({
      url: '/delete',
      method: 'POST',
      success: function() {
          console.log('服务器数据已清除');
      },
      error: function(xhr) {
          console.error('删除失败:', xhr.responseText);
      }
    });
  });

  // 读取apiUrl
  const apiUrl = localStorage.getItem('apiUrl');
  if (apiUrl) {
    $(".settings-common .api-url").val(apiUrl);
  }

  // apiUrl输入框事件
  $(".settings-common .api-url").blur(function() {
    const apiUrl = $(this).val();
    if(apiUrl.length!=0){
      localStorage.setItem('apiUrl', apiUrl);
    }else{
      localStorage.removeItem('apiUrl');
    }
  })


  // 读取apiKey
  const apiKey = localStorage.getItem('apiKey');
  if (apiKey) {
    $(".settings-common .api-key").val(apiKey);
  }

  // apiKey输入框事件
  $(".settings-common .api-key").blur(function() { 
    const apiKey = $(this).val();
    if(apiKey.length!=0){
      localStorage.setItem('apiKey', apiKey);
    }else{
      localStorage.removeItem('apiKey');
    }
  })

  // 是否保存历史对话
  var archiveSession = localStorage.getItem('archiveSession');

  // 初始化archiveSession
  if(archiveSession == null){
    archiveSession = "false";
    localStorage.setItem('archiveSession', archiveSession);
  }
  
  if(archiveSession == "true"){
    $("#chck-1").prop("checked", true);
  }else{
    $("#chck-1").prop("checked", false);
  }

  $('#chck-1').click(function() {
    if ($(this).prop('checked')) {
      // 开启状态的操作
      localStorage.setItem('archiveSession', true);
      if(messages.length != 0){
        localStorage.setItem("session",JSON.stringify(messages));
      }
    } else {
      // 关闭状态的操作
      localStorage.setItem('archiveSession', false);
      localStorage.removeItem("session");
    }
  });
  
  // 加载历史保存会话
  if(archiveSession == "true"){
    const messagesList = JSON.parse(localStorage.getItem("session"));
    if(messagesList){
      messages = messagesList;
      $.each(messages, function(index, item) {
        if (item.role === 'user') {
          addRequestMessage(item.content)
        } else if (item.role === 'assistant') {
          addResponseMessage(item.content)
        }
      });
      $(".answer .others .center").css("display", "none");
      // 添加复制
      copy();
    }
  }

  // 是否连续对话
  var continuousDialogue = localStorage.getItem('continuousDialogue');

  // 初始化continuousDialogue
  if(continuousDialogue == null){
    continuousDialogue = "true";
    localStorage.setItem('continuousDialogue', continuousDialogue);
  }
  
  if(continuousDialogue == "true"){
    $("#chck-2").prop("checked", true);
  }else{
    $("#chck-2").prop("checked", false);
  }

  $('#chck-2').click(function() {
    if ($(this).prop('checked')) {
       localStorage.setItem('continuousDialogue', true);
    } else {
       localStorage.setItem('continuousDialogue', false);
    }
  });

  // 删除功能
  $(".delete a").click(function(){
    //后端操作
    $.ajax({
      url: '/delete',
      method: 'POST',
      success: function() {
          console.log('服务器数据已清除');
      },
      error: function(xhr) {
          console.error('删除失败:', xhr.responseText);
      }
    });



    //前端操作
    chatWindow.empty();
    $(".answer .tips").css({"display":"flex"});
    messages = [];
    localStorage.removeItem("session");
  });

  // 截图功能
  $(".screenshot a").click(function() {
    // 创建副本元素
    const clonedChatWindow = chatWindow.clone();
    clonedChatWindow.css({
      position: "absolute",
      left: "-9999px",
      overflow: "visible",
      width: chatWindow.width(),
      height: "auto"
    });
    $("body").append(clonedChatWindow);
    // 截图
    html2canvas(clonedChatWindow[0], {
      allowTaint: false,
      useCORS: true,
      scrollY: 0,
    }).then(function(canvas) {
      // 将 canvas 转换成图片
      const imgData = canvas.toDataURL('image/png');
      // 创建下载链接
      const link = document.createElement('a');
      link.download = "screenshot_" + Math.floor(Date.now() / 1000) + ".png";
      link.href = imgData;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      clonedChatWindow.remove();
    });
  });

  // 复制代码功能
  function copy(){
    $('pre').each(function() {
      let btn = $('<button class="copy-btn">复制</button>');
      $(this).append(btn);
      btn.hide();
    });

    $('pre').hover(
      function() {
        $(this).find('.copy-btn').show();
      },
      function() {
        $(this).find('.copy-btn').hide();
      }
    );

    $('pre').on('click', '.copy-btn', function() {
      let text = $(this).siblings('code').text();
      // 创建一个临时的 textarea 元素
      let textArea = document.createElement("textarea");
      textArea.value = text;
      document.body.appendChild(textArea);

      // 选择 textarea 中的文本
      textArea.select();

      // 执行复制命令
      try {
        document.execCommand('copy');
        $(this).text('复制成功');
      } catch (e) {
        $(this).text('复制失败');
      }

      // 从文档中删除临时的 textarea 元素
      document.body.removeChild(textArea);

      setTimeout(() => {
        $(this).text('复制');
      }, 2000);
    });
  }



  //添加文件知识库上传功能
  // 在原有$(document).ready内添加以下代码

// 文件上传容器
const uploadPanel = $('.upload-panel');
const fileList = $('.file-list');

// 初始化上传事件
$('#multiUpload').on('change', handleFileSelect);
uploadPanel.on('dragover', handleDragOver);
uploadPanel.on('drop', handleFileDrop);

// 文件选择处理
function handleFileSelect(e) {
  processFiles(e.target.files);
}

// 拖拽处理
function handleDragOver(e) {
  e.preventDefault();
  uploadPanel.addClass('dragover');
}

function handleFileDrop(e) {
  e.preventDefault();
  uploadPanel.removeClass('dragover');
  processFiles(e.originalEvent.dataTransfer.files);
}

// 核心处理函数
function processFiles(files) {
  Array.from(files).forEach(file => {
    // 显示文件名
    const fileItem = $(`
      <div class="file-item">
        <span>${file.name}</span>
        <div class="progress-bar"></div>
      </div>
    `);
    fileList.append(fileItem);
    
    // 上传文件
    uploadFile(file, fileItem);
  });
}

// 文件上传逻辑（需调整的AJAX配置）
function uploadFile(file, container) {
  const formData = new FormData();
  formData.append('file', file);  // 修改参数名为单数[3](@ref)

  $.ajax({
    //url: 'http://127.0.0.1:5000/upload', // 明确后端地址[3,4](@ref)
    url: 'https://2maar3390283.vicp.fun:443/upload', // 明确后端地址[3,4](@ref)
    type: 'POST',
    data: formData,
    processData: false,
    contentType: false,
    xhr: function() {
      const xhr = new XMLHttpRequest();
      xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
          const percent = (e.loaded / e.total) * 100;
          container.find('.progress-bar').css('width', percent + '%');
        }
      }, false);
      return xhr;
    },
    success: function(response) {
      container.addClass('success');
      console.log('服务器响应:', response); // 添加响应日志[3](@ref)
    },
    error: function(xhr) {
      console.error('错误详情:', xhr.responseText); // 显示详细错误[4](@ref)
      container.addClass('error').find('span').append(' (失败: '+xhr.status+')');
    }
  });
}

// 文件列表加载函数
function loadFileList() {
  $.ajax({
    url: '/list_files',
    method: 'GET',
    success: function(files) {
      const fileList = $('#serverFileList');
      fileList.empty();
      
      files.forEach(file => {
        const item = $(`
          <div class="file-item">
            <div class="file-info">
              <i class="fa ${file.type === 'file' ? 'fa-file' : 'fa-folder'} file-type-icon"></i>
              <span class="file-name">${file.name}</span>
              <span class="file-size">${(file.size/1024).toFixed(1)}KB</span>
            </div>
            <div class="file-actions">
              <button class="btn btn-danger btn-sm delete-file" 
                data-filename="${file.name}">
                <i class="fa fa-trash"></i>
              </button>
            </div>
          </div>
        `);
        fileList.append(item);
      });
    }
  });
}


// 初始化加载文件列表
$(document).ready(function() {
  loadFileList();
  
  // 删除文件事件
  $(document).on('click', '.delete-file', function() {
    const filename = $(this).data('filename');
    if(confirm(`确认删除 ${filename} 吗？`)) {
      $.ajax({
        url: '/delete_file',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ filename }),
        success: () => {
          loadFileList(); // 刷新列表
          showToast('文件删除成功', 'success');
          
        },
        error: (xhr) => {
          showToast(`删除失败: ${xhr.responseJSON.error}`, 'error');
        }
      });
    }
  });

  // 刷新按钮事件
  $('#refreshFiles').click(function() {
    loadFileList();
    $.ajax({
        url: '/refresh',        // 请求地址
        type: 'POST',           // 请求方法
        contentType: 'application/json', // 声明数据格式（可选，见下文说明）
        success: function(response) {
            console.log('刷新成功:', response.status);
            // 可在此处更新页面状态，例如显示成功提示
            alert('系统文件已更新！');
        },
        error: function(xhr, status, error) {
            console.error('刷新失败:', error);
            alert('刷新失败，请检查网络或日志');
        }
    });
  });



});

// Toast提示函数
function showToast(message, type = 'info') {
  const toast = $(`<div class="toast ${type}">${message}</div>`);
  $('body').append(toast);
  setTimeout(() => toast.remove(), 3000);
}



// 网络延迟检测（网页6、7的优化实现）
let latencyCheckInterval;
let isQueryMode = false;

// 初始化模式切换
$('#modeToggle').prop('checked', isQueryMode);

// 模式切换事件
$('#modeToggle').change(function() {
  isQueryMode = this.checked;
  if(isQueryMode) {
    $('#chatInput').attr('placeholder', '查询模式：输入问题获取原始数据').addClass('query-mode');
    $('#chatBtn').text('查询').addClass('btn-info').removeClass('btn-primary');
    //后端操作
    $.ajax({
      url: '/querymode',
      method: 'POST',
      success: function() {
          console.log('聊天模式成功');
      },
      error: function(xhr) {
          console.error('聊天模式成功失败:', xhr.responseText);
      }
    });
  } else {
    $('#chatInput').attr('placeholder', '').removeClass('query-mode');
    $('#chatBtn').text('发送').addClass('btn-primary').removeClass('btn-info');
    //后端操作
    $.ajax({
      url: '/chatmode',
      method: 'POST',
      success: function() {
          console.log('查询模式成功成功');
      },
      error: function(xhr) {
          console.error('查询模式失败失败:', xhr.responseText);
      }
    });
  }
});

// 网络延迟检测函数（优化版）
function checkNetworkLatency() {
  const checkStart = Date.now();
  const testURL = 'https://www.gstatic.com/generate_204'; // Google空请求地址
  
  fetch(testURL, { mode: 'no-cors', cache: 'no-store' })
    .then(() => {
      const latency = Date.now() - checkStart;
      updateDelayDisplay(latency);
    })
    .catch(() => {
      updateDelayDisplay(9999); // 网络不可用
    });
}

// 更新延迟显示（参考网页6颜色逻辑）
function updateDelayDisplay(latency) {
  const delayElement = $('#networkDelay');
  // delayElement.text(`延迟: ${latency === 9999 ? '离线' : latency} ms`);
  if (latency === 9999) {
    delayElement.text("延迟: 离线 ms"); // 更新文本
                        // 执行离线函数
    //后端操作
    $.ajax({
      url: '/network',
      method: 'POST',
      success: function() {
          console.log('网络监听成功');
      },
      error: function(xhr) {
          console.error('网络监听失败:', xhr.responseText);
      }
    });

  } else {
    delayElement.text(`延迟: ${latency} ms`);
  }
  
  // 颜色分级（参考网页6）
  if(latency < 100) {
    delayElement.css('color', '#4CAF50');
  } else if(latency < 300) {
    delayElement.css('color', '#FFC107');
  } else {
    delayElement.css('color', '#F44336');
  }
}

// 启动延迟检测（每5秒检测一次）
function startLatencyCheck() {
  checkNetworkLatency();
  latencyCheckInterval = setInterval(checkNetworkLatency, 5000);
}

// 停止检测（当页面隐藏时）
document.addEventListener('visibilitychange', () => {
  if(document.hidden) {
    clearInterval(latencyCheckInterval);
  } else {
    startLatencyCheck();
  }
});

// 初始化检测
startLatencyCheck();

// 修改现有发送逻辑（在chatBtn.click事件顶部添加）
if(isQueryMode) {
  // 查询模式下的特殊处理
  data.queryMode = true;
  data.maxTokens = 500; // 限制响应长度
}




});
