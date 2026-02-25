FEATURE_DESCRIPTIONS = {
    'GR': 'Gamma Ray log. Grain size & shale indicator (higher → finer sediment, shale, mudstone; lower → clean sandstones or carbonates).',
    'ILD_log10': 'Resistivity log (log10 scale). Indicates fluid type & lithology. High values often reflect hydrocarbons or tight carbonates; low values indicate water-bearing formations or shales.',
    'DeltaPHI': 'Porosity difference (Neutron - Density). Sensitive to gas/light hydrocarbons and carbonate effects. Positive suggests gas/light fluids; negative suggests tight lithologies or cementation.',
    'PHIND': 'Porosity indicator. Higher values indicate higher effective porosity and better reservoir quality; lower values indicate tight or low-quality facies.',
    'PE': 'Photoelectric factor. Lithology discriminator. Carbonates (limestone/dolomite) generally show higher PE than siliciclastic sediments.',
    'NM_M': 'Nonmarine/Marine environmental indicator. Helps distinguish depositional setting and stratigraphic transitions.',
    'RELPOS': 'Relative stratigraphic position. Encodes vertical stacking patterns and transgressive-regressive sequences; useful for facies adjacency.'}

LABEL_DESCRIPTIONS = {
  "Nonmarine sandstone": "A clastic sedimentary rock composed of sand-sized grains deposited in terrestrial environments such as rivers or deserts. It typically exhibits high porosity and serves as a primary reservoir rock in continental depositional systems.",
  "Nonmarine coarse siltstone": "A terrestrial sedimentary rock characterized by grain sizes predominantly in the coarse silt range, often deposited in floodplains or lake margins. It represents a depositional setting with moderate to low hydraulic energy compared to sandstone units.",
  "Nonmarine fine siltstone": "A fine-grained siliciclastic rock deposited in low-energy nonmarine settings like deep lacustrine environments. It usually appears as thin beds and reflects quiet water conditions where fine particles can settle out of suspension.",
  "Marine siltstone and shale": "Fine-grained clastic rocks formed in oceanic environments, often exhibiting distinct lamination or fissility. These units are frequently organic-rich and serve as critical source rocks or seals within marine petroleum systems.",
  "Mudstone": "A fine-grained, blocky sedimentary rock composed of clay and silt-sized particles that lacks the fine layering or fissility of shale. Its dense, low-permeability structure makes it an effective regional seal for fluid migration.",
  "Wackestone": "A matrix-supported carbonate rock containing more than 10% grains according to the Dunham classification. This texture indicates a relatively low-energy depositional environment where lime mud was able to accumulate and support the rock's framework.",
  "Dolomite": "A carbonate rock primarily composed of the mineral calcium magnesium carbonate, often formed by the chemical replacement of limestone. It frequently develops significant secondary intercrystalline porosity, making it a highly productive reservoir lithology.",
  "Packstone-grainstone": "A group of grain-supported carbonate rocks characterized by minimal to no lime mud between grains, representing high-energy environments like shoals or reef fronts. These rocks are highly valued in geology for their excellent primary porosity and permeability.",
  "Phylloid-algal bafflestone": "An in-situ carbonate rock formed by leaf-like algae that acted as baffles to trap and bind fine-grained sediment during growth. This lithology is characteristic of bioherms or carbonate mounds and often features complex framework porosity."
}

CLASSIFICATION_SUGGESTIONS={
    'Nonmarine sandstone': """- Coarse-to-medium clastic grains; better sorting and higher porosity
        - Lower GR (clean sand), higher AC/CNL, lower DEN
        - Resistivity moderately elevated due to porosity and grain framework""",
    'Nonmarine coarse siltstone': """- Intermediate between sandstone and fine silt/mud units
        - GR slightly increased relative to sandstone due to finer grains & clay
        - Porosity moderate; resistivity mildly reduced vs sandstone""",
    'Nonmarine fine siltstone': """- Finer grain size and higher clay content
        - GR further elevated; AC/CNL lower; DEN slightly increased
        - Resistivity modest; transitional to mudstone""",
    'Marine siltstone and shale': """- High mud/clay fraction; poor sorting
        - Elevated GR; relatively low porosity; DEN comparatively higher
        - Resistivity low to moderate; more uniform trends due to marine deposition""",
    'Mudstone': """- Dominantly clay; minimal grain support
        - Very high GR; low AC/CNL; high DEN; very poor porosity
        - Resistivity generally low unless cementation increases""",
    'Wackestone': """- Carbonate matrix supporting allochems; moderate mud content
        - GR low to moderate (cleaner than shale but muddier than grainstones)
        - Resistivity variable; porosity mixed but often modest""",
    'Dolomite': """- Dolomitized carbonate; often enhanced secondary porosity
        - Lower GR; DEN reduced relative to limestone; AC/CNL signatures variable
        - Resistivity often elevated due to porosity + fabric changes""",
    'Packstone-grainstone': """- Coarse carbonate grains; grain-supported; higher porosity and cleaner
        - Low GR; good AC/CNL indications; lower DEN
        - Resistivity elevated relative to muddier carbonates""",
    'Phylloid-algal bafflestone': """- Complex fabric with biogenic baffling and interstitial porosity
        - Low to moderate GR; porosity highly variable (interparticle + moldic)
        - Resistivity variable; local heterogeneity common"""
}


def build_trend_prompt(window):
    prompt = """# Well Log Data Trend Analysis Task
    ## Task Description
    You are a petroleum well log data analysis expert. Please conduct detailed trend analysis on the given well log data window, focusing on the trend variations of each feature in the target sample segment."""

    prompt += """
    ## Analysis Requirements
    Please conduct in-depth trend analysis of the above data with the following specific requirements:

    ### 1. Overall Window Trend Overview
    - Describe the basic geological characteristics of the entire data window
    - Analyze the continuity and changes between context, target segment, and post sections

    ### 2. Detailed Feature Trend Analysis
    For each feature, conduct detailed analysis focusing on:
    - **Value Change Trends**: Increasing, decreasing, stable, fluctuating, etc.
    - **Curve Morphology**: Left convex, right convex, sawtooth, smooth, etc.
    - **Relative Value Levels**: High or low relative to the entire window baseline
    - **Mutation Point Identification**: Obvious value jumps or trend reversals
    - **Periodic Fluctuations**: Whether there are regular ups and downs

    ### 3. Inter-feature Correlation Analysis
    - Analyze synergistic changes between different features
    - Identify possible geological significance combinations 
    - Resistivity features relationship with other features

    ### 4. Geological Interpretation Suggestions
    - Based on trend analysis results, provide possible geological layer type tendencies
    - Focus on feature combinations related to reservoir quality
    - Identify possible hydrocarbon indication features"""

    prompt+=f"Here is the well log data window for analysis:{window}\n"

    prompt+="""
        ## Output Format Requirements
        Please organize your analysis results according to the following structure:

        **Overall Trend Overview:**
        [Basic characteristics and continuity analysis of the entire window]

        **Detailed Feature Analysis:**
        - GR Trend: [Specific description]
        - ILD_log10 Trend: [Specific description]
        - DeltaPHI Trend: [Specific description]
        - PHIND Trend: [Specific description]
        - PE Trend: [Specific description]
        - NM_M Trend: [Specific description]
        - RELPOS Trend: [Specific description]

        Please ensure the analysis is detailed and specific, using professional geological terminology to provide valuable trend information for subsequent reservoir classification.
        """
    return prompt