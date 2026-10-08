from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

base = Path(__file__).resolve().parent
out = base / '基于自反馈的三元组抽取方法研究_初步计划.docx'
sections = [
('1 研究背景与问题', [
('', '三元组抽取旨在从非结构化文本中提取“主体—关系—客体”形式的知识，是知识图谱构建的重要环节。大语言模型可以完成这一任务，但结果仍可能存在事实遗漏、关系表达不准确、实体边界不完整及缺少原文依据等问题。本研究拟引入自反馈机制，使模型依据源文本检查并修正已有结果，重点研究如何在保留正确事实的同时补充遗漏、修正错误，并避免引入新的错误。'),
]),
('2 研究目标', [
('', '构建具备自主检查与修正能力的三元组抽取 Agent，提高抽取的准确性、完整性和稳定性，以达到业界领先水平为目标。研究工作包括建立可靠的反馈机制、比较不同修正策略、分析反馈有效或失效的原因，并在公开数据集和选定应用场景中验证方法效果。最终通过与代表性方法的对比，判断实际达到的水平。'),
]),
('3 拟研究的关键问题', [
('如何生成可靠的反馈', '反馈应能指出遗漏事实和疑似错误，同时需要控制反馈本身的误判。重点检查反馈是否有原文依据，以及重建文本或比较过程是否会产生新的信息偏差，避免据此修改原本正确的结果。'),
('如何利用反馈修正抽取结果', '重新抽取可能发现更多事实，但也可能丢失已有的正确内容；增量修正能够保留已有结果，但可能补漏不足。需要研究不同策略的适用条件，以及二者能否形成有效结合。'),
('如何判断自反馈带来了真实改善', '除比较最终评分外，还需分析正确补漏、错误修正、原有事实丢失和新增错误，区分事实质量的改善与表达形式变化引起的评分变化，并考察收益是否稳定、是否值得额外的调用成本。'),
]),
('4 初步技术路线', [
('', '以现有 KARMA 框架为起点，先完成实体与关系抽取，得到初始三元组集合，再依据源文本检查结果、生成反馈，并根据反馈修正实体与三元组。实体候选用于辅助检查事实覆盖，关系判断仍以源文本为依据。KARMA 作为初始实现，后续可根据实验结果调整各环节。'),
('', '初步采用“由三元组重建文本，再与源文本比较”的方式生成反馈，同时考察其中的信息丢失或比较误差。根据问题分析，进一步验证直接对照源文本审校三元组等方式，确定适合本任务的反馈来源。'),
('', '修正环节重点比较重新抽取与增量抽取：前者根据源文本和反馈生成完整结果，后者在已有三元组上新增、删除和替换。同时探索重新抽取后合并两轮结果，研究事实保留、重复消除和冲突处理。上述方案均为初始候选，最终方案由实验确定。'),
]),
('5 数据集与实验设计', [
('数据集选择', '根据开放三元组抽取的任务形式、标注质量、领域覆盖和使用条件选择数据集，核查源文本与标准三元组的对应关系，记录歧义标注和清洗规则。划分开发、验证和测试数据，已用于分析和修改提示词的案例不再作为独立测试依据。'),
('中英文提示词验证', '在相同模型和源文本上，对比任务要求、示例和输出格式尽量一致的中英文提示词，检查抽取质量及输出稳定性。将提示词语言实验与反馈策略实验分开，避免同时改变多个条件而无法解释差异。'),
('反馈效果与方案对比', '以无反馈抽取为基础对照，在统一第一轮结果、模型配置和评估条件下比较不同反馈策略。既评估最终精确率、召回率和 F1，也分析相对第一轮的收益及逐篇变化。标准答案仅用于离线评估，不参与反馈生成。'),
('作用分析与外部对比', '通过消融实验分析实体候选、反馈内容和已有三元组的作用，结合自动指标与人工案例核查，检查事实质量、运行稳定性和成本。选择适合本任务的代表性方法进行对比，并在独立数据上验证改进能否推广。'),
]),
('6 已有基础与初步观察', [
('', '目前已基于 KARMA 实现重新抽取与增量抽取的对比流程，并完成 6 篇文档的预实验。在这次运行中，重新抽取增加的自动评估覆盖较多，但也失去了部分已有覆盖；增量抽取保留了已有覆盖，新增覆盖相对较少，两种方案最终评分接近。部分案例涉及真实遗漏，另一些涉及表达结构变化。目前样本有限，尚不能判断哪种方案整体更优，也不能将差异直接归因于某一机制。'),
]),
('7 研究安排与预期成果', [
('方案与评测准备', '完成相关方法调研、研究方案细化、数据集选择和评估规则制定，明确需要验证的假设及对照方法。'),
('基线与反馈实现', '建立统一的基础抽取流程，验证中英文提示词效果，实现候选反馈方案。保存各阶段输入、模型回复和处理结果，检查解析、操作执行和异常回退。'),
('实验与能力提升', '完成正式对照实验，根据抽取质量、稳定性和成本确定重点优化的方案。围绕具体错误改进提示词；必要时调整反馈生成或结果处理，再通过对照实验判断修改是否有效。'),
('验证与成果整理', '在独立测试数据上验证效果，形成可运行的知识抽取 Agent、实验复现材料、研究报告和使用说明。报告说明方法相对基线和代表性方法的效果、适用条件及局限。'),
]),
]

doc=Document()
sec=doc.sections[0]
sec.page_width,sec.page_height=Cm(21),Cm(29.7)
sec.top_margin=sec.bottom_margin=Cm(2.1)
sec.left_margin=sec.right_margin=Cm(2.3)
for name,size,east in [('Normal',11,'宋体'),('Title',18,'黑体'),('Heading 1',12,'黑体')]:
    s=doc.styles[name]
    s.font.name='Times New Roman'
    s.font.size=Pt(size)
    s.font.color.rgb=RGBColor(0,0,0)
    s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),east)
normal=doc.styles['Normal'].paragraph_format
normal.line_spacing=1.2
normal.space_after=Pt(5)
normal.widow_control=True
hstyle=doc.styles['Heading 1'].paragraph_format
hstyle.space_before=Pt(9)
hstyle.space_after=Pt(5)
hstyle.keep_with_next=True
p=doc.add_paragraph('基于自反馈的三元组抽取方法研究','Title')
p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after=Pt(5)
p=doc.add_paragraph('初步方案')
p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after=Pt(9)
for i,(heading,items) in enumerate(sections):
    p=doc.add_paragraph(heading,'Heading 1')
    if i==4:
        p.paragraph_format.page_break_before=True
    for label,text in items:
        p=doc.add_paragraph()
        p.paragraph_format.keep_together=True
        p.paragraph_format.first_line_indent=Pt(22)
        if label:
            p.add_run(label+'。').bold=True
        p.add_run(text)
doc.core_properties.title='基于自反馈的三元组抽取方法研究'
doc.core_properties.subject='初步方案'
doc.core_properties.author=''
doc.core_properties.last_modified_by=''
doc.core_properties.comments=''
for root in (doc.styles.element,doc.element):
    for node in list(root.iter(qn('w:pBdr'))):
        node.getparent().remove(node)
doc.save(out)
print(out)
