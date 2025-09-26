# OpenAI API 流式输出配置指南

## 概述

现在系统已经支持直接连接OpenAI API进行流式输出。用户在前端输入查询后，后端会：

1. 使用RAG检索相关文档
2. 调用OpenAI API进行流式生成
3. 实时将token流式传输到前端

## 配置步骤

### 1. 设置环境变量

复制 `env.example` 到 `.env` 并配置：

```bash
cp env.example .env
```

在 `.env` 文件中设置你的OpenAI API密钥：

```env
# LLM Configuration
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-actual-openai-api-key-here
LLM_MODEL=gpt-3.5-turbo
```

### 2. 安装依赖

确保安装了新添加的httpx依赖：

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 启动后端
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（在另一个终端）
cd frontend
python -m http.server 3000
```

## 支持的模型

系统支持任何OpenAI兼容的API，包括：

- OpenAI官方API (gpt-3.5-turbo, gpt-4, etc.)
- Azure OpenAI
- 其他兼容OpenAI格式的API服务

只需在 `.env` 文件中相应地设置 `LLM_BASE_URL` 和 `LLM_MODEL`。

## 工作流程

1. **用户查询**: 用户在前端聊天界面输入问题
2. **文档检索**: 后端使用BGE-M3模型检索相关文档
3. **流式生成**: 将检索到的文档作为上下文，调用OpenAI API流式生成回答
4. **实时显示**: 前端通过Server-Sent Events实时接收并显示生成的token
5. **完整响应**: 生成完成后显示来源链接和元数据

## 注意事项

- 确保API密钥有足够的配额
- 流式输出需要稳定的网络连接
- 系统会自动处理API错误并显示友好的错误信息
- 所有配置都通过环境变量管理，便于部署

## 故障排除

1. **API密钥错误**: 检查 `.env` 文件中的 `LLM_API_KEY` 是否正确
2. **网络连接问题**: 检查 `LLM_BASE_URL` 是否可访问
3. **模型不存在**: 确认 `LLM_MODEL` 在你的API账户中可用
4. **依赖缺失**: 运行 `pip install -r requirements.txt` 确保所有依赖已安装






