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

CVAT 上游源码已固定并合入开发分支。下一步建立最小本地部署覆盖层，随后按 `REQUIREMENTS.md` 逐项实现和验证。

## 开发原则

- 保留 CVAT 上游核心代码，只隐藏或禁用无关入口。
- 产品差异保持集中、可追踪，避免无关重构和脆弱补丁。
- 数据集、模型权重、运行数据、日志和构建产物不得提交到 Git。
- 测试与修改风险匹配，不做无目的测试；SHA-256 不作为日常验证手段。

## 许可证

CVAT Community 核心代码使用 MIT License。部分服务器无关模型资产和第三方依赖可能采用其他许可证；本项目 MVP 不启用 serverless 自动标注组件，引入或发布其他资产前仍需逐项核对许可证。
