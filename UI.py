import streamlit as st
import requests
from datetime import date

API_BASE = st.secrets["API_BASE"]


def api_call(path: str, method="post", params=None, json=None, data=None, files=None, timeout=60):
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    try:
        r = requests.request(method.upper(), url, params=params, json=json, data=data, files=files, timeout=timeout)
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
        return None

    if r.status_code == 204:
        return {}
    ctype = r.headers.get("content-type", "")
    text = r.text

    if "application/json" not in ctype:
        st.error(f"Non-JSON response (HTTP {r.status_code}) from {url}")
        st.code(text[:2000])
        return None

    try:
        data = r.json()
    except ValueError:
        st.error(f"Invalid JSON (HTTP {r.status_code}) from {url}")
        st.code(text[:2000])
        return None

    if not r.ok:
        detail = data.get("detail") if isinstance(data, dict) else data
        st.error(f"HTTP {r.status_code}: {data.get('detail', data)}")
        return None

    return data


st.set_page_config(page_title="Style Recommender", page_icon="🧥", layout="wide")

st.title('Size Detector A.K.A Your personal stylish_maker')
st.write('This app helps to define your style, helps you get the best size of selected clothe and be your '
         'fashion helper')

left, right = st.columns(2, gap='large')

if "client_id" not in st.session_state:
    st.session_state["client_id"] = None

st.session_state.setdefault("plan_token", None)
st.session_state.setdefault("needed", [])
st.session_state.setdefault("plan_unit", "EU")
st.session_state.setdefault("instructions", [])

with left:
    with st.form('Fashion Helper'):
        name = st.text_input("Name (placeholder)", placeholder="John Doe")
        email = st.text_input("Email (placeholder)", placeholder="youremail@example.com")
        height = st.number_input('Insert your Height in cm', min_value=0, max_value=None)
        weight = st.number_input('Insert your Weight in kg', min_value=0, max_value=None)
        gender = st.selectbox('Select your Gender', ['', 'Male', 'Female', 'Divers'], index=0)
        birthdate = st.date_input('Insert your date of birth in format DD.MM.YYYY',
                                  min_value=date(1990, 1, 1), max_value=date.today(), format="MM.DD.YYYY")
        img = st.file_uploader("Optional: upload a photo (image/*) for auto-caption",
                               type=['png', 'jpg', 'jpeg', 'webp'])
        submit = st.form_submit_button('Let\'s get your advice!')
        if submit:
            with st.spinner('Getting the result...'):
                user_res = api_call(
                    "/users",
                    method="post",
                    json={"name": name, "email": email, "height": height,
                          "weight": weight, "gender": gender,
                          'birthdate': birthdate.isoformat() if birthdate else None})
                if not user_res:
                    st.error('Failed to save user.')
                    st.stop()
                public_id = user_res.get('public_id')
                if not public_id:
                    st.error('Server did not return public_id.')
                    st.stop()
                st.session_state["client_public_id"] = public_id

                if img is not None:
                    with st.spinner(f'Uploading image and getting caption and advice...'):
                        files = {'file': (img.name, img.getvalue(), img.type or 'image/jpeg')}
                    data = {'client_id': public_id,
                            'height': height,
                            'weight': weight,
                            'gender': gender}

                    res = api_call(
                        "/get_image_and_description",
                        method="post",
                        data=data,
                        files=files
                    )
                    if not res:
                        st.error('Failed to process image.')
                    else:
                        st.success("Done")
                        st.subheader("Advice")
                        st.write(res.get("Type_fig") or "")
                else:
                    st.warning("Profile saved. Upload an image to get caption + advice.")

with right:
    token = None
    with st.form('Size from the link'):
        name = st.text_input("Name (placeholder)", placeholder="John Doe")
        email = st.text_input("Email (placeholder)", placeholder="youremail@example.com")
        link = st.text_input('Link', placeholder='Enter a link')
        brand = st.text_input('Brand (if applicable)', placeholder='Enter a brand')
        size_type = st.selectbox('Select your  type of size', ('EU', 'US'), index=0)
        submit = st.form_submit_button('Let\'s get your size!')
        if submit:
            with st.spinner('Getting the result...'):
                user_res = api_call(
                    "/users",
                    method="post",
                    json={"name": name, "email": email})
                result = api_call("/size_detection", method="post", json={'link': link,
                                                                          'size_type': size_type,
                                                                          'brand': brand or None})
                st.session_state["plan_token"] = result["token"]
                st.session_state["needed"] = result["needed_measurements"]
                st.session_state["plan_unit"] = result["unit_system"]
                st.session_state["instructions"] = result["short_instructions"]

            st.success("Please enter the following measures")
    if st.session_state["needed"]:
        with st.form('Measurements'):
            values = {}
            for i, m in enumerate(st.session_state["needed"]):
                values[m] = st.number_input(m.title(), min_value=0, max_value=None, key=f'm_{m}',
                                            help=st.session_state['instructions'][i])
                with st.expander(f'How to measure {m}', expanded=False):
                    st.write(st.session_state['instructions'][i])
            go = st.form_submit_button("Get best size")
        if go:
            payload = {
                "token": st.session_state["plan_token"],
                "unit_system": st.session_state["plan_unit"],
                "values": values,
            }
            best = api_call("/get_params", method="post", json=payload)
            if best:
                st.success(f"Best size: {best['best_size']}")

                st.session_state["plan_token"] = None
                st.session_state["needed"] = []
                st.session_state["plan_unit"] = 'EU'
                st.session_state["instructions"] = []
