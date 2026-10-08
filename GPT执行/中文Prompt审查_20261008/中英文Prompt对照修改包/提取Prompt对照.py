"""Extract local prompt text without importing agents or making model calls."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r'E:\huawei after\KARMA')
NEWER = Path(r'E:\huawei after\临时\KARMA')
OLD = ROOT / '旧版' / 'KARMA'
OUT = Path(__file__).resolve().parent
OUT.relative_to(ROOT.resolve())

ENTITY = 'karma/agents/entity_extraction/agent.py'
RELATION = 'karma/agents/relationship_extraction/agent.py'
SHARED = 'karma/agents/extraction_support.py'
GENERATION = 'karma/agents/text_generation/agent.py'
COMPARISON = 'karma/agents/text_comparison/agent.py'
READER = 'karma/agents/reader/agent.py'
SUMMARY = 'karma/agents/summarizer/agent.py'

PAIRED_PATH = OUT / '中英文Prompt逐项对照与修改稿_合并后.md'
TEMPLATE_PATH = OUT / '核心Prompt完整模板参考_合并后.md'
MANIFEST_PATH = OUT / '摘录定位与校验_合并后.json'
MIGRATION_PATH = ROOT / 'GPT执行/中文Prompt审查_20261008/Prompt合并整理/合并验证结果.json'

_source_cache = {}

def source(path):
    """Read and parse source only; no agent imports or execution."""
    path = Path(path)
    if path not in _source_cache:
        raw = path.read_text(encoding='utf-8-sig')
        _source_cache[path] = (raw.splitlines(), ast.parse(raw))
    return _source_cache[path]

def locations(path):
    """Identify AST nodes by lexical scope rather than current line numbers."""
    found = {}
    counts = {}
    def visit(node, scope=()):
        key = None
        next_scope = scope
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            key = ('function', scope, node.name)
            next_scope = scope + (node.name,)
        elif isinstance(node, ast.ClassDef):
            key = ('class', scope, node.name)
            next_scope = scope + (node.name,)
        elif isinstance(node, ast.Assign):
            names = tuple(ast.unparse(t) for t in node.targets)
            key = ('assignment', scope, names)
        elif isinstance(node, ast.Return):
            key = ('return', scope)
        if key is not None:
            occurrence = counts.get(key, 0)
            counts[key] = occurrence + 1
            found[key + (occurrence,)] = node
        for child in ast.iter_child_nodes(node):
            visit(child, next_scope)
    visit(source(path)[1])
    return found

def constant_node(path, name):
    for node in source(path)[1].body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            return node
    raise ValueError(f'未找到字符串常量 {name}: {path}')

def difference_return(path):
    for node in source(path)[1].body:
        if isinstance(node, ast.FunctionDef) and node.name == 'difference_context':
            returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
            if len(returns) != 1:
                raise ValueError(f'difference_context 应有一个返回节点: {path}')
            return returns[0]
    raise ValueError(f'未找到 difference_context: {path}')

def resolve_current(item):
    """Map historical excerpt selections to their current AST-owned location.

    The unchanged temporary checkout supplies the historical selection anchors.
    The current file/line is discovered from AST, and the selected source text
    must still match; a future wording change fails explicitly rather than
    silently pointing at an unrelated line.
    """
    baseline_path = NEWER / item['path']
    baseline_lines, _ = source(baseline_path)
    anchors = locations(baseline_path)
    candidates = [(key, node) for key, node in anchors.items()
                  if node.lineno <= item['first'] and item['last'] <= node.end_lineno]
    if not candidates:
        raise ValueError(f'摘录不在可定位的 AST 节点内: {item}')
    key, before = min(candidates, key=lambda pair: pair[1].end_lineno - pair[1].lineno)
    destination = item['path']
    if item['path'] == SHARED:
        if key[0] != 'assignment' or key[1]:
            raise ValueError(f'原共享摘录必须属于字符串常量: {item}')
        name = key[2][0]
        destination = ENTITY if name == 'ENTITY_RULES' else RELATION
        after = constant_node(ROOT / destination, name)
    else:
        current_nodes = locations(ROOT / destination)
        if key not in current_nodes:
            raise ValueError(f'当前源码缺少原 AST 节点 {key}: {destination}')
        after = current_nodes[key]
    selected = baseline_lines[item['first'] - 1:item['last']]
    current_lines, _ = source(ROOT / destination)
    first = after.lineno + item['first'] - before.lineno
    last = first + len(selected) - 1
    if current_lines[first - 1:last] != selected:
        matches = [i + 1 for i in range(after.lineno - 1,
                   after.end_lineno - len(selected) + 1)
                   if current_lines[i:i + len(selected)] == selected]
        if len(matches) != 1:
            raise ValueError(f'摘录措辞已变化或无法唯一定位，请更新选项: {item}')
        first = matches[0]
        last = first + len(selected) - 1
    return {**item, 'path': destination, 'first': first, 'last': last,
            'reference_file': str(baseline_path),
            'reference_first': item['first'], 'reference_last': item['last'],
            'ast_anchor': repr(key)}

def piece(path, first, last, label=''):
    return {'path': path, 'first': first, 'last': last, 'label': label}

ISSUES = [
    {
        'title': '文本重建：完整保留与压缩删减冲突',
        'cn': [piece(GENERATION, 47, 59, '完整保留要求'),
               piece(GENERATION, 75, 108, '领域压缩与删减要求'),
               piece(GENERATION, 214, 231, 'User忠实性与流畅性要求')],
        'en': [],
        'note': '旧版没有text_generation模块，没有可配对的英文重建Prompt。这是中文新增模块内部的冲突。',
        'draft': '逐条忠实表达输入三元组，保留全部信息及否定、情态、条件、数量和方向。不得按领域重要性压缩或删除事实，不添加外部知识。仅在完整含义不变时合并句子；不得为连贯而添加因果、时间、组成、条件或指代关系。输出仅包含重建文本。',
    },
    {
        'title': '差异比较：只有完整语义等价的改写才忽略',
        'cn': [piece(COMPARISON, 183, 208, '差异验证与数量要求')],
        'en': [],
        'note': '旧版没有text_comparison模块，没有对应英文Prompt。A有B无与B有A无应使用相同的事实判定标准。',
        'draft': '只有完整事实含义相同的表达才视为等价，包括主客体、方向、否定、情态、条件、数量、时间及限定范围。改写、摘要或浓缩若改变或遗漏这些信息，仍应报告差异。不得凭领域常识认定文本已表达某事实。覆盖全部可核实差异，去除重复与猜测；确无差异时返回空数组。',
    },
    {
        'title': '差异比较：JSON示例需要合法',
        'cn': [piece(COMPARISON, 49, 55, '当前输出示例')],
        'en': [],
        'note': '旧版无对应模块。当前示例中的省略号和尾逗号不能作为合法JSON直接解析。',
        'draft': '仅返回合法JSON对象，无差异时使用：\n{"unique_to_text_a": [], "unique_to_text_b": []}\n有差异时两字段均为字符串数组，不使用省略号或尾逗号。',
    },
    {
        'title': '事实限定：明确最终三元组如何保留条件等信息',
        'cn': [piece(SHARED, 20, 34, '两轮共用的事实规则'),
               piece(RELATION, 50, 51, '第一轮输出字段')],
        'en': [piece(RELATION, 100, 105, '旧英文质量控制，包含相反规则'),
               piece(RELATION, 107, 117, '旧英文输出结构')],
        'note': '旧英文没有同功能的限定承载规则，且要求忽略否定。这一旧规则不应恢复。中文已有保护要求，缺的是限定在最终结果中如何保存的约定。',
        'draft': 'head、relation、tail的完整组合必须保留原文的否定、情态、条件和数量范围，必要限定不得只放入context或evidence。不能为了缩短三元组删除限制，必要时保留较长原文表达。若采用独立限定字段，须同时修改数据结构、重建输入、去重和评价。',
    },
    {
        'title': '证据：统一第一轮和第二轮的来源与充分性要求',
        'cn': [piece(RELATION, 50, 51, '第一轮context'),
               piece(RELATION, 151, 152, '第二轮evidence'),
               piece(ENTITY, 26, 27, '实体context')],
        'en': [piece(RELATION, 78, 79, '旧英文关系条件'),
               piece(RELATION, 105, 105, '旧英文关系证据要求'),
               piece(RELATION, 111, 115, '旧英文关系输出字段'),
               piece(ENTITY, 85, 94, '旧英文实体输出，无context字段')],
        'note': '英文关系要求直接引文，可以借鉴；英文实体没有context证据要求，不能把关系证据冒充实体证据。英文也没有第二轮增量证据规则。',
        'draft': 'context或evidence应逐字引用源文，覆盖支持完整事实及其限定的连续上下文。存在跨句指代时包含必要前文。不以释义替代原文证据。JSON键按各接口保留，但证据标准统一。还需代码保存证据并校验其确实来自源文。',
    },
    {
        'title': '评分：补判定锚点，不把可能性自动当作低支持度',
        'cn': [piece(SHARED, 36, 38, '当前三维评分定义'),
               piece(RELATION, 61, 62, '当前may query评分示例')],
        'en': [piece(RELATION, 81, 98, '旧英文confidence分档')],
        'note': '旧英文可以借鉴分档结构，医学实验标准及may自动降分不宜复制。当前confidence衡量抽取事实与源文是否一致，不衡量事件已发生的概率。',
        'draft': 'confidence衡量原文对完整陈述的支持度；原文明说“可能”且结果保留“可能”，可以具有高支持度。缺少原文支持的事实不应因给低分而输出。clarity衡量角色和表达是否清楚，不能因对象短语长而机械降分。relevance衡量与当前文档主题的相关性。为三维分别提供高、中、低的可观察判定示例，再统一数值区间。',
    },
    {
        'title': '实体：补全称、简称、缩写及源内别名规则',
        'cn': [piece(SHARED, 13, 13, '当前最接近的不同提及规则')],
        'en': [piece(ENTITY, 75, 77, '旧英文缩写与别名规则'),
               piece(ENTITY, 151, 151, '旧英文User别名要求')],
        'note': '当前未单列此要求，不等于模型无法识别。只吸收原文出现的形式，不恢复外部知识生成别名。',
        'draft': '原文出现的全称、简称、缩写及明确标注的别名分别保留为候选，不推测未出现的展开形式，不凭外部知识生成别名或身份关系。不同提及形式分别保留，是否等价仅依据原文明确说明。',
    },
    {
        'title': '实体：同类对象的类型名称保持一致',
        'cn': [piece(ENTITY, 25, 25, '当前类型要求')],
        'en': [piece(ENTITY, 83, 83, '旧英文一致性要求'),
               piece(ENTITY, 149, 149, '旧英文User类型要求')],
        'note': '不需要恢复固定医学类型；应在当前开放对象范围中统一命名。类型语言与命名表可在此修改稿中进一步确定。',
        'draft': '类型使用简短、贴合语境的名称，同篇文档中同类对象使用一致的类型名称和命名语言；不要将同类对象交替标为多个同义类型。不确定时填写Unknown。类型命名不能改变原文提及或缩窄允许抽取的对象范围。',
    },
    {
        'title': '实体边界：原文提及与并列共享成分补齐的例外',
        'cn': [piece(ENTITY, 37, 38, '输出中的原文提及'),
               piece(SHARED, 11, 15, '边界与并列补齐要求')],
        'en': [piece(ENTITY, 72, 74, '旧英文精确提及要求'),
               piece(ENTITY, 89, 89, '旧英文mention字段')],
        'note': '英文没有并列补齐规则。中文的合法语法补齐应保留，但不能与通常逐字保留的要求混淆。',
        'draft': '通常逐字保留源文表达及其必要限定、大小写和格式。仅对语法明确的并列项允许补齐共享成分，例如first and second cables可识别为first cable与second cable。补齐不允许翻译、同义改写或加入外部信息；证据仍引用原文。',
    },
    {
        'title': '内容语言：中文指令、源文字段和混合缩写分别规定',
        'cn': [piece(SHARED, 11, 12, '原格式要求'),
               piece(ENTITY, 25, 27, '类型及字段要求'),
               piece(GENERATION, 53, 53, 'System按实体语言决定输出'),
               piece(GENERATION, 212, 212, 'User按实体语言决定输出'),
               piece(COMPARISON, 218, 218, '比较输出语言')],
        'en': [piece(ENTITY, 72, 73, '旧英文原文保留要求')],
        'note': '两版都没有完整的集中语言约定。旧英文这里只是原文保留参考，不能冒充完整对应条款。中文关系中出现ECU等字母缩写不应自动把整段输出切换成英文。',
        'draft': '任务指令采用中文。mention、head、relation、tail及原始证据保留源文表达和语言，不为中文指令翻译英文事实。JSON键保持程序约定。type使用统一命名约定，Unknown原样保留；审校reason使用中文。混合文本按事实原表达生成，不凭字母缩写判定整段语言。',
    },
    {
        'title': '示例：补中文业务样例及第二轮实体审校样例',
        'cn': [piece(ENTITY, 40, 48, '当前初抽示例'),
               piece(ENTITY, 89, 91, '当前E2任务'),
               piece(ENTITY, 112, 116, '当前E2审校顺序')],
        'en': [piece(ENTITY, 101, 107, '旧英文实体示例')],
        'note': '两版示例源文都为英文；旧英文没有E2任务或对应样例。当前E2复用初抽输出说明，需新增审校样例。下面是新增中文示例草案，不是源码原文。',
        'draft': '新增样例源文：控制器可以查询ECU。ECU存储读数。\n当前候选：控制器、ECU、读数、GPS。当前错误三元组：控制器—包含—ECU。\n审校要点：源文中的ECU真实存在，关系错误不应导致删除ECU；GPS无源文依据，应删除；若读数漏抽，应补回。另增加中文否定、条件、并列共享成分和长宾语样例。',
    },
    {
        'title': '不确定情况：统一指代、方向和修订的保守处理',
        'cn': [piece(SHARED, 13, 13, '代词保留'),
               piece(SHARED, 22, 24, '语法角色与方向'),
               piece(RELATION, 155, 155, '第二轮无法确认的处理')],
        'en': [piece(RELATION, 76, 79, '旧英文实体及方向条件')],
        'note': '旧英文没有代词歧义或第二轮保守修订规则。保留未能确认的旧条目，不等于它已经被核实正确。',
        'draft': '不得自行补全无法确认的指代、身份、角色、关系方向或限定范围。能忠实表达的原文代词可以保留，不能无依据替换为具体对象。第一轮不新增需要猜测的事实；第二轮无足够依据修订时保留原条目，另记录待核查状态，不把保留解释为确认正确。待核查状态需要相应接口支持。',
    },
    {
        'title': 'Reader：旧生物医学领域规则需适配当前文档',
        'cn': [piece(READER, 36, 38, '角色与评分目标'),
               piece(READER, 55, 60, '低相关性分类'),
               piece(READER, 68, 73, '评分要求')],
        'en': [piece(READER, 44, 46, '旧英文角色与目标'),
               piece(READER, 63, 68, '旧英文低相关性分类'),
               piece(READER, 76, 81, '旧英文评分要求')],
        'note': '这是旧英文继承问题；不能说中文翻译漏掉技术领域规则。Reader默认评分，但当前不按此结果裁剪默认抽取全文。',
        'draft': '根据段落包含源文可支持事实的潜力评分，覆盖动作、状态、定义、组成、属性与比较。设备描述、操作流程、系统组件和条件参数可能具有很高抽取价值，不能仅因文档类型而判低相关。不使用生物医学术语密度作为通用文档评分标准。',
    },
    {
        'title': 'Summarizer：任务领域、长度和输入名称冲突（默认关闭）',
        'cn': [piece(SUMMARY, 35, 37, '当前System角色和长度'),
               piece(SUMMARY, 61, 65, '当前System输出要求'),
               piece(SUMMARY, 128, 139, '当前User任务和长度')],
        'en': [piece(SUMMARY, 35, 37, '旧英文System'),
               piece(SUMMARY, 61, 65, '旧英文System输出'),
               piece(SUMMARY, 126, 140, '旧英文User')],
        'note': 'System近似翻译，User从医学摘要改成技术压缩，产生100词与400—600词冲突。此模块默认关闭，重新开启前统一；不能把它当作当前默认流程已经造成摘要遗漏。',
        'draft': '启用前先确定摘要的业务用途，再统一System、User与代码长度限制。输入是源文档，不应误称三元组。需要完整事实抽取时，应避免把压缩摘要作为唯一事实来源；若不需要摘要，保持默认关闭。',
    },
    {
        'title': 'Summarizer：示例不应将并列观察强化为因果（默认关闭）',
        'cn': [piece(SUMMARY, 69, 71, '当前示例')],
        'en': [piece(SUMMARY, 69, 71, '旧英文示例')],
        'note': '英文原示例也使用by decreasing COX-2，中文通过降低COX-2继承了同样的因果强化。此处是两版共有问题。',
        'draft': '摘要只能保留源文明确支持的因果或机制。原文并列报告治疗后指标变化时，描述观察到的各项变化，不额外写成“通过某变化导致另一结果”。',
    },
    {
        'title': 'Ingestion：估算年份与不猜测冲突（元数据调用停用）',
        'cn': [piece('karma/agents/ingestion/agent.py', 56, 59, '日期字段规则'),
               piece('karma/agents/ingestion/agent.py', 62, 66, '准确性规则')],
        'en': [piece('karma/agents/ingestion/agent.py', 70, 73, '旧英文日期规则'),
               piece('karma/agents/ingestion/agent.py', 76, 80, '旧英文准确性规则')],
        'note': '冲突是旧英文继承的；当前元数据模型调用停用。该文件User仍为英文，如以后启用，应一并改为中文任务指令。',
        'draft': '只提取文中明确给出的发表日期；缺失时使用Unknown，不根据研究内容、文风或引用推测年份。若业务需要日期推断，应单列推断字段及依据，不能冒充文档已给出的元数据。',
    },
]

manifest = []

def link(path, first=None):
    suffix = f':{first}' if first else ''
    return f'[{path.name}{suffix}](<{path.as_posix()}{suffix}>)'

def current_code_link(path, first, last=None):
    item = resolve_current(piece(path, first, last or first))
    return (f'{link(ROOT / item["path"], item["first"])}，'
            f'第{item["first"]}—{item["last"]}行')

def extract(base, item):
    if base == ROOT:
        item = resolve_current(item)
    path = base / item['path']
    raw = path.read_text(encoding='utf-8-sig')
    lines = raw.splitlines()
    assert 1 <= item['first'] <= item['last'] <= len(lines), item
    selected = lines[item['first'] - 1:item['last']]
    # Remove only Python string delimiters, keeping prompt wording and indentation.
    selected[0] = re.sub(r'^\s*(?:system_prompt|ENTITY_RULES|FACT_RULES|SCORE_RULES)\s*=\s*(?:f)?"""', '', selected[0])
    selected[-1] = re.sub(r'"""\s*$', '', selected[-1])
    text = '\n'.join(selected)
    manifest.append({'file': str(path), 'first_line': item['first'], 'last_line': item['last'],
                     'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'excerpt_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                     **{key: value for key, value in item.items()
                        if key.startswith('reference_') or key == 'ast_anchor'}})
    return path, text, item

