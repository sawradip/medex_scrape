# All Companies Page to Company Data

import requests
from bs4 import BeautifulSoup
import csv
import re
from pprint import pprint


def max_pagination_pages(soup):
    page_items = soup.find_all('li', class_='page-item')
    page_values = [item.get_text(strip=True) for item in page_items]

    pageList = [int(value) for value in page_values if value.isdigit()]
    if pageList:
        max_page = max(pageList)
        return max_page
    else:
        return None


def pagesoup_to_company_data(soup):
    companies_data = []

    company_blocks = soup.find_all('div', class_='row data-row')

    for block in company_blocks:
        name_tag = block.find('a')
        if name_tag:
            company_name = name_tag.get_text(strip=True)
            url = name_tag['href'] if name_tag['href'].endswith("brands") else f"{name_tag['href']}/brands"
            
            details_tag = block.find_all('div', class_='col-xs-12')[-1]
            # print(details_tag)
            if details_tag:
                details_text = details_tag.get_text(strip=True).split(',')
                generics_str = details_text[0].replace("generics", "").strip()
                brand_names_str = details_text[1].replace("brand names", "").strip()

                generics = int(generics_str) if generics_str.isdigit() else 0
                brand_names = int(brand_names_str) if generics_str.isdigit() else 0
            
                companies_data.append({
                    'name': company_name,
                    'generics': generics,
                    'brand_names': brand_names,
                    'company_url': url
                })
    return companies_data


def pagesoup_to_brand_data(soup, company_name=""):
    brand_blocks = soup.find_all('a', class_='hoverable-block')

    brands_data = []
    for brand_block in brand_blocks:
        name_elem = brand_block.find('div', class_='data-row-top')
        dosage_elem = brand_block.find('span', class_='inline-dosage-form')
        strength_elem = brand_block.find('span', class_='grey-ligten')
        # generic_elem = brand_block.find_all('div')[2]  # Assuming the generic name is in the third div
        price_elem = brand_block.find('span', class_='package-pricing')

        url = brand_block['href'] if 'href' in brand_block.attrs else ''
        dosage = dosage_elem.get_text(strip=True) if dosage_elem else ''
        name = (name_elem.get_text(strip=True) if name_elem else '').strip(dosage)  # Exclude dosage form
        strength = strength_elem.get_text(strip=True) if strength_elem else ''
        # generic = generic_elem.get_text(strip=True) if generic_elem else ''
        price = price_elem.get_text(strip=True).replace('Unit Price : ', '') if price_elem else ''
        
        brands_data.append({
            "company": company_name,
            'url': url,
            'name': name,
            'dosage': dosage,
            'strength': strength,
            # 'generic': generic,
            'price': price
        })
    return brands_data



def pagesoup_to_medicine_info(soup):
    for br in soup.find_all('br'):
        br.replace_with('\n')

    medication_info = []

    indications_divs = soup.find_all('div', class_='ac-body')

    for indications_div in indications_divs:
        if indications_div.parent:
            parent_div = indications_div.parent
            if len(parent_div.find_all('div')) == 2:  # Check if it has exactly two child divs
                child_divs = parent_div.find_all('div')
                medication_info.append({
                    "section": child_divs[0].get_text(strip=True),
                    "text": child_divs[1].get_text(strip=True),
                })

    return medication_info


# base_url = "http://medex.com.bd/companies?page=1"

# response = requests.get(base_url)
# soup = BeautifulSoup(response.content, 'html.parser')

# max_company_pages = max_pagination_pages(soup)
# max_company_pages

# all_company_info = []
# for page in range(max_company_pages):
#     base_url = "http://medex.com.bd/companies"

#     response = requests.get(
#         base_url,
#         params={
#             'page': page + 1
#             }
#         )
#     # pprint(response.json())
#     soup = BeautifulSoup(response.content, 'html.parser')
#     company_data = pagesoup_to_company_data(soup)
#     all_company_info.extend(company_data)


# print("Total Companies: ", len(all_company_info))

import json

with open('all_company_info.json', 'r', encoding='utf-8') as f:
    all_company_info = json.load(f)


# n = 0

## All Companies Page to Company Data

import requests
from bs4 import BeautifulSoup
import csv
import re
from pprint import pprint
from tqdm.auto import tqdm

start = 150
for n, company_data in tqdm(enumerate(all_company_info)):
    if n < start:
        continue
    company_name = company_data["name"]
    company_url = company_data["company_url"]
    response = requests.get(company_url)
    # pprint(response.json())

    soup = BeautifulSoup(response.content, 'html.parser')
    print()
    print(">>  ", company_name)
    print(">>  ", company_url)
    max_page_dict = {
        "AqVida bangladesh": 1,
        "Arges Life Science Limited": 1,
        "Aztec Pharmaceuticals Ltd.": 1,
        "Beauty Formulas": 1,
    }
    max_pages = max_page_dict.get(company_name, max_pagination_pages(soup)) or 1
    # max_pages

    all_brands_info = []
    for page in tqdm(range(max_pages)):
        base_url = company_url

        response = requests.get(
            base_url,
            params={
                'page': page + 1
                }
            )
        # pprint(response.json())
        soup = BeautifulSoup(response.content, 'html.parser')
        brands_data = pagesoup_to_brand_data(soup, company_name=company_name)

        for brand_data in tqdm(brands_data, leave=False):
            medicine_url = brand_data["url"]

            response = requests.get(medicine_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            en_medication_info = pagesoup_to_medicine_info(soup)

            response = requests.get(f"{medicine_url}/bn")
            soup = BeautifulSoup(response.text, 'html.parser')
            bn_medication_info = pagesoup_to_medicine_info(soup)

            medication_info = {
                "bn": bn_medication_info,
                "en": en_medication_info
            }
            brand_data["info"] = medication_info

            all_brands_info.append(brand_data)
    pprint(f"{company_name}: {len(all_brands_info)} brands")

    company_data["all_brands"] = all_brands_info
    # all_company_info.extend(company_data)

    with open(f'{(n+1):03d}.{company_name.strip(".")}.json', 'w', encoding='utf-8') as f:
        json.dump(company_data, f, ensure_ascii=False, indent=4)
# pprint(len(company_data))


print("Total Companies: ", len(company_data))
