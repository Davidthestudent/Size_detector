import re
import json
from openai import OpenAI
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from io import BytesIO

num = 0
path = './checkpoint-250'
API_KEY = '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'


def image_description(raw):
    if isinstance(raw, bytes):
        pil = Image.open(BytesIO(raw)).convert("RGB")
    elif isinstance(raw, str):
        pil = Image.open(raw).convert("RGB")
    elif isinstance(raw, Image.Image):
        pil = raw.convert("RGB")
    else:
        raise TypeError("img must be in bytes | str (path) | PIL.Image.Image")
    model = BlipForConditionalGeneration.from_pretrained(path)
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    inputs = processor(images=pil, return_tensors="pt")

    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    return caption


def calculate_type_fig(caption, height, weight, gender):
    client = OpenAI(
        api_key='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')
    prompt = (
        f"Analyze a person with the following details:\n"
        f"- Height: {height} cm\n"
        f"- Weight: {weight} kg\n"
        f"- Gender: {gender}\n"
        f"- The description of a clothe that person is wearing on the photo (if available): {caption}\n\n"
        "Provide your answer in structured JSON format. DO NOT add any comments "
        "The answer should feel natural and human-like in tone, but the output must be represented as a JSON file.\n\n"
        "  \"body_type\": \"Stylish nicely constructed description of the body type e.g.: You have or Your body type is...\",\n"
        "  \"style_vibes\": [\"list of styles and vibes that fit this person based on the persons figure, e.g. casual, elegant, sporty,minimum 5 different styles\"],\n"
        "  \"recommended_clothes\": [\"list of clothing items minimum of 10 items\"],\n"
        "   \"combinations\" : [\" list of different combinations of items  according to selected styles represented as a list of lists where each combination is written just as a list of items\"],\n"
        "  \"color_palette\": [\"list of suggested color hex codes combined into lists according to style\"],\n"
    )

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a helpful assistant that classifies body types."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.output_text

    if "```json" in result:
        result = result[7:]
    if result[-3:] == '```':
        result = result[:-3]
    #print(result)
    return json.loads(result)


def get_brand_data(brand, brand_sizes):
    for b in brand_sizes:
        if b['brand'].lower() == brand.lower():
            return b
    return ai_size_detector(brand)


def size_getter(brand, clothe_type, gender):
    with open('brand_sizes.json', 'r', encoding='utf-8') as f:
        brand_sizes = json.load(f)
    brand_data = get_brand_data(brand, brand_sizes)
    selected_clothing = brand_data['categories'][gender][clothe_type]
    requirements = selected_clothing['required_measurements']
    print(f"For detecting the size we need to know the following measurements:{requirements}\n")
    user_params = {}
    for requirement in requirements:
        value = input(f"Enter {requirement}: ")
        user_params[requirement] = float(value)
    if 'numeric' in selected_clothing:
        return find_best_size(selected_clothing['numeric'], user_params)
    elif 'alpha' in selected_clothing:
        return find_best_size(selected_clothing['alpha'], user_params)
    else:
        raise ValueError("No size table found for this clothing item.")


def find_best_size(size_table, user_params, type_of_measure):
    best_size = None
    min_diff = float('inf')
    if type_of_measure == 'in':
        size_chart = 'US'
    else:
        size_chart = 'EU'
    size_table = size_table[size_chart]
    for size_label, measurements in size_table.items():
        diff = 0
        for param, user_value in user_params.items():
            if param in measurements:
                diff += abs(measurements[param] - user_value)
        if diff < min_diff:
            min_diff = diff
            best_size = size_label
    return f'The best size for you is: {best_size} {size_chart}'


def pars_json(t: str):
    t = t.strip()
    t = re.sub(r'^```(?:json)?\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    return json.loads(t)


def ai_size_detector(link, size_type='EU', brand='Some_brand'):
    if size_type == 'EU':
        measure_type = 'cm'
    else:
        measure_type = 'in'
    client = OpenAI(
        api_key=API_KEY)
    prompt = (
        f'Analyse the clothe with the following link: {link} from {brand} check only for {size_type} sizes\n'
        f'Ask for measures which are needed to determine the size of the clothes\n'
        f'Provide your answer in structured JSON format. DO NOT add any comments. You should get all the information '
        f'and keep only the necessary one which is listed in the official chart tables.'
        f'In the following form:'
        " f\"Needed_measurements\": \"Send a list of measurements that are needed e.g hips,brest, etc.\",\n"
        f'\"Short_instructions\":  ["How to measure needed_measurement_1 ...","How to measure needed_measurement_2 '
        f'...","..."],,\n'
        f'\"Size_table\" :[\" For each size get the approximate measurement for each size of needed measurements and '
        f'represent it as a dict. It should have the following structure:  ""{size_type}": {{'
        f'"Size_value": {{"needed_measure": "measurement in {measure_type} without word and return it as a number", '
        f'example: "waist",length of the feet,etc:'
        f'"...", "hips": "..."}},'
        f'}},'
    )

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a helpful fashion-assistant that classifies correctly the sizes "
                                          "for clothes."},
            {"role": "user", "content": prompt}
        ]
    )

    return pars_json(response.output_text)


if __name__ == '__main__':
    tests = [
        'https://www.zara.com/at/de/soft-bomberjacke-p03046264.html?v1=485598703'
    ]
    for link in tests:
        print(ai_size_detector(link))
