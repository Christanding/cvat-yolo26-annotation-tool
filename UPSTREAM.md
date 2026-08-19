# CVAT 上游基线

## 固定版本

| 项目 | 值 |
| --- | --- |
| 上游项目 | CVAT Community |
| 官方仓库 | <https://github.com/cvat-ai/cvat> |
| 固定标签 | `v2.73.0` |
| 固定提交 | `ac6e63b96bddbc462a0a8c0acce307c4c0c6e972` |
| 发布日期 | 2026-08-12 |
| 许可证 | MIT |
| 上游远程名 | `cvat-upstream` |

`v2.73.0` 是引入时最新的正式稳定版本，不使用浮动的 `develop` 或 `latest`。该版本改善了数据集导入错误信息，并修复了本地文件共享入口跳转问题，与本项目的本地导入流程直接相关。

## 集成方式

本仓库是 CVAT 的产品 fork：上游源码和提交历史直接合入仓库根目录，产品修改在其上以普通 Git 提交维护。这样可以直接使用官方构建和 Docker Compose 结构，并在升级时通过 Git 比较、审查和合并上游稳定标签。

## 默认运行依赖

以下组件由 CVAT `v2.73.0` 官方 Compose 引入，本项目没有另造替代服务：

| 组件 | 版本 | 许可证 | 用途 |
| --- | --- | --- | --- |
| CVAT Server / UI | `v2.73.0` | MIT | 标注后端与前端 |
| PostgreSQL | `15-alpine` | PostgreSQL License | 任务、账户和标注元数据 |
| Redis | `7.2.11-alpine` | BSD-3-Clause | 内存队列和运行状态 |
| Apache Kvrocks | `2.15.0` | Apache-2.0 | 磁盘缓存 |
| Traefik | `v3.6` | MIT | 本机反向代理 |
| Open Policy Agent | `1.12.2` | Apache-2.0 | CVAT 权限策略 |

前端依赖由根目录 `yarn.lock` 锁定，Python 依赖由 `cvat/requirements/` 中的固定版本文件管理。PostgreSQL 和 Traefik 的上游 Compose 标签只固定到版本系列，正式离线发布时必须记录实际打包镜像版本，不能在用户安装阶段在线拉取浮动镜像。

本项目默认不启动 ClickHouse、Vector、Grafana，以及 Webhook、质量报告和共识审核工作进程；这些上游能力不在 MVP 范围内，但源码仍保留以维持上游升级路径。

## 升级规则

1. 阅读目标版本官方 Release Notes、升级说明和安全公告。
2. 获取新的正式稳定标签，不跟随 `develop`。
3. 比较本项目修改过的文件和上游变化，先解决真实冲突。
4. 验证数据库迁移、任务与标注保留、图片标注、抽帧、导入导出和离线安装主路径。
5. 验证通过后再更新固定版本、镜像标签和离线安装包。

上游升级不得静默覆盖本项目修改，也不得以构建成功代替真实数据流程验证。

## 许可证边界

- CVAT Community 核心代码为 MIT License，根目录 `LICENSE` 必须保留。
- CVAT 官方说明指出，部分 serverless 模型资产及第三方组件可能具有单独许可证。
- MVP 不启用 serverless 自动标注组件；未来启用前必须重新核对模型、权重、运行时和发布方式的许可证。
- Docker Desktop 是用户独立安装的外部运行环境，不捆绑在本项目安装包中。
