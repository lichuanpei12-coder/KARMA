from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parent
OUT = BASE / '基于自反馈的三元组抽取方法研究_初步计划.docx'
sections = [
('1 让模型检查自己抽出的事实',
 '本研究从一个设想出发：将抽出的三元组重新组织成文本，再与原文比较，能否发现初次抽取时遗漏或表达错误的信息，并据此修正结果？以 KARMA 为起点实现这一过程，重点研究反馈是否准确、如何利用反馈，以及修正后是否真正改善了事实表达。目标是得到具备自主补漏和纠错能力的知识抽取 Agent。'),
('2 选择能够检验补漏和纠错的数据',
 '先检查现有 DocOIE 数据是否适合开放三元组抽取，再补充其他领域的数据用于验证。样本应包含并列关系、较长宾语、否定、条件和指代等情况。逐篇核对源文本与 Gold 的对应关系，记录空尾实体、重复标注和歧义标注的处理方式。已反复查看的案例用于开发，另留未参与提示词修改的数据做最终测试。'),
('3 建立统一的第一轮实体与关系抽取',
 '先由 Entity Agent 找出可能参与事实的对象，再由 Relationship Agent 结合源文本抽取三元组；实体名单作为提示，不限制头尾必须来自名单。固定这一轮的提示词和后处理，保存实体集合 E1 与三元组集合 T1，作为反馈实验的共同起点。另设直接抽取三元组的对照，检验实体候选是否确实帮助发现更多事实。'),
('4 单独比较中英文提示词的影响',
 '在同一模型、同一批源文本上，对比任务要求、示例和输出格式尽量一致的中英文提示词。先比较第一轮实体与三元组结果，再按需要验证反馈环节。实验只改变提示词语言，不同时翻译源文本或切换反馈策略。根据抽取质量、格式错误和重复运行表现选择后续配置，避免把提示词差异误认为反馈收益。'),
('5 核查文本差异能否指向真实抽取问题',
 '将 T1 生成的文本 B 与源文本 A 比较，把 A 中有而 B 中未体现的信息作为候选遗漏，把 B 中有而 A 中未找到依据的信息作为待复核内容。检查这些提示是否能追溯到具体三元组，尤其关注重建时遗漏信息、补写信息，以及原三元组已包含事实却被判为遗漏的情况。如果问题主要来自重建或比较，再实验直接对照原文审校三元组的方式。'),
('6 实现重新抽取和增量修正两条反馈路径',
 '重新抽取路径根据源文本和反馈重新提取实体，再生成完整的三元组列表；增量路径先参考 E1、T1 和反馈审校实体，再对 T1 输出 add、remove、replace。Python 负责校验格式并执行操作，保留未被修改的三元组。两条路径均从第二轮实体环节开始，保存完整请求、回复和拒绝记录，并检查解析失败、编号冲突和回退是否正确处理。'),
('7 从同一份 T1 判断哪种反馈更有效',
 '同一篇文档的两条路径共用 E1、T1 和反馈作为实验基准，使用相同 Gold 与评估规则。既比较最终精确率、召回率和 F1，也分别统计新增与失去的覆盖，再核查是否对应真实补漏或事实丢失。复用重新抽取结果，增加与 T1 合并的对照，检查保留旧事实的收益及冗余代价。当前 6 篇结果仅作为预实验，扩大样本后再确定重点优化的方案。'),
('8 针对补漏不足和旧事实丢失改进提示词',
 '已有案例给出两个具体方向：一篇文档的长三元组包含多个服务类别，信息虽已出现，却没有单独表达系统与类别之间的关系；另一篇文档重新抽取后丢失了原有的两条数值方法实例关系。后续分别研究独立关系的展开和正确旧事实的保留，并明确空 tail 等不合格式结果的处理。对已有三元组是否让模型忽略新事实这一猜测，另设对照验证，不直接当作修改依据。'),
('9 检验改进是否能跨文档和领域成立',
 '每次针对一个主要问题修改，在固定第一轮结果上复测，并在独立测试数据上检查收益。重点观察反馈能否稳定补漏、是否引入新错误，以及多一次修正是否值得增加调用成本。选取适合开放三元组任务的代表性方法，在可比的数据和评分条件下对照。以业界领先为目标，但依据最终结果说明实际优势，而非仅比较本项目的两个版本。'),
('10 交付能够复查修正过程的抽取 Agent',
 '最终程序接收源文本，返回三元组，并能查看初始结果、反馈内容和修正依据。保留无反馈、重新抽取和增量抽取的切换方式，推荐实际验证效果较好的配置。交付代码、提示词、数据处理与评估脚本、运行说明和研究报告；报告用具体案例说明哪些事实被补充、保留或改错，以及哪些问题仍未解决。'),
]

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.1)
sec.left_margin = sec.right_margin = Cm(2.3)
for name, size, east in [('Normal',11,'宋体'),('Title',18,'黑体'),('Heading 1',12,'黑体')]:
    style = doc.styles[name]
    style.font.name = 'Times New Roman'
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0,0,0)
    style.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),east)
normal = doc.styles['Normal'].paragraph_format
normal.line_spacing = 1.25
normal.space_after = Pt(6)
normal.widow_control = True
heading = doc.styles['Heading 1'].paragraph_format
heading.space_before = Pt(10)
heading.space_after = Pt(5)
heading.keep_with_next = True
title = doc.add_paragraph('基于自反馈的三元组抽取方法研究', 'Title')
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(5)
sub = doc.add_paragraph('初步研究计划')
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(10)
for n,(name,text) in enumerate(sections):
    h = doc.add_paragraph(name, 'Heading 1')
    if n == 5:
        h.paragraph_format.page_break_before = True
    p = doc.add_paragraph(text)
    p.paragraph_format.first_line_indent = Pt(22)
    p.paragraph_format.keep_together = True
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
