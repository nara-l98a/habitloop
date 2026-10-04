# Habitloop

Habitloop 是一个**本地优先、中文友好**的 Python 习惯追踪 CLI。它有主题专属逻辑：daily 习惯按连续日期计算连续记录，weekly 习惯按每周目标（1–7 次）判断完成周，报告分别计算日完成率或周完成率，并提供月历视图。每周完成率以报告范围触及的所有自然周为分母（包含零打卡周）；首尾不完整周也按自然周内的目标判定。

## 功能边界与版本

支持创建 daily（每天一次）和 weekly（每周 1–7 次）习惯、按 ISO 日期打卡/取消、重复打卡检测、未来日期拒绝、连续天/周统计、月历和日期范围报告。只使用 **Python 3.10+ 标准库**；不提供提醒、云同步、账户、图形界面或跨时区日历，日期按本机日期解释。

## 安装与命令

```bash
python -m pip install -e .
habitloop --help
```

所有命令接受全局 `--data PATH`（别名 `--db`），也支持环境变量 `HABITLOOP_DATA=/tmp/habits.json`；默认是 `~/.habitloop.json`。

```bash
habitloop --data ./habits.json add "晨跑"
habitloop --data ./habits.json add "力量训练" --cadence weekly --target 3
habitloop --data ./habits.json list
habitloop --data ./habits.json checkin 1 --date 2024-04-15
habitloop --data ./habits.json uncheck 1 --date 2024-04-15
habitloop --data ./habits.json status --date 2024-04-15
habitloop --data ./habits.json calendar 1 --month 2024-04
habitloop --data ./habits.json report 1 --start 2024-04-01 --end 2024-04-30
```

示例输出：

```text
已创建 #1 晨跑（daily，目标 1）
已打卡：晨跑 / 2024-04-15
#1 晨跑 | 连续 1天 | 总打卡 1 次
晨跑 报告 2024-04-01 至 2024-04-30
打卡次数：1；周期完成率：3.3%
```

参数：`add NAME` 名称非空；`--cadence` 为 `daily`/`weekly`；daily 的 `--target` 必须为 1，weekly 必须为 1–7。`checkin`/`uncheck` 的 ID 必须存在，`--date` 为 `YYYY-MM-DD`（默认今天）；`status --date` 为截至日期（默认今天）；`calendar ID --month` 为 `YYYY-MM`（默认本月）；`report ID` 的 `--start`/`--end` 为日期（默认结束今天、开始为前 29 天）。无效日期、未来日期、重复打卡、取消不存在的打卡和倒置范围会中文报错并返回 2。

## 数据格式、隐私与安全限制

JSON 顶层为 `version`、`next_id`、`habits`；习惯含 `id`、`name`、`cadence`、`target`、`created`、`checkins`，其中 checkins 是日期字符串数组。写盘先写同目录临时文件、`fsync` 后原子替换，尽量避免半写文件；它不是事务数据库，请自行备份。文件可能包含你输入的名称和日期，权限遵循 umask；软件不联网、不发送数据、不读取凭据，也不提供加密或密码保护，命令行参数可能进入 shell 历史。`examples/example-data.json` 是虚构示例，不含个人数据。
每次读取时都会校验版本、ID 唯一性、习惯字段、目标范围及所有日期；文件被手工编辑后若结构或日期非法，会给出中文错误并返回 2，而不会继续执行造成更隐蔽的数据损坏。

## 开发与测试

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

测试使用 `tempfile.TemporaryDirectory`，覆盖持久化、重复/未来日期、weekly 报告、取消打卡和错误月份，不触碰真实用户文件。CI 位于 `.github/workflows/tests.yml`。
