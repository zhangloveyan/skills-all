# Codex Skills

个人维护的 Codex Skills 集合。目前包含任务接入、长任务交接和闪念记录工具。

## Skills

### 任务接入（task-intake）

把一句自然语言需求整理为范围清晰、投入匹配的任务，避免简单任务过度调研、过度设计和过度测试。

核心能力：

- 自动判断任务类型、规模、风险和预计消耗。
- 明确调研、改动、验证及外部资料查询范围。
- 使用两阶段确认：先确认方向，再确认详细方案。
- 编码前集中收敛所有能够提前发现的关键选择。
- 默认只运行与修改内容直接相关的测试。

使用示例：

```text
使用 task-intake 处理这个需求：
给图片生成接口增加单图和多参考图支持。
```

也可以直接用一句自然语言描述任务；允许隐式调用 Skill 时，Codex 会自动完成任务接入。

### 任务交接（task-handoff）

在对话过长、目标变化或开发阶段切换时，自动整理精简交接包并准备下一任务。

核心能力：

- 接近 30 个用户回合时检查是否需要交接。
- 在上下文压缩、方案反复、开发转部署等场景立即整理交接。
- 从对话、Git、文件和验证结果中自动提取当前状态。
- 创建新任务后检查就绪状态，可靠地设置并验证任务标题。
- 重命名失败时保留任务 ID，避免重复创建任务。

使用示例：

```text
使用 task-handoff 整理当前进度，我确认后新开任务。
```

### 闪念助手（flash-note-assistant）

捕捉链接、文本和图片，自动分类并写入飞书多维表格，同时支持每日统计推送。

## 安装

克隆仓库：

```powershell
git clone https://github.com/zhangloveyan/skills-all.git
```

复制需要的 Skill 到 Codex 用户技能目录：

```powershell
Copy-Item -Recurse .\skills-all\task-intake "$HOME\.codex\skills\"
Copy-Item -Recurse .\skills-all\task-handoff "$HOME\.codex\skills\"
```

也可以让 Codex 安装：

```text
请安装 https://github.com/zhangloveyan/skills-all 中的 task-intake 和 task-handoff。
```

安装完成后重新启动或刷新 Codex，使 Skill 被重新加载。

## 推荐工作流

```text
一句自然语言需求
        ↓
task-intake：初判范围与消耗
        ↓
用户确认 → 详细方案 → 用户确认
        ↓
最小实现与针对性测试
        ↓
task-handoff：长任务或阶段切换时生成交接包
        ↓
新任务继续
```

## 目录

```text
skills-all/
├── task-intake/
├── task-handoff/
└── flash-note-assistant/
```

## License

[MIT](LICENSE)
