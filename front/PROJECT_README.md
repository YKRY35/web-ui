# Browser Use WebUI - Vue 2 前端项目

这是一个基于 Vue 2 + Element UI 的浏览器自动化工具前端项目，用于与后端 API 交互。

## 项目结构

```
src/
├── api/
│   └── index.js          # API 请求封装
├── assets/               # 静态资源
├── components/
│   ├── common/           # 公共组件
│   │   ├── TabContainer.vue     # 标签页容器
│   │   ├── FormGroup.vue        # 表单分组
│   │   └── FormItem.vue         # 表单项
│   └── pages/            # 页面组件
│       ├── AgentSettingsTab.vue         # 代理设置页
│       ├── BrowserSettingsTab.vue       # 浏览器设置页
│       ├── BrowserUseAgentTab.vue       # 运行代理页
│       ├── DeepResearchAgentTab.vue     # 深度研究页
│       └── LoadSaveConfigTab.vue        # 配置管理页
├── plugins/
│   └── element.js        # Element UI 插件配置
├── utils/
│   ├── request.js        # axios 请求封装
│   └── storage.js        # 本地存储工具
├── views/
│   └── MainView.vue      # 主视图
├── App.vue               # 根组件
├── main.js               # 入口文件
└── router.js             # 路由配置
```

## 功能模块

### 1. 代理设置 (Agent Settings)
- LLM 提供商和模型配置
- 系统提示设置
- 温度等参数配置
- MCP 服务器配置
- 计划器 LLM 配置

### 2. 浏览器设置 (Browser Settings)
- 浏览器二进制路径配置
- 窗口大小设置
- 远程调试配置
- 录制和下载路径配置

### 3. 运行代理 (Run Agent)
- 任务输入和聊天界面
- 代理控制（运行、停止、暂停、恢复）
- 浏览器实时视图
- 任务输出下载

### 4. 深度研究 (Deep Research)
- 研究任务配置
- 研究报告显示
- 报告下载功能

### 5. 配置管理 (Load & Save Config)
- 配置文件加载
- 配置文件保存

## 安装依赖

```bash
npm install
```

## 开发模式

```bash
npm run serve
```

## 生产构建

```bash
npm run build
```

## 主要依赖

- Vue 2.6.x - 前端框架
- Element UI 2.15.x - UI 组件库
- Vue Router 3.x - 路由管理
- Axios 0.27.x - HTTP 请求库
- marked 4.x - Markdown 解析
- highlight.js 11.x - 代码高亮
- vue-clipboard2 0.3.x - 剪贴板功能

## 后端 API 配置

后端 API 地址默认配置在 `src/utils/request.js` 中，默认为 `/api`。如果需要修改后端地址，请修改 `baseURL` 配置。

## 注意事项

1. 本项目需要配合后端服务一起使用
2. 后端需要实现 API 接口设计中定义的 RESTful API
3. 配置数据会自动保存到浏览器的 localStorage 中

## 下一步

后端需要将 Gradio 接口重构为 RESTful API，保持功能不变但改变数据交互方式。