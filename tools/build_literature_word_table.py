from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Inches, Pt, RGBColor


OUT = Path(r"E:\huawei after\KARMA\outputs\自反馈开发信息抽取相关论文参考表.docx")


GROUPS = [
    (
        "一 综述与研究全景",
        [
            {
                "date": "2024.11\nFindings of EMNLP",
                "title": "A Survey on Open Information Extraction from Rule-based Model to Large Language Model",
                "url": "https://aclanthology.org/2024.findings-emnlp.560/",
                "boundary": "OpenIE 专项综述\n关系类型不预定义",
                "summary": "按规则方法、神经方法和大语言模型方法回顾 OpenIE，讨论数据集、评价方法、跨语言和开放关系规范化。适合建立开放三元组抽取的概念边界，也是本项目说明“为什么关系集合不能完全预定义”的主要综述依据。",
            },
            {
                "date": "2025.01\nCOLING 主会",
                "title": "A Survey of Generative Information Extraction",
                "url": "https://aclanthology.org/2025.coling-main.324/",
                "boundary": "生成式 IE 综述\n以封闭 Schema 为主",
                "summary": "系统整理生成式 NER、关系抽取和事件抽取，重点讨论输出线性化、提示学习、约束解码、数据增强、大小模型协作及统一信息抽取。正文明确把长文档 IE、OpenIE 和低资源 IE 列为未来方向；但主体仍以预定义 Schema 的封闭式抽取为主。",
            },
            {
                "date": "2025.07\nArtificial Intelligence Review",
                "title": "A Survey on Cutting-edge Relation Extraction Techniques Based on Language Models",
                "url": "https://link.springer.com/article/10.1007/s10462-025-11280-0",
                "boundary": "关系抽取综述\n句子级 文档级 少样本",
                "summary": "分析 2020 至 2023 年 ACL 系列会议中的 137 篇论文，覆盖传统关系抽取、少样本和文档级关系抽取。综述显示 BERT 和 RoBERTa 类模型在标准基准上仍占主导，LLM 尚未全面替代专用模型；发表时间较新，但统计文献主要截止到 2023 年。",
            },
            {
                "date": "2025\n山西大学学报 自然科学版",
                "title": "关系抽取方法研究综述",
                "url": "https://cjournal.hep.com.cn/0253-2395/CN/PDF/10.13451/j.sxu.ns.2025015",
                "boundary": "中文 RE 综述\n传统方法到 LLM",
                "summary": "从规则、机器学习和深度学习梳理到大语言模型，讨论提示学习、数据生成、联合抽取和不确定性过滤。总结的数据噪声、跨领域泛化、重叠关系等挑战，以及文档级和无监督关系抽取方向，适合用于中文技术方案的研究背景。",
            },
            {
                "date": "2026\n中文期刊综述",
                "title": "大语言模型驱动下知识图谱的构建及应用综述",
                "url": "https://html.rhhz.net/ZZDXXBLXB/html/20260201.htm",
                "boundary": "知识图谱全流程\n含实体与关系抽取",
                "summary": "覆盖知识建模、实体识别、关系抽取和知识图谱应用，并将 LLM 关系抽取区分为自然语言生成与代码生成两条路线。适合描述出版知识图谱的整体流程，但范围宽于抽取算法，不宜作为抽取方法的唯一综述。",
            },
            {
                "date": "2020.12\nAACL 主会",
                "title": "More Data, More Relations, More Context and More Openness A Review and Outlook for Relation Extraction",
                "url": "https://aclanthology.org/2020.aacl-main.75/",
                "boundary": "关系抽取前瞻综述",
                "summary": "从更多数据、更多关系、更复杂上下文和更开放场景四个维度总结关系抽取。论文较早，但对长尾关系、跨句上下文和开放关系的任务拆分很清晰，可用于技术方案的问题定义和研究路线说明。",
            },
            {
                "date": "2024\nACM Computing Surveys",
                "title": "A Comprehensive Survey on Relation Extraction Recent Advances and New Frontiers",
                "url": "https://doi.org/10.1145/3674501",
                "boundary": "关系抽取综合综述",
                "summary": "系统整理深度学习关系抽取的任务分类、流水线与联合建模、预训练模型、文档级和少样本方向。适合补充较完整的关系抽取方法谱系；与本项目最相关的是联合实体关系抽取、复杂上下文和开放类别部分。",
            },
            {
                "date": "2024\nFuturED Workshop",
                "title": "A Comprehensive Survey on Document-Level Information Extraction",
                "url": "https://aclanthology.org/2024.futured-1.6/",
                "boundary": "文档级 IE 综述",
                "summary": "聚焦文档级信息抽取，并结合错误分析指出实体共指、推理不足、标注噪声和关系传递性是主要障碍。会议层级不高，但任务贴合出版物长文本，适合设计跨句抽取与错误分类。",
            },
        ],
    ),
    (
        "二 开放式与生成式抽取方法",
        [
            {
                "date": "2023.12\nEMNLP 主会",
                "title": "Set Learning for Generative Information Extraction",
                "url": "https://aclanthology.org/2023.emnlp-main.806/",
                "boundary": "生成式 IE\n多结构对象输出",
                "summary": "指出三元组等结构对象本质上是无序集合，而 Seq2Seq 训练强制采用固定顺序会引入顺序偏差。通过采样多个输出排列近似集合概率，不修改模型结构即可接入现有生成式 IE；适合改进一次抽取多个三元组时的训练目标。",
            },
            {
                "date": "2023.12\nEMNLP 主会",
                "title": "Abstractive Open Information Extraction",
                "url": "https://aclanthology.org/2023.emnlp-main.376/",
                "boundary": "抽象式 OpenIE\n允许隐含关系",
                "summary": "把传统只抽取原文表层关系短语的 OpenIE 扩展为可生成隐含语义关系的抽象式 OpenIE，并构建数据集、基线和语义评价方法。它能提高知识覆盖，但也扩大推断与幻觉风险，适合论证证据绑定和事实校验的必要性。",
            },
            {
                "date": "2025.11\nSTARSEM",
                "title": "Relation-Aware Prompting Makes Large Language Models Effective Zero-shot Relation Extractors",
                "url": "https://aclanthology.org/2025.starsem-1.22/",
                "boundary": "给定实体对\n固定关系集合",
                "summary": "先围绕实体对生成定向摘要，再缩小候选关系标签空间、合成 SVO 示例，最后进行多选式判断。在 TACRED 等四个数据集上超过既有零样本提示方法；提示流程可借鉴，但它不是从原始文本端到端抽取实体和关系。",
            },
            {
                "date": "2026.07\nACL 主会长文",
                "title": "On the Role of Discriminative Models in Generative Relation Extraction",
                "url": "https://aclanthology.org/2026.acl-long.2093/",
                "boundary": "给定实体对\n固定关系集合",
                "summary": "D2G 先用判别模型给出 Top-k 候选关系，再通过上下文学习或提示学习引导生成模型。在五个基准上持续提升，长尾关系收益突出；但正确关系未进入 Top-k 时性能骤降。适合设计“小模型候选约束加大模型判断”的混合架构。",
            },
        ],
    ),
    (
        "三 文档级与实体关系联合抽取",
        [
            {
                "date": "2021.08\nFindings of ACL",
                "title": "DocOIE A Document-level Context-Aware Dataset for OpenIE",
                "url": "https://aclanthology.org/2021.findings-acl.210/",
                "boundary": "文档上下文 OpenIE\n关系类型开放",
                "summary": "构建包含医疗与交通领域的 DocOIE 数据集，证明利用上下文有助于解决词性和句法歧义。数据规模不大，但任务与出版文档中的跨句语境直接相关；本项目已有 DocOIE 数据，可用于文档上下文消融实验。",
            },
            {
                "date": "2025.01\nGenAIK Workshop",
                "title": "Effective Modeling of Generative Framework for Document-level Relational Triple Extraction",
                "url": "https://aclanthology.org/2025.genaik-1.1/",
                "boundary": "文档级三元组抽取\n三阶段生成",
                "summary": "3G-DocRTE 将任务拆成实体提及抽取、实体聚类与类型识别、关系三元组生成，处理跨句共指和多次提及。在 DocRED 上超过早期生成模型并接近多阶段判别方法；任务很贴合，但仅属 Workshop 且主要验证 BART。",
            },
            {
                "date": "2025.04\nFindings of NAACL",
                "title": "Prototype Tuning A Meta-Learning Approach for Few-Shot Document-Level Relation Extraction with Large Language Models",
                "url": "https://aclanthology.org/2025.findings-naacl.62/",
                "boundary": "文档级少样本 RE\n新关系类别",
                "summary": "把支持文档中的实体对聚合为关系原型，并通过元训练提升模型利用示例的能力。相对普通 ICL 总体提高约 9.79 F1，但作者指出仍低于充分监督方法，跨领域场景距离实用较远；适合研究新关系与跨领域迁移。",
            },
            {
                "date": "2025.08\nXLLM Workshop",
                "title": "DocIE XLLM25 In-Context Learning for Information Extraction using Fully Synthetic Demonstrations",
                "url": "https://aclanthology.org/2025.xllm-1.26/",
                "boundary": "长文档零样本\n实体关系联合抽取",
                "summary": "使用 LLM 构造约 5000 篇合成文档、约 5.9 万实体和 3 万关系三元组，再做检索式 ICL，并用规则和模型验证。结果显示大量输出无法解析且关系 F1 很低；其 JSON 约束、实体 ID、一致性与方向检查对本项目很有借鉴价值。",
            },
        ],
    ),
    (
        "四 评价基准 鲁棒性与现实检验",
        [
            {
                "date": "2019.11\nEMNLP IJCNLP",
                "title": "CaRB A Crowdsourced Benchmark for Open IE",
                "url": "https://aclanthology.org/D19-1651/",
                "boundary": "OpenIE 自动评价基准",
                "summary": "构建众包 OpenIE 基准并改进元组匹配与评价指标，是长期使用的经典评价资源。其基于词槽重叠的匹配仍可能奖励事实并不等价的输出，因此更适合作为基础指标，而不宜作为唯一评价。",
            },
            {
                "date": "2022.05\nACL 主会长文",
                "title": "BenchIE A Framework for Multi-Faceted Fact-Based Open Information Extraction Evaluation",
                "url": "https://aclanthology.org/2022.acl-long.307/",
                "boundary": "事实级 OpenIE 评价\n英中德三语",
                "summary": "用事实同义集合列出同一事实的可接受表述，并从事实正确性、紧凑性和最小性等维度评价。实验显示既有 OpenIE 系统的真实效果低于旧基准给出的结果；适合本项目建立语义等价而非纯字符串匹配的评价体系。",
            },
            {
                "date": "2024.08\nFindings of ACL",
                "title": "BenchIE FL A Manually Re-Annotated Fact-Based Open Information Extraction Benchmark",
                "url": "https://aclanthology.org/2024.findings-acl.496/",
                "boundary": "重新标注的 OpenIE 评价基准",
                "summary": "重新检查 BenchIE 的标注与匹配偏差，给出更明确的标注指南和更灵活的匹配函数，并验证基准分数与下游任务表现的相关性。本项目已经使用 BenchIE FL，可把它作为人工复核和语义评价设计的重要依据。",
            },
            {
                "date": "2023.12\nEMNLP 主会",
                "title": "Preserving Knowledge Invariance Rethinking Robustness Evaluation of Open Information Extraction",
                "url": "https://aclanthology.org/2023.emnlp-main.360/",
                "boundary": "OpenIE 鲁棒性评价",
                "summary": "把表达不同但知识含义相同的句子组成知识不变簇，评价模型在句法与表达漂移下能否持续正确。典型模型最大下降 23.43 F1，说明单一测试集高分不能代表真实稳定性；适合设计同义改写和版式变化测试。",
            },
            {
                "date": "2023.07\nACL 主会长文",
                "title": "When to Use What An In-Depth Comparative Empirical Analysis of OpenIE Systems for Downstream Applications",
                "url": "https://aclanthology.org/2023.acl-long.53/",
                "boundary": "OpenIE 模型与下游任务比较",
                "summary": "系统比较神经 OpenIE 模型、训练数据和评价基准，并证明不同模型及数据假设会显著影响下游表现。核心启示是不存在脱离应用场景的唯一最佳抽取器；技术方案应按出版检索、知识库构建等目标分别评价。",
            },
            {
                "date": "2025.01\nCOLING 主会",
                "title": "LLM4RE A Data-centric Feasibility Study for Relation Extraction",
                "url": "https://aclanthology.org/2025.coling-main.447/",
                "boundary": "句子级关系分类\n联合三元组抽取",
                "summary": "对五个 LLM、不同提示与示例检索策略进行系统实验。LLM 对大标签空间、多关系、实体重叠、类别不平衡和假阴性表现脆弱，增加 few-shot 示例也未必持续提升；直接支持本项目加入校验、置信度与错误分析。",
            },
            {
                "date": "2023 首发\n2024 修订 arXiv",
                "title": "An Empirical Study on Information Extraction using Large Language Models",
                "url": "https://arxiv.org/abs/2305.14450",
                "boundary": "LLM 信息抽取现实检验\n预印本",
                "summary": "从性能、评价标准、鲁棒性和错误类型四个角度分析 GPT-4 信息抽取，并指出其与任务专用 SOTA 仍有明显差距。篇幅较长、实验覆盖面广，但未正式发表，应作为补充证据而非顶会结论。",
            },
        ],
    ),
    (
        "五 近期 LLM 关系抽取与数据方法",
        [
            {
                "date": "2025.07\nACL 主会长文",
                "title": "Generating Diverse Training Samples for Relation Extraction with Large Language Models",
                "url": "https://aclanthology.org/2025.acl-long.35/",
                "boundary": "关系抽取数据生成\n非推理模型",
                "summary": "发现直接提示生成的训练样本句式和关系表达高度重复，提出逐条生成、反相似提示和 DPO，提高多样性与正确性。合成数据与少量人工数据混合时效果较好，但生成到一定数量后收益趋于饱和；适合反馈样本沉淀与难例扩充。",
            },
            {
                "date": "2025.11\nEMNLP 主会",
                "title": "LLM-OREF An Open Relation Extraction Framework Based on Large Language Models",
                "url": "https://aclanthology.org/2025.emnlp-main.459/",
                "boundary": "实体对已给定\n发现未见关系类别",
                "summary": "包含关系发现器和关系预测器，推理分为关系发现、关系去噪和重新预测三阶段。在 FewRel、TACRED 与 FewRel-LT 上超过聚类式 OpenRE 方法。其自校正过程非常贴合项目，但这里的 OpenRE 不等于从原文直接抽取任意三元组。",
            },
        ],
    ),
]


