# YOLO26 图片标注工具

这是一个基于 CVAT Community 的本地图片标注工具，主要用于制作 YOLO26 Detect 数据集。它保留了 CVAT 成熟的标注底层，但把界面收窄到日常需要的几件事：创建任务、矩形框标注、视频抽帧，以及 YOLO Detect 标注包的导入和导出。

项目按单机使用设计。每台电脑运行一套 Docker 服务，图片、视频和标注数据都留在本机，不需要单独部署团队服务器。

## 功能范围

- 标注 8 位 JPG、PNG 图片，支持大分辨率图像。
- 使用水平矩形框制作 YOLO26 Detect 标注。
- 从 MP4、MOV 视频按起止时间和整数秒间隔抽取 PNG。
- 提供低、中、高三档连续帧去重，并显示处理统计。
- 把新抽取的图片追加到已有标注任务。
- 自动保存标注，使用 `A`、`D` 切换上一张和下一张图片。
- 导入、导出未划分的 Ultralytics YOLO Detect 标注包。
- 任务、账户和标注长期保存在工作目录的 `.cvat-local` 中。

当前不支持分割、关键点、旋转框、3D、目标跟踪、多人协作和自动划分训练集。

## Windows 安装

普通使用者不需要下载本仓库的完整 CVAT 源码。请使用只有 7 个文件的 [简化部署仓库](https://github.com/Christanding/cvat-yolo26-annotation-deploy)。

安装 Docker Desktop 和 Git 后，在 PowerShell 中运行：

```powershell
git clone https://github.com/Christanding/cvat-yolo26-annotation-deploy.git
cd cvat-yolo26-annotation-deploy
powershell -ExecutionPolicy Bypass -File .\Start.ps1
```

启动脚本会自动创建工作目录、下载镜像、启动服务、创建本地账户并打开 Edge。日常启动、停止、更新和更换工作目录的方式都写在部署仓库的 README 中。

本仓库保留完整源码是为了开发、审查许可证和跟进 CVAT 上游版本，不是普通使用者的安装包。需要从源码调试时，才使用 `.env.example`、`docker-compose.yml` 和 `docker-compose.local.yml`。

## 标注包格式

项目导入、导出的格式为：

```text
dataset/
├── images/
├── labels/
└── data.yaml
```

包内不创建 `train`、`val`、`test`。没有目标的图片仍会保留，并生成同名的空标签文件。

## 上游与许可证

本项目固定在 CVAT Community `v2.73.0`，上游提交为 `ac6e63b96bddbc462a0a8c0acce307c4c0c6e972`。版本选择、依赖和升级规则见 [UPSTREAM.md](UPSTREAM.md)，产品范围见 [REQUIREMENTS.md](REQUIREMENTS.md)。

CVAT Community 使用 MIT License。本仓库保留了上游的 [LICENSE](LICENSE)、版权和来源信息。部分可选模型及第三方组件可能采用其他许可证；本项目当前不启用 serverless 自动标注组件。

## 当前验证状态

图片任务、矩形框标注、视频抽帧、连续帧去重、任务追加、持久化和 YOLO Detect 标注包导入导出已经通过真实文件流程验证。Windows 10/11 x64、WSL 2 和 Edge 的完整部署流程仍需在实际 Windows 电脑上完成最终验收。
