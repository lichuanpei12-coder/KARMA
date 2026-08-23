import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


OUT = Path(r"E:\huawei after\paper\GPT基础推荐")
HEADERS = [
    "序号", "论文名称", "会议/期刊", "年份", "知识抽取主题", "主要内容",
    "为什么值得读", "优先级", "阅读难度", "建议阅读方式", "论文链接", "代码/项目链接"
]

ROWS = [
    [1, "Open Information Extraction from the Web", "IJCAI", 2007, "OpenIE基础",
     "TextRunner奠基工作：在不预定义关系类型的情况下，从大规模网页文本自动抽取关系。",
     "建立OpenIE的问题意识和基本任务定义。", "必读", "中", "精读摘要、引言、任务定义和实验结论；旧分类器细节可略读。",
     "https://www.ijcai.org/Proceedings/07/Papers/429.pdf", ""],
    [2, "Open Information Extraction: The Second Generation", "IJCAI", 2011, "规则与约束",
     "ReVerb通过句法和词汇约束减少不完整、无意义的开放关系。",
     "理解规则、约束与Precision/Recall之间的关系。", "必读", "中", "重点阅读约束设计、错误类型和与TextRunner的比较。",
     "https://www.ijcai.org/Proceedings/11/Papers/012.pdf", ""],
    [3, "ClausIE: Clause-Based Open Information Extraction", "WWW", 2013, "句法型OpenIE",
     "根据英语从句类型、依存句法和语法成分抽取关系及其参数。",
     "典型传统句法方法，适合建立实体—谓词—参数的直观认识。", "必读", "中", "结合例句追踪从句识别到三元组生成过程。",
     "https://doi.org/10.1145/2488388.2488420", "https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/ambiverse-nlu/clausie"],
    [4, "REBEL: Relation Extraction By End-to-End Language Generation", "Findings EMNLP", 2021, "生成式关系抽取",
     "把关系抽取转化为序列到序列生成，并设计三元组线性化形式。",
     "从分类式关系抽取过渡到生成式知识抽取的清晰入口。", "必读", "中", "阅读输出线性化方式，并运行预训练模型完成三元组抽取。",
     "https://aclanthology.org/2021.findings-emnlp.204/", "https://github.com/Babelscape/rebel"],
    [5, "Unified Structure Generation for Universal Information Extraction", "ACL Long", 2022, "Universal IE",
     "用统一结构语言和Schema Prompt统一实体、关系、事件及情感抽取。",
     "理解现代通用信息抽取、Schema提示和Text-to-Structure范式的基础。", "必读", "中高", "精读统一结构表示和Schema Instructor；之后运行推理示例。",
     "https://aclanthology.org/2022.acl-long.395/", "https://github.com/universal-ie/UIE"],
    [6, "DeepKE: A Deep Learning Based Knowledge Extraction Toolkit", "EMNLP Demo", 2022, "知识抽取工具箱",
     "支持NER、属性、关系、文档级、低资源和多模态知识抽取。",
     "适合从工程角度比较传统监督模型、深度学习方法和LLM方法。", "必做", "中", "先运行NER或标准关系抽取示例，不要一次安装所有模块。",
     "https://aclanthology.org/2022.emnlp-demos.10/", "https://github.com/zjunlp/DeepKE"],
    [7, "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer", "NAACL Long", 2024, "开放类型NER",
     "根据用户给出的任意实体类型，从文本中识别相应实体。",
     "代码简单、模型较轻，是工业实体抽取最合适的第一个实践项目。", "必做", "低", "用20—50段工业文本和5—8种自定义类型建立零样本NER基线。",
     "https://aclanthology.org/2024.naacl-long.300/", "https://github.com/urchade/GLiNER"],
    [8, "UniversalNER: Targeted Distillation from Large Language Models for Open NER", "ICLR", 2024, "开放NER与蒸馏",
     "把大模型的开放实体识别能力定向蒸馏到较小的专用模型。",
     "理解开放类型NER、跨领域泛化、合成标注和模型蒸馏。", "推荐", "中高", "与GLiNER对照阅读；重点看数据构建、类型泛化和评测。",
     "https://proceedings.iclr.cc/paper_files/paper/2024/hash/34678d08b36076de986df95c5bbba92f-Abstract-Conference.html", "https://github.com/universal-ner/universal-ner"],
    [9, "GoLLIE: Annotation Guidelines Improve Zero-Shot Information-Extraction", "ICLR", 2024, "Schema-guided IE",
     "用Python类、docstring和详细标注指南表示动态Schema，完成零样本实体、关系和事件抽取。",
     "直接说明Schema为何不能只有标签名称，以及定义、规则、示例和反例如何控制抽取。", "必读", "中高", "先阅读自定义任务Notebook和Schema定义；有GPU后再运行7B模型。",
     "https://openreview.net/forum?id=Y3wpuxd7u9", "https://github.com/hitz-zentroa/GoLLIE"],
    [10, "KnowCoder: Coding Structured Knowledge into LLMs for Universal Information Extraction", "ACL Long", 2024, "代码式Schema",
     "把实体、关系和事件Schema编码成代码，通过代码生成完成通用知识抽取。",
     "理解类型系统、复杂结构输出以及代码表示对Schema约束的作用。", "必读", "高", "先读Schema表示和推理案例，不建议作为第一个完整复现项目。",
     "https://aclanthology.org/2024.acl-long.475/", "https://github.com/ICT-GoKnow/KnowCoder"],
    [11, "Learning to Extract Structured Entities Using Language Models", "EMNLP Main", 2024, "结构化实体与评价",
     "提出多阶段结构化实体抽取MuSEE及AESOP评价指标，处理具有内部属性的复杂实体。",
     "工业对象通常包含属性、数值和单位；该工作有助于超越简单实体名称抽取。", "必读", "中高", "重点阅读任务定义、多阶段分解、Exact Match不足和AESOP指标。",
     "https://aclanthology.org/2024.emnlp-main.388/", "https://github.com/microsoft/Structured-Entity-Extraction"],
    [12, "Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction", "EMNLP Main", 2024, "关系抽取与Schema规范化",
     "EDC执行开放关系抽取、关系定义、Schema诱导和后处理规范化。",
     "最贴近从开放抽取到统一知识库的关键过渡，能研究关系同义和Schema对齐。", "必做", "中", "在小型工业文本上运行；分析关系错误合并、错误拆分和Schema检索。",
     "https://aclanthology.org/2024.emnlp-main.548/", "https://github.com/clear-nus/edc"],
    [13, "OneKE: A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction System", "WWW Companion/Demo", 2025, "Schema-guided LLM抽取系统",
     "支持文本、网页和PDF，以及多类Schema-guided知识抽取任务和错误案例修正。",
     "适合观察完整知识抽取系统如何组织Schema、模型、工具和纠错。", "必做", "中高", "先跑最简单文本样例，只跟踪一条输入—Schema—输出链路。",
     "https://arxiv.org/abs/2412.20005", "https://github.com/zjunlp/OneKE"],
    [14, "GLiNER2: Schema-Driven Multi-Task Learning for Structured Information Extraction", "EMNLP Demo", 2025, "轻量结构化抽取",
     "将GLiNER扩展到实体、分类和Schema驱动的结构化字段抽取。",
     "工程门槛较低，适合快速建立可运行的结构化抽取基线。", "推荐实践", "低", "在完成GLiNER后运行；注意Demo论文与主会长文的学术权重不同。",
     "https://aclanthology.org/2025.emnlp-demos.10/", "https://github.com/fastino-ai/GLiNER2"],
    [15, "AutoSchemaKG: Autonomous Knowledge Graph Construction through Dynamic Schema Induction", "ACL", 2026, "动态Schema诱导",
     "从大规模语料中进行概念化、动态Schema induction和知识图谱构建。",
     "对应长期研究中的动态Schema和自动KG构建，但系统规模较大。", "进阶", "高", "先读架构和小规模实验，只复现Schema induction子流程。",
     "https://arxiv.org/abs/2505.23628", "https://github.com/HKUST-KnowComp/AutoSchemaKG"],
    [16, "ReLiK: Retrieve and LinK, Fast and Accurate Entity Linking and Relation Extraction on an Academic Budget", "Findings ACL", 2024, "实体链接与关系抽取",
     "采用Retriever—Reader架构，先检索候选实体或关系，再用一次前向计算完成文本跨度链接与关系抽取。",
     "知识库构建不仅要识别实体，还要把实体链接到统一ID；该项目轻量、代码成熟，适合动手。", "必做", "中", "先运行实体链接示例，再尝试关系抽取；重点观察候选召回错误与Reader判断错误。",
     "https://aclanthology.org/2024.findings-acl.839/", "https://github.com/SapienzaNLP/relik"],
    [17, "ADELIE: Aligning Large Language Models on Information Extraction", "EMNLP Main", 2024, "LLM统一信息抽取",
     "构建IEInstruct与IEFeedback，通过指令微调和DPO让LLM同时处理封闭、开放和按需信息抽取。",
     "帮助理解通用IE模型的数据如何组织，以及SFT、偏好优化与多任务抽取之间的关系。", "必读", "高", "先读任务分类和数据统一格式；基础阶段直接运行1.5B或3B模型，不要从头训练7B。",
     "https://aclanthology.org/2024.emnlp-main.419/", "https://github.com/THU-KEG/ADELIE"],
    [18, "LogicST: A Logical Self-Training Framework for Document-Level Relation Extraction with Incomplete Annotations", "EMNLP Main", 2024, "文档级关系抽取",
     "利用逻辑规则诊断伪标签冲突，缓解DocRE数据中因事实未完全标注造成的大量假阴性问题。",
     "补足跨句关系、弱标注和神经—符号结合知识；这些问题在工业长文中非常常见。", "推荐", "高", "先理解DocRED、假阴性和自训练，再看逻辑诊断模块；不必立即完整复现训练。",
     "https://aclanthology.org/2024.emnlp-main.314/", "https://github.com/XingYing-stack/LogicST"],
    [19, "Toward Reliable Ad-hoc Scientific Information Extraction: A Case Study on Two Materials Dataset", "Findings ACL", 2024, "科学文献可靠抽取",
     "用GPT-4按临时Schema从材料科学全文抽取数据，并与领域专家合作进行细致人工错误分析。",
     "与工业科研文档场景高度相似；价值主要在失败模式、可靠性评价和人工复核设计，而非刷榜。", "必读", "中", "重点精读错误分类和研究建议；把其中的错误类型改造成自己的抽取检查清单。",
     "https://aclanthology.org/2024.findings-acl.897/", ""],
    [20, "Learning to Generate Structured Output with Schema Reinforcement Learning", "ACL Long", 2025, "Schema约束与输出验证",
     "构建约4万种JSON Schema的SchemaBench，并用细粒度Schema验证器提供强化学习奖励，提高合法JSON生成能力。",
     "虽不是纯IE论文，却直接解决抽取系统最常见的结构不合法、字段类型错误和Schema不服从问题。", "推荐实践", "中高", "先运行SchemaBench或验证器；把自己的抽取JSON Schema接入验证，不必先训练强化学习模型。",
     "https://aclanthology.org/2025.acl-long.243/", "https://github.com/thunlp/SchemaReinforcementLearning"],
    [21, "Adaptive Schema-aware Event Extraction with Retrieval-Augmented Generation", "Findings EMNLP", 2025, "Schema-aware事件抽取",
     "ASEE先从大量候选中检索并改写适用事件Schema，再生成目标结构；MD-SEE整合12个多领域、多语言数据集。",
     "补足事件抽取与大Schema集合选择问题，适合研究Schema动态选择及幻觉控制。", "推荐", "中高", "先看任务定义与MD-SEE，再运行单数据集示例；与GoLLIE的固定输入Schema方式对照。",
     "https://aclanthology.org/2025.findings-emnlp.419/", "https://github.com/USTC-StarTeam/ASEE"],
    [22, "Schema-adaptable Knowledge Graph Construction", "Findings EMNLP", 2023, "动态Schema适应",
     "提出Schema-adaptable KGC任务，以横向、纵向和混合Schema扩展评测模型无需重训练适应新实体、关系和事件类型的能力，并提出AdaKGC。",
     "直接对应动态Schema与持续知识图谱构建，是从UIE过渡到AutoSchemaKG的重要论文。", "必读", "中高", "重点阅读任务定义、三种Schema扩展和动态解码；随后运行AdaKGC样例。",
     "https://aclanthology.org/2023.findings-emnlp.425/", "https://github.com/zjunlp/AdaKGC"],
    [23, "RexUIE: A Recursive Method with Explicit Schema Instructor for Universal Information Extraction", "Findings EMNLP", 2023, "复杂Schema统一抽取",
     "通过显式Schema Instructor和递归抽取处理三元组、四元组、五元组等复杂结构，改善类型间错误连接。",
     "补充UIE在复杂和嵌套Schema上的不足，有助于理解复杂工业对象及其属性关系如何表示。", "推荐", "中高", "在UIE之后阅读，重点比较隐式与显式Schema；暂不要求完整复现。",
     "https://aclanthology.org/2023.findings-emnlp.1024/", ""],
    [24, "SocraticKG: Knowledge Graph Construction via QA-Driven Fact Extraction", "Findings ACL", 2026, "QA驱动知识图谱构建",
     "先用5W1H生成自包含问答，再从问答抽取原子三元组，改善直接抽取时事实覆盖率与图连通性之间的矛盾。",
     "方法直观并有代码，适合用工业长文比较直接三元组抽取和问答分解抽取。", "推荐实践", "中", "选一篇技术文档做两种流程对照，统计遗漏、幻觉、证据可追溯性和图连通性。",
     "https://aclanthology.org/2026.findings-acl.1951/", "https://github.com/LABA-SNU/SocraticKG"],
    [25, "Capability Decomposition for Unified Information Extraction via Hierarchical Mixture-of-Experts", "ACL Long", 2026, "能力分解与统一IE",
     "UC-UIE将抽取显式分解为判断、定位、关联三种能力，并以LoRA层次化MoE适配器实现参数高效训练。",
     "代表统一信息抽取的最新模型设计，但LoRA、MoE与路由机制对基础阶段偏难。", "进阶", "高", "目前只读摘要、引言、能力分解图和实验结论；掌握UIE与ADELIE后再精读。",
     "https://aclanthology.org/2026.acl-long.561/", ""],
    [26, "LLMs as Knowledge Graph Refiners: Mitigating Factual Inconsistencies in Generative Knowledge Extraction", "ACL Long", 2026, "三元组事实纠错",
     "GraphRefine分析生成式知识抽取中的事实不一致，让微调LLM逐三元组选择保留、删除、修改或重写。",
     "补足抽取后的质量控制与事实一致性环节，对工业知识库的可靠构建和维护非常重要。", "必读", "中高", "重点阅读错误分类、修正操作和评价方法；把错误分类加入自己的抽取检查表。",
     "https://aclanthology.org/2026.acl-long.1353/", ""],
]


