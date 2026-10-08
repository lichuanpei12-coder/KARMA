from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

base=Path(__file__).resolve().parent
out=base/'基于自反馈的三元组抽取方法研究_初步计划.docx'
sections=[
('1 研究背景与目标',[
('1.1 研究问题','大语言模型抽取三元组时，可能遗漏事实、误判关系或丢失否定和条件等限定。本研究拟让模型依据源文本检查已有结果，重点解决三个问题：反馈能否找准问题、修正能否补漏纠错，以及怎样避免修改后丢失原本正确的事实。'),
('1.2 研究目标','构建具备自主检查与修正能力的知识抽取 Agent，以达到业界领先水平为目标。通过无反馈基线、不同反馈策略及代表性方法的对比，验证准确性、完整性和稳定性的提升，同时衡量额外调用成本。'),
]),
('2 自反馈抽取方案设计',[
('2.1 初始实体与关系抽取','以 KARMA 为起点，先由 Entity Agent 提取可能作为主体或客体的候选对象，再由 Relationship Agent 结合源文本抽取三元组。实体名单用于提醒模型检查覆盖，允许抽取名单之外有原文依据的事实，得到第一轮实体 E1 和三元组 T1。'),
('2.2 反馈生成与可靠性检查','将 T1 重建为文本 B，与源文本 A 比较，生成候选遗漏和疑似无依据内容。抽样核查差异能否对应真实抽取问题，区分抽取遗漏、重建遗漏和比较误判。反馈只作为线索，实体和关系是否成立仍依据源文本判断。'),
('2.3 重新抽取方案','第二轮从实体抽取开始，根据源文本和反馈重新生成实体候选，再抽取完整三元组列表。检查这种方式是否能发现更多事实，同时记录第一轮已有事实在第二轮消失的情况，分析其属于合理纠错还是意外丢失。'),
('2.4 增量抽取方案','第二轮先参考源文本、E1、T1 和反馈，返回完整的审校后实体列表，再由关系 Agent 对 T1 输出新增、删除和替换操作。模型负责事实判断并给出修正依据，Python 校验格式和编号后执行操作，保留未被修改的三元组。'),
('2.5 两轮结果合并方案','将重新抽取结果与 T1 合并，先只去除按固定规则判定的重复条目，检验能否同时保留旧事实和第二轮新增内容。进一步检查错误保留、语义重复与冲突情况，再决定是否需要增加基于源文本的合并审校。'),
]),
('3 数据集与评测准备',[
('3.1 数据集选择','以现有 DocOIE 数据作为开发起点，根据开放三元组任务、标注质量和使用条件选择补充数据。覆盖并列关系、长句、否定、条件和指代等难点，并选择不同领域的数据检验方法能否推广，避免只在单一类型文本上优化。'),
('3.2 数据核查与划分','核对文档编号、源文本和 Gold 的对应关系，记录空字段、重复项和歧义标注的处理规则，冻结各版数据。划分开发、验证和测试集；用于案例分析与提示词修改的文档留在开发集，最终效果在独立测试集上验证。'),
('3.3 评估规则与过程记录','统一匹配阈值、去重方式和统计范围，保存完整匹配信息，区分预测匹配数与 Gold 覆盖数。记录每次调用的输入、完整回复、解析结果和拒绝操作。标准答案只用于离线评估，不参与抽取和反馈生成。'),
]),
('4 提示词与反馈方案对照实验',[
('4.1 中英文提示词效果验证','使用同一模型和同一批源文本，对比任务要求、示例和输出格式尽量一致的中英文提示词。先比较第一轮抽取，再验证反馈阶段；只改变提示词语言，不同时翻译源文本或切换反馈策略，据此选择后续实验配置。'),
('4.2 统一第一轮的方案比较','每篇文档只生成一份共同的 E1、T1 和反馈，两个分支分别从第二轮实体环节运行，使用相同的模型配置与后处理。比较的是完整反馈方案，第二轮实体可以不同；需要定位关系修正本身的作用时，再另设固定实体输入的实验。'),
('4.3 反馈提升与事实变化分析','以 T1 为无反馈基线，比较各方案最终精确率、召回率和 F1，同时统计新增与失去的覆盖。结合原文核查代表性变化，区分真实补漏、错误修正、旧事实丢失及表达结构带来的评分变化，避免仅凭分数解释反馈效果。'),
('4.4 方案选择与稳定性验证','综合完整样本上的质量、逐篇变化和成本选择重点优化的方案，并在固定第一轮结果上重复反馈运行，检查结论是否稳定。失败、条目拒绝和回退单独报告，不因结果不利而排除文档，也不预设增量抽取一定优于重新抽取。'),
]),
('5 抽取能力提升与原因验证',[
('5.1 针对事实遗漏和表达边界优化提示词','重点检查长三元组中的嵌套关系、同一对象的多个关系、并列项及必要限定是否得到完整表达。明确真实补漏与已有事实展开的区别，优化新增和替换规则；针对空 tail 等不合格式结果完善表达要求，避免为满足格式编造内容。'),
('5.2 检验实体候选和已有结果的影响','通过直接抽取三元组与实体辅助抽取的对照，检验实体候选是否帮助补漏。进一步控制已有三元组的呈现方式，测试它是否让模型过度保守。每次只改变一个主要因素，判断问题来自实体覆盖、关系判断还是修订任务本身。'),
('5.3 改进反馈来源与迭代方式','若文本重建或比较误差限制了修正效果，增加直接对照原文审校三元组的实验，并比较使用与不使用差异提示的结果。在有效的单次反馈基础上，再研究多轮修正和停止条件，检查新增收益是否足以抵消错误累积和调用成本。'),
('5.4 独立测试与代表性方法对比','将选定的改进用于未参与调试的数据，检查不同领域和困难句式上的表现。与适合开放三元组任务的代表性方法在可比条件下对照，报告效果和成本，判断优势能否推广，而非只依赖少数开发案例。'),
]),
('6 研究实施与成果交付',[
('6.1 实施顺序','先完成相关方法调研、数据选择和基线代码整理，再验证提示词语言并冻结实验配置。随后运行反馈方案对比，依据错误分析逐项优化，最后开展独立测试和外部方法对比。每阶段保留代码、提示词和结果版本，修改收益不明确时回到前一版本核查。'),
('6.2 Agent 与实验材料交付','交付接收源文本并输出三元组的 Agent，提供反馈策略切换、运行说明和异常记录，能够复查第一轮结果、反馈内容及修正过程。同时整理数据处理与评估脚本、实验配置和完整结果，支持复现。'),
('6.3 研究报告与方案结论','报告说明自反馈是否带来提升、哪种修正方式更合适，以及提升来自哪些环节。用原文和三元组案例解释补漏、纠错与失败情况，给出推荐配置、适用范围和未解决问题，为后续研究提供依据。'),
]),
]
doc=Document()
sec=doc.sections[0]
sec.page_width,sec.page_height=Cm(21),Cm(29.7)
sec.top_margin=sec.bottom_margin=Cm(2.1)
sec.left_margin=sec.right_margin=Cm(2.3)
for name,size,east in [('Normal',11,'宋体'),('Title',18,'黑体'),('Heading 1',14,'黑体'),('Heading 2',11,'黑体')]:
    s=doc.styles[name]
    s.font.name='Times New Roman'
    s.font.size=Pt(size)
    s.font.color.rgb=RGBColor(0,0,0)
    s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),east)
normal=doc.styles['Normal'].paragraph_format
normal.line_spacing=1.15
normal.space_after=Pt(5)
normal.widow_control=True
for name,before,after in [('Heading 1',10,6),('Heading 2',6,3)]:
    pf=doc.styles[name].paragraph_format
    pf.space_before=Pt(before)
    pf.space_after=Pt(after)
    pf.keep_with_next=True
p=doc.add_paragraph('基于自反馈的三元组抽取方法研究','Title')
p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after=Pt(5)
p=doc.add_paragraph('初步方案')
p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after=Pt(8)
for i,(heading,items) in enumerate(sections):
    p=doc.add_paragraph(heading,'Heading 1')
    if i in (2,4):
        p.paragraph_format.page_break_before=True
    for label,text in items:
        doc.add_paragraph(label,'Heading 2')
        p=doc.add_paragraph(text)
        p.paragraph_format.keep_together=True
        p.paragraph_format.first_line_indent=Pt(22)
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
