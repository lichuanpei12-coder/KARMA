"""Add stage of source-grounded feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """你负责检查源句中哪些关系还没有抽取出来。先看前一步的结果，再自己逐句检查。输出问题清单、新增三元组和需要其他阶段处理的问题。 完整回复采用 User 指定的 JSON 结构。"""

TASK_PROMPT = """# 任务：补充源句中完全没有抽取出来的关系
先列出遗漏问题，再生成新增三元组。

# 步骤
1. 阅读源句，找出它表达的各项关系。
2. 在当前完整集合中查找这些关系，包括长字段中的内容。
3. 对照文本差异，检查它指出的问题是否真的存在。
4. 已有正确表达时，保留现有条目。
5. 已有条目表达不对时，把具体问题交给 Replace。
6. 关系已包含在长字段中、但还没有拆成独立三元组时，交给 Replace 拆分。
7. 关系在整个集合中都没有表达时，列入新增问题清单。
8. 为每个遗漏生成三元组，保留源句中的主体、词形和必要限定。
9. 与现有条目及本轮其他新增项比较，取消重复的新增建议。
10. 输出问题清单、新增项和交给其他阶段的问题。
"""

EXAMPLES = """# 示例：源句有关系完全没有抽取
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The controller reads and stores sensor data."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The controller",
        "relation": "reads",
        "tail": "sensor data",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：stores 没有出现在任何现有条目中。
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
      "finding": "stores 没有出现在任何现有条目中。",
      "evidence": "The controller reads and stores sensor data.",
      "result": "新增 stores 关系。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [
    {
      "head": "The controller",
      "relation": "stores",
      "tail": "sensor data",
      "source_sentence_ids": [
        "S1"
      ],
      "evidence": "The controller reads and stores sensor data.",
      "confidence": 0.95,
      "clarity": 0.95,
      "relevance": 0.9,
      "issue_id": "I1",
      "reason": "当前只表达 reads，源句还表达 stores。"
    }
  ],
  "replace": [],
  "remove": []
}

# 示例：已有动作需要修改，不另加一份
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
核查结论：identify 已有对应条目，但没有保留与 query 的目的联系。
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
      "finding": "identify 已有对应条目，但没有保留与 query 的目的联系。",
      "evidence": "The controller may query the ECU to identify the fault.",
      "result": "交给 Replace 修改第 1 条。"
    }
  ],
  "handoff": [
    {
      "issue_id": "I1",
      "target": "replace",
      "related_indices": [
        0,
        1
      ],
      "finding": "identify 已有对应条目，但没有保留与 query 的目的联系。",
      "evidence": "The controller may query the ECU to identify the fault."
    }
  ],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}

# 示例：内容已在长字段中，交给 Replace 拆分
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
核查结论：processes data 已在 tail 中，但尚未独立表达。
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
      "finding": "processes data 已在 tail 中，但尚未独立表达。",
      "evidence": "The system includes a module that processes data.",
      "result": "交给 Replace 将第 0 条替换为所需的多条三元组。"
    }
  ],
  "handoff": [
    {
      "issue_id": "I1",
      "target": "replace",
      "related_indices": [
        0
      ],
      "finding": "processes data 已在 tail 中，但尚未独立表达。",
      "evidence": "The system includes a module that processes data."
    }
  ],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}

# 示例：重建文本改错连接词
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The module receives signals and generates alerts."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The module",
        "relation": "receives",
        "tail": "signals",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 1,
        "head": "The module",
        "relation": "generates",
        "tail": "alerts",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：重建文本写成 receives signals or generates alerts，但当前两条正确表达了源句的两个动作。
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
      "finding": "重建文本写成 receives signals or generates alerts，但当前两条正确表达了源句的两个动作。",
      "evidence": "The module receives signals and generates alerts.",
      "result": "保留三元组，记录重建文本错误。"
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
      "finding": "重建文本写成 receives signals or generates alerts，但当前两条正确表达了源句的两个动作。",
      "evidence": "The module receives signals and generates alerts."
    }
  ],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}"""

class FeedbackAddAgent(FeedbackAgent):
    stage = 'add'
    task_prompt = TASK_PROMPT
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
