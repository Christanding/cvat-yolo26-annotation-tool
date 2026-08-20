# Project Context

## Project Overview

本项目开发一款图片标注软件，产出可供 YOLO26 模型训练使用的高质量标注数据。

## Current Phase

MVP 产品需求已冻结，核心功能代码已实现并进入 Windows 发布验收阶段。正式范围见 `REQUIREMENTS.md`；CVAT Community `v2.73.0` 已作为上游基线合入，版本与升级边界见 `UPSTREAM.md`。

## Architecture Decision

- 基于 CVAT Community 进行最小化二次开发，采用 Web 访问方式，并优先使用 Docker Compose 部署。
- 固定上游版本为 CVAT Community `v2.73.0`，不跟随浮动的 `develop` 或 `latest`。
- 产品按 Windows 10/11 x64 单用户本地实例交付，每名用户独立部署，不建设团队协作服务器。
- MVP 使用固定本地工作根目录，任务直接引用其中的源文件，不复制或修改原始媒体。
- 应用通过公开源码和 Docker Compose 部署；Docker Desktop 与 Git 由用户从官方渠道预先安装，Edge为首选浏览器，Chrome为回退。
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
- `docker-compose.local.yml` 使用 Compose `!override` 关闭默认分析依赖；README 必须提示用户使用支持该语法的新版 Docker Compose。
- 默认不启动 `upstream-analytics` 和 `upstream-extra` 配置组；不要在 MVP 安装流程中启用它们。
- `APP_VERSION` 控制本项目 Server/UI 镜像标签；Windows x64 用户由本机 Docker Desktop 从源码构建 Linux 容器镜像。

## Implementation Details

- `GET /api/local/workspace` 返回固定工作区内的文件夹、JPG、PNG、MP4、MOV和 ZIP；`path` 使用工作区相对路径，`recursive` 控制是否递归。
- 工作区 API 需要登录，只返回相对路径和文件类型，不暴露宿主机绝对路径。
- 路径解析必须阻止绝对路径、`..` 越界和指向工作区外的符号链接，并以大小写无关方式排除 `.cvat-local`。
- 顶部导航只显示“任务列表”“新建任务”“视频抽帧”和“导入”；图片标注与导出从具体任务进入，设置位于用户菜单。
- “关于”窗口必须保留 CVAT Community、MIT 许可证和上游源码信息。
- 新建任务默认使用“本地工作区”，并保留“拖拽上传”；远程 URL 与云存储入口在 MVP 中隐藏。
- 本地工作区选择器通过 `/api/local/workspace` 读取受限文件列表，选中的相对路径仍按 CVAT `server_files` 流程创建任务。
- `GET /api/local/videos` 递归发现工作区内的 MP4、MOV；`POST /api/local/extractions` 创建抽帧任务，`GET /api/local/extractions/<id>` 返回进度和统计。
- 视频抽帧输出 PNG 到源视频同级的 `images/<视频名>/`，仅在当前视频内按“上一张保留帧”去重，覆盖前必须由用户确认。
- `GET /api/local/tasks` 返回可追加图片的本地工作区任务；`POST /api/local/tasks/<id>/images` 将所选抽帧目录中的新图片追加到任务末尾，新图片保持“未检查”。
- 标注工作区仅暴露 Detect 矩形框所需工具；`A`/`D` 固定为上一张/下一张，切图前保存当前标注。
- `GET/POST /api/local/tasks/<id>/frames/<frame>/status` 管理单图完成状态，`GET/POST /api/local/tasks/<id>/review` 返回或完成整任务图片检查状态。
- `YOLO26 Detect 标注包` 是唯一产品导入导出格式；顶层 `POST /api/local/packages` 从 ZIP 创建任务，任务内导入用于覆盖当前标注。
- GitHub 仓库只提交源码、Compose 配置和文档；不得提交 `.env`、`.cvat-local`、容器镜像归档或用户数据。
- 设置弹窗只显示当前图片框选流程需要的“图像浏览”和“标注界面”选项。
