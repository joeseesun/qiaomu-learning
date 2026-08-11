# Creation Handoff

## Result

- Skill: `qiaomu-socratic-learning` 1.1.0
- Date: 2026-08-11
- Mode: Governed，面向公开复用
- Job: 把教材、截图、PDF、笔记、题目或一个主题变成“一轮一个认知台阶”的自适应苏格拉底学习对话，并用主动回忆、最小搭架、故事/视觉桥和新情境迁移积累可见的学习证据。
- Local path: `/Users/joe/Documents/日常对话/qiaomu-socratic-learning`
- Publication status: `v1.0.0` 已发布；`v1.1.0` 本地 release candidate 已就绪，远端 PR、Release 与 clean-install 证据在本次报告生成时仍待发布流程完成。

## v1.1.0 feedback-driven improvement

- 真实失败：学习者明确反馈“太抽象、不理解、为什么不配图”，但旧协议只把视觉写成弱可选项，模型因此继续用文字推进空间关系。
- 领域无关改写：当学习者明确求图或报告抽象/不理解，且当前认知台阶能表示为空间、相对运动、流程、几何、因果或曲线关系时，下一回合立即换模态；图后附文字替代，只问一个更具体的观察问题。
- Generalization gate：该行为属于 learner-control 与 scaffold recovery 的核心机制；“火车与相对论”只保留为回归情境，不写进通用核心规则。若当前缺口没有结构性视觉收益，仍拒绝装饰图并改用具体情境。
- Prior-art decision：未重新扩展候选检索。v1.0.0 已研究的 `education-agent-skills` dual-coding / nondecorative visual 机制仍直接相关；本次是把已有设计原则从“可选门”修成可执行恢复协议，而非引入新的外部机制。

## Reference skills studied