def set_run_font(run, name="Microsoft YaHei", size=10, bold=False, color="000000"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Aptos")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_hyperlink(paragraph, text, url, size=9.2):
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Aptos")
    fonts.set(qn("w:hAnsi"), "Aptos")
    fonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    r_pr.extend([fonts, color, underline, sz])
    run.append(r_pr)
    text_el = OxmlElement("w:t")
    text_el.text = text
    run.append(text_el)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=90, bottom=90, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_border(cell, color="D9D9D9", size="6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), color)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_fixed_cell_width(cell, inches):
    cell.width = Inches(inches)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def style_cell_paragraph(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=0):
    paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.08


def add_group_table(doc, rows):
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [1.02, 2.12, 1.35, 2.91]
    headers = ["发表时间与渠道", "论文题目 点击可打开原文", "任务边界", "正文内容总结与参考价值"]
    header = table.rows[0]
    set_repeat_table_header(header)
    header.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    for i, cell in enumerate(header.cells):
        set_fixed_cell_width(cell, widths[i])
        shade_cell(cell, "1F4E78")
        set_cell_border(cell)
        set_cell_margins(cell, 100, 90, 100, 90)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        style_cell_paragraph(p, WD_ALIGN_PARAGRAPH.CENTER)
        r = p.add_run(headers[i])
        set_run_font(r, size=9.0, bold=True, color="FFFFFF")

    for idx, item in enumerate(rows):
        row = table.add_row()
        fill = "EDF4FB" if idx % 2 == 0 else "FFFFFF"
        for i, cell in enumerate(row.cells):
            set_fixed_cell_width(cell, widths[i])
            shade_cell(cell, fill)
            set_cell_border(cell)
            set_cell_margins(cell, 105, 95, 105, 95)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        p = row.cells[0].paragraphs[0]
        style_cell_paragraph(p, WD_ALIGN_PARAGRAPH.CENTER)
        r = p.add_run(item["date"])
        set_run_font(r, size=8.8)

        p = row.cells[1].paragraphs[0]
        style_cell_paragraph(p)
        add_hyperlink(p, item["title"], item["url"], size=9.0)
        p2 = row.cells[1].add_paragraph()
        style_cell_paragraph(p2, space_after=0)
        r2 = p2.add_run("原文链接")
        set_run_font(r2, size=8.0, color="666666")
        add_hyperlink(p2, " 访问", item["url"], size=8.0)

        p = row.cells[2].paragraphs[0]
        style_cell_paragraph(p, WD_ALIGN_PARAGRAPH.CENTER)
        r = p.add_run(item["boundary"])
        set_run_font(r, size=8.7)

        p = row.cells[3].paragraphs[0]
        style_cell_paragraph(p)
        r = p.add_run(item["summary"])
        set_run_font(r, size=8.9)

    return table


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr_text, fld_char2])
    set_run_font(run, size=9.0, color="777777")