doc = [
    '# 中英文 Prompt 逐项对照与修改稿（合并后）',
    '',
    '日期：2026年10月8日。已确定采用中文Prompt；本文件用于检查规则及编辑修改草案。主目录已完成未提交的Prompt位置整理，实际措辞保持不变；下列规则修改草案尚未应用。',
    '',
    '## 版本与使用方式',
    '',
    '- GitHub仓库：<https://github.com/lichuanpei12-coder/KARMA>。',
    r'- 当前主目录 `E:\huawei after\KARMA` 的Git HEAD仍为main的 `127f1a1399376fb5e9214cb656b045ca9a698a0b`；最近线上核查的远程main为同一提交。当前实体、关系与支持工具源码已有未提交的位置整理，HEAD相同不表示工作树未修改。',
    '- 更新分支为 `codex/feedback-comparison-entity`，领先main两个提交，最新为 `9d6883e2e56a008ecf70bb5ca695fead32a1abea`，北京时间2026年9月11日11:06:48。',
    r'- 更新分支本地副本在 `E:\huawei after\临时\KARMA`，HEAD为上述9d6883e；保留合并前布局，本次未修改。两个目录的实体、关系和支持工具文件现在字节不同，不能沿用历史“8文件相同”结论描述当前状态。',
    r'- 中文摘录来自当前主目录；旧英文摘录来自 `E:\huawei after\KARMA\旧版\KARMA`。当前中文位置通过AST定位，旧英文行号保持不变；临时副本的实体/关系行号不适用本稿。',
    '- ENTITY_RULES已移入实体agent；FACT_RULES、SCORE_RULES已移入关系agent；两份difference_context分别在各agent中。extraction_support仅保留结构解析与工具函数。',
    '- 已有迁移验证记录确认8个实际请求的system/user/parameters逐字一致且无网络调用；这验证位置整理未改变Prompt，不表示修改草案已执行或模型效果已验证。',
    '- 每项按“当前中文原文—旧英文原文—区别与建议—中文修改草案—我的修改记录”排列。可直接编辑草案和修改记录。',
    '- 摘录保留源码中的Prompt措辞和行号，只移除Python字符串包裹；不把注释、中文回译或新写英文冒充原文。',
    '- 旧版无对应条款时明确标注。完整核心模板和源文件链接另见同目录 `核心Prompt完整模板参考_合并后.md`。旧两份Markdown及原摘录定位JSON保留。',
    '',
    '## 修改项索引',
    '',
    '| 编号 | 修改项 | 有旧英文参考 |',
    '|---|---|---|',
]
for i, issue in enumerate(ISSUES, 1):
    doc.append(f'| {i:02d} | {issue["title"]} | {"有，适用程度见该项说明" if issue["en"] else "无对应模块"} |')

