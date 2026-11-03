"""Replace stage of source-grounded feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """你负责修正已有三元组，包括主语、关系、客体、修饰语和拆分问题。先看前一步的结果，再自己检查全部条目。一条旧三元组可以替换成一条或多条新三元组，拆分结果直接写在 replace 的 new_triples 中。 完整回复采用 User 指定的 JSON 结构。"""

TASK_PROMPT = """# 任务：修正已有三元组；需要拆分时，一条直接替换成多条
检查全部当前三元组，包括 Add 刚新增的条目。先列出问题，再给出替换结果。

# 步骤
1. 查看前一步提出的问题，并找到对应条目。
2. 自己检查每条当前三元组，找到源句中对应的关系。
3. 检查 head：它是不是这项关系的主体？是否把中间的修饰短语当成主体？
4. 检查 relation：动作和词形是否与源句一致？目的、条件、危险等联系是否保留？
5. 检查 tail：对象是否正确？有没有把其他关系也放进这个字段？
6. 对需要补充或删去的修饰语，说明它是否影响对象或关系。仅因原文更长，不要求把原文全部补入字段。
7. 列出需要修改的条目、字段和原文依据。
8. 普通修正：将一条完整的新三元组放入 new_triples。
9. 嵌套拆分：先检查内部关系是否已经有独立条目。
10. 已有正确内部条目时，保留它；已有错误内部条目时，替换它；尚无内部条目时，将拆出的关系写进原条目的 new_triples。
11. 检查原来的长字段是否可以收短。用于识别对象或保留必要限定的内容继续保留。
12. 检查替换后的完整集合：原有关系是否都保留，是否又重复生成已有关系。
13. 每个旧 index 最多输出一项 replace；new_triples 至少有一条完整三元组。
14. 完全遗漏的关系交给 Add；重复条目交给 Remove；无法修正的无依据条目写入 review。
15. 输出问题清单和 replace。拆分后的多条都写在 new_triples 中，add 为空。

# 选择和集合
or 连接的选项保留在同一表达中，保留 or；不要把选项改成两个各自成立的断言。
and 连接的是一套设备的组成时，保留整套设备作为主体；多个对象各自参与关系时才分别表达。
步骤名称说明具体是什么步骤时可以保留，如 a pre-step of grinding the rubber；句首 In some embodiments 按背景省略。
"""

EXAMPLES = """# 示例：一条嵌套三元组直接换成两条
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The system includes a module that processes data."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The system",
        "relation": "includes",
        "tail": "a module that processes data",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：第 0 条包含 includes 和 processes 两项关系，processes 没有其他独立条目。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0
      ],
      "finding": "第 0 条包含 includes 和 processes 两项关系，processes 没有其他独立条目。",
      "evidence": "The system includes a module that processes data.",
      "result": "用两条完整三元组替换第 0 条。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [
    {
      "issue_id": "I1",
      "index": 0,
      "reason": "将原条目中的两项关系分别表达。",
      "new_triples": [
        {
          "head": "The system",
          "relation": "includes",
          "tail": "a module",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The system includes a module that processes data.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        },
        {
          "head": "a module",
          "relation": "processes",
          "tail": "data",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The system includes a module that processes data.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        }
      ]
    }
  ],
  "remove": []
}

# 示例：已有内部关系时修正它，不再重复拆出
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The system includes a module that processes data."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The system",
        "relation": "includes",
        "tail": "a module that processes data",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 1,
        "head": "The system",
        "relation": "processes",
        "tail": "data",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：第 1 条已表达 processes，但主体错误；第 0 条的内部关系可由修正后的第 1 条表达。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0,
    1
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0,
        1
      ],
      "finding": "第 1 条已表达 processes，但主体错误；第 0 条的内部关系可由修正后的第 1 条表达。",
      "evidence": "The system includes a module that processes data.",
      "result": "修正第 1 条主体，并收短第 0 条。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [
    {
      "issue_id": "I1",
      "index": 1,
      "reason": "processes 的主体是 a module。",
      "new_triples": [
        {
          "head": "a module",
          "relation": "processes",
          "tail": "data",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The system includes a module that processes data.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        }
      ]
    },
    {
      "issue_id": "I1",
      "index": 0,
      "reason": "内部关系已由第 1 条表达。",
      "new_triples": [
        {
          "head": "The system",
          "relation": "includes",
          "tail": "a module",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The system includes a module that processes data.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        }
      ]
    }
  ],
  "remove": []
}

# 示例：同时修正主语和用途表达
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The application relates to a bracket system for mounting to a vehicle to provide a support structure."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "mounting to a vehicle",
        "relation": "provides",
        "tail": "a support structure",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：主体应是 bracket system，to provide 表达用途，provide 词形应保留。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0
      ],
      "finding": "主体应是 bracket system，to provide 表达用途，provide 词形应保留。",
      "evidence": "The application relates to a bracket system for mounting to a vehicle to provide a support structure.",
      "result": "将第 0 条换成主体和用途均正确的一条。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [
    {
      "issue_id": "I1",
      "index": 0,
      "reason": "找回系统主体并保留 to provide 的用途含义。",
      "new_triples": [
        {
          "head": "a bracket system for mounting to a vehicle",
          "relation": "is to provide",
          "tail": "a support structure",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The application relates to a bracket system for mounting to a vehicle to provide a support structure.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        }
      ]
    }
  ],
  "remove": []
}

