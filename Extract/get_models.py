import requests
from bs4 import BeautifulSoup
import threading
import csv
import argparse

def get_brand_models(brand_href):
    page_num = 1
    models = []
    while True:
        page_link = f"https://www.motorcycle.com{brand_href}?page_num={page_num}"
        response = requests.get(page_link)

        if response.status_code != 200:
            break
        else:
            soup = BeautifulSoup(response.text, "html.parser")
            model_tags = soup.find_all(
                "a", {"class": "card-link flex flex-column flex-one"}
            )
            for tag in model_tags:
                href = tag["href"]
                name = tag.select("h6")[0].text.strip()
                models.append({"model_href": href, "model_name": name})

            page_num += 1

    return models


def thread_function(manufacture):
    global results, PROCESSED_COUNT

    brand_href = manufacture["brand_href"]
    brand_name = manufacture["brand_name"]

    result = get_brand_models(brand_href)
    for model in result:
        model["brand_href"] = brand_href
        model["brand_name"] = brand_name
        results.append(model)

    PROCESSED_COUNT += 1
    update_progress(PROCESSED_COUNT / len(manufacturers))


def update_progress(progress):
    bar_length = 40
    block = int(round(bar_length * progress))
    progress_bar = "█" * block + "-" * (bar_length - block)
    print(f"\r[{progress_bar}] {round(progress * 100, 2)}%", end="", flush=True)

    if progress == 1:
        print("\nDone!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=str, help='Output file directory')
    args = parser.parse_args()

    url = "https://www.motorcycle.com/specs/"
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    manufacturer_tags = soup.select("ul.brands-list li.sl-manufacturer a")

    manufacturers = []
    for tag in manufacturer_tags:
        href = tag["href"]
        name = tag.text.strip()
        manufacturers.append({"brand_href": href, "brand_name": name})

    results = []
    threads = []
    PROCESSED_COUNT = 0

    print("Crawling...")
    for manufacture in manufacturers:
        thread = threading.Thread(target=thread_function, args=(manufacture,))
        threads.append(thread)
        thread.start()

    update_progress(0)
    for thread in threads:
        thread.join()

    csv_file = args.output
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"Data written to {csv_file}")
