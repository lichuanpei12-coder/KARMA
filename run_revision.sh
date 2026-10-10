#!/usr/bin/env bash
# 第二部分：复用固定基线，重新执行文本重建、比较和第二轮修订。
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# 默认留空，自动使用 run_baseline.sh 记录的基线。
# 如需指定旧基线，在数组中填入路径，例如：
# BASELINE_FILES=("outputs/baselines/某次运行/1_数据集/baseline.json")
BASELINE_FILES=()
CURRENT_BASELINES="outputs/current_baselines.txt"
REVISION_ROOT="outputs/revisions"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"

if (( ${#BASELINE_FILES[@]} == 0 )); then
    if [[ ! -s "$CURRENT_BASELINES" ]]; then
        echo "没有可用的当前基线。请先成功运行：bash run_baseline.sh" >&2
        exit 1
    fi
    while IFS= read -r baseline || [[ -n "$baseline" ]]; do
        baseline="${baseline%$'\r'}"
        [[ -z "$baseline" ]] || BASELINE_FILES+=("$baseline")
    done < "$CURRENT_BASELINES"
fi
if (( ${#BASELINE_FILES[@]} == 0 )); then
    echo "基线路径清单为空，请先运行第一部分。" >&2
    exit 1
fi
for baseline in "${BASELINE_FILES[@]}"; do
    if [[ ! -f "$baseline" ]]; then
        echo "找不到基线包：$baseline" >&2
        exit 1
    fi
done

index=0
for baseline in "${BASELINE_FILES[@]}"; do
    index=$((index + 1))
    dataset_name="$(basename -- "$(dirname -- "$baseline")")"
    output_dir="$REVISION_ROOT/$RUN_ID/${index}_$dataset_name"
    echo "第二部分读取基线：$baseline"
    echo "本次优化结果保存到：$output_dir"
    if ! python main.py --stage revise --baseline "$baseline" --output-dir "$output_dir"; then
        echo "第二部分运行失败；基线保持不变，请查看错误后重试。" >&2
        exit 1
    fi
done
echo "第二部分完成。下次优化后再次运行 bash run_revision.sh，即复用同一基线并另存结果。"
