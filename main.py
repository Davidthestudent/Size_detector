import os
import json
import torch
from openai import OpenAI

num = 0
def calculate_type_fig(img_path, height, weight, gender,num):
    client = OpenAI(
        api_key='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')
    with open(img_path, "rb") as f:
        image_bytes = f.read()
    prompt = (
        f"Analyze a person with the following details:\n"
        f"- Height: {height} cm\n"
        f"- Weight: {weight} kg\n"
        f"- Gender: {gender}\n"
        f"- Image description (if available): extracted separately\n\n"
        "Provide your answer in structured JSON format. "
        "The answer should feel natural and human-like in tone, but the output must strictly follow JSON.\n\n"
        "JSON structure:\n"
        "{\n"
        "  \"body_type\": \"short description of the body type\",\n"
        "  \"style_vibes\": [\"list of styles or vibes that fit this person, e.g. casual, elegant, sporty\"],\n"
        "  \"recommended_clothes\": [\"list of clothing items\"],\n"
        "  \"color_palette\": [\"list of suggested color hex codes or names\"],\n"
        "  \"keywords\": [\"separate keywords describing the person, style, or body type\"]\n"
        "}\n"
    )

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "You are a helpful assistant that classifies body types."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.output_text

    try:
        result_json = json.loads(result)
    except:
        result_json = {"error": "Invalid JSON from model", "raw": result}

    with open(f"result.json_{num}", "w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=4)

    num+=1
    return result_json


if __name__ == '__main__':
    height, weight, gender = input().split(',')
    height = int(height)
    weight = int(weight)
    print('Choose an image to upload')
    img_path = input()
    result = calculate_type_fig(img_path, height, weight, gender,num)