# 示例：在已有条目补回目的联系
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The controller may query the ECU to identify the fault."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The controller",
        "relation": "may query",
        "tail": "the ECU",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 1,
        "head": "The controller",
        "relation": "may identify",
        "tail": "the fault",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：第 1 条把查询目的写成了独立动作。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0,
    1
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0,
        1
      ],
      "finding": "第 1 条把查询目的写成了独立动作。",
      "evidence": "The controller may query the ECU to identify the fault.",
      "result": "保留第 0 条，修正第 1 条。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [
    {
      "issue_id": "I1",
      "index": 1,
      "reason": "保留查询与识别之间的目的联系。",
      "new_triples": [
        {
          "head": "The controller",
          "relation": "may query the ECU to identify",
          "tail": "the fault",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The controller may query the ECU to identify the fault.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        }
      ]
    }
  ],
  "remove": []
}

# 示例：内部动作要保留与危险的联系
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The risk of cargo falling from the deck causes concern."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "cargo",
        "relation": "falls from",
        "tail": "the deck",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 1,
        "head": "The risk of cargo falling from the deck",
        "relation": "causes",
        "tail": "concern",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：cargo 是 falling 的主体，但原文用这个动作描述风险；第 0 条丢掉了风险联系并改变词形。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0,
    1
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0,
        1
      ],
      "finding": "cargo 是 falling 的主体，但原文用这个动作描述风险；第 0 条丢掉了风险联系并改变词形。",
      "evidence": "The risk of cargo falling from the deck causes concern.",
      "result": "修正第 0 条的风险表达。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [
    {
      "issue_id": "I1",
      "index": 0,
      "reason": "保留风险与内部动作之间的联系及 falling 词形。",
      "new_triples": [
        {
          "head": "The risk",
          "relation": "is of cargo falling from",
          "tail": "the deck",
          "source_sentence_ids": [
            "S1"
          ],
          "evidence": "The risk of cargo falling from the deck causes concern.",
          "confidence": 0.95,
          "clarity": 0.95,
          "relevance": 0.9
        }
      ]
    }
  ],
  "remove": []
}

# 示例：原三元组正确，重建文本错误
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The process includes a grinding step to reduce particle size."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The process",
        "relation": "includes",
        "tail": "a grinding step",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 1,
        "head": "a grinding step",
        "relation": "is to reduce",
        "tail": "particle size",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：重建文本写成 A grinding step reduces particle size；第 1 条原本已保留目的表达。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0,
    1
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0,
        1
      ],
      "finding": "重建文本写成 A grinding step reduces particle size；第 1 条原本已保留目的表达。",
      "evidence": "The process includes a grinding step to reduce particle size.",
      "result": "保留两条三元组，记录重建文本错误。"
    }
  ],
  "handoff": [
    {
      "issue_id": "I1",
      "target": "text_generation",
      "related_indices": [
        0,
        1
      ],
      "finding": "重建文本写成 A grinding step reduces particle size；第 1 条原本已保留目的表达。",
      "evidence": "The process includes a grinding step to reduce particle size."
    }
  ],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}

# 示例：保留 or 的选择含义
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The operator can use a standard mode or an emergency mode."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The operator",
        "relation": "can use",
        "tail": "a standard mode or an emergency mode",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：源句表达可选择的两种模式，当前条目已保留 or。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0
      ],
      "finding": "源句表达可选择的两种模式，当前条目已保留 or。",
      "evidence": "The operator can use a standard mode or an emergency mode.",
      "result": "保留当前条目，replace 为空。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}

# 示例：and 描述一套设备的组成
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "A pair of upper and lower rollers supports the sheet."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "A pair of upper and lower rollers",
        "relation": "supports",
        "tail": "the sheet",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：参与 supports 的是一对滚轮，upper and lower 说明这一对的组成。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0
      ],
      "finding": "参与 supports 的是一对滚轮，upper and lower 说明这一对的组成。",
      "evidence": "A pair of upper and lower rollers supports the sheet.",
      "result": "保留整对滚轮作为主体，replace 为空。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}

# 示例：保留步骤名称，省略句首背景
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "In some embodiments, the process includes a pre-step of washing the parts."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "the process",
        "relation": "includes",
        "tail": "a pre-step of washing the parts",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：a pre-step of 说明预处理步骤；In some embodiments 只是句首背景。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0
      ],
      "finding": "a pre-step of 说明预处理步骤；In some embodiments 只是句首背景。",
      "evidence": "In some embodiments, the process includes a pre-step of washing the parts.",
      "result": "当前条目已表达正确，replace 为空。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}"""

class FeedbackReplaceAgent(FeedbackAgent):
    stage = 'replace'
    task_prompt = TASK_PROMPT
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
