# Demo 演示稿（5 分钟版）

> 说一段话 → 4 周后产出可直接发布的公众号文章。
> 阶跃 Step-Audio + Step-2 标杆 demo，MVP v0.1.0。

## 0. 演示前 30 秒检查

```bash
# 进入项目（如果项目在 ~/Desktop 系列被 macOS TCC 锁，先挪到 ~/Documents）
cd ~/Documents/voice2article

# 1) backend/.env 里 STEP_API_KEY 是有效的（看脱敏头尾即可）
grep STEP_API_KEY backend/.env | sed 's|=\(.\{6\}\).*\(.\{4\}\)$|=\1...\2|'

# 2) 一键起服务
bash scripts/demo-up.sh
```

如果 8000/5173 已被占（系统里跑着别的项目），改端口：

```bash
BACKEND_PORT=8003 FRONTEND_PORT=5174 bash scripts/demo-up.sh
```

成功输出会显示 demo 入口和账号：
- 入口：`http://localhost:5173/`
- 账号：`demo@aiken.dev` / 密码：`demo-password-1`
- 已预置 3 个会话（评测 / 读书心得 / 产品复盘）

---

## 1. Demo 流程（按这个顺序讲）

### 0:00 — 0:30　开场（30 秒）

> "公众号写作有两个痛点：**灵感转文字慢**、**风格不一致**。这个项目用阶跃 Step-Audio 把语音想法直接转成可发布的微信公众号文章。MVP 4 周完成，今天给大家走一遍完整链路。"

打开浏览器 `http://localhost:5173`，已自动跳到登录页。

### 0:30 — 1:00　登录（30 秒）

输入账号 `demo@aiken.dev` / `demo-password-1` → 点登录。

> "登录用的是标准 JWT，密码 bcrypt cost 12 哈希存。这一步看起来普通，但每个会话、每篇文章都隔离到具体用户，跨用户访问会被拦下来。"

进首页后展示左侧菜单：**对话创作 / 生成历史**。

### 1:00 — 2:00　语音转写（60 秒）

点"对话创作" → 顶部"新建" → 切到「实时录音」Tab。

> "Step-Audio 实测延迟 < 0.5 秒，准确率 90%+，自带中文标点。"

按"开始录音"，对着麦克风说一段（**建议提前练**）：

> "今天想写一篇关于阶跃星辰 Step-2 模型的评测，重点讲长文本能力。结尾给开发者一个上手建议。"

按"停止并转写"，文字会作为 user 消息出现在右侧消息气泡。

**Plan B**（如果当场录音环境差）：
- 切到「上传文件」Tab，拖一个准备好的 .wav 文件
- 或者直接选左侧已经 seed 好的"评测 Step-2 长文本"会话，跳过这一步

### 2:00 — 3:30　LLM 流式生成（90 秒）

下拉到「生成文章」面板：
- **风格**：亲切（默认）
- **篇幅**：中（约 1700 字）
- 点 **生成草稿**

> "走的是 Step-2-16k 的 Server-Sent Events 流式，能看到逐字往外吐。这样用户在 30 秒内就有反馈，不用等完整结果。"

文字会一字一字流出来。完成后：
- 上方显示标题 + 字数
- "复制" / "一键排版" 两个按钮亮起

**口播亮点**：
- "整篇文章是从你刚才说的那段话直接生成的，没有人工 prompt 调试"
- "标题、引言、主体、总结四段结构都是 prompt 模板里强制的"

### 3:30 — 4:30　一键排版（60 秒）

点 **一键排版**。Modal 打开，左上角 3 个模板可切：**简约 / 商务蓝 / 科技绿**。

> "切模板 → 实时刷新预览。手机/PC 双端能看效果。"

切到"科技绿" → 点 **复制 HTML** → notify 提示已复制。

> "这是 inline-style HTML，没有外链 CSS。直接 Cmd+V 粘到微信公众号编辑器，样式就在了。"

如果有微信公众号草稿后台，**真贴一次**给观众看（这是最有冲击力的一步）。

退而求其次：点 **下载 .html**，本地用浏览器打开看完整效果。

### 4:30 — 5:00　收尾（30 秒）

> "整个 MVP 4 周，3000 行代码，覆盖语音→文章→排版的完整链路。后端用 FastAPI + SQLite + alembic + JWT，前端 Vite + React + AntD。下一步会接文档库（Phase 2）和多模态（Step-1V）。"

打开侧栏 **生成历史**，让大家看到刚才那篇文章已经存进库里。

---

## 2. 现场救场预案

| 现象 | 应对 |
|---|---|
| 8000/5173 被占 | `BACKEND_PORT=8003 FRONTEND_PORT=5174 bash scripts/demo-up.sh`（提前演练时已知会被占就直接用 8003）|
| 麦克风没声音 | 切「上传文件」Tab，准备一个测试 wav 在 `~/Documents/voice2article/demo-assets/` |
| Step API 401 | 后端窗口会有 `code: stt_auth` / `llm_auth` 日志，说明 .env 里 key 失效 → 换新 key 重启 backend |
| 流式生成不动 | 极少数情况下 httpx 走系统代理握手失败，已加 trust_env=False。如再发生，立刻切到「同步生成」（Swagger 里手动调 `/generations` 不带 stream）|
| 浏览器麦克风权限被拒 | 系统设置 → 隐私 → 麦克风 → 把 Chrome / Safari 打开，**重启浏览器** |
| Step 上游限流 | 平台后台调高 RPS，或临时换一把无限速的 key |

## 3. 现场可能被问到的 Q & A

**Q：跟自己拿 Whisper + Claude 拼一个有什么区别？**
A：Step-Audio 中文标点比 Whisper 强；Step-2 写公众号风格的中文比 Claude 自然，且都跑在阶跃，账单一份、延迟更低。这套链路也是阶跃生态 demo 的标杆。

**Q：会泄露用户内容吗？**
A：所有数据都在本机 SQLite，没有第三方分析。生产化时换 Postgres + 用户级隔离已经在 schema 里。

**Q：能用阶跃以外的模型吗？**
A：`StepLLMClient` 是 OpenAI 兼容封装，改 `STEP_API_BASE_URL` + `STEP_LLM_MODEL` 就能切 Claude / GPT-4o / 文心。一行代码不用改。

**Q：流式中断怎么办？**
A：UI 有"停止"按钮，后端会持久化已经流出来的部分；下次刷新页面在「生成历史」能看到草稿。

**Q：为什么不做更花哨的排版？**
A：MVP 优先「能直接发」。3 套模板 + inline style 已经覆盖 80% 场景。SVG 动效在 V2 路线图。

## 4. 演示后清理

```bash
bash scripts/demo-down.sh
```

会停掉后端 + 前端，保留 `dev.db` 和 `.env`。下次再 `demo-up.sh` 数据还在。

如果要彻底重置（删 demo 账号 + 数据）：

```bash
rm backend/dev.db
cd backend && uv run alembic upgrade head
```

---

**MVP v0.1.0** · 2026-05-07 · [github.com/Zgh332358/voice2article](https://github.com/Zgh332358/voice2article)
