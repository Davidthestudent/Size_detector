import streamlit as st
import requests
import os
import uuid

API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")


def api_call(path: str, method="post", params=None, json=None, files=None, timeout=60):
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    req = requests.post if method.lower() == "post" else requests.get
    try:
        r = req(url, params=params, json=json, files=files, timeout=timeout)
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
        return None

    ctype = r.headers.get("content-type", "")
    text = r.text

    # если это не JSON — покажем, что пришло (обычно там traceback)
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
        # FastAPI HTTPException обычно вернёт {"detail": "..."}
        st.error(f"HTTP {r.status_code}: {data.get('detail', data)}")
        return None

    return data


st.set_page_config(page_title="Style Recommender", page_icon="🧥", layout="wide")

st.title('Size Detector A.K.A Your personal stylish_maker')
st.write('This app helps to define your style, helps you get the best size of selected clothe and be your '
         'fashion helper')

with st.sidebar:
    st.title('Style Recommender')
    st.sidebar.selectbox("Language", ['EN', 'DE', 'RU'], index=0)
    st.caption(f"API: {API_BASE}")

left, right = st.columns(2, gap='large')

if "client_id" not in st.session_state:
    st.session_state["client_id"] = int(uuid.uuid4().int % 10 ** 9)

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
        age = st.number_input('Insert your age', min_value=0, max_value=None)
        img = st.file_uploader("Optional: upload a photo (image/*) for auto-caption",
                               type=['png', 'jpg', 'jpeg', 'webp'])
        submit = st.form_submit_button('Let\'s get your advice!')
        if submit:
            with st.spinner('Getting the result...'):
                cid = st.session_state["client_id"]
                _ = api_call(
                    "/get_info",
                    method="get",
                    params={
                        "client_id": cid,
                        "name": name,
                        "age": int(age),
                        "gender": gender,
                        "height": int(height),
                        "weight": int(weight),
                        "email": email,
                    },
                )

                if img is not None:
                    files = {'file': (img.name, img.getvalue(), img.type or 'image/jpeg')}
                    res = api_call(
                        "/get_image_and_description",
                        method="post",
                        params={"client_id": cid},  # ВАЖНО: в query, не в json
                        files=files,
                    )
                    st.success("Done")
                    st.subheader("Caption")
                    if res:
                        st.subheader("Advice")
                        st.write(res.get("Type_fig") or "")
                else:
                    st.warning("Upload an image to get caption + advice.")

with right:
    token = None
    with st.form('Size from the link'):
        link = st.text_input('Link', placeholder='Enter a link')
        brand = st.text_input('Brand (if applicable)', placeholder='Enter a brand')
        size_type = st.selectbox('Select your  type of size', ('EU', 'US'), index=0)
        submit = st.form_submit_button('Let\'s get your size!')
        if submit:
            with st.spinner('Getting the result...'):
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
                values[m] = st.number_input(m.title(), min_value=0, max_value=100, key=f'm_{m}',
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
