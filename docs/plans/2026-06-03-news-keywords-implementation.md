# News Keywords Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 扩展 `TrendRadar-plus` 的关键词与 AI 兴趣描述，使其优先采集社会民生、养老、健康养生相关热点。

**Architecture:** 本次只修改配置文件，不改采集代码。`config/frequency_words.txt` 负责当前 `keyword` 筛选模式的实际命中；`config/ai_interests.txt` 负责未来切换到 `ai` 筛选模式时保持同一兴趣方向。验证通过现有 `trendradar.core.frequency` 加载器解析配置，并用正反样本标题测试命中与过滤结果。

**Tech Stack:** Python 3、TrendRadar 配置文件、`trendradar.core.frequency.load_frequency_words`、`trendradar.core.frequency.matches_word_groups`。

---

## Preconditions

- 项目目录：`E:/Software-LargeAI/ClaudeCode/项目/ai-news-writer-新闻重写/TrendRadar-plus`
- 已批准设计文档：`docs/plans/2026-06-03-news-keywords-design.md`
- 当前全局筛选方式：`config/config.yaml` 中 `filter.method: "keyword"`
- 本计划不修改 Python 采集代码、不新增数据源、不修改调度配置。

## Task 1: 备份并整理关键词配置修改范围

**Files:**
- Read: `config/frequency_words.txt`
- Modify: `config/frequency_words.txt`

**Step 1: 确认当前关键词文件仍可读取**

Run:

```bash
python - <<'PY'
from pathlib import Path
p = Path('config/frequency_words.txt')
print(p.exists(), p.stat().st_size)
print(p.read_text(encoding='utf-8').splitlines()[0])
PY
```

Expected: 输出 `True`、文件大小大于 0，并打印第一行注释。

**Step 2: 保留现有三大类结构**

保留这些现有分区标题：

```text
养老相关
健康养生
社会民生
```

不要把它们改回科技、AI、金融方向。

**Step 3: Commit checkpoint（如本环境允许提交）**

```bash
git add config/frequency_words.txt docs/plans/2026-06-03-news-keywords-design.md docs/plans/2026-06-03-news-keywords-implementation.md
git commit -m "docs: plan news keyword expansion"
```

Expected: 提交成功。若执行环境或用户指令不允许提交，跳过并在结果中说明。

---

## Task 2: 扩展 `config/frequency_words.txt` 的全局过滤词

**Files:**
- Modify: `config/frequency_words.txt`

**Step 1: 在 `[GLOBAL_FILTER]` 中只保留无条件排除词**

当前至少保留：

```text
震惊
博彩
赌博
娱乐圈
明星
八卦
游戏
手游
网红
竟然
太可怕
刚刚
```

不要把 `彩票`、`直播带货`、`神药`、`偏方`、`秘方`、`祖传秘方`、`根治`、`特效药`、`包治百病`、`一招治好`、`永不复发` 放入 `[GLOBAL_FILTER]`，避免误杀监管、辟谣、防诈、彩票公益金支持养老等目标热点。

**Step 2: 将健康营销风险词改为具体复合词**

在养老防诈、食品安全、消费维权等相关分组中确保存在具体语境词：

```text
神药虚假宣传
神药骗局
偏方骗局
秘方骗局
偏方虚假宣传
特效药虚假宣传
包治百病虚假宣传
包治百病骗局
一招治好骗局
一招治好虚假宣传
永不复发虚假宣传
永不复发骗局
直播带货乱象
直播带货监管
彩票公益金
```

**Step 3: 验证过滤与保留同时生效**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words, matches_word_groups
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
negative = ['震惊！明星八卦内幕曝光', '博彩平台推出新活动', '包治百病神药限时促销']
positive = ['监管部门查处神药虚假宣传', '警方曝光保健品偏方骗局', '彩票公益金支持养老服务']
for title in negative:
    print(title, matches_word_groups(title, word_groups, filter_words, global_filters))
for title in positive:
    print(title, matches_word_groups(title, word_groups, filter_words, global_filters))
