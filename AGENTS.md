# Project Context

## Project Overview

本项目开发一款图片标注软件，产出可供 YOLO26 模型训练使用的高质量标注数据。

## Current Phase

MVP 产品需求已冻结并进入实现阶段。正式范围见 `REQUIREMENTS.md`；CVAT Community `v2.73.0` 已作为上游基线合入，版本与升级边界见 `UPSTREAM.md`。

## Architecture Decision

- 基于 CVAT Community 进行最小化二次开发，采用 Web 访问方式，并优先使用 Docker Compose 部署。
- 固定上游版本为 CVAT Community `v2.73.0`，不跟随浮动的 `develop` 或 `latest`。
- 产品按 Windows 10/11 x64 单用户本地实例交付，每名内部用户独立安装，不建设团队协作服务器。
- MVP 使用固定本地工作根目录，任务直接引用其中的源文件，不复制或修改原始媒体。
- 应用通过内部离线大安装包交付；Docker Desktop 由用户从官方渠道预先安装，Edge为首选浏览器，Chrome为回退。
- 尽量通过官方 API、扩展点和独立服务实现项目特有能力，减少对 CVAT 核心代码的修改和长期升级负担。
- 引入 CVAT 前必须固定稳定版本，并核对该版本的官方文档、许可证、依赖和升级说明。

## Requirements Governance

- `REQUIREMENTS.md` 是当前 MVP 功能范围的唯一正式来源。
- 新需求、范围变化或与文档冲突的实现必须先向用户澄清并确认，不得自行扩展。
- 对模糊、矛盾或可能显著增加开发成本的需求，应立即指出并继续澄清，不得自行补全为实现假设。

## Design Constraints

- 人工审核结果是训练真值来源；模型预标注只能作为待审核建议。
- 保留原始图片和标注历史，不静默覆盖用户数据。
- 数据集、模型权重、训练结果和运行时上传文件不得混入源码仓库。
- 导出训练数据时必须校验图片与标签配对、类别映射、坐标合法性和空标注。
- 新增开源依赖前核对官方来源、版本、许可证、维护状态和兼容性，并维护 lockfile。

## Engineering Discipline

- 代码保持简单、清晰、可维护；禁止堆砌逻辑、无效抽象、死代码和未使用文件。
- 只做与当前需求直接相关的修改，不顺手扩展、重构或增加假想功能。
- 仓库内不得遗留调试输出、临时脚本、缓存或中间产物。确需临时文件时放在系统临时目录，并在任务结束前清理。
- 测试范围与修改风险匹配。只运行能够证明当前修改有效的最小测试，不做重复、无关或没有明确验证目标的测试。
- 构建成功不等于功能完成；涉及真实文件读写、标注保存或导出时，应验证对应的核心用户流程。
- SHA-256 不是日常默认检查。普通文件操作优先核对路径、数量、大小、Git 状态和真实运行结果。
- 仅在正式发布物、跨设备传输完整性、冻结的数据集或模型快照，以及用户明确要求时使用 SHA-256。

## Verification

按 `REQUIREMENTS.md` 的“验收主路径”选择与修改风险匹配的最小验证；必须覆盖真实图片、视频、持久化和导入导出，不能只报告构建或单元测试通过。

## Runbook

- 本地开发配置以根目录 `.env.example` 为模板，实际 `.env` 不提交。
- 启动命令：`docker compose -f docker-compose.yml -f docker-compose.local.yml up -d`。
- `CVAT_WORKSPACE_ROOT` 是用户工作根目录，容器只读挂载到 `/home/django/share`。
- `CVAT_STATE_DIR` 必须指向工作根目录内的 `.cvat-local`，数据库、任务数据、密钥、日志和缓存均绑定到其子目录。
- `.cvat-local` 在共享目录视图中使用临时挂载遮蔽，不能作为标注源目录出现。
- `docker-compose.local.yml` 使用 Compose `!override` 关闭默认分析依赖，安装程序必须检查所装 Docker Compose 支持该语法。
- 默认不启动 `upstream-analytics` 和 `upstream-extra` 配置组；不要在 MVP 安装流程中启用它们。
- `APP_VERSION` 控制本项目 Server/UI 镜像标签；正式离线包必须构建 `linux/amd64` 镜像，不能把开发机的 ARM 镜像交付给 Windows x64 用户。

## Implementation Details

- `GET /api/local/workspace` 返回固定工作区内的文件夹、JPG、PNG、MP4、MOV和 ZIP；`path` 使用工作区相对路径，`recursive` 控制是否递归。
- 工作区 API 需要登录，只返回相对路径和文件类型，不暴露宿主机绝对路径。
- 路径解析必须阻止绝对路径、`..` 越界和指向工作区外的符号链接，并以大小写无关方式排除 `.cvat-local`。
- 顶部导航只显示已实现的产品入口；当前为“任务列表”和“新建任务”。不得为尚未实现的页面添加占位链接。
- “关于”窗口必须保留 CVAT Community、MIT 许可证和上游源码信息。
