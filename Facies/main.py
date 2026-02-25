import pandas as pd
import json
import os
from process import process_logic

target_columns = ['Depth', 'GR', 'ILD_log10', 'DeltaPHI', 'PHIND', 'PE', 'NM_M', 'RELPOS', 'Predicted_Facies']


def main(file_path, output_jsonl):
    output_dir = os.path.dirname(output_jsonl)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = pd.read_csv(file_path)
    window_size = 16
    step_size = 16

    start_window_idx = 0
    if os.path.exists(output_jsonl):
        with open(output_jsonl, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            start_window_idx = len(lines)

    start_row_index = start_window_idx * step_size

    if start_row_index >= len(df):
        print("all windows have been processed. No more data to process.")
        return

    print(f"Starting processing from window {start_window_idx + 1} (Row index {start_row_index})...")

    with open(output_jsonl, 'a', encoding='utf-8') as f:
        for i in range(start_row_index, len(df), step_size):
            current_window_id = i // step_size + 1
            print(f"Processing window {current_window_id} (Rows {i} → {min(i + window_size, len(df)) - 1})")

            window_df = df.iloc[i: i + window_size]

            try:
                meta_data = {}
                meta_data['target_columns'] = target_columns
                meta_data['current_window_id'] = current_window_id
                meta_data['window_df'] = window_df
                meta_data['window_up'] = df.iloc[max(0, i - step_size): i] if i - step_size >= 0 else pd.DataFrame()
                meta_data['window_down'] = df.iloc[i + window_size: i + window_size + step_size] if i + window_size < len(df) else pd.DataFrame()
                meta_data['is_full_window'] = (len(window_df) == window_size)

                print('Calling API / Agent pipeline...')

                prompt, think, answer, meta_data = process_logic(meta_data)
                print(f"Window {current_window_id} API call successful.")

                # 将 raw 里的 DataFrame 转成可序列化结构
                raw = meta_data.get("raw", {})
                if isinstance(raw.get("window_df"), pd.DataFrame):
                    raw["window_df"] = raw["window_df"].to_dict(orient='records')
                if isinstance(raw.get("window_up"), pd.DataFrame):
                    raw["window_up"] = raw["window_up"].to_dict(orient='records')
                if isinstance(raw.get("window_down"), pd.DataFrame):
                    raw["window_down"] = raw["window_down"].to_dict(orient='records')
                meta_data["raw"] = raw

                meta_data['window_df'] = meta_data['window_df'].to_dict(orient='records')
                meta_data['window_up'] = meta_data['window_up'].to_dict(orient='records')
                meta_data['window_down'] = meta_data['window_down'].to_dict(orient='records')

                record = {
                    "meta_data": meta_data,
                    "content": {
                        "prompt": prompt,
                        "think": think,
                        "answer": answer,
                    },
                }

                print(f"Window {current_window_id} processed.")
                print("-" * 50)

                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

            except Exception as e:
                print(f"Error processing window {current_window_id}: {e}")

                break

    print(f"Done. Results saved in: {output_jsonl}")


if __name__ == "__main__":
    input_file = ""
    output_file = ""
    main(input_file, output_file)
