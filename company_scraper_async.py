# All Companies Page to Company Data

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from tqdm.auto import tqdm
from pprint import pprint


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def max_pagination_pages(soup):
    page_items = soup.find_all('li', class_='page-item')
    page_values = [item.get_text(strip=True) for item in page_items]

    pageList = [int(value) for value in page_values if value.isdigit()]
    if pageList:
        max_page = max(pageList)
        return max_page
    else:
        return None


async def pagesoup_to_company_data(soup):
    companies_data = []

    company_blocks = soup.find_all('div', class_='row data-row')

    for block in company_blocks:
        name_tag = block.find('a')
        if name_tag:
            company_name = name_tag.get_text(strip=True)
            url = name_tag['href'] if name_tag['href'].endswith("brands") else f"{name_tag['href']}/brands"

            details_tag = block.find_all('div', class_='col-xs-12')[-1]
            if details_tag:
                details_text = details_tag.get_text(strip=True).split(',')
                generics_str = details_text[0].replace("generics", "").strip()
                brand_names_str = details_text[1].replace("brand names", "").strip()

                generics = int(generics_str) if generics_str.isdigit() else 0
                brand_names = int(brand_names_str) if brand_names_str.isdigit() else 0
            
                companies_data.append({
                    'name': company_name,
                    'generics': generics,
                    'brand_names': brand_names,
                    'company_url': url
                })
    return companies_data


async def pagesoup_to_brand_data(soup, company_name=""):
    brand_blocks = soup.find_all('a', class_='hoverable-block')

    brands_data = []
    for brand_block in brand_blocks:
        name_elem = brand_block.find('div', class_='data-row-top')
        dosage_elem = brand_block.find('span', class_='inline-dosage-form')
        strength_elem = brand_block.find('span', class_='grey-ligten')
        price_elem = brand_block.find('span', class_='package-pricing')
        generic_elem = brand_block.find_all('div')[3]

        url = brand_block['href'] if 'href' in brand_block.attrs else ''
        dosage = dosage_elem.get_text(strip=True) if dosage_elem else ''
        name = (name_elem.get_text(strip=True) if name_elem else '').strip(dosage)
        strength = strength_elem.get_text(strip=True) if strength_elem else ''
        price = price_elem.get_text(strip=True).replace('Unit Price : ', '') if price_elem else ''
        generic = generic_elem.get_text(strip=True) if generic_elem else ''
        
        brands_data.append({
            "company": company_name,
            'url': url,
            'name': name,
            'dosage': dosage,
            'strength': strength,
            'price': price,
            'generic': generic
        })
    return brands_data


async def pagesoup_to_medicine_info(soup):
    for br in soup.find_all('br'):
        br.replace_with('\n')

    medication_info = []

    indications_divs = soup.find_all('div', class_='ac-body')

    for indications_div in indications_divs:
        if indications_div.parent:
            parent_div = indications_div.parent
            if len(parent_div.find_all('div')) == 2:
                child_divs = parent_div.find_all('div')
                medication_info.append({
                    "section": child_divs[0].get_text(strip=True),
                    "text": child_divs[1].get_text(strip=True),
                })

    return medication_info


async def main():
    with open('all_company_info.json', 'r', encoding='utf-8') as f:
        all_company_info = json.load(f)

    start = 85
    async with aiohttp.ClientSession() as session:
        for n, company_data in tqdm(enumerate(all_company_info)):
            if n < start:
                continue
            company_name = company_data["name"]
            company_url = company_data["company_url"]
            response = await fetch(session, company_url)
            soup = BeautifulSoup(response, 'html.parser')
            print()
            print(">>  ", company_name)
            print(">>  ", company_url)
            max_page_dict = {
                "AqVida bangladesh": 1,
                "Arges Life Science Limited": 1,
                "Aztec Pharmaceuticals Ltd.": 1,
                "Beauty Formulas": 1,
            }
            max_pages = max_page_dict.get(company_name, await max_pagination_pages(soup)) or 1

            all_brands_info = []
            for page in tqdm(range(max_pages)):
                response = await fetch(session, f"{company_url}?page={page + 1}")
                soup = BeautifulSoup(response, 'html.parser')
                brands_data = await pagesoup_to_brand_data(soup, company_name=company_name)

                for brand_data in tqdm(brands_data, leave=False):
                    medicine_url = brand_data["url"]

                    response = await fetch(session, medicine_url)
                    soup = BeautifulSoup(response, 'html.parser')
                    en_medication_info = await pagesoup_to_medicine_info(soup)

                    response = await fetch(session, f"{medicine_url}/bn")
                    soup = BeautifulSoup(response, 'html.parser')
                    bn_medication_info = await pagesoup_to_medicine_info(soup)

                    medication_info = {
                        "bn": bn_medication_info,
                        "en": en_medication_info
                    }
                    brand_data["info"] = medication_info

                    all_brands_info.append(brand_data)
            pprint(f"{company_name}: {len(all_brands_info)} brands")

            company_data["all_brands"] = all_brands_info

            with open(f'{(n+1):03d}.{company_name.strip(".")}.json', 'w', encoding='utf-8') as f:
                json.dump(company_data, f, ensure_ascii=False, indent=4)

    print("Total Companies: ", len(all_company_info))


if __name__ == "__main__":
    asyncio.run(main())