PY
```

Expected: negative 三行结果都以 `False` 结尾；positive 三行结果都以 `True` 结尾。

**Step 4: Commit checkpoint（如允许）**

```bash
git add config/frequency_words.txt
git commit -m "config: tighten low quality news filters"
```

---

## Task 3: 强化养老关键词分组

**Files:**
- Modify: `config/frequency_words.txt`

**Step 1: 将养老分组整理为这些组名**

确保存在以下组：

```text
[养老金政策]
[养老生活]
[老年健康]
[照护护理]
[养老防诈]
[银发经济]
```

**Step 2: 扩展 `[养老金政策]`**

确保该组包含以下关键词：

```text
养老金
退休金
养老保险
个人养老金
养老金调整
养老金上调
养老金补发
养老金发放
养老金到账
社保基金
企业年金
职业年金
延迟退休
渐进式退休
退休年龄
退休人员
城乡居民养老保险
职工养老保险
基本养老金
基础养老金
城乡居民基础养老金
养老待遇
退休待遇
退休工资
退休政策
退休办理
退休待遇核定
养老金资格认证
养老金认证
养老待遇资格认证
社保缴费
社保基数
缴费年限
工龄
高龄津贴
老龄津贴
法定退休年龄
提前退休
银发政策
人社
```

**Step 3: 扩展 `[养老生活]`**

确保该组包含以下关键词：

```text
养老
养老院
敬老院
养老服务
养老机构
机构养老
居家养老
社区养老
居家社区养老
智慧养老
适老化
老年人
老人
老年
高龄
独居老人
空巢老人
孤寡老人
失能老人
半失能老人
护理院
养老社区
养老公寓
养老中心
日间照料
老年食堂
老年餐桌
助餐
老年助餐
养老助餐
助餐服务
助老
为老服务
探访关爱
老有所养
老有所依
老有所乐
银龄
银发族
老年生活
退休生活
老年大学
老年教育
老年旅游
老年消费
老年用品
适老产品
老年代步车
家庭养老床位
上门助浴
```

**Step 4: 扩展 `[老年健康]` 与 `[照护护理]`**

确保两组包含：

```text
老年健康
老人健康
中老年健康
老年病
慢病管理
老年体检
老年医疗
老年护理
老年康复
康复护理
认知障碍
认知症
阿尔茨海默
老年痴呆
帕金森
骨质疏松
跌倒
防跌倒
吞咽困难
听力下降
视力下降
老年营养
老人饮食
中老年饮食
老年用药
```

```text
照护
老人照护
养老照护
长期照护
家庭照护
上门照护
上门护理
护理员
养老护理员
护工
陪护
陪诊
长护险
长期护理保险
适老改造
适老化改造
无障碍改造
老旧小区适老化
家庭病床
医养结合
康养
康养中心
康养服务
安宁疗护
临终关怀
失能照护
认知照护
喘息服务
```

**Step 5: 验证养老样本命中**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words, matches_word_groups
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
samples = [
    '多地上调城乡居民基础养老金',
    '个人养老金制度迎来新调整',
    '社区养老服务中心提供老年助餐',
    '长期护理保险覆盖更多失能老人',
    '警方提醒防范养老诈骗和保健品骗局',
    '银发经济带动适老产品消费增长',
]
for title in samples:
    print(title, matches_word_groups(title, word_groups, filter_words, global_filters))
PY
```

Expected: 所有样本都以 `True` 结尾。

**Step 6: Commit checkpoint（如允许）**

```bash
git add config/frequency_words.txt
git commit -m "config: expand elderly care and pension keywords"
```

---

## Task 4: 强化健康养生关键词分组

**Files:**
- Modify: `config/frequency_words.txt`

**Step 1: 保留并扩展这些健康养生组**

确保存在：

```text
[健康总论]
[医疗健康]
[中医养生]
[常见疾病]
[营养饮食]
[食物功效]
[日常饮食]
[四季养生]
[人群营养]
[肠胃代谢]
[食品安全]
```

新增或确保存在：

```text
[睡眠心理]
[运动康复]
```

**Step 2: 扩展 `[医疗健康]`**

确保包含：

```text
医院
医生
医保
医疗
看病
就医
门诊
住院
挂号
手术
急诊
急救
120
药品
药价
集采
医保报销
医保支付
医保目录
医保谈判
处方药
慢病用药
家庭医生
基层医疗
社区医院
卫生院
公共卫生
疫苗
接种
传染病
流感
```

