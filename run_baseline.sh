#!/usr/bin/env bash
# 第一部分：生成第一轮基线；在 Git Bash / MINGW64 中运行 bash run_baseline.sh。
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# 平时只需修改这里：数据集路径、样本数量、过滤阈值。
DATASETS=("data/DocIOE/DocOIE_transportation_gold_input.json")
SAMPLE_LIMIT=5                 # 当前跑前 5 篇；改成 20 跑 20 篇；0 表示全部。
INTEGRATION_THRESHOLD=0        # 与原来脚本的默认阈值一致。

BASELINE_ROOT="outputs/baselines"
CURRENT_BASELINES="outputs/current_baselines.txt"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"

if ! [[ "$SAMPLE_LIMIT" =~ ^[0-9]+$ ]]; then
    echo "SAMPLE_LIMIT 必须是非负整数。" >&2
    exit 1
fi
if (( ${#DATASETS[@]} == 0 )); then
    echo "请在 DATASETS 中配置至少一个数据集。" >&2
    exit 1
fi
for dataset in "${DATASETS[@]}"; do
    if [[ ! -f "$dataset" ]]; then
        echo "找不到数据集：$dataset" >&2
        exit 1
    fi
done

mkdir -p -- "$BASELINE_ROOT"
# 仅重置路径清单，不改动任何旧基线。失败时保持为空，避免误用旧基线。
: > "$CURRENT_BASELINES"
baseline_files=()
index=0
for dataset in "${DATASETS[@]}"; do
    index=$((index + 1))
    dataset_name="$(basename -- "$dataset")"
    dataset_name="${dataset_name%.*}"
    output_dir="$BASELINE_ROOT/$RUN_ID/${index}_$dataset_name"
    args=(--stage baseline --input "$dataset" --output-dir "$output_dir"
          --integration-threshold "$INTEGRATION_THRESHOLD")
    if (( SAMPLE_LIMIT > 0 )); then
        args+=(--limit "$SAMPLE_LIMIT")
    fi
    echo "第一部分：$dataset；样本上限：$SAMPLE_LIMIT（0 表示全部）"
    if ! python main.py "${args[@]}"; then
        echo "基线生成失败；当前基线清单未启用。请查看错误后重新运行。" >&2
        exit 1
    fi
    if [[ ! -f "$output_dir/baseline.json" ]]; then
        echo "运行结束但未找到基线包：$output_dir/baseline.json" >&2
        exit 1
    fi
    baseline_files+=("$output_dir/baseline.json")
done

printf '%s\n' "${baseline_files[@]}" > "$CURRENT_BASELINES"
echo "第一部分完成。基线包路径："
printf '  %s\n' "${baseline_files[@]}"
echo "路径已记录到 $CURRENT_BASELINES；接下来运行：bash run_revision.sh"
