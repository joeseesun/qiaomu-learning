# Prior-Art Research

- Skill: `qiaomu-learning` 2.0.0
- Mode: Governed（面向公开复用）
- Researched at: 2026-08-10
- Queries: `Socratic tutoring agent`; `active recall learning coach`; `one question at a time tutoring`; `story based concept learning`
- Catalogs: skills.sh、SkillsMP，以及候选的 canonical GitHub source
- Reproducible catalog artifact: `reports/prior-art-candidates.json`
- Rating evidence: unavailable

> 2026-08-11 v1.1.0 note：本次没有重新扩展候选检索。真实使用暴露的是既有 dual-coding / nondecorative visual 原则没有被写成强制恢复路径；因此沿用下列已核验参考，把“明确困惑或求图 + 当前台阶可视觉化”提升为立即换模态的通用协议，并把相对论火车场景仅作为回归情境。

四组查询在 skills.sh 和 SkillsMP 均成功，共得到 97 个去重候选 family。skills.sh 的数字是生态安装量；SkillsMP 展示的是候选所在 GitHub 仓库的 stars。二者都不是用户评分、正确率或单个 skill 的质量证据，也未合并成跨目录分数。下表中的可变数字均观测于 2026-08-10。

| Query | skills.sh candidates | SkillsMP candidates | Status |
|---|---:|---:|---|
| `Socratic tutoring agent` | 14 | 10 | both succeeded |
| `active recall learning coach` | 16 | 8 | both succeeded |
| `one question at a time tutoring` | 19 | 8 | both succeeded |
| `story based concept learning` | 13 | 9 | both succeeded |

## Shortlist and source review

