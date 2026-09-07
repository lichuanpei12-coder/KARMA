#!/bin/bash

# 定义数据集列表
# "CUAD.json" "kleister_nda_sentences.json"DocOIE_transportation_eval_sent.json
DATASETS=("data/DocIOE/DocOIE_transportation_gold_input.json")

# 循环运行 main.py
for dataset in "${DATASETS[@]}"; do
    echo "=========================================="
    echo "正在处理数据集: $dataset"
    echo "=========================================="
    python main.py --input "$dataset"
    
    # 检查执行状态
    if [ $? -eq 0 ]; then
        echo "✅ $dataset 处理完成"
    else
        echo "❌ $dataset 处理失败"
    fi
    echo ""
done

echo "=========================================="
echo "所有数据集处理完毕！"
echo "========================================"
