import json
from typing import Any, Dict, List

import pandas as pd

from api import get_result
from tool_call import get_tool_selection
from tools import (
    ExpertFeatureDescriptionTool,
    ExpertLabelDescriptionTool,
    ClassificationSuggestionsTool,
    TrendAnalysisTool,
    NeighborFindTool,
)

def parse_labels_from_answer(answer_str: str) -> List[str]:
    try:
        obj = json.loads(answer_str)
        labels = obj.get("answer", [])
        if isinstance(labels, list):
            return [str(x) for x in labels]
    except Exception:
        pass
    return []


STRICT_NONMARINE_LABELS = {
    "Nonmarine sandstone",
    "Nonmarine coarse siltstone",
    "Nonmarine fine siltstone",
}

STRICT_MARINE_LABELS = {
    "Wackestone",
    "Dolomite",
    "Packstone-grainstone",
    "Phylloid-algal bafflestone",
}

AMBIGUOUS_LABELS = {
    "Marine siltstone and shale",
    "Mudstone",
}


def enforce_nm_m_consistency(meta_data: Dict[str, Any],
                             labels: List[str]) :

    window_df: pd.DataFrame = meta_data["window_df"]
    nm_list = window_df["NM_M"].tolist()

    if "Predicted_Facies" in window_df.columns:
        pred_list = [str(x) for x in window_df["Predicted_Facies"].tolist()]
    else:
        pred_list = [None] * len(nm_list)

    n = min(len(labels), len(nm_list))
    fixed = labels[:]
    corrections = []

    for i in range(n):
        env = nm_list[i]
        facies = labels[i]
        pred_facies = pred_list[i]

        if env == 1:
            if facies in STRICT_MARINE_LABELS:
                old = facies
                if pred_facies and pred_facies not in STRICT_MARINE_LABELS:
                    facies_new = pred_facies
                else:
                    facies_new = "Nonmarine sandstone"
                fixed[i] = facies_new
                corrections.append({
                    "index": i,
                    "env": int(env),
                    "old_label": old,
                    "new_label": facies_new,
                    "reason": "NM_M=1 (non-marine), but label is strictly marine; corrected.",
                })

        elif env == 2:
            if facies in STRICT_NONMARINE_LABELS:
                old = facies
                if pred_facies and pred_facies not in STRICT_NONMARINE_LABELS:
                    facies_new = pred_facies
                else:
                    facies_new = "Wackestone"
                fixed[i] = facies_new
                corrections.append({
                    "index": i,
                    "env": int(env),
                    "old_label": old,
                    "new_label": facies_new,
                    "reason": "NM_M=2 (marine), but label is strictly non-marine; corrected.",
                })

        else:
            pass

    info = {
        "num_corrections": len(corrections),
        "details": corrections,
    }
    return fixed, info


def aggregate_panel(label_lists: Dict[str, List[str]]):
    if not label_lists:
        return [], [], 0.0

    max_len = max(len(v) for v in label_lists.values())
    final_labels: List[str] = []
    agreement_per_depth: List[float] = []

    for i in range(max_len):
        votes: List[str] = []
        for _, seq in label_lists.items():
            if i < len(seq):
                votes.append(seq[i])

        if not votes:
            final_labels.append("UNKNOWN")
            agreement_per_depth.append(0.0)
            continue

        counts: Dict[str, int] = {}
        for v in votes:
            counts[v] = counts.get(v, 0) + 1

        best_label, best_count = max(counts.items(), key=lambda x: x[1])
        final_labels.append(best_label)
        agreement_per_depth.append(best_count / len(votes))

    if agreement_per_depth:
        global_agreement = sum(agreement_per_depth) / len(agreement_per_depth)
    else:
        global_agreement = 0.0

    return final_labels, agreement_per_depth, global_agreement


# =============== 1. Planner 阶段（工具选择） ===============

from typing import Any, Dict, List
import pandas as pd

def process_logic_part1(meta_data: Dict[str, Any]) -> Dict[str, Any]:
    window_df: pd.DataFrame = meta_data["window_df"]
    target_columns: List[str] = meta_data["target_columns"].copy()

    if "Predicted_Facies" in target_columns:
        target_columns.remove("Predicted_Facies")

    table_df = window_df[target_columns]
    table_str = table_df.to_string(index=False)

    planner_prompt, think, answer, tool_call_list = get_tool_selection(table_str)

    meta_data["tool_call_prompt"] = planner_prompt
    meta_data["tool_call_think"] = think
    meta_data["tool_call_answer"] = answer
    meta_data["tool_call_list"] = tool_call_list
    return meta_data