| Candidate | Role and relevance | Dated adoption / trust signal | Concrete lesson | Deliberate rejection or adaptation | License |
|---|---|---|---|---|---|
| [anthropics/claude-for-legal — `law-student/socratic-drill`](https://github.com/anthropics/claude-for-legal/tree/main/law-student/skills/socratic-drill) | Trust anchor；与逐问训练和按回答分支高度重合 | GitHub repository 9,071 stars | 用 hypothetical 先迫使学习者推理；按 right / sloppy / wrong / stuck 分支；在尝试之后再纠正 | 保留“先推理后纠正”，但移除法律领域刚性和“必须挣到答案”的惩罚感；连续卡住或用户要求时允许最小解释或直接答案 | Apache-2.0 |
| [github/awesome-copilot — `mentoring-juniors`](https://github.com/github/awesome-copilot/tree/main/skills/mentoring-juniors) | 高关注度的通用 mentoring 参考 | GitHub repository 37,651 stars | 渐进线索、类比、让学习者自己解释，以及把控制权还给学习者 | 吸收最小帮助与 learner autonomy；拒绝巨型触发描述、固定 persona、emoji 风格和“永远不给答案”的刚性 | MIT |
| [GarethManning/education-agent-skills](https://github.com/GarethManning/education-agent-skills) | 教育机制 specialist；补足主动回忆与视觉学习 | skills.sh 中 `retrieve-first-gate` 49 installs；GitHub repository 591 stars | retrieve-first gate、progressive hint ladder、dual coding；先自由回忆，再逐级增加帮助，视觉必须补充而非装饰 | 改造成严格的一回合一问、显式退出和问题承载型视觉。只学习机制并给予署名，不复制文字、示例或资产，以避免把 CC BY-SA 内容并入 MIT 包 | CC BY-SA 4.0 |
| [joeseesun/qiaomu-course-designer](https://github.com/joeseesun/qiaomu-course-designer) | Qiaomu 交互与状态管理参考 | GitHub repository 2 stars；同时检查本地 canonical skill | 每轮一个实质问题、按依赖选择下一问、暂停/恢复、把用户证据与模型判断分开 | 将“课程决策状态”改造成逐概念的学习证据状态；不沿用课程设计的交付物、访谈目标或规划流程 | MIT |
| [EveryInc/compound-engineering-plugin — `coding-tutor` catalog record](https://skills.sh/everyinc/compound-engineering-plugin/coding-tutor) | skills.sh 的表面 popularity anchor | catalog 显示 2.5K installs | 证明目录流行度必须回到当前 source 复核 | 当前仓库已移除该 skill，仓库 changelog 也记录了移除；因此把目录条目判为 stale，不把其内容、安装量或名称作为设计证据 | N/A：当前 source artifact 不存在，未复用 |

检查以 canonical `SKILL.md`、相关 reference、许可证及必要的仓库历史为准；没有为了研究而运行任何第三方脚本。列出来源是贡献说明，不代表这些作者或仓库认可、审核或背书本 skill。

## What we learned from each candidate

- `socratic-drill`：最有价值的是“先给可推理情境，再按回答质量分支”，而不是法律语气或永久 withholding。它落到 `references/socratic-protocol.md` 的“回答分支”和“卡住时的最小帮助阶梯”。
- `mentoring-juniors`：渐进线索、类比和 learner explanation 能维持主动性；真正可复用的是帮助顺序，不是 persona。它落到 `SKILL.md` 的 `Adaptation Rules` 和 `references/socratic-protocol.md` 的“学习者控制权”。
- `education-agent-skills`：retrieve-first、free recall 和 dual coding 应有清晰门槛，视觉不能只是装饰。它落到 `references/socratic-protocol.md` 的“开始”和“卡住时的最小帮助阶梯”，以及 `references/story-visual-learning.md` 的“模态选择”“图像生成门”和“视觉后的学习闭环”。
- `qiaomu-course-designer`：一问一回合与 dependency-aware next question 能从需求访谈迁移到学习对话，但状态必须由学习证据而非设计决策驱动。它落到 `SKILL.md` 的 `Hard Invariants`、`Compact Workflow`，以及 `references/socratic-protocol.md` 的“学习证据账本”。
- `coding-tutor`：目录 adoption signal 不能替代现存 source。这个 stale hit 被保留为反例，防止把 2.5K installs 错写成可复用或高质量证据。

## Contribution ledger

### Keep

- hypothetical-first / retrieve-first：在可以从材料或情境推理时，先让学习者尝试。
- 按回答质量分支，而不是按预写题单机械推进。
- progressive hints、analogy、free recall、learner explanation 和 learner autonomy。
- 一轮一个实质问题、按依赖选择下一问、支持暂停和恢复。
- dual coding 仅在另一模态能补充结构关系时使用。

### Adapt

- 将 right / sloppy / wrong / stuck 改成更细且非惩罚性的正确完整、结论对但理由松、部分正确、错误/猜测、偏题和连续卡住分支。
- 将通用 hint ladder 收紧为 `cue → contrast → story → visual → micro_explanation`，每次只升级一级并等待尝试。
- 将 course-design decision state 改成 `unseen / exposed / recalled / applied / confused` 学习证据账本，并另记 `own_words` 与 `transfer`。
- 将“never answer”改成 learner-controlled exit：用户可提示、跳过、暂停、先讲再继续或直接要答案。
- 将 dual coding 改成带成本、授权、隐私、准确性、文字替代和失败降级的图像生成门；v1.1.0 再把明确困惑或求图后的可视觉化台阶升级为立即换模态，并保留无结构收益时拒绝装饰图的边界。

### Reject

- 法律领域专用假设、审讯式语气、羞辱或“未挣到就永远不给答案”。
- 巨型关键词触发描述、固定 persona、emoji 表演和用语气代替协议。
- 一轮多个问题、伪装成单问的复合任务、固定题数和预生成整套问卷。
- 装饰性图像、把答案写进图、无文字替代、把生成图当成精确或权威证据。
- 未经 source review 就按 installs/stars 采纳候选；`coding-tutor` 的 stale catalog record 是明确反例。

### Invent

- **句子级一问协议与检查器**：不仅定义问号数量，还定义一个语义作答目标、复合动作、管理型小问、问题是否位于最后及问后答案泄漏。规范见 `SKILL.md` 的 `Hard Invariants` 和 `references/socratic-protocol.md` 的“一问检查器”；`scripts/validate_skill.py` 与 fixture 只检查可机器判定的结构，未见输出的语义边界仍需 provider 或人工评审。
- **学习者证据状态机**：`unseen / exposed / recalled / applied / confused` 加 `own_words / transfer`，使下一问由刚出现的学习证据驱动，而不是由固定脚本驱动。
- **具名人物故事桥**：故事必须含人物、目标、约束和可观察结果，之后立即用一个 reconstruction question 让学习者重建机制，并说明类比边界。
- **受治理的视觉恢复门**：只在空间、相对运动、因果、流程、几何、曲线或多组件关系确有收益时调用图示；明确困惑或求图且当前台阶可视觉化时立即换模态，要求最少信息、准确性检查、无答案泄漏、等价文字替代、一个降阶观察题和文本 fallback。
- **双证据掌握门**：只有学习者能用自己的话解释，并在新表面情境成功迁移，才可称为掌握。
- **来源注入处理**：教材、截图、PDF 或笔记中的命令被视为被学习内容，不得改变 skill 指令；材料主张、模型补充和虚构类比分开标记。

## Created skill advantages

- **Design advantage**：相比已检查候选，本包把“一次只问一个问题”写成语义级、句子级协议，并为其中可机器判定的结构增加 deterministic gate，而不是只靠 persona 或示例。证据：`SKILL.md` 的 `Hard Invariants`、`references/socratic-protocol.md` 的“一问检查器”、`scripts/validate_skill.py`。
- **Design advantage**：下一问显式依赖学习证据状态，并把 `exposed`、`recalled`、`applied` 和具体误解分开；单次猜对不会自动升级为掌握。证据：`references/socratic-protocol.md` 的“学习证据账本”“回答分支”“收束”。
- **Design advantage**：故事和图像都必须接回 reconstruction / transfer question；生图有授权、隐私、准确性、文字替代和失败降级门。证据：`references/story-visual-learning.md` 的“具名人物情境”“图像生成门”“Codex / OpenAI 适配”“视觉后的学习闭环”。
- **Design advantage**：显式处理来源注入和 learner-controlled exit，避免“苏格拉底法”压过用户指令或材料边界。证据：`references/socratic-protocol.md` 的“学习者控制权”“来源与纠错”。
- **Validated advantage**：standalone validator、15 个单元测试与 qiaomu-meta trigger evaluator 已通过；trigger 为 24/24、0 false positives、0 false negatives。该证据只证明包内规定的触发边界、静态回合合同、分支、退出、视觉恢复/拒绝装饰图边界和 mastery fixture 符合预期，不等于真实学习效果优于参考 skill。
- **Hypothesis**：语义级单问与最小帮助可能减少认知负荷并提高主动回忆质量，但尚无 provider-backed 多轮或真实学习者证据。
- **Hypothesis**：具名人物故事后立即重建，以及 explain + novel transfer 双门，可能比被动解释更有利于概念迁移；尚无 head-to-head 或延迟保持实验。

## Missing evidence

- 没有任何目录提供可复核的用户 rating/review；installs 与 repository stars 不能代替。
- 尚无 provider-backed 多轮会话，无法证明真实模型在长对话中始终遵守一问协议、状态更新和退出。
- 尚无与四个参考 skill 或直接讲解 baseline 的公平 head-to-head comparison。
- 尚无人类学习者盲评、教师评审、完成率、主观负担、延迟回忆、迁移保持或真实学习结果。
- 生成图的 provider 可用性、费用、视觉准确性和无障碍体验尚无 live runtime 证据；文本 fallback 只构成设计边界。
- clean install、公开发布、远端 release 和跨平台运行不在本次研究范围，不能据此声称已发布或可发现。