for i, issue in enumerate(ISSUES, 1):
    doc += ['', f'## {i:02d}. {issue["title"]}', '', '### 当前中文原文', '']
    for item in issue['cn']:
        path, text, item = extract(ROOT, item)
        doc += [f'**{item["label"]}**：{link(path, item["first"])}，第{item["first"]}—{item["last"]}行。', '', '```text', text, '```', '']
    doc += ['### 旧英文原文', '']
    if not issue['en']:
        doc += ['**无对应英文模块或条款。** 不补造英文原文。', '']
    for item in issue['en']:
        path, text, item = extract(OLD, item)
        doc += [f'**{item["label"]}**：{link(path, item["first"])}，第{item["first"]}—{item["last"]}行。', '', '```text', text, '```', '']
    doc += ['### 区别与建议', '', issue['note'], '', '### 中文修改草案（尚未应用，可直接编辑）', '',
            '```text', issue['draft'], '```', '', '### 我的修改记录', '', '- 采用的措辞：', '- 需要进一步确认的规则：', '- 对应源码修改位置：', '']

doc += [
    '## 配套代码问题：与Prompt修改分开处理', '',
    '| 问题 | 位置 | 原因 |', '|---|---|---|',
    f'| 实体context未强制验证 | {current_code_link(ENTITY, 144, 155)} | 目前主要验证mention，证据缺失仍可接受 |',
    f'| 三元组对象未保存证据 | {current_code_link(RELATION, 376, 391)}；{current_code_link("karma/core/data_structures.py", 30)} | 原回复在审计中，标准结果没有context/evidence字段 |',
    f'| 第二轮evidence仅检查非空 | {current_code_link(RELATION, 328)} | 没验证逐字来自源文 |',
    f'| 去重只用小写头关系尾 | {current_code_link(RELATION, 536)} | 不能区分只存在于证据中的不同条件 |',
    f'| 比较解析失败返回空差异 | {current_code_link(COMPARISON, 258, 267)} | 与真正没有差异混淆 |',
    f'| 调用失败用两侧前200字代替差异 | {current_code_link(COMPARISON, 307, 314)} | 这些是未比较的文本片段，不能当成已核实差异 |',
    '',
    'Evaluator、Conflict和Schema现行执行的是Python评分或规则，不是把system文字交给模型完成所有检查。修改其文字不能代替实现修改。当前未调用的医学评分备用函数也不能作为现行模型已被医学规则错误评分的证据。',
    '',
    '## 建议修改顺序', '',
    '先处理01—05的当前反馈与事实保真问题，再完善06—12的核心规则。13的Reader需适配当前领域；14—16为关闭或停用模块，启用前处理。配套代码问题需与证据及错误状态一起实现。修改后的验证使用实际业务样本，检查忠实性、完整性和反馈准确性。',
]
PAIRED_PATH.write_text('\n'.join(doc) + '\n', encoding='utf-8')
MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