def build_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.58)
    section.bottom_margin = Inches(0.58)
    section.left_margin = Inches(0.55)
    section.right_margin = Inches(0.55)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.18

    title_style = styles["Title"]
    title_style.font.name = "Microsoft YaHei"
    title_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    title_style.font.size = Pt(22)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0, 0, 0)
    title_style_p_pr = title_style._element.get_or_add_pPr()
    title_style_border = title_style_p_pr.find(qn("w:pBdr"))
    if title_style_border is not None:
        title_style_p_pr.remove(title_style_border)

    for style_name, size in (("Heading 1", 15), ("Heading 2", 12)):
        style = styles[style_name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("自反馈开发信息抽取相关论文参考表")
    title_p_pr = title._p.get_or_add_pPr()
    title_border = title_p_pr.find(qn("w:pBdr"))
    if title_border is not None:
        title_p_pr.remove(title_border)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(12)
    run = subtitle.add_run("开放式抽取 生成式抽取 文档级抽取 评价与近期大模型方法")
    set_run_font(run, size=11, color="555555")

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run("用途  ")
    set_run_font(r, size=10.5, bold=True)
    r = p.add_run(
        "本表汇总前期检索和全文核对中重点讨论的论文，供出版内容信息抽取技术方案选题、方法设计、评价体系和后续精读使用。论文题目均设置为可点击超链接。"
    )
    set_run_font(r, size=10.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run("任务边界  ")
    set_run_font(r, size=10.5, bold=True)
    r = p.add_run(
        "OpenIE 是在不预定义关系类型的情况下从文本抽取关系及其参数；OpenRE 常指实体对已经给定、模型发现或预测训练时未见的关系类别；固定 head relation tail 输出字段不等于固定关系类别。"
    )
    set_run_font(r, size=10.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("建议优先顺序  ")
    set_run_font(r, size=10.5, bold=True)
    r = p.add_run(
        "先读生成式 IE 与 OpenIE 综述，再读 LLM4RE 理解现实限制，随后精读 DocOIE 和 3G DocRTE，最后参考 LLM OREF 与 D2G 设计候选约束、去噪和再判断机制。"
    )
    set_run_font(r, size=10.5)

    for group_idx, (heading, rows) in enumerate(GROUPS):
        h = doc.add_paragraph(heading, style="Heading 1")
        h.paragraph_format.keep_with_next = True
        add_group_table(doc, rows)
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(2)

    h = doc.add_paragraph("六 面向技术方案的引用建议", style="Heading 1")
    recommendations = [
        ("研究背景", "用 OpenIE 综述、生成式 IE 综述和关系抽取综合综述说明任务演进与研究缺口。"),
        ("技术架构", "用 DocOIE 和 3G DocRTE 支撑文档级分阶段抽取，用 D2G 支撑候选约束，用 LLM OREF 支撑发现 去噪 再预测。"),
        ("评价体系", "以 CaRB 作为传统基线，以 BenchIE 与 BenchIE FL 进行事实级评价，并加入知识不变改写的鲁棒性测试。"),
        ("数据建设", "参考多样化训练样本论文构造难例和长尾关系样本，但人工数据与合成数据应分开统计并进行事实校验。"),
        ("风险控制", "引用 LLM4RE、DocIE XLLM25 和大模型信息抽取实证研究，说明输出可解析性、关系方向、幻觉、跨域退化和假阴性不能只靠一次提示解决。"),
    ]
    for label, content in recommendations:
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Inches(0.18)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        r = p.add_run(label + "  ")
        set_run_font(r, size=10.5, bold=True)
        r = p.add_run(content)
        set_run_font(r, size=10.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run("更新日期 2026 年 9 月")
    set_run_font(r, size=9.5, color="666666")

    for sec in doc.sections:
        sec.footer_distance = Inches(0.28)
        add_page_number(sec.footer.paragraphs[0])

    doc.core_properties.title = "自反馈开发信息抽取相关论文参考表"
    doc.core_properties.subject = "开放式抽取 生成式信息抽取 文档级关系抽取与评价"
    doc.core_properties.keywords = "信息抽取, 关系抽取, OpenIE, 文档级抽取, 大语言模型"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build_document()
