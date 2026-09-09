"""Evaluator Agent Implementation"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from karma.core.base_agent import BaseAgent
from karma.core.data_structures import KnowledgeTriple
from karma.agents.extraction_support import safe_score

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class EvaluatorAgent(BaseAgent):
    """Evaluator Agent (EA) for final quality assessment and integration decisions."""

    def __init__(self, client, model_name: str, integrate_threshold: float = 0):
        system_prompt = """你是一个三元组抽取质量的评估代理。你的任务是评估提取的知识三元组的质量，并基于综合质量指标做出最终集成决策。

目标：使用多维度质量评估来评估知识三元组，并根据既定阈值确定集成资格。

评估维度：

1. 置信度（权重：50%）：
   - 提取过程的可靠性
   - 文本证据的强度
   - 与领域知识的一致性
   - 统计显著性（如适用）

2. 清晰度（权重：25%）：
   - 关系的语言精确性
   - 实体引用的具体性
   - 无歧义性
   - 关系陈述的明确性

3. 相关性（权重：25%）：
   - 生物医学意义
   - 对知识发现的潜在影响
   - 新颖性或确认价值
   - 与领域优先级的一致性

集成评分：
集成分数 = （0.5 x 置信度）+（0.25 x 清晰度）+（0.25 x 相关性）

质量阈值：
- 优秀（>=0.8）：高质量、证据充分的关系
- 良好（0.6-0.79）：可靠但有轻微限制的关系
- 可接受（0.5-0.59）：质量足够集成
- 存疑（0.3-0.49）：可靠性有限，需要审查
- 差（<0.3）：质量不足以集成

决策标准：
集成条件：
- 集成分数 >= 阈值（通常为0.6）
- 所有维度分数 >= 0.3（最低质量底线）
- 未发现重大质量问题
- 关系为知识库增加价值

拒绝条件：
- 集成分数 < 阈值
- 任一维度分数 < 0.3
- 与既定事实矛盾
- 支持证据不充分

处理要求：
- 应用一致的评估标准
- 记录质量评估理由
- 保持决策透明
- 保留原始质量指标
- 支持不同用例的阈值调整"""
        super().__init__(client, model_name, system_prompt)
        self.integrate_threshold = integrate_threshold

        # 每次运行一个时间戳文件夹，存放抽取出的三元组 json
        self._dump_dir = Path("data/result") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self._dump_dir.mkdir(parents=True, exist_ok=True)
        self._dump_counter = 0

    def process(self, triples: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """Evaluate and filter triples based on quality metrics.

        This version also logs the integration score for each triple and prints the
        average score across all evaluated triples.
        """
        # `finalize_triples` returns a tuple where the first element is the list of
        # integrated triples. We keep the original behaviour for the pipeline but
        # add logging of scores here.
        integrated, _, _, _ = self.finalize_triples(triples)
        # Compute scores for logging – reuse the same aggregation logic.
        scores = [self._aggregate_scores(t) for t in triples]
        if scores:
            avg_score = sum(scores) / len(scores)
            logger.info(f"📊 Average integration score for all triples: {avg_score:.3f}")
            for t, s in zip(triples, scores):
                logger.info(f"Triple: ({t.head}, {t.relation}, {t.tail}) – score: {s:.3f}, conf: {t.confidence}, cla: {t.clarity}, rele: {t.relevance}")
        else:
            logger.info("No triples to evaluate.")

        # 每次调用都写一个文件（空也写 []），保证文件序号 = 调用顺序，
        # 这样 evaluate.py 能按 2i/2i+1 对齐 gold（每篇第 2 轮 = 最终结果）。
        dump_path = self._dump_dir / f"{self._dump_counter:03d}_{datetime.now().strftime('%H%M%S')}.json"
        # Non-numeric prefix keeps the candidate audit outside evaluate.py's
        # two-files-per-document sequence.
        audit_path = self._dump_dir / f"_evaluation_{self._dump_counter:03d}_candidates.json"
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump([
                {"head": t.head, "relation": t.relation, "tail": t.tail,
                 "confidence": t.confidence, "clarity": t.clarity,
                 "relevance": t.relevance, "score": s}
                for t, s in zip(triples, scores)
            ], f, ensure_ascii=False, indent=2)
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump([
                {"head": t.head, "relation": t.relation, "tail": t.tail,
                 "confidence": t.confidence, "clarity": t.clarity,
                 "relevance": t.relevance, "score": self._aggregate_scores(t)}
                for t in integrated
            ], f, ensure_ascii=False, indent=2)
        self._dump_counter += 1
        return integrated

    def finalize_triples(self, candidate_triples: List[KnowledgeTriple]) -> Tuple[List[KnowledgeTriple], int, int, float]:
        """Filter triples based on integration threshold."""
        integrated_triples = []

        for triple in candidate_triples:
            # Ensure all metrics are set
            triple.confidence = safe_score(triple.confidence)
            triple.clarity = safe_score(triple.clarity)
            triple.relevance = safe_score(triple.relevance)

            # Calculate integration score
            integration_score = self._aggregate_scores(triple)

            # Keep triple if it meets threshold
            if integration_score >= self.integrate_threshold:
                integrated_triples.append(triple)

        return integrated_triples, 0, 0, 0.0

    def _aggregate_scores(self, triple: KnowledgeTriple) -> float:
        """Combine quality metrics into final score."""
        # Weighted average: confidence=50%, clarity=25%, relevance=25%
        return (0.5 * triple.confidence + 0.25 * triple.clarity + 0.25 * triple.relevance)