# Expand rules now owned by the entity/relation modules using AST only.
# extraction_support contains tools only; no source module is imported.
rule_nodes = {name: (relative, constant_node(ROOT / relative, name))
              for name, relative in (('ENTITY_RULES', ENTITY),
                                     ('FACT_RULES', RELATION),
                                     ('SCORE_RULES', RELATION))}
env = {name: node.value.value for name, (_, node) in rule_nodes.items()}
diff_returns = {relative: difference_return(ROOT / relative)
                for relative in (ENTITY, RELATION)}
diff_return = diff_returns[ENTITY]

def render(node, output_example=''):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, '{动态输入：' + node.id + '}')
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return render(node.left, output_example) + render(node.right, output_example)
    if isinstance(node, ast.JoinedStr):
        return ''.join(render(n.value, output_example) if isinstance(n, ast.FormattedValue)
                       else render(n, output_example) for n in node.values)
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func)
        if name.endswith('_output_instructions'):
            return output_example
        if name == 'difference_context':
            return render(diff_return.value)
        if name == 'json.dumps':
            return '{动态JSON输入：' + ast.unparse(node.args[0]) + '}'
    return '{动态输入：' + ast.unparse(node) + '}'

templates = ['# 核心Prompt完整模板参考（合并后）', '',
             '由源码AST提取，不执行代理、不调用模型。中文两轮共享规则已展开。动态文档、实体、三元组、差异等以花括号占位，保留变量表达式便于追溯；这不是某次实际模型请求。', '',
             r'主目录E:\huawei after\KARMA已完成未提交的位置整理：ENTITY_RULES位于实体agent，FACT_RULES/SCORE_RULES位于关系agent，两份difference_context分别位于各agent。Git HEAD仍为main的127f1a1，实际Prompt措辞未改；修改草案未应用。',
             r'E:\huawei after\临时\KARMA保持原布局，HEAD为9d6883e，未随本次整理修改。两个目录当前源文件不再全部字节相同，不能复用历史相同行号；本文链接定位当前主目录。',
             '历史8文件相同记录保留为整理前核查。迁移验证记录另确认8个实际请求的system/user/parameters逐字一致且无网络调用。原两份Markdown和摘录定位JSON保留，本文另存为合并后版本。', '',
             '中文当前模板与旧英文模板按模块放在一起。旧英文为旧版医学任务，新增模块无对应英文。可选差异拼接单列；运行时数据处理与分支控制不在模板文本中重现。', '']

