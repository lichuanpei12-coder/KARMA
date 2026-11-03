"""Remove stage of source-grounded feedback."""
from karma.agents.feedback_common import FeedbackAgent

SYSTEM_PROMPT = """你负责独立检查整个集合中的重复三元组。自己判断是否重复、保留哪条和删除哪条。前一步没有提示的重复也要检查。 完整回复采用 User 指定的 JSON 结构。"""

TASK_PROMPT = """# 任务：自己找出重复三元组，决定保留哪条、删除哪条
前一步的疑似重复清单只是提示。即使它为空，也要检查完整集合。

# 步骤
1. 阅读源句和当前全部三元组。
2. 查找可能表达同一事实的条目。
3. 比较它们的主体、关系、客体，以及否定、可能性、条件、数量、时间和范围。
4. 回查源句，区分完整重复、字段部分重叠和同一主体的不同关系。
5. 列出重复问题清单。
6. 选择保留项：主体和关系正确，符合原文用词，且必要限定完整。
7. 不因条目更新、更长或分数更高就优先保留。同样正确且等价时，保留编号较小的一条。
8. 检查要删除的条目是否还有保留项没有表达的内容。
9. 每项删除写清 index 和 keep_index，并确认保留项不在本轮删除清单中。
10. 两条都需要修改或只是部分重叠时，交给 Replace；无法判断时写明原因。
11. 输出问题清单和删除项。add、replace 为空。
"""

EXAMPLES = """# 示例：自主找重复，并说明保留谁
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
        "relation": "receives",
        "tail": "signals",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 2,
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
核查结论：第 0、1 条完整重复；第 2 条表达另一项关系。
完整回复：
{
  "reviewed_sentence_ids": [
    "S1"
  ],
  "reviewed_indices": [
    0,
    1,
    2
  ],
  "issues": [
    {
      "issue_id": "I1",
      "sentence_ids": [
        "S1"
      ],
      "related_indices": [
        0,
        1,
        2
      ],
      "finding": "第 0、1 条完整重复；第 2 条表达另一项关系。",
      "evidence": "The module receives signals and generates alerts.",
      "result": "保留第 0、2 条，删除第 1 条。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": [
    {
      "issue_id": "I1",
      "index": 1,
      "keep_index": 0,
      "reason": "两条完整表达相同的 receives 关系。",
      "evidence": "The module receives signals and generates alerts."
    }
  ]
}

# 示例：字段部分重叠，不删除整条
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
        "head": "a module",
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
核查结论：两条分别表达 includes 和 processes；只是第 0 条的 tail 包含了内部关系。
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
      "finding": "两条分别表达 includes 和 processes；只是第 0 条的 tail 包含了内部关系。",
      "evidence": "The system includes a module that processes data.",
      "result": "保留两条关系，将字段收短问题交给 Replace。"
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
      "finding": "两条分别表达 includes 和 processes；只是第 0 条的 tail 包含了内部关系。",
      "evidence": "The system includes a module that processes data."
    }
  ],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}

# 示例：同一主体、同一动作词也不一定重复
输入：
{
  "source_sentences": [
    {
      "sentence_id": "S1",
      "text": "The module may send a warning and must send a report."
    }
  ],
  "current_collection": {
    "version": "V0",
    "triples": [
      {
        "index": 0,
        "head": "The module",
        "relation": "may send",
        "tail": "a warning",
        "source_sentence_ids": [
          "S1"
        ]
      },
      {
        "index": 1,
        "head": "The module",
        "relation": "must send",
        "tail": "a report",
        "source_sentence_ids": [
          "S1"
        ]
      }
    ]
  },
  "handoff": []
}
核查结论：两条的对象和情态不同，源句分别支持它们。
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
      "finding": "两条的对象和情态不同，源句分别支持它们。",
      "evidence": "The module may send a warning and must send a report.",
      "result": "两条都保留，remove 为空。"
    }
  ],
  "handoff": [],
  "handoff_results": [],
  "add": [],
  "replace": [],
  "remove": []
}"""

class FeedbackRemoveAgent(FeedbackAgent):
    stage = 'remove'
    task_prompt = TASK_PROMPT
    examples_prompt = EXAMPLES

    def __init__(self, client, model_name):
        super().__init__(client, model_name, SYSTEM_PROMPT)
