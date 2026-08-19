# YOLO26 图片标注软件

本仓库基于 CVAT Community 二次开发，用于在 Windows 10/11 本地完成图片标注、视频抽帧及未划分 YOLO26 Detect 标注包的导入导出。

## 当前基线

- 上游：CVAT Community `v2.73.0`
- 上游提交：`ac6e63b96bddbc462a0a8c0acce307c4c0c6e972`
- 官方仓库：<https://github.com/cvat-ai/cvat>
- 许可证：MIT，保留上游 `LICENSE`、版权和来源说明
- 部署：Windows x64、Docker Desktop、Docker Compose、本地 Web

版本选择和升级边界详见 [UPSTREAM.md](UPSTREAM.md)，冻结的 MVP 范围详见 [REQUIREMENTS.md](REQUIREMENTS.md)。

## MVP 边界

- 只支持 YOLO26 Detect 水平矩形框。
- 只支持 8 位 JPG、PNG；视频输入为 MP4、MOV，常见编码为 H.264、H.265。
- 每名用户独立安装和使用，不建设团队协作服务器。
- 原始图片和视频始终只读，任务、标注和配置持久化到工作区 `.cvat-local/`。
- 导出未划分的 `images/`、`labels/`、`data.yaml` 标注包。
- 通过内部离线安装包交付，日常使用不要求 Git 或命令行。

## 当前阶段

已完成 MVP 代码主线：固定工作区、本地持久化、中文核心界面、图片任务创建、Detect 矩形框标注、图片完成状态、自动保存、类别锁定、视频抽帧，以及未划分 YOLO26 Detect 标注包的导入导出。抽帧支持起止时间、整数秒间隔、低中高三档连续帧去重、覆盖确认和处理统计。

Windows 离线安装源码位于 [`installer/windows/`](installer/windows/README.md)，用户安装时只需预先安装 Docker Desktop，再双击 `标注软件-Setup.exe`。安装程序实物、Windows 10/11 x64 断网安装和 Edge 端到端兼容性仍需在正式发布机上验收。

## 开发启动

开发环境先根据 `.env.example` 配置工作区和持久化目录，再运行：

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

这是开发阶段的启动方式。最终用户不需要执行命令，正式交付使用离线安装程序和桌面快捷方式。

## 开发原则

- 保留 CVAT 上游核心代码，只隐藏或禁用无关入口。
- 产品差异保持集中、可追踪，避免无关重构和脆弱补丁。
- 数据集、模型权重、运行数据、日志和构建产物不得提交到 Git。
- 测试与修改风险匹配，不做无目的测试；SHA-256 不作为日常验证手段。

## 许可证

CVAT Community 核心代码使用 MIT License。部分服务器无关模型资产和第三方依赖可能采用其他许可证；本项目 MVP 不启用 serverless 自动标注组件，引入或发布其他资产前仍需逐项核对许可证。