**Step 3: 扩展慢病、饮食与食品安全**

确保包含：

```text
高血压
糖尿病
高血脂
脂肪肝
冠心病
脑卒中
中风
心梗
脑梗
阿尔茨海默
老年痴呆
骨质疏松
关节炎
颈椎病
腰椎
痛风
高尿酸
癌症
肿瘤
慢性病
```

```text
营养
膳食
膳食指南
合理膳食
蛋白质
优质蛋白
维生素
补钙
补铁
补锌
益生菌
膳食纤维
低盐
控盐
低油
控油
低糖
控糖
减脂
减肥
肥胖
全谷物
粗粮
杂粮
豆制品
牛奶
酸奶
鸡蛋
绿叶菜
深色蔬菜
```

```text
食品安全
食品添加剂
预制菜
农残
农药残留
毒蘑菇
变质
过期食品
假药
保健品骗局
保健品诈骗
食物中毒
饮水安全
```

**Step 4: 新增 `[睡眠心理]`**

```text
[睡眠心理]
睡眠
失眠
熬夜
入睡困难
早醒
浅眠
多梦
助眠
安神
心理健康
焦虑
抑郁
压力
情绪
心理咨询
精神卫生
```

**Step 5: 新增 `[运动康复]`**

```text
[运动康复]
运动
健身
康复
康复训练
运动康复
拉伸
散步
太极
太极拳
八段锦
五禽戏
广场舞
骨关节
膝关节
肩周炎
腰椎间盘
颈椎
肌肉拉伤
```

**Step 6: 验证健康养生样本命中**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words, matches_word_groups
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
samples = [
    '医保目录调整新增多款慢病用药',
    '高温天气老年人如何防中暑',
    '食品安全抽检发现不合格产品',
    '专家提醒糖尿病患者注意控糖饮食',
    '长期失眠可能影响心理健康',
    '八段锦和太极成为中老年运动新选择',
]
for title in samples:
    print(title, matches_word_groups(title, word_groups, filter_words, global_filters))
PY
```

Expected: 所有样本都以 `True` 结尾。

**Step 7: Commit checkpoint（如允许）**

```bash
git add config/frequency_words.txt
git commit -m "config: expand health and wellness keywords"
```

---

## Task 5: 强化社会民生关键词分组

**Files:**
- Modify: `config/frequency_words.txt`

**Step 1: 保留并扩展已有民生组**

确保存在：

```text
[社会保障]
[住房民生]
[就业民生]
[教育民生]
[物价消费]
[安全灾害]
```

新增或确保存在：

```text
[交通出行]
[人口家庭]
[消费维权]
[公共服务]
```

**Step 2: 扩展社会保障、住房、就业、教育**

确保包含：

```text
社保
医保
低保
救助
补贴
津贴
失业保险
工伤保险
生育保险
大病保险
医疗救助
公积金
住房公积金
灵活就业
居民医保
城乡居民
社会保障
五险一金
困难群众
特困人员
低收入
残疾人补贴
```

```text
房价
楼市
住房
保障房
公租房
廉租房
共有产权房
租房
房租
房贷
房贷利率
物业
物业费
业委会
老旧小区
小区改造
老旧小区改造
加装电梯
危房
烂尾楼
交房
棚改
旧改
```

```text
就业
失业
裁员
招聘
工资
最低工资
最低时薪
欠薪
讨薪
劳动仲裁
劳动争议
劳动合同
劳动权益
农民工
灵活就业
退休返聘
社保缴费
求职
应届生
毕业生
就业率
失业率
```

```text
教育
学校
中考
高考
学费
托育
幼儿园
义务教育
学生
校园
校园安全
霸凌
补课
双减
课后服务
招生
入学
升学
职业教育
助学金
营养午餐
```

**Step 3: 新增交通、人口家庭、消费维权、公共服务**

```text
[交通出行]
交通
出行
公交
地铁
高铁
火车
网约车
出租车
打车
停车
停车费
堵车
拥堵
限行
电动车
电瓶车
充电桩
快递
外卖
配送
通勤
```

```text
[人口家庭]
户口
户籍
身份证
居住证
落户
积分落户
人口
生育
三孩
二孩
出生率
结婚
离婚
彩礼
婚姻
家暴
赡养
抚养
监护
遗产
继承
丧葬
殡葬
```

```text
[消费维权]
消费维权
消费者权益
投诉
举报
退款
退费
预付卡
充值卡
价格欺诈
虚假宣传
假冒伪劣
霸王条款
售后
召回
315
市场监管
```

```text
[公共服务]
便民
惠民
政务服务
公共服务
社区服务
供水
停水
供电
停电
燃气
燃气费
水费
电费
取暖费
供暖
供热
垃圾分类
环境卫生
```

**Step 4: 验证民生样本命中**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words, matches_word_groups
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
samples = [
    '灵活就业人员社保缴费基数调整',
    '老旧小区加装电梯有新政策',
    '多地上调最低工资标准',
    '中小学课后服务收费政策发布',
    '菜价上涨影响居民生活成本',
    '消费者预付卡退费纠纷增多',
    '多地优化公交地铁换乘服务',
]
for title in samples:
    print(title, matches_word_groups(title, word_groups, filter_words, global_filters))
PY
```

