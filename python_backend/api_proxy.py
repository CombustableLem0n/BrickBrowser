from flask import Flask, jsonify, request
from flask_cors import CORS
from requests_oauthlib import OAuth1Session
import traceback


app = Flask(__name__)
CORS(app)

consumer_key = '146AC42D62B34D48AF6F24196AA9693F'
consumer_secret = '11F3308D90AB453D853C3DD0D0770F98'
token = 'F9FA0615CE78489CBD7C34F7AC1CE063'
token_secret = '02522E662C2C4FB58A1FDBBA690F8F01'

@app.route('/part-images', methods=['POST'])
def part_images():
    data = request.json
    part_numbers = data.get('part_numbers')

    if not part_numbers or not isinstance(part_numbers, list):
        return jsonify({'error': 'Missing or invalid part_numbers'}), 400

    oauth = OAuth1Session(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
    )

    results = []

    try:
        for part_number in part_numbers:
            print(f"Looking up image for part {part_number}")
            image_url = None
            color_used = None

            # Step 1: Get known colors for the part
            colors_url = f'https://api.bricklink.com/api/store/v1/items/PART/{part_number}/colors'
            colors_resp = oauth.get(colors_url)

            if colors_resp.status_code == 200:
                colors_data = colors_resp.json().get('data', [])
                if colors_data:
                    # Pick the first known color's ID
                    color_used = colors_data[0].get('color_id') or colors_data[0].get('id')
                    print(f"Found known color {color_used} for part {part_number}")

                    # Step 2: Get image for that part in the first known color
                    image_url_api = f'https://api.bricklink.com/api/store/v1/items/PART/{part_number}/images/{color_used}'
                    image_resp = oauth.get(image_url_api)

                    if image_resp.status_code == 200:
                        image_data = image_resp.json().get('data', {})
                        image_url = image_data.get('thumbnail_url')
                        print(f"Found image for part {part_number} in color {color_used}")
                    else:
                        print(f"Image not found for part {part_number} in color {color_used}")
                else:
                    print(f"No known colors found for part {part_number}")
            else:
                print(f"Failed to get colors for part {part_number}, status: {colors_resp.status_code}")

            results.append({
                'part_number': part_number,
                'image_url': image_url,
                'color_id': color_used,
                'external_url': f'https://www.bricklink.com/v2/catalog/catalogitem.page?P={part_number}' + (f'&C={color_used}' if color_used else '')
            })

        return jsonify({'images': results})

    except Exception as e:
        print("Exception in /part-images:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
