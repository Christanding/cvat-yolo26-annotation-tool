# Windows 离线安装包

## 用户安装

1. 使用 Docker 官方安装程序安装 Docker Desktop，选择 WSL 2 后端并接受官方许可条款。
2. 双击 `标注软件-Setup.exe`。
3. 选择长期保留的工作根目录，设置本地账户。
4. 安装程序自动导入镜像、启动服务并优先打开 Microsoft Edge。

日常使用双击桌面的“启动标注软件”。开始菜单提供“停止标注软件”，停止不会删除数据。普通卸载只移除应用和容器，工作根目录下的 `.cvat-local` 默认保留。

## 构建

构建机需要 Docker Desktop 和官方 Inno Setup `7.1.0` x64。在 Windows PowerShell 中运行：

```powershell
.\installer\windows\Build-OfflinePackage.ps1 -Version 1.0.0
```

脚本会构建本项目 Server/UI 镜像，拉取 Compose 需要的固定基础镜像，导出单个离线归档，并在 `dist\windows\` 生成安装程序。`dist\` 是构建产物目录，不提交到 Git。

更新时使用新版本号重新构建并运行新安装包。安装脚本会执行原有 Compose 项目的受控更新，不删除 `.cvat-local`。

## 验证边界

当前仓库已提供可构建的安装源码和启停脚本。`Setup.exe`、Windows 10/11 x64、WSL 2、Edge 和完全断网安装必须在实际 Windows 电脑上完成发布验收；macOS 上的静态检查不能替代该验收。
