# 安装与运行依赖

## Inno Setup

- 固定构建版本：`7.1.0` x64。
- 官方来源：<https://jrsoftware.org/isdl.php>
- 许可证：Inno Setup License，<https://jrsoftware.org/files/is/license.txt>
- 用途：将离线镜像、Compose 配置、启停脚本和许可说明打包为单个 Windows 安装程序。
- 本仓库不再分发 Inno Setup 本身；只用其官方编译器生成安装包。商业使用时按官方说明购买商业许可。

## Docker Desktop

- 官方来源：<https://docs.docker.com/desktop/setup/install/windows-install/>
- 许可说明：<https://docs.docker.com/subscription/desktop-license/>
- 用途：在 Windows 10/11 x64 上以 WSL 2 后端运行本项目容器。
- Docker Desktop 不包含在本项目安装包中。用户必须使用 Docker 官方安装程序安装，自行接受其条款，组织负责人在内部发布前确认所需订阅。

## 容器与应用依赖

CVAT Community 及默认容器组件的版本、官方来源和许可边界见仓库根目录 `UPSTREAM.md`。每次正式打包生成的 `image-list.txt` 记录安装包实际包含的镜像标签。