def write_csv(path: Path):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(ROWS)


def write_xlsx(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "知识抽取论文推荐"
    ws.append(HEADERS)
    for row in ROWS:
        ws.append(row)

    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    odd_fill = PatternFill("solid", fgColor="EAF2F8")
    even_fill = PatternFill("solid", fgColor="FFFFFF")
    must_fill = PatternFill("solid", fgColor="FFF2CC")
    practice_fill = PatternFill("solid", fgColor="E2F0D9")
    border = Border(
        left=Side(style="thin", color="C8C8C8"),
        right=Side(style="thin", color="C8C8C8"),
        top=Side(style="thin", color="C8C8C8"),
        bottom=Side(style="thin", color="C8C8C8"),
    )

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border

    for r in range(2, ws.max_row + 1):
        base_fill = odd_fill if r % 2 == 0 else even_fill
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(r, c)
            cell.fill = base_fill
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        priority = ws.cell(r, 8).value
        if priority in {"必读", "必做"}:
            ws.cell(r, 8).fill = must_fill if priority == "必读" else practice_fill
            ws.cell(r, 8).font = Font(bold=True, color="9C6500" if priority == "必读" else "375623")
        for c in (1, 3, 4, 8, 9):
            ws.cell(r, c).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    widths = {
        1: 7, 2: 48, 3: 22, 4: 9, 5: 24, 6: 48,
        7: 48, 8: 12, 9: 12, 10: 52, 11: 48, 12: 48,
    }
    for idx, width in widths.items():
        ws.column_dimensions[get_column_letter(idx)].width = width

    ws.row_dimensions[1].height = 32
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 82

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    ws.print_title_rows = "1:1"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    guide = wb.create_sheet("使用说明")
    guide_rows = [
        ["项目", "说明"],
        ["推荐实践顺序", "GLiNER → JSON Schema + LLM → EDC → OneKE → KARMA对照"],
        ["必读", "应认真阅读任务定义、方法、实验和局限。"],
        ["必做", "除阅读外，建议实际运行代码并保存自己的输入、输出和错误分析。"],
        ["推荐/推荐实践", "根据当前学习进度选择性阅读或运行。"],
        ["进阶", "完成基础任务后再进入，不建议现在完整复现。"],
        ["本轮补检来源", "PaperNotes用于发现线索；正式会议与论文信息由ACL Anthology/DBLP核验，代码链接由论文或作者GitHub核验。"],
        ["新增论文", "第16—21篇补充实体链接、统一IE训练、文档级关系、科学文献可靠抽取、JSON Schema约束和事件抽取；第22—26篇补充动态Schema、复杂UIE、QA驱动构图、能力分解与三元组纠错。"],
        ["CSV说明", "CSV不支持颜色、列宽和冻结表头；上述格式仅保存在XLSX文件中。"],
    ]
    for row in guide_rows:
        guide.append(row)
    guide.column_dimensions["A"].width = 22
    guide.column_dimensions["B"].width = 90
    for cell in guide[1]:
        cell.fill = header_fill
        cell.font = header_font
    for row in guide.iter_rows():
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    guide.freeze_panes = "A2"
    guide.sheet_view.showGridLines = False

    wb.save(path)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "知识抽取论文推荐.csv")
    write_xlsx(OUT / "知识抽取论文推荐.xlsx")
    print(OUT / "知识抽取论文推荐.csv")
    print(OUT / "知识抽取论文推荐.xlsx")
