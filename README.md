# Mistral API Proxy for OpenWebUI

用于修复 OpenWebUI 对接 Mistral 模型时常见的 `400` 和 `422` 错误。

## 问题背景

在 OpenWebUI 中使用 Mistral 时，常见报错包括：

- 选择 Mistral 模型时出现 `422: OpenWebUI: Server Connection Error`
- 点击 Continue Response 时出现 `400: OpenWebUI: Server Connection Error`

主要原因是 OpenWebUI 会发送部分 OpenAI 风格的字段或请求结构，而 Mistral API 不完全兼容这些内容。

## 这个代理做了什么

- 移除不受支持字段（如 `logit_bias`、`user` 等）
- 修复 Continue Response 场景（当最后一条是 assistant 时自动补一条 user 消息）
- 透明转发其他请求，并保留流式响应能力

## 使用 Docker Compose 运行（兼容 ARM64）

### 1. 准备环境变量文件

在项目目录创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
MISTRAL_API_KEY=your_actual_key_here
```

### 2. 构建并启动

```bash
docker compose up -d --build
```

### 3. 服务地址

代理默认监听：

```text
http://localhost:6432
```

在 OpenWebUI 中填写：

```text
API Base: http://localhost:6432/v1
API Key: 任意值
```

## 不使用 Docker 的本地运行方式

```bash
pip install flask requests python-dotenv
python python.py
```

默认本地地址：

```text
http://localhost:6432
```

## 说明

- 请妥善保管 `.env`

## 来源声明

本项目基于以下 GitHub Gist 修改与扩展而来：

https://gist.github.com/ricjcosme/6dc440d4a2224f1bb2112f6c19773384

本仓库在原有实现基础上进行了 Docker 化封装及部分兼容逻辑增强。

原始代码版权归 Gist 原作者所有。如原作者对本仓库存在任何异议，请联系删除。
