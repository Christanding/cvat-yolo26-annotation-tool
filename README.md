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

## Windows 部署

下面的方式和 CVAT Community 官方部署流程基本一致：下载源码，配置本地目录，再用 Docker Compose 启动。

### 准备环境

请先安装：

- Windows 10/11 x64；
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)，使用 WSL 2 后端；
- [Git for Windows](https://git-scm.com/download/win)；
- Microsoft Edge，或 Google Chrome。

启动 Docker Desktop，确认下面的命令可以正常执行：

```powershell
docker version
docker compose version
```

项目的 Compose 配置使用 `!override`。如果 Docker 提示无法识别这个标签，请先更新 Docker Desktop。

### 1. 获取源码

在 PowerShell 中运行：

```powershell
git clone https://github.com/Christanding/cvat-yolo26-annotation-tool.git
cd cvat-yolo26-annotation-tool
```

### 2. 准备工作目录

工作目录用于存放原始图片、视频、抽帧结果和 CVAT 的持久化数据。建议使用固定路径，例如：

```powershell
New-Item -ItemType Directory -Force D:\YOLO-Workspace
```

任务开始后，不要移动、重命名或删除任务引用的图片、视频和文件夹。

### 3. 配置环境变量

复制配置模板：

```powershell
Copy-Item .env.example .env
```

打开 `.env`，按实际情况修改工作目录：

```dotenv
CVAT_VERSION=v2.73.0
APP_VERSION=dev
CVAT_HOST=localhost
CVAT_WORKSPACE_ROOT=D:/YOLO-Workspace
CVAT_STATE_DIR=D:/YOLO-Workspace/.cvat-local
```

`CVAT_STATE_DIR` 必须位于工作目录内，并指向 `.cvat-local`。这个目录保存数据库、账户、任务和标注，不要手动修改，也不要提交到 Git。

### 4. 构建并启动

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

第一次启动会下载基础镜像并构建本项目的 Server 和 UI，因此需要联网，也会比日常启动耗时更长。

查看运行状态：

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml ps
```

### 5. 创建账户

首次部署后创建一个本地账户：

```powershell
docker exec -it cvat_server python manage.py createsuperuser
```

按照提示输入用户名和密码。创建完成后，用 Edge 或 Chrome 打开：

<http://localhost:8080>

登录一次后，浏览器会保留登录状态。

## 日常使用

启动：

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

停止：

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml stop
```

停止服务不会删除任务、标注或源文件。服务构建完成后，标注、抽帧和导入导出可以在断网环境下使用。

## 更新

更新前先停止正在进行的导入、导出和抽帧任务，然后运行：

```powershell
git pull --ff-only
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

更新不会主动删除 `.cvat-local`。需要迁移到另一台电脑时，先停止服务，再复制整个工作目录；原始媒体和 `.cvat-local` 必须一起保留。

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
