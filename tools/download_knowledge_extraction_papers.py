from pathlib import Path
import re
import time
import urllib.request


OUT = Path(r"E:\huawei after\paper\GPT基础推荐")

PAPERS = [
    ("IJCAI2007-Open Information Extraction from the Web", ["https://www.ijcai.org/Proceedings/07/Papers/429.pdf"]),
    ("IJCAI2011-Open Information Extraction The Second Generation", ["https://www.ijcai.org/Proceedings/11/Papers/012.pdf"]),
    ("WWW2013-ClausIE Clause-Based Open Information Extraction", ["https://resources.mpi-inf.mpg.de/d5/clausie/clausie-www13.pdf"]),
    ("FindingsEMNLP2021-REBEL Relation Extraction By End-to-End Language Generation", ["https://aclanthology.org/2021.findings-emnlp.204.pdf"]),
    ("ACL2022-Unified Structure Generation for Universal Information Extraction", ["https://aclanthology.org/2022.acl-long.395.pdf"]),
    ("EMNLPDemo2022-DeepKE A Deep Learning Based Knowledge Extraction Toolkit", ["https://aclanthology.org/2022.emnlp-demos.10.pdf"]),
    ("NAACL2024-GLiNER Generalist Model for Named Entity Recognition using Bidirectional Transformer", ["https://aclanthology.org/2024.naacl-long.300.pdf"]),
    ("ICLR2024-UniversalNER Targeted Distillation from Large Language Models for Open NER", ["https://proceedings.iclr.cc/paper_files/paper/2024/file/34678d08b36076de986df95c5bbba92f-Paper-Conference.pdf", "https://arxiv.org/pdf/2308.03279"]),
    ("ICLR2024-GoLLIE Annotation Guidelines Improve Zero-Shot Information-Extraction", ["https://proceedings.iclr.cc/paper_files/paper/2024/file/cda04d7ea67ea1376bf8c6962d8541e0-Paper-Conference.pdf", "https://openreview.net/pdf?id=Y3wpuxd7u9"]),
    ("ACL2024-KnowCoder Coding Structured Knowledge into LLMs for Universal Information Extraction", ["https://aclanthology.org/2024.acl-long.475.pdf"]),
    ("EMNLP2024-Learning to Extract Structured Entities Using Language Models", ["https://aclanthology.org/2024.emnlp-main.388.pdf"]),
    ("EMNLP2024-Extract Define Canonicalize An LLM-based Framework for Knowledge Graph Construction", ["https://aclanthology.org/2024.emnlp-main.548.pdf"]),
    ("WWW2025-OneKE A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction System", ["https://arxiv.org/pdf/2412.20005"]),
    ("EMNLPDemo2025-GLiNER2 Schema-Driven Multi-Task Learning for Structured Information Extraction", ["https://aclanthology.org/2025.emnlp-demos.10.pdf"]),
    ("ACL2026-AutoSchemaKG Autonomous Knowledge Graph Construction through Dynamic Schema Induction", ["https://arxiv.org/pdf/2505.23628"]),
    ("FindingsACL2024-ReLiK Retrieve and LinK Fast and Accurate Entity Linking and Relation Extraction", ["https://aclanthology.org/2024.findings-acl.839.pdf"]),
    ("EMNLP2024-ADELIE Aligning Large Language Models on Information Extraction", ["https://aclanthology.org/2024.emnlp-main.419.pdf"]),
    ("EMNLP2024-LogicST A Logical Self-Training Framework for Document-Level Relation Extraction", ["https://aclanthology.org/2024.emnlp-main.314.pdf"]),
    ("FindingsACL2024-Toward Reliable Ad-hoc Scientific Information Extraction", ["https://aclanthology.org/2024.findings-acl.897.pdf"]),
    ("ACL2025-Learning to Generate Structured Output with Schema Reinforcement Learning", ["https://aclanthology.org/2025.acl-long.243.pdf"]),
    ("FindingsEMNLP2025-Adaptive Schema-aware Event Extraction with Retrieval-Augmented Generation", ["https://aclanthology.org/2025.findings-emnlp.419.pdf"]),
]


def safe_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', " ", name).strip()
    prefix, title = cleaned.split("-", 1)
    return f"{prefix.strip():<20} - {title.strip()}.pdf"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (paper download for personal research)"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    if not data.startswith(b"%PDF"):
        raise ValueError(f"not PDF ({len(data)} bytes)")
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ok, failed = [], []
    for label, urls in PAPERS:
        target = OUT / safe_name(label)
        if target.exists() and target.stat().st_size > 10_000:
            ok.append((target.name, "existing", target.stat().st_size))
            continue
        errors = []
        for url in urls:
            try:
                data = fetch(url)
                target.write_bytes(data)
                ok.append((target.name, url, len(data)))
                break
            except Exception as exc:
                errors.append(f"{url}: {exc}")
                time.sleep(1)
        else:
            failed.append((target.name, errors))
    print(f"SUCCESS {len(ok)}")
    for name, _, size in ok:
        print(f"OK\t{size}\t{name}")
    print(f"FAILED {len(failed)}")
    for name, errors in failed:
        print(f"FAIL\t{name}\t{' || '.join(errors)}")


if __name__ == "__main__":
    main()