METHODS = {
    'entity_extraction': ['__init__', '_output_instructions', '_extract_entities_from_text', 'revise_entities'],
    'relationship_extraction': ['__init__', '_extract_relationships_from_text', 'revise_relationships'],
    'text_generation': ['__init__', '_build_generation_prompt'],
    'text_comparison': ['__init__', '_build_comparison_prompt'],
    'reader': ['__init__', '_batch_score_relevance'],
    'summarizer': ['__init__', '_summarize_single_segment'],
}
for mod, methods in METHODS.items():
    templates += [f'## {mod}', '']
    for base, language in ((ROOT, '当前中文'), (OLD, '旧英文')):
        path = base / 'karma/agents' / mod / 'agent.py'
        templates += [f'### {language}', '']
        if not path.exists():
            templates += ['旧版无此模块，无法提供对应英文模板。', '']
            continue
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        if base == ROOT and mod in ('entity_extraction', 'relationship_extraction'):
            diff_return = diff_returns[ENTITY if mod == 'entity_extraction' else RELATION]
        output_example = ''
        if '_output_instructions' in funcs:
            returns = [n for n in ast.walk(funcs['_output_instructions']) if isinstance(n, ast.Return)]
            if len(returns) != 1:
                raise ValueError(f'_output_instructions 应有一个返回节点: {path}')
            output_example = render(returns[0].value)
        emitted = 0
        for method in methods:
            # Old core methods have their original names; choose those containing prompts.
            candidates = [funcs[method]] if method in funcs else []
            if base == OLD and method == '_extract_entities_from_text' and not candidates:
                candidates = [fn for name, fn in funcs.items() if name in ('_extract_entities', 'extract_entities')]
            if base == OLD and method == '_extract_relationships_from_text' and not candidates:
                candidates = [fn for name, fn in funcs.items() if name in ('_extract_relationships', 'extract_relationships')]
            for fn in candidates:
                for node in ast.walk(fn):
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('system_prompt', 'prompt', 'revision_system_prompt') for t in node.targets):
                        if isinstance(node.value, ast.Call):
                            continue
                        text = render(node.value, output_example)
                        if any(isinstance(t, ast.Name) and t.id == 'prompt' for t in node.targets):
                            for extra in fn.body:
                                if (isinstance(extra, ast.AugAssign)
                                        and isinstance(extra.target, ast.Name)
                                        and extra.target.id == 'prompt'
                                        and isinstance(extra.value, ast.Call)
                                        and ast.unparse(extra.value.func).endswith('_output_instructions')):
                                    text += render(extra.value, output_example)
                    elif fn.name == '_output_instructions' and isinstance(node, ast.Return):
                        text = render(node.value, output_example)
                    else:
                        continue
                    templates += [f'**{fn.name}**：{link(path, node.lineno)}，源码第{node.lineno}—{node.end_lineno}行。', '', '```text', text, '```', '']
                    emitted += 1
        if emitted == 0:
            templates += ['此版本未找到同名模板，逐项摘录仍在主对照稿中。', '']