def build_base_decision_prompt(meta_data: Dict[str, Any]) -> str:
    window_df: pd.DataFrame = meta_data["window_df"]
    target_columns: List[str] = meta_data["target_columns"]

    parts: List[str] = []

    parts.append(
        "You are a petroleum well log data analysis expert. "
        "Please classify each depth point (each row/sample) in the Well Log Facies Dataset "
        "into one of 9 lithofacies categories using the provided well log features.\n"
    )

    if meta_data.get("expert_feature_description"):
        parts.append(meta_data["expert_feature_description"] + "\n")

    if meta_data.get("expert_label_description"):
        parts.append(meta_data["expert_label_description"] + "\n")

    if meta_data.get("classification_suggestions"):
        parts.append(meta_data["classification_suggestions"] + "\n")

    parts.append("## Data to be Classified:\n")
    parts.append("### Well Log Data to Classify:\n")
    parts.append(str(window_df[target_columns]) + "\n")

    parts.append(
        "The Predicted_Facies column is provided by XGBoost for reference. "
        "You may refine or override it based on your expert analysis of the well log features.\n"
    )

    if "trend_analysis_answer" in meta_data:
        parts.append(
            "\nHere is the trend analysis results to assist your classification:\n"
            "### Trend Analysis Results:\n"
            f"{meta_data['trend_analysis_answer']}\n"
        )

    parts.append(
        "In the features, NM_M means non-marine or marine.\n"
        "1 means non-marine. The label can only be one of: "
        "Nonmarine sandstone, Nonmarine coarse siltstone, Nonmarine fine siltstone, "
        "Marine siltstone and shale, Mudstone.\n"
        "2 means marine. The label can only be one of: "
        "Wackestone, Dolomite, Packstone-grainstone, Phylloid-algal bafflestone.\n"
    )

    parts.append(
        "You must output a JSON object in the following format:\n"
        "{ \"answer\": [\"X1\", \"X2\", ...] }\n"
        "Each Xi is the facies label for the corresponding depth point, "
        "strictly chosen from the 9 categories above.\n"
    )

    return "\n".join(parts)


def build_decision_prompt(style: str, meta_data: Dict[str, Any]) -> str:
    base = build_base_decision_prompt(meta_data)

    if style == "expert":
        tail = (
            "\n## Decision Preference (EXPERT MODE)\n"
            "- Rely primarily on expert feature descriptions, label definitions, and heuristic rules.\n"
            "- Treat XGBoost Predicted_Facies only as a weak prior that can be freely overridden.\n"
        )
    elif style == "model_aware":
        tail = (
            "\n## Decision Preference (MODEL-AWARE MODE)\n"
            "- Use XGBoost Predicted_Facies as a strong prior.\n"
            "- Only change the predicted label when multiple evidence sources clearly indicate inconsistency.\n"
        )
    elif style == "trend_focus":
        tail = (
            "\n## Decision Preference (TREND-FOCUSED MODE)\n"
            "- Emphasize vertical continuity and trend patterns across the window and its context.\n"
            "- Avoid frequent, noisy facies switching between adjacent depth points unless strongly supported by logs.\n"
        )
    else:
        tail = "\n## Decision Preference\n- Use a balanced combination of all information sources.\n"

    return base + tail


# =============== 3. 主流程：工具执行 + Panel 决策 + 环境纠偏 ===============

def process_logic(meta_data: Dict[str, Any]):
    meta_data = process_logic_part1(meta_data)
    tool_call_list: List[str] = meta_data["tool_call_list"]
    print("Selected Tools:", tool_call_list)

    if "expert_feature_description_tool" in tool_call_list:
        tool_expert_feature_description = ExpertFeatureDescriptionTool()
        meta_data["expert_feature_description"] = tool_expert_feature_description.run()

    if "expert_label_description_tool" in tool_call_list:
        tool_expert_label_description = ExpertLabelDescriptionTool()
        meta_data["expert_label_description"] = tool_expert_label_description.run()

    classification_tool_names = {
        "classification_suggestions_tool",
        "expert_classification_suggestions_tool",
    }
    if any(name in tool_call_list for name in classification_tool_names):
        tool_classification_suggestions = ClassificationSuggestionsTool()
        meta_data["expert_classification_suggestions"] = tool_classification_suggestions.run()

    if "trend_analysis_tool" in tool_call_list:
        tool_trend_analysis = TrendAnalysisTool()
        meta_data = tool_trend_analysis.run(meta_data)

    if "neighbor_finding_tool" in tool_call_list or "neighbor_finding_tool" in tool_call_list:
        tool_neighbor_find = NeighborFindTool()
        meta_data = tool_neighbor_find.run(meta_data)

    styles = ["expert", "model_aware", "trend_focus"]
    panel_outputs: Dict[str, Dict[str, Any]] = {}
    label_lists: Dict[str, List[str]] = {}

    for style in styles:
        prompt_i = build_decision_prompt(style, meta_data)
        think_i, answer_i = get_result(prompt_i)
        labels_i = parse_labels_from_answer(answer_i)

        panel_outputs[style] = {
            "prompt": prompt_i,
            "think": think_i,
            "answer": answer_i,
            "labels": labels_i,
        }
        label_lists[style] = labels_i

    meta_data["panel"] = panel_outputs

    final_labels, agreement_per_depth, global_agreement = aggregate_panel(label_lists)
    meta_data["panel_aggregation"] = {
        "final_labels_before_env_fix": final_labels,
        "agreement_per_depth": agreement_per_depth,
        "global_agreement": global_agreement,
    }

    fixed_labels, nm_info = enforce_nm_m_consistency(meta_data, final_labels)
    meta_data["env_consistency"] = nm_info
    meta_data["panel_aggregation"]["final_labels"] = fixed_labels

    expert_prompt = panel_outputs["expert"]["prompt"]
    expert_think = panel_outputs["expert"]["think"]
    final_answer_obj = {"answer": fixed_labels}
    final_answer_str = json.dumps(final_answer_obj, ensure_ascii=False)

    return expert_prompt, expert_think, final_answer_str, meta_data