Expected: 所有样本都以 `True` 结尾。

**Step 5: Commit checkpoint（如允许）**

```bash
git add config/frequency_words.txt
git commit -m "config: expand public livelihood keywords"
```

---

## Task 6: 更新 `config/ai_interests.txt`

**Files:**
- Modify: `config/ai_interests.txt`

**Step 1: 替换科技方向兴趣描述**

用以下内容替换文件主体，保留文件用途说明即可：

```text
下面是我要关注的内容：
# 重要性排序说明：从上到下优先级递减，越靠前越重要。
# 如果一条新闻同时可能匹配多个方向，请优先归入更靠前的方向。

1. 社会民生政策与公共服务：重点关注社保、医保、低保、救助、补贴、公积金、政务服务、便民惠民措施，以及影响居民日常生活的公共服务变化。
2. 养老政策与养老金：重点关注养老金调整、退休金发放、养老保险、个人养老金、延迟退休、退休政策、待遇认证、社保缴费和高龄津贴。
3. 养老服务与银发经济：关注居家养老、社区养老、机构养老、养老院、老年助餐、适老化改造、家庭养老床位、长护险、医养结合、康养服务和银发消费。
4. 老年健康与照护护理：关注老年慢病管理、认知障碍、阿尔茨海默、骨质疏松、防跌倒、老年营养、老年用药、长期照护、上门护理、陪诊和安宁疗护。
5. 医疗医保与公共卫生：关注医院、医生、门诊、住院、挂号、药品集采、医保目录、医保报销、基层医疗、家庭医生、疫苗接种、传染病和公共卫生事件。
6. 健康养生与慢病管理：关注高血压、糖尿病、高血脂、痛风、脂肪肝、冠心病、脑卒中、癌症筛查、睡眠、心理健康、运动康复和科学养生建议。
7. 营养饮食与食品安全：关注膳食指南、控盐控油控糖、蛋白质、维生素、益生菌、全谷物、食品添加剂、预制菜、农残、过期食品、食物中毒和饮水安全。
8. 住房、就业、教育与生活成本：关注房价、租房、保障房、公租房、老旧小区改造、加装电梯、就业、工资、欠薪、劳动权益、托育、教育、物价、菜价、取暖费和消费券。
9. 交通出行、消费维权与家庭人口：关注公交、地铁、网约车、电动车、停车、快递外卖、消费投诉、退款退费、预付卡、价格欺诈、户籍、生育、婚姻、赡养、继承和殡葬。
10. 安全灾害与应急提醒：关注暴雨、洪水、台风、地震、火灾、燃气事故、交通事故、食品中毒、高温、寒潮、传染病预警、应急救援和安全生产。

# 标题质量要求（即使匹配了上面的标签，符合以下特征的标题也请跳过）
- 不要标题党/震惊体（如“震惊！”、“太可怕了！”、“竟然...”、“刚刚！”）
- 不要营销软文、广告推广类标题
- 不要保健品夸大宣传、神药偏方、包治百病类标题
- 不要娱乐八卦、明星绯闻、博彩彩票、游戏直播等无关内容
- 优先保留政策变化、公共服务、权威健康提醒、民生价格、养老照护和安全预警类新闻
```