templates += ['## 中文模块内共用规则与可选差异上下文', '',
              '规则现已放回所属agent，保留两轮复用。修改difference_context时须同步实体和关系中的两份定义。', '']
for name, value in env.items():
    relative, node = rule_nodes[name]
    templates += [f'### {name}', '', f'位置：{link(ROOT / relative, node.lineno)}。', '',
                  '```text', value, '```', '']
for relative, node in diff_returns.items():
    templates += [f'### difference_context：{relative}', '',
                  f'位置：{link(ROOT / relative, node.lineno)}。第一轮可选拼接，第二轮模板中已展开。',
                  '', '```text', render(node.value), '```', '']
TEMPLATE_PATH.write_text('\n'.join(templates) + '\n', encoding='utf-8')

record_path = OUT / 'Git线上核查记录.json'
record = json.loads(record_path.read_text(encoding='utf-8'))
current_comparison = []
for rel in (SHARED, ENTITY, RELATION, GENERATION, COMPARISON, READER, SUMMARY, 'karma/core/pipeline.py'):
    current_hash = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    newer_hash = hashlib.sha256((NEWER / rel).read_bytes()).hexdigest()
    current_comparison.append({'path': rel, 'root_sha256': current_hash,
                               'temporary_sha256': newer_hash,
                               'equal': current_hash == newer_hash})
