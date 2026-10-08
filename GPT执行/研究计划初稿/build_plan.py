from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parent
OUT = BASE / '基于自反馈的三元组抽取方法研究_初步计划.docx'
sections = [
('1 方案提出', [
('1.1 研究问题', '从三元组抽取中的事实遗漏、关系错误和实体边界不完整等问题出发，研究模型能否依据源文本检查自己的抽取结果，并通过反馈完成补漏和纠错。'),
('1.2 研究目标', '以构建业界领先的知识抽取 Agent 为目标，重点提高抽取的准确性、完整性和稳定性，同时关注运行成本。通过公开数据集和代表性方法对比，检验实际达到的水平。'),
('1.3 候选方案', '重点考虑重新抽取和增量抽取两种方案：前者根据反馈生成完整的新结果，后者在已有结果上新增、删除和替换。同时探索将重新抽取结果与第一轮结果合并的方式。'),
]),
('2 技术方案', [
('2.1 整体流程', '以 KARMA 为起点，设计初始抽取、反馈生成和结果修正三个环节。明确每一步使用什么输入、返回什么结果，先形成可以完整运行和比较的流程。'),
('2.2 实体与关系抽取', '由 Entity Agent 提取候选实体，再由 Relationship Agent 结合源文本抽取三元组。反馈阶段仍从实体审校开始，检查实体候选是否有助于关系补漏和边界修正。'),
('2.3 自反馈机制', '先将三元组重建成文本，再与源文本比较，生成候选遗漏和疑似错误。修正时以源文本为依据，检查反馈是否可靠；标准答案仅用于评估，不参与反馈生成。'),
('2.4 实验设计', '分别验证提示词语言和反馈策略的影响。比较反馈方案时，固定同一份第一轮结果、模型配置和评估规则，避免多个条件同时变化而无法判断效果来源。'),
]),
('3 代码实现与实验准备', [
('3.1 数据集选择', '根据应用场景选择数据集，检查领域、语言、文本长度和标注质量。完成原文与标准三元组的对齐，记录清洗规则，并划分开发、验证和测试数据。'),
('3.2 程序实现', '实现两种反馈方案，打通实体抽取、关系抽取及后处理流程。检查输出解析、无效操作和异常回退，保存独立版本，保证修改后的程序可运行、可回退。'),
('3.3 中英文 Prompt 效果验证', '在相同源文本和模型配置下，使用任务要求尽量一致的中英文提示词，对比抽取效果和输出稳定性。本阶段只改变提示词语言，源文本语言保持一致。'),
('3.4 过程记录', '保存各阶段的完整输入、模型回复、修正操作和评估结果。统一文档编号，记录失败、重试和被拒绝的条目，方便后续复查和定位问题。'),
]),
('4 方案效果验证', [
('4.1 验证方案提升效果', '以第一轮无反馈结果为基线，比较反馈后的精确率、召回率和 F1，检查是否补充了遗漏、修正了错误，以及是否丢失已有的正确事实。'),
('4.2 两种方案效果对比', '在相同第一轮基准上，比较重新抽取与增量抽取的最终效果、逐篇表现和调用成本。将重新抽取后合并作为补充实验，检查是否能保留两轮结果中的有效信息。'),
('4.3 差异原因分析', '选取能解释主要差异的三元组，结合原文、反馈和修改记录逐项检查。区分真实补漏、错误引入和表达变化造成的评分变化，不直接把自动匹配当作事实正确。'),
('4.4 确定方案', '根据整体指标、案例核查和运行成本，确定后续重点优化的方案。如果两者效果接近，进一步考虑稳定性和实现复杂度，并保留对照版本。'),
]),
('5 抽取能力提升', [
('5.1 优化 Prompt', '根据具体问题修改提示词，重点检查事实覆盖、实体边界、关系表达和反馈使用方式。保留修改前后的对照，每次优先调整一个主要问题，确认收益后再继续。'),
('5.2 改进反馈与处理逻辑', '对于提示词无法解决的问题，检查反馈生成、结果合并和操作执行等环节。根据证据决定是否调整流程，避免增加没有明确收益的复杂度。'),
('5.3 验证改进效果', '通过对照实验和消融实验检查各项修改的作用，并在相同条件下重复运行，观察提升是否稳定。同步记录新增错误、失败情况和额外调用成本。'),
('5.4 检查泛化与竞争力', '在未用于提示词调试的测试数据上验证效果，考察不同领域和困难句式的表现。与选定的代表性方法比较，明确 Agent 的优势、适用范围和仍需改进的问题。'),
]),
('6 成果交付', [
('6.1 程序交付', '交付可运行的知识抽取 Agent，整理配置、运行入口和结果目录，保留方案切换与回退方式，并提供版本记录和使用说明。'),
('6.2 实验材料', '整理数据处理规则、提示词版本、实验配置和逐篇结果，保留能够复查主要结论的输入输出与评估记录，支持后续复现。'),
('6.3 报告与展示', '形成研究报告和演示案例，说明方案设计、实验结果、改进依据及局限。根据最终对比结果给出推荐方案，并列出下一步值得继续研究的问题。'),
]),
]

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.1)
sec.left_margin = sec.right_margin = Cm(2.3)
for name, size, east in [('Normal',11,'宋体'),('Title',18,'黑体'),('Heading 1',13,'黑体')]:
    style = doc.styles[name]
    style.font.name = 'Times New Roman'
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0,0,0)
    style.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),east)
normal = doc.styles['Normal'].paragraph_format
normal.line_spacing = 1.2
normal.space_after = Pt(5)
normal.widow_control = True
heading = doc.styles['Heading 1'].paragraph_format
heading.space_before = Pt(9)
heading.space_after = Pt(5)
heading.keep_with_next = True
title = doc.add_paragraph('基于自反馈的三元组抽取方法研究', 'Title')
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(5)
sub = doc.add_paragraph('初步研究计划')
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(10)
intro = doc.add_paragraph('本研究拟构建能够依据源文本自查和修正结果的知识抽取 Agent。先验证不同反馈方案的效果，再根据具体问题改进抽取能力。整体工作安排如下。')
intro.paragraph_format.first_line_indent = Pt(22)
for n,(name,items) in enumerate(sections):
    h = doc.add_paragraph(name, 'Heading 1')
    if n == 3:
        h.paragraph_format.page_break_before = True
    for label, text in items:
        p = doc.add_paragraph()
        p.paragraph_format.keep_together = True
        p.add_run(label + '  ').bold = True
        p.add_run(text)
doc.core_properties.title = '基于自反馈的三元组抽取方法研究'
doc.core_properties.subject = '初步研究计划'
doc.core_properties.author = ''
doc.core_properties.last_modified_by = ''
doc.core_properties.comments = ''
for root in (doc.styles.element, doc.element):
    for border in list(root.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
doc.save(OUT)
print(OUT)
