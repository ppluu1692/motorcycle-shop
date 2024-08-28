import json
import threading
from bs4 import BeautifulSoup
import pandas as pd
import requests
import argparse


def get_detail_model(model_href):
    url = f"https://www.motorcycle.com{model_href}"
    response = requests.get(url)
    result = {}

    if response.status_code != 200:
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    panel_title = soup.find_all("h4", {"class": "panel-title opensans-it fs18 lh15"})
    panel_title = [tag.text for tag in panel_title]

    panel_content = soup.find_all("div", {"class": "vs-specs-table fs16 lh15"})

    for title, content in zip(panel_title, panel_content):
        result[title] = {}
        key_divs = content.find_all("div", class_="spec-key bold")
        for key_div in key_divs:
            field = key_div.text.strip()
            value = key_div.find_next_sibling("div").text.strip()

            result[title][field] = value

    return result


def thread_function(model_batch):
    global results, PROCESSED_COUNT, N_MODELS

    for id, href in model_batch.items():
        results[id] = get_detail_model(href)
        PROCESSED_COUNT += 1
        if PROCESSED_COUNT % 10 == 9:
            update_progress(PROCESSED_COUNT / N_MODELS)


def update_progress(progress):
    bar_length = 40
    block = int(round(bar_length * progress))
    progress_bar = "█" * block + "-" * (bar_length - block)
    print(f"\r[{progress_bar}] {round(progress * 100, 2)}%", end="", flush=True)

    if progress == 1:
        print("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='Input file directory')
    parser.add_argument('output', type=str, help='Output file directory')
    args = parser.parse_args()

    print("Preparing...")
    df = pd.read_csv(args.input, encoding="utf-8")
    df = df.drop_duplicates()

    N_MODELS = df.shape[0]

    results = [None] * N_MODELS
    threads = []
    json_file = args.output
    PROCESSED_COUNT = 0
    BATCH_SIZE = 100

    for i in range(N_MODELS // BATCH_SIZE + 1):
        df_ranged = df[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        batch_href = dict(zip(df_ranged.index, df_ranged["model_href"]))
        thread = threading.Thread(target=thread_function, args=(batch_href,))
        threads.append(thread)
        thread.start()

    print("Crawling...")
    update_progress(0)
    for thread in threads:
        thread.join()
    update_progress(1)

    output = {}
    for i in range(N_MODELS):
        row_data = df.iloc[i]
        output[i] = {
            "name": row_data.model_name,
            "brand": row_data.brand_name,
            "href": row_data.model_href,
            "specs": results[i],
        }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Data written to {json_file}")