# Earlier remote evidence and the historical eight-file equality list remain.
record['prompt_reorganization_check'] = {
    'checked_date': '2026-10-08',
    'root_directory': str(ROOT),
    'root_git_head': record['local_head'],
    'root_has_uncommitted_source_reorganization': True,
    'temporary_directory': str(NEWER),
    'temporary_copy_modified_by_this_run': False,
    'historical_verified_identical_files_preserved': True,
    'description': 'Prompt常量和difference_context移回实体/关系agent；工具保留于extraction_support。当前源码位置不同，实际Prompt措辞未改。',
    'actual_request_validation_record': str(MIGRATION_PATH),
    'actual_request_validation': json.loads(MIGRATION_PATH.read_text(encoding='utf-8')),
    'current_file_comparison': current_comparison,
    'current_rule_locations': [
        {'name': name, 'path': relative, 'first_line': node.lineno,
         'last_line': node.end_lineno} for name, (relative, node) in rule_nodes.items()],
}
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'issues': len(ISSUES), 'excerpts': len(manifest),
                  'paired_document': str(PAIRED_PATH), 'templates_document': str(TEMPLATE_PATH),
                  'historical_identical_files_preserved': len(record['verified_identical_files']),
                  'current_equal_files': sum(item['equal'] for item in current_comparison),
                  'current_different_files': [item['path'] for item in current_comparison if not item['equal']]},
                 ensure_ascii=False))
