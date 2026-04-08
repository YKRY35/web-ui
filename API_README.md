# Backend API 说明

## 后端服务启动方式

### 方式一：使用新的 FastAPI 后端（推荐用于与 Vue 前端配合）

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动后端服务
python backend_api.py
```

服务地址：http://127.0.0.1:7788

### 方式二：使用原有的 Gradio 后端

```bash
python webui.py
```

服务地址：http://127.0.0.1:7788

## API 接口文档

### 配置管理

#### 加载配置
- **接口**: `POST /api/load-config`
- **Content-Type**: `multipart/form-data`
- **参数**: `file` (JSON 文件)
- **返回**:
  ```json
  {
    "success": true,
    "message": "Successfully loaded config: xxx.json",
    "config": { ... }
  }
  ```

#### 保存配置
- **接口**: `GET /api/save-config`
- **返回**:
  ```json
  {
    "success": true,
    "message": "UI settings saved successfully",
    "filename": "20240408-123456.json",
    "path": "./tmp/webui_settings/20240408-123456.json"
  }
  ```

### 代理设置

#### 获取代理设置
- **接口**: `GET /api/agent-settings`
- **返回**:
  ```json
  {
    "success": true,
    "settings": {
      "llm_provider": "openai",
      "llm_model_name": "gpt-4",
      ...
    }
  }
  ```

#### 更新代理设置
- **接口**: `POST /api/agent-settings`
- **Content-Type**: `application/json`
- **参数**:
  ```json
  {
    "llm_provider": "openai",
    "llm_model_name": "gpt-4",
    "llm_temperature": 0.6,
    "use_vision": true,
    ...
  }
  ```

### 浏览器设置

#### 获取浏览器设置
- **接口**: `GET /api/browser-settings`

#### 更新浏览器设置
- **接口**: `POST /api/browser-settings`

### 浏览器使用代理

#### 运行代理
- **接口**: `POST /api/agent/run`
- **参数**:
  ```json
  {
    "task": "用户的任务描述"
  }
  ```

#### 停止代理
- **接口**: `POST /api/agent/stop`
- **参数**: `task_id` (form-data)

#### 暂停/恢复代理
- **接口**: `POST /api/agent/pause`
- **接口**: `POST /api/agent/resume`
- **参数**: `task_id` (form-data)

#### 获取代理状态
- **接口**: `GET /api/agent/status?task_id=xxx`

#### 发送用户响应
- **接口**: `POST /api/agent/respond`
- **参数**: `task_id` 和 `message` (form-data)

### 深度研究代理

#### 运行研究
- **接口**: `POST /api/deep-research/run`
- **参数**:
  ```json
  {
    "topic": "研究主题",
    "parallel_num": 1,
    "save_dir": "./tmp/deep_research"
  }
  ```

#### 停止研究
- **接口**: `POST /api/deep-research/stop`

#### 获取研究报告
- **接口**: `GET /api/deep-research/report?task_id=xxx`

## 前端配置

前端需要配置环境变量文件 `.env.development` 和 `.env.production`：

```bash
VUE_APP_API_BASE_URL=http://127.0.0.1:7788
```

## 使用说明

1. 首先启动后端服务：`python backend_api.py`
2. 然后启动前端服务：`cd front && npm run serve`
3. 访问前端页面：http://localhost:8082

## 注意事项

- 新的 `backend_api.py` 目前是一个占位实现，需要根据实际需求集成原有的 Gradio 逻辑
- 所有的 API 接口都支持 CORS 跨域请求
- 接口返回数据格式统一，方便前端处理