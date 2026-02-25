# tools.py
from prompts import FEATURE_DESCRIPTIONS, LABEL_DESCRIPTIONS, CLASSIFICATION_SUGGESTIONS, build_trend_prompt
from api import get_result_trend
import pandas as pd


class ExpertFeatureDescriptionTool:
    def __init__(self):
        self.name = "expert_feature_description_tool"
        self.description = "Provide detailed descriptions of log features."

    def run(self) -> str:
        text = 'Here are the descriptions of various features:\n'
        for key, desc in FEATURE_DESCRIPTIONS.items():
            text += f"**{key}**: {desc}\n"
        return text

class ExpertLabelDescriptionTool:
    def __init__(self):
        self.name = "expert_label_description_tool"
        self.description = "Provide detailed descriptions of lithofacies labels."

    def run(self) -> str:
        text = 'Here are the descriptions of various labels:\n'
        for key, desc in LABEL_DESCRIPTIONS.items():
            text += f"**{key}**: {desc}\n"
        return text


class ClassificationSuggestionsTool:
    def __init__(self):
        self.name = "expert_classification_suggestions_tool"
        self.description = "Provide heuristic suggestions for facies classification."

    def run(self) -> str:
        text = 'Here are some suggestions for classification tasks:\n\n'
        for label, suggestion in CLASSIFICATION_SUGGESTIONS.items():
            text += f"### {label}\n{suggestion}\n\n"

        text += """
## General Analysis Framework:
### Step 1: Lithology & Grain-Size Assessment
- **Low GR + good AC/CNL + low DEN** → Cleaner, coarser clastics / grainstones
- **High GR + low AC/CNL + high DEN** → Mud-rich shales/mudstones
- **Carbonates vs siliciclastics** are often distinguished by GR + density + neutron response patterns.

### Step 2: Porosity & Fabric Indicators
- **High porosity**: Enhanced AC/CNL mismatch, density drop, possible resistivity gain.
- **Low porosity**: Compressed AC/CNL, DEN↑, uniform resistivity trends.

### Step 3: Depositional Context & Facies Grouping
- **Nonmarine clastics**: Sandstone → coarse siltstone → fine siltstone → shale sequence.
- **Carbonates**: Wackestone → Packstone-grainstone → Phylloid-algal bafflestone → Dolomite transitions.

**Important**: These relationships reflect general depositional and lithological tendencies.
Facies boundaries are gradational, and curve variability is high. 
Interpret trends holistically rather than relying on single-curve thresholds.
"""
        return text


class TrendAnalysisTool:
    def __init__(self):
        self.name = "trend_analysis_tool"
        self.description = "Analyze up-target-down window trends in well logs."

    def run(self, meta_data):
        window_up = meta_data.get("window_up", pd.DataFrame())
        window_df = meta_data["window_df"]
        window_down = meta_data.get("window_down", pd.DataFrame())
        target_columns = meta_data["target_columns"]

        full_window = pd.concat([window_up, window_df, window_down])

        cols = [c for c in target_columns if c != "Predicted_Facies"]
        full_window = full_window[cols]

        prompt = build_trend_prompt(full_window)
        think, answer = get_result_trend(prompt)

        meta_data["trend_analysis_prompt"] = prompt
        meta_data["trend_analysis_think"] = think
        meta_data["trend_analysis_answer"] = answer

        return meta_data


class NeighborFindTool:
    def __init__(self):
        self.name = "neighbor_finding_tool"
        self.description = "Placeholder tool to find nearest-neighbor wells (not yet implemented)."

    def run(self, meta_data):
        return meta_data