- [anthropics/claude-for-legal — `socratic-drill`](https://github.com/anthropics/claude-for-legal/tree/main/law-student/skills/socratic-drill)：2026-08-10 观察到仓库 9,071 GitHub stars。学习 hypothetical-first drilling、按回答质量分支和“先推理、后纠正”；落到 `references/socratic-protocol.md` 的“回答分支”和“卡住时的最小帮助阶梯”。法律领域刚性与惩罚式 withholding 未采用。
- [github/awesome-copilot — `mentoring-juniors`](https://github.com/github/awesome-copilot/tree/main/skills/mentoring-juniors)：2026-08-10 观察到仓库 37,651 GitHub stars。学习渐进线索、类比、learner explanation 与 autonomy；落到 `SKILL.md` 的 `Adaptation Rules` 和协议的“学习者控制权”。巨型触发描述、persona、emoji 和 never-answer 刚性未采用。
- [GarethManning/education-agent-skills](https://github.com/GarethManning/education-agent-skills)：2026-08-10 观察到仓库 591 GitHub stars，skills.sh 的 `retrieve-first-gate` 为 49 installs。学习 retrieve-first gate、progressive hint ladder 与 nondecorative dual coding；落到 `references/socratic-protocol.md` 的“开始”“卡住时的最小帮助阶梯”，以及 `references/story-visual-learning.md` 的“模态选择”“视觉后的学习闭环”。因其为 CC BY-SA 4.0，本包只吸收机制并署名，不复制 prose、案例或资产。
- [joeseesun/qiaomu-course-designer](https://github.com/joeseesun/qiaomu-course-designer)：2026-08-10 观察到仓库 2 GitHub stars。学习每轮一个实质问题、dependency-aware next question、暂停/恢复和 evidence separation；将课程决策状态改造成 `references/socratic-protocol.md` 的“学习证据账本”。

上述 installs 与 stars 分别只表示目录采用度和仓库关注度，不是 rating、正确率或 skill 质量。引用表示研究与贡献说明，不表示来源作者或仓库认可、审核或背书本 skill。

## Absorbed and rejected

- **Keep**：先取证再教学；按回答质量分支；自由回忆；渐进线索；类比；学习者用自己的话解释；一轮一个实质问题；暂停/恢复与 learner autonomy。
- **Adapt**：把通用提示阶梯改成每次只升级一级的 `cue → contrast → story → visual → micro_explanation`；把课程决策状态改为 `unseen / exposed / recalled / applied / confused` 加 `own_words / transfer`；把 dual coding 收紧为有成本、权限、隐私、准确性和文字 fallback 的视觉门。
- **Reject**：领域专用法律 rigidity、羞辱和永久 withholding；never-answer 规则；多个问题或复合作答目标；巨型触发关键词、固定 persona 和 emoji 表演；装饰性或答案泄漏型图片；用目录 popularity 替代 current-source review。skills.sh 中 2.5K installs 的 EveryInc `coding-tutor` 已从当前 source 移除，因此明确不采用。
- **Invent**：语义级句子一问检查器；学习者证据状态机；具名人物故事后立即 reconstruction；Codex 内置生图的治理门与文本替代；`own_words + novel transfer` 掌握门；针对教材/截图/PDF 内提示注入的来源边界。

## Advantages and highlights

- **Design advantage**：每个活跃用户可见回合的协议要求只有一个语义学习问题、一个作答目标且问题位于最后；validator 覆盖可机器判定的结构，未见输出的语义边界仍需 provider 或人工判断。证据：`SKILL.md` 的 `Hard Invariants`、`references/socratic-protocol.md` 的“一问检查器”及 `scripts/validate_skill.py`。
- **Design advantage**：下一问由逐概念证据状态与最近回答决定，`exposed` 不冒充 `recalled`，单次答对也不冒充 `applied`。证据：`references/socratic-protocol.md` 的“学习证据账本”“回答分支”。
- **Design advantage**：具名人物情境和教学图都必须服务当前唯一问题，并在之后回到重建或迁移；明确困惑或求图且当前台阶可视觉化时会立即进入视觉恢复，图后降成一个观察题；视觉路径带授权、准确性、隐私、文字替代和失败降级。证据：`SKILL.md` 的“显式困惑立即换模态”及 `references/story-visual-learning.md` 的“视觉恢复协议”“图像生成门”“视觉后的学习闭环”。
- **Design advantage**：mastery 必须同时有学习者自己的解释和新表面情境迁移；来源内命令不能改变教学协议。证据：`references/socratic-protocol.md` 的“收束”“来源与纠错”。
- **Validated advantage**：`scripts/validate_skill.py` 已通过，15 个单元测试全绿，qiaomu-meta trigger evaluator 为 24/24、0 false positives、0 false negatives。静态 fixture 额外覆盖“太抽象 / 不理解 / 给我画图”的空间、流程、几何恢复正例及无结构收益时拒绝装饰图的负例；该验证不支持真实学习效果或相对优越性声明。
- **Hypothesis**：单问、最小帮助和 learner-controlled exit 预计能减少认知负担并维持主动性，但 provider-backed 多轮和真实学习者证据仍为 `missing evidence`。
- **Hypothesis**：故事重建与 explain + novel transfer 双门预计能提升抽象概念迁移，但尚无 head-to-head、延迟回忆或人类学习结果。

## Verification and limits

- Prior-art discovery：四组查询的 skills.sh 与 SkillsMP 均成功，97 个去重 candidate families；详见 `reports/prior-art-candidates.json` 和 `reports/prior-art-research.md`。
- Deterministic verification：standalone validator 通过；15/15 单元测试通过；qiaomu-meta trigger evaluator 24/24 通过，0 false positives、0 false negatives；`reports/output-evidence.json` 记录静态 fixture 边界。
- Deterministic scope：中英文 trigger 边界；一个语义问题且问题位于最后；source diagnostic opener 与 injection/OCR resistance；正确、部分正确、错误、三次卡住分支；故事边界；图像 eligibility / success / failure / fallback / no leakage；显式困惑后的视觉恢复与无结构收益负例；显式退出；10 回合序列；`own_words + novel transfer` mastery。
- `missing evidence`：provider-backed 实跑、与参考 skill 的公平对照、人类教师或学习者盲评、真实完成率、认知负担、延迟回忆、迁移保持和长期学习结果。
- 默认不需要网络、shell、文件写入或持久学习档案。可选生图只在视觉门通过且现有授权允许时使用；需要额外费用或新授权时，确认本身必须是当轮唯一问题；失败后使用文字、ASCII 或小表格降级。
- 用户要求停止、暂停或直接答案时立即退出逐问模式；高风险安全说明可以打断节奏。不得代做禁止外援的评分任务，也不得把生成图当成精确数值、医学、法律或安全证据。
- Publication boundary：本报告生成时尚未执行 `v1.1.0` 的推送、远端 release 或 clean install，因此这些状态须由后续发布器证据确认；既有 `v1.0.0` 发布不构成 `v1.1.0` 证明。