**Step 2: 验证文件方向不再是科技主题**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path('config/ai_interests.txt').read_text(encoding='utf-8')
required = ['社会民生', '养老', '养老金', '医疗医保', '健康养生', '食品安全']
for word in required:
    print(word, word in text)
for old in ['DeepSeek', 'OpenAI', '英伟达', 'SpaceX']:
    print(old, old in text)
PY
```

Expected:

- `社会民生`、`养老`、`养老金`、`医疗医保`、`健康养生`、`食品安全` 均为 `True`。
- `DeepSeek`、`OpenAI`、`英伟达`、`SpaceX` 均为 `False`。

**Step 3: Commit checkpoint（如允许）**

```bash
git add config/ai_interests.txt
git commit -m "config: align ai interests with livelihood news"
```

---

## Task 7: 运行综合验证

**Files:**
- Read: `config/frequency_words.txt`
- Read: `config/ai_interests.txt`

**Step 1: 解析关键词文件**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
print('groups=', len(word_groups))
print('filters=', len(filter_words))
print('global_filters=', len(global_filters))
assert len(word_groups) >= 25
assert len(global_filters) >= 15
PY
```

Expected: 命令成功，且无 AssertionError。

**Step 2: 验证正向样本命中**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words, matches_word_groups
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
positive = [
    '多地上调城乡居民基础养老金',
    '医保目录调整新增多款慢病用药',
    '老旧小区加装电梯有新政策',
    '高温天气老年人如何防中暑',
    '食品安全抽检发现不合格产品',
    '灵活就业人员社保缴费基数调整',
    '社区养老服务中心提供老年助餐',
    '消费者预付卡退费纠纷增多',
    '长期失眠可能影响心理健康',
]
failed = []
for title in positive:
    matched = matches_word_groups(title, word_groups, filter_words, global_filters)
    print(title, matched)
    if not matched:
        failed.append(title)
assert not failed, failed
PY
```

Expected: 所有样本都为 `True`，无 AssertionError。

**Step 3: 验证反向样本过滤**

Run:

```bash
python - <<'PY'
from trendradar.core.frequency import load_frequency_words, matches_word_groups
word_groups, filter_words, global_filters = load_frequency_words('config/frequency_words.txt')
negative = [
    '震惊！明星八卦内幕曝光',
    '彩票中大奖秘诀',
    '包治百病神药限时促销',
]
failed = []
for title in negative:
    matched = matches_word_groups(title, word_groups, filter_words, global_filters)
    print(title, matched)
    if matched:
        failed.append(title)
assert not failed, failed
PY
```

Expected: 所有样本都为 `False`，无 AssertionError。

**Step 4: 查看 diff**

Run:

```bash
git diff -- config/frequency_words.txt config/ai_interests.txt docs/plans/2026-06-03-news-keywords-design.md docs/plans/2026-06-03-news-keywords-implementation.md
```

Expected: diff 只包含关键词、AI 兴趣描述、设计文档和实施计划。

**Step 5: Final commit（如允许）**

```bash
git add config/frequency_words.txt config/ai_interests.txt docs/plans/2026-06-03-news-keywords-design.md docs/plans/2026-06-03-news-keywords-implementation.md
git commit -m "config: focus news collection on livelihood aging health"
```

Expected: 提交成功。若之前已做分步提交，此步骤可跳过。

---

## Acceptance Criteria

- `config/frequency_words.txt` 覆盖社会民生、养老、健康养生三大类。
- `config/ai_interests.txt` 不再是科技/AI/金融方向，已改为社会民生、养老、健康养生方向。
- 关键词文件可由 `load_frequency_words('config/frequency_words.txt')` 正常解析。
- 正向样本标题全部命中。
- 标题党、博彩、娱乐八卦、低质健康营销样本被过滤。
- 不修改采集代码、不修改数据源、不修改调度逻辑。

## Rollback

如命中噪音过高，优先回滚宽泛词，而不是删除整个大类：

1. 在 `config/frequency_words.txt` 中保留具体词，如 `医保目录`、`养老金调整`、`老旧小区改造`。
2. 收窄宽泛词，如 `健康`、`教育`、`住房`、`运动`。
3. 增加全局过滤词或组内 `!过滤词`。
4. 重新运行 Task 7 的综合验证。
