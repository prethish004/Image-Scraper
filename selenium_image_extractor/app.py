# # # # import streamlit as st
# # # # import pandas as pd
# # # # import time
# # # # import os
# # # # import requests
# # # # from urllib.parse import quote
# # # # from io import BytesIO
# # # # from PIL import Image

# # # # from selenium import webdriver
# # # # from selenium.webdriver.chrome.service import Service
# # # # from selenium.webdriver.chrome.options import Options
# # # # from selenium.webdriver.common.by import By
# # # # from selenium.webdriver.support.ui import WebDriverWait
# # # # from selenium.webdriver.support import expected_conditions as EC
# # # # from webdriver_manager.chrome import ChromeDriverManager

# # # # # ============================================================
# # # # # STREAMLIT PAGE CONFIG
# # # # # ============================================================

# # # # st.set_page_config(
# # # #     page_title="Food Image URL Scraper",
# # # #     page_icon="🍽️",
# # # #     layout="wide"
# # # # )

# # # # st.title("🍽️ Smart Food Image URL Scraper")
# # # # st.caption("Intelligent fallback-based image search with quality filtering")

# # # # # ============================================================
# # # # # SIDEBAR – SEARCH & QUALITY SETTINGS
# # # # # ============================================================

# # # # st.sidebar.header("🔍 Search Settings")

# # # # taste_modifier = st.sidebar.selectbox(
# # # #     "Food Style / Taste",
# # # #     ["None", "Hot", "Spicy", "Sweet", "Cool", "Dessert", "Street Food", "Indian"]
# # # # )

# # # # headless_mode = st.sidebar.checkbox("Run Browser in Headless Mode", value=True)

# # # # st.sidebar.header("📐 Image Quality Filters")

# # # # MIN_WIDTH = st.sidebar.slider("Minimum Width (px)", 100, 800, 300)
# # # # MIN_HEIGHT = st.sidebar.slider("Minimum Height (px)", 100, 800, 300)

# # # # MIN_FILE_SIZE = st.sidebar.slider("Minimum File Size (KB)", 5, 100, 15) * 1024
# # # # MAX_FILE_SIZE = st.sidebar.slider("Maximum File Size (KB)", 50, 1000, 500) * 1024

# # # # PREFERRED_WIDTH = st.sidebar.number_input("Preferred Width", 300, 1000, 600)
# # # # PREFERRED_HEIGHT = st.sidebar.number_input("Preferred Height", 300, 1000, 600)

# # # # # ============================================================
# # # # # INPUT SECTION
# # # # # ============================================================

# # # # st.subheader("📥 Input Food Items")

# # # # input_mode = st.radio(
# # # #     "Choose Input Method",
# # # #     ["Upload CSV", "Manual Entry"]
# # # # )

# # # # food_items = []

# # # # if input_mode == "Upload CSV":
# # # #     uploaded_file = st.file_uploader("Upload CSV (must contain Item_Name column)", type=["csv"])
# # # #     if uploaded_file:
# # # #         df_input = pd.read_csv(uploaded_file)
# # # #         if "Item_Name" not in df_input.columns:
# # # #             st.error("CSV must contain `Item_Name` column")
# # # #             st.stop()
# # # #         food_items = df_input["Item_Name"].dropna().astype(str).tolist()

# # # # else:
# # # #     manual_text = st.text_area(
# # # #         "Enter food names (one per line)",
# # # #         height=150,
# # # #         placeholder="Chicken Biryani\nMasala Dosa\nIce Cream"
# # # #     )
# # # #     if manual_text.strip():
# # # #         food_items = [x.strip() for x in manual_text.split("\n") if x.strip()]

# # # # st.info(f"Total items loaded: {len(food_items)}")

# # # # # ============================================================
# # # # # SELENIUM SCRAPER CLASS
# # # # # ============================================================

# # # # class SmartImageScraper:

# # # #     def __init__(self, headless=True):
# # # #         chrome_options = Options()
# # # #         if headless:
# # # #             chrome_options.add_argument("--headless=new")

# # # #         chrome_options.add_argument("--no-sandbox")
# # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # #         chrome_options.add_argument("--window-size=1920,1080")

# # # #         service = Service(ChromeDriverManager().install())
# # # #         self.driver = webdriver.Chrome(service=service, options=chrome_options)
# # # #         self.driver.set_page_load_timeout(15)

# # # #     def close(self):
# # # #         self.driver.quit()

# # # #     def search(self, food_name, modifier):
# # # #         query_parts = [food_name]
# # # #         if modifier != "None":
# # # #             query_parts.append(modifier.lower())

# # # #         search_query = quote(" ".join(query_parts))
# # # #         url = f"https://www.bing.com/images/search?q={search_query}"

# # # #         self.driver.get(url)
# # # #         time.sleep(1.5)

# # # #         self.driver.execute_script("window.scrollBy(0,600)")
# # # #         time.sleep(1)

# # # #         images = self.driver.find_elements(By.TAG_NAME, "img")

# # # #         for img in images:
# # # #             src = img.get_attribute("src")
# # # #             if src and src.startswith("http"):
# # # #                 info = self.check_quality(src)
# # # #                 if info:
# # # #                     return info

# # # #         return None

# # # #     def check_quality(self, url):
# # # #         try:
# # # #             r = requests.get(url, timeout=4)
# # # #             if r.status_code != 200:
# # # #                 return None

# # # #             size = len(r.content)
# # # #             if size < MIN_FILE_SIZE or size > MAX_FILE_SIZE:
# # # #                 return None

# # # #             img = Image.open(BytesIO(r.content))
# # # #             w, h = img.size

# # # #             if w < MIN_WIDTH or h < MIN_HEIGHT:
# # # #                 return None

# # # #             score = (
# # # #                 (100 - abs(w - PREFERRED_WIDTH) / 10) +
# # # #                 (100 - abs(h - PREFERRED_HEIGHT) / 10)
# # # #             ) / 2

# # # #             return {
# # # #                 "url": url,
# # # #                 "width": w,
# # # #                 "height": h,
# # # #                 "size_kb": round(size / 1024, 1),
# # # #                 "score": round(score, 1)
# # # #             }

# # # #         except:
# # # #             return None

# # # # # ============================================================
# # # # # PROCESS BUTTON
# # # # # ============================================================

# # # # if st.button("🚀 Start Image Search", disabled=len(food_items) == 0):

# # # #     scraper = SmartImageScraper(headless=headless_mode)
# # # #     results = []

# # # #     progress = st.progress(0)
# # # #     status = st.empty()

# # # #     for i, food in enumerate(food_items):
# # # #         status.write(f"Searching image for **{food}**...")
# # # #         result = scraper.search(food, taste_modifier)

# # # #         if result:
# # # #             results.append({
# # # #                 "Item_Name": food,
# # # #                 "Image_URL": result["url"],
# # # #                 "Width": result["width"],
# # # #                 "Height": result["height"],
# # # #                 "Size_KB": result["size_kb"],
# # # #                 "Score": result["score"]
# # # #             })
# # # #         else:
# # # #             results.append({
# # # #                 "Item_Name": food,
# # # #                 "Image_URL": "Not Found",
# # # #                 "Width": 0,
# # # #                 "Height": 0,
# # # #                 "Size_KB": 0,
# # # #                 "Score": 0
# # # #             })

# # # #         progress.progress((i + 1) / len(food_items))

# # # #     scraper.close()

# # # #     # ========================================================
# # # #     # OUTPUT SECTION
# # # #     # ========================================================

# # # #     st.subheader("📤 Results")

# # # #     result_df = pd.DataFrame(results)
# # # #     st.dataframe(result_df, use_container_width=True)

# # # #     st.subheader("🖼️ Image Preview")

# # # #     cols = st.columns(4)
# # # #     idx = 0
# # # #     for _, row in result_df.iterrows():
# # # #         if row["Image_URL"].startswith("http"):
# # # #             with cols[idx % 4]:
# # # #                 st.image(row["Image_URL"], caption=row["Item_Name"], use_container_width=True)
# # # #             idx += 1

# # # #     csv = result_df.to_csv(index=False).encode("utf-8")
# # # #     st.download_button(
# # # #         "⬇️ Download Result CSV",
# # # #         csv,
# # # #         "food_images_with_preview.csv",
# # # #         "text/csv"
# # # #     )

# # # #     st.success("✅ Image scraping completed successfully")
# # # import streamlit as st
# # # import pandas as pd
# # # import time
# # # import requests
# # # from io import BytesIO
# # # from PIL import Image
# # # from urllib.parse import urlparse, parse_qs, unquote

# # # from selenium import webdriver
# # # from selenium.webdriver.chrome.service import Service
# # # from selenium.webdriver.chrome.options import Options
# # # from selenium.webdriver.common.by import By
# # # from webdriver_manager.chrome import ChromeDriverManager

# # # # =========================================================
# # # # STREAMLIT CONFIG
# # # # =========================================================

# # # st.set_page_config(
# # #     page_title="Food Image URL Scraper",
# # #     layout="wide"
# # # )

# # # st.title("🍽️ Smart Food Image Scraper")
# # # st.caption("Search order: Bing → DuckDuckGo → Wikimedia Commons")

# # # # =========================================================
# # # # SIDEBAR SETTINGS
# # # # =========================================================

# # # st.sidebar.header("🔍 Search Settings")

# # # taste = st.sidebar.selectbox(
# # #     "Food Type / Taste",
# # #     ["None", "Hot", "Spicy", "Sweet", "Cool", "Dessert", "Indian"]
# # # )

# # # headless = st.sidebar.checkbox("Run browser headless", value=True)

# # # st.sidebar.header("📐 Image Quality Filters")

# # # MIN_WIDTH = st.sidebar.slider("Min Width (px)", 100, 800, 300)
# # # MIN_HEIGHT = st.sidebar.slider("Min Height (px)", 100, 800, 300)
# # # MIN_SIZE = st.sidebar.slider("Min File Size (KB)", 5, 100, 15) * 1024
# # # MAX_SIZE = st.sidebar.slider("Max File Size (KB)", 50, 1000, 500) * 1024

# # # # =========================================================
# # # # INPUT SECTION
# # # # =========================================================

# # # st.subheader("📥 Input")

# # # mode = st.radio("Input Method", ["Upload CSV", "Manual Entry"])

# # # food_items = []

# # # if mode == "Upload CSV":
# # #     file = st.file_uploader("Upload CSV (column: Item_Name)", type="csv")
# # #     if file:
# # #         df = pd.read_csv(file)
# # #         if "Item_Name" not in df.columns:
# # #             st.error("CSV must contain 'Item_Name' column")
# # #             st.stop()
# # #         food_items = df["Item_Name"].dropna().astype(str).tolist()

# # # else:
# # #     text = st.text_area(
# # #         "Enter food names (one per line)",
# # #         height=150,
# # #         placeholder="Ice Cream\nMasala Dosa\nChicken Biryani"
# # #     )
# # #     if text.strip():
# # #         food_items = [x.strip() for x in text.split("\n") if x.strip()]

# # # st.info(f"Total items: {len(food_items)}")

# # # # =========================================================
# # # # IMAGE URL EXTRACTION (USING YOUR TAGS)
# # # # =========================================================

# # # def extract_image_url(src):
# # #     if not src:
# # #         return None

# # #     # Handle // URLs
# # #     if src.startswith("//"):
# # #         src = "https:" + src

# # #     # DuckDuckGo proxy decoding
# # #     if "duckduckgo.com/iu/" in src:
# # #         parsed = urlparse(src)
# # #         real = parse_qs(parsed.query).get("u")
# # #         if real:
# # #             return unquote(real[0])
# # #         return None

# # #     # Direct image (Bing, Wikimedia, websites)
# # #     if src.startswith("http"):
# # #         return src

# # #     return None

# # # # =========================================================
# # # # IMAGE QUALITY CHECK
# # # # =========================================================

# # # def check_quality(url):
# # #     try:
# # #         r = requests.get(url, timeout=5)
# # #         if r.status_code != 200:
# # #             return None

# # #         size = len(r.content)
# # #         if size < MIN_SIZE or size > MAX_SIZE:
# # #             return None

# # #         img = Image.open(BytesIO(r.content))
# # #         w, h = img.size

# # #         if w < MIN_WIDTH or h < MIN_HEIGHT:
# # #             return None

# # #         return {
# # #             "url": url,
# # #             "width": w,
# # #             "height": h,
# # #             "size_kb": round(size / 1024, 1)
# # #         }
# # #     except:
# # #         return None

# # # # =========================================================
# # # # SEARCH ENGINES
# # # # =========================================================

# # # def search_bing(driver, query):
# # #     driver.get(f"https://www.bing.com/images/search?q={query.replace(' ', '+')}")
# # #     time.sleep(2)

# # #     for img in driver.find_elements(By.TAG_NAME, "img"):
# # #         src = img.get_attribute("src")
# # #         url = extract_image_url(src)
# # #         if url:
# # #             result = check_quality(url)
# # #             if result:
# # #                 result["engine"] = "Bing"
# # #                 return result
# # #     return None


# # # def search_duckduckgo(driver, query):
# # #     driver.get(f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=images&iax=images")
# # #     time.sleep(3)

# # #     for img in driver.find_elements(By.TAG_NAME, "img"):
# # #         src = img.get_attribute("src")
# # #         url = extract_image_url(src)
# # #         if url:
# # #             result = check_quality(url)
# # #             if result:
# # #                 result["engine"] = "DuckDuckGo"
# # #                 return result
# # #     return None


# # # def search_wikimedia(query):
# # #     api = (
# # #         "https://commons.wikimedia.org/w/api.php"
# # #         "?action=query&format=json"
# # #         "&prop=imageinfo&iiprop=url"
# # #         "&generator=search"
# # #         "&gsrlimit=5"
# # #         "&gsrsearch=" + query.replace(" ", "%20")
# # #     )

# # #     try:
# # #         data = requests.get(api, timeout=5).json()
# # #         pages = data.get("query", {}).get("pages", {})
# # #         for page in pages.values():
# # #             info = page.get("imageinfo")
# # #             if info:
# # #                 url = info[0]["url"]
# # #                 result = check_quality(url)
# # #                 if result:
# # #                     result["engine"] = "Wikimedia"
# # #                     return result
# # #     except:
# # #         pass

# # #     return None

# # # # =========================================================
# # # # FALLBACK SEARCH PIPELINE
# # # # =========================================================

# # # def find_image(driver, food):
# # #     parts = [food]
# # #     if taste != "None":
# # #         parts.append(taste.lower())

# # #     query = " ".join(parts)

# # #     result = search_bing(driver, query)
# # #     if result:
# # #         return result

# # #     result = search_duckduckgo(driver, query)
# # #     if result:
# # #         return result

# # #     return search_wikimedia(query)

# # # # =========================================================
# # # # RUN BUTTON
# # # # =========================================================

# # # if st.button("🚀 Start Search", disabled=len(food_items) == 0):

# # #     options = Options()
# # #     if headless:
# # #         options.add_argument("--headless=new")

# # #     driver = webdriver.Chrome(
# # #         service=Service(ChromeDriverManager().install()),
# # #         options=options
# # #     )

# # #     results = []
# # #     progress = st.progress(0)

# # #     for i, food in enumerate(food_items):
# # #         res = find_image(driver, food)
# # #         if res:
# # #             results.append({
# # #                 "Item_Name": food,
# # #                 "Image_URL": res["url"],
# # #                 "Width": res["width"],
# # #                 "Height": res["height"],
# # #                 "Size_KB": res["size_kb"],
# # #                 "Engine": res["engine"]
# # #             })
# # #         else:
# # #             results.append({
# # #                 "Item_Name": food,
# # #                 "Image_URL": "Not Found",
# # #                 "Width": 0,
# # #                 "Height": 0,
# # #                 "Size_KB": 0,
# # #                 "Engine": "None"
# # #             })

# # #         progress.progress((i + 1) / len(food_items))

# # #     driver.quit()

# # #     # =====================================================
# # #     # OUTPUT
# # #     # =====================================================

# # #     df_out = pd.DataFrame(results)

# # #     st.subheader("📊 Results Table")
# # #     st.dataframe(df_out, use_container_width=True)

# # #     st.subheader("🖼️ Image Preview")

# # #     cols = st.columns(4)
# # #     idx = 0
# # #     for _, row in df_out.iterrows():
# # #         if row["Image_URL"].startswith("http"):
# # #             with cols[idx % 4]:
# # #                 st.image(row["Image_URL"], caption=f"{row['Item_Name']} ({row['Engine']})")
# # #             idx += 1

# # #     csv = df_out.to_csv(index=False).encode("utf-8")
# # #     st.download_button(
# # #         "⬇️ Download CSV",
# # #         csv,
# # #         "food_images.csv",
# # #         "text/csv"
# # #     )

# # #     st.success("✅ Completed successfully")
# # import streamlit as st
# # import pandas as pd
# # import time
# # import requests
# # from io import BytesIO
# # from PIL import Image
# # from urllib.parse import urlparse, parse_qs, unquote

# # from selenium import webdriver
# # from selenium.webdriver.chrome.service import Service
# # from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.common.by import By
# # from webdriver_manager.chrome import ChromeDriverManager

# # # =========================================================
# # # STREAMLIT CONFIG
# # # =========================================================

# # st.set_page_config(page_title="Universal Image Scraper", layout="wide")

# # st.title("🖼️ Universal Food Image Scraper")
# # st.caption("Bing → DuckDuckGo → Wikimedia | No source restrictions | Download images")

# # # =========================================================
# # # SIDEBAR SETTINGS
# # # =========================================================

# # st.sidebar.header("🔍 Search Settings")

# # taste = st.sidebar.selectbox(
# #     "Food Type / Taste",
# #     ["None", "Hot", "Spicy", "Sweet", "Cool", "Dessert", "Indian"]
# # )

# # headless = st.sidebar.checkbox("Run browser headless", value=True)

# # st.sidebar.header("📐 Image Quality Filters (Optional)")

# # MIN_WIDTH = st.sidebar.slider("Min Width (px)", 0, 800, 0)
# # MIN_HEIGHT = st.sidebar.slider("Min Height (px)", 0, 800, 0)
# # MIN_SIZE = st.sidebar.slider("Min File Size (KB)", 0, 200, 0) * 1024
# # MAX_SIZE = st.sidebar.slider("Max File Size (KB)", 50, 2000, 2000) * 1024

# # # =========================================================
# # # INPUT SECTION
# # # =========================================================

# # st.subheader("📥 Input Food Items")

# # mode = st.radio("Input Method", ["Upload CSV", "Manual Entry"])

# # food_items = []

# # if mode == "Upload CSV":
# #     file = st.file_uploader("Upload CSV (column: Item_Name)", type="csv")
# #     if file:
# #         df = pd.read_csv(file)
# #         if "Item_Name" not in df.columns:
# #             st.error("CSV must contain 'Item_Name' column")
# #             st.stop()
# #         food_items = df["Item_Name"].dropna().astype(str).tolist()

# # else:
# #     text = st.text_area(
# #         "Enter food names (one per line)",
# #         height=150,
# #         placeholder="Ice Cream\nMasala Dosa\nChicken Biryani"
# #     )
# #     if text.strip():
# #         food_items = [x.strip() for x in text.split("\n") if x.strip()]

# # st.info(f"Total items loaded: {len(food_items)}")

# # # =========================================================
# # # UNIVERSAL IMAGE URL EXTRACTION (NO RESTRICTIONS)
# # # =========================================================

# # def extract_image_url(img):
# #     candidates = [
# #         img.get_attribute("data-original"),
# #         img.get_attribute("data-src"),
# #         img.get_attribute("src"),
# #     ]

# #     for src in candidates:
# #         if not src:
# #             continue

# #         if src.startswith("//"):
# #             src = "https:" + src

# #         if "duckduckgo.com/iu/" in src:
# #             parsed = urlparse(src)
# #             real = parse_qs(parsed.query).get("u")
# #             if real:
# #                 return unquote(real[0])
# #             continue

# #         if src.startswith("http"):
# #             return src

# #     return None

# # # =========================================================
# # # IMAGE QUALITY CHECK (OPTIONAL)
# # # =========================================================

# # def check_quality(url):
# #     try:
# #         r = requests.get(url, timeout=6)
# #         if r.status_code != 200:
# #             return None

# #         size = len(r.content)
# #         if size < MIN_SIZE or size > MAX_SIZE:
# #             return None

# #         img = Image.open(BytesIO(r.content))
# #         w, h = img.size

# #         if w < MIN_WIDTH or h < MIN_HEIGHT:
# #             return None

# #         return {
# #             "url": url,
# #             "bytes": r.content,
# #             "width": w,
# #             "height": h,
# #             "size_kb": round(size / 1024, 1),
# #         }
# #     except:
# #         return None

# # # =========================================================
# # # SEARCH ENGINES
# # # =========================================================

# # def search_bing(driver, query):
# #     driver.get(f"https://www.bing.com/images/search?q={query.replace(' ', '+')}")
# #     time.sleep(2)

# #     for img in driver.find_elements(By.TAG_NAME, "img"):
# #         url = extract_image_url(img)
# #         if url:
# #             result = check_quality(url)
# #             if result:
# #                 result["engine"] = "Bing"
# #                 return result
# #     return None


# # def search_duckduckgo(driver, query):
# #     driver.get(f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=images&iax=images")
# #     time.sleep(3)

# #     for img in driver.find_elements(By.TAG_NAME, "img"):
# #         url = extract_image_url(img)
# #         if url:
# #             result = check_quality(url)
# #             if result:
# #                 result["engine"] = "DuckDuckGo"
# #                 return result
# #     return None


# # def search_wikimedia(query):
# #     api = (
# #         "https://commons.wikimedia.org/w/api.php"
# #         "?action=query&format=json"
# #         "&prop=imageinfo&iiprop=url"
# #         "&generator=search"
# #         "&gsrlimit=10"
# #         "&gsrsearch=" + query.replace(" ", "%20")
# #     )

# #     try:
# #         data = requests.get(api, timeout=5).json()
# #         pages = data.get("query", {}).get("pages", {})
# #         for page in pages.values():
# #             info = page.get("imageinfo")
# #             if info:
# #                 url = info[0]["url"]
# #                 result = check_quality(url)
# #                 if result:
# #                     result["engine"] = "Wikimedia"
# #                     return result
# #     except:
# #         pass

# #     return None

# # # =========================================================
# # # FALLBACK PIPELINE
# # # =========================================================

# # def find_image(driver, food):
# #     parts = [food]
# #     if taste != "None":
# #         parts.append(taste.lower())

# #     query = " ".join(parts)

# #     result = search_bing(driver, query)
# #     if result:
# #         return result

# #     result = search_duckduckgo(driver, query)
# #     if result:
# #         return result

# #     return search_wikimedia(query)

# # # =========================================================
# # # RUN SCRAPER
# # # =========================================================

# # if st.button("🚀 Start Image Search", disabled=len(food_items) == 0):

# #     options = Options()
# #     if headless:
# #         options.add_argument("--headless=new")

# #     driver = webdriver.Chrome(
# #         service=Service(ChromeDriverManager().install()),
# #         options=options
# #     )

# #     results = []
# #     progress = st.progress(0)

# #     for i, food in enumerate(food_items):
# #         res = find_image(driver, food)
# #         if res:
# #             results.append({
# #                 "Item_Name": food,
# #                 "Image_URL": res["url"],
# #                 "Width": res["width"],
# #                 "Height": res["height"],
# #                 "Size_KB": res["size_kb"],
# #                 "Engine": res["engine"],
# #                 "Bytes": res["bytes"],
# #             })
# #         else:
# #             results.append({
# #                 "Item_Name": food,
# #                 "Image_URL": "Not Found",
# #                 "Width": 0,
# #                 "Height": 0,
# #                 "Size_KB": 0,
# #                 "Engine": "None",
# #                 "Bytes": None,
# #             })

# #         progress.progress((i + 1) / len(food_items))

# #     driver.quit()

# #     # =====================================================
# #     # OUTPUT
# #     # =====================================================

# #     df_out = pd.DataFrame(results)

# #     st.subheader("📊 Results Table")
# #     st.dataframe(df_out.drop(columns=["Bytes"]), use_container_width=True)

# #     st.subheader("🖼️ Image Preview & Download")

# #     cols = st.columns(4)
# #     idx = 0

# #     for _, row in df_out.iterrows():
# #         if isinstance(row["Bytes"], (bytes, bytearray)):
# #             with cols[idx % 4]:
# #                 st.image(row["Bytes"], caption=f"{row['Item_Name']} ({row['Engine']})")
# #                 st.download_button(
# #                     label="⬇️ Download Image",
# #                     data=row["Bytes"],
# #                     file_name=f"{row['Item_Name'].replace(' ', '_')}.jpg",
# #                     mime="image/jpeg"
# #                 )
# #             idx += 1

# #     csv = df_out.drop(columns=["Bytes"]).to_csv(index=False).encode("utf-8")
# #     st.download_button(
# #         "⬇️ Download CSV",
# #         csv,
# #         "food_images.csv",
# #         "text/csv"
# #     )

# #     st.success("✅ Image scraping completed successfully")
# import streamlit as st
# import pandas as pd
# import time
# import requests
# from io import BytesIO
# from PIL import Image
# from urllib.parse import urlparse, parse_qs, unquote
# import hashlib

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager

# # =========================================================
# # STREAMLIT CONFIG
# # =========================================================

# st.set_page_config(page_title="High Quality Image Scraper", layout="wide")

# st.title("🖼️ High-Quality Image Scraper")
# st.caption("Always prioritizes best quality | Multiple images per item")

# # =========================================================
# # SIDEBAR CONTROLS
# # =========================================================

# st.sidebar.header("🔍 Search Controls")

# taste = st.sidebar.selectbox(
#     "Food Type / Taste",
#     ["None", "Hot", "Spicy", "Sweet", "Cool", "Dessert", "Indian"]
# )

# images_per_item = st.sidebar.slider(
#     "Images per food item",
#     min_value=1,
#     max_value=10,
#     value=3
# )

# headless = st.sidebar.checkbox("Run browser headless", value=True)

# st.sidebar.header("📐 Minimum Quality (Hard Limits)")

# MIN_WIDTH = st.sidebar.slider("Min Width (px)", 200, 800, 300)
# MIN_HEIGHT = st.sidebar.slider("Min Height (px)", 200, 800, 300)
# MIN_SIZE = st.sidebar.slider("Min File Size (KB)", 10, 200, 30) * 1024

# # =========================================================
# # INPUT
# # =========================================================

# st.subheader("📥 Input Food Names")

# mode = st.radio("Input Method", ["Upload CSV", "Manual Entry"])

# food_items = []

# if mode == "Upload CSV":
#     file = st.file_uploader("Upload CSV (Item_Name)", type="csv")
#     if file:
#         df = pd.read_csv(file)
#         food_items = df["Item_Name"].dropna().astype(str).tolist()
# else:
#     text = st.text_area(
#         "Enter food names (one per line)",
#         height=150
#     )
#     food_items = [x.strip() for x in text.split("\n") if x.strip()]

# st.info(f"Food items loaded: {len(food_items)}")

# # =========================================================
# # IMAGE EXTRACTION (UNIVERSAL)
# # =========================================================

# def extract_image_url(img):
#     for attr in ["data-original", "data-src", "src"]:
#         src = img.get_attribute(attr)
#         if not src:
#             continue

#         if src.startswith("//"):
#             src = "https:" + src

#         if "duckduckgo.com/iu/" in src:
#             parsed = urlparse(src)
#             real = parse_qs(parsed.query).get("u")
#             if real:
#                 return unquote(real[0])
#             continue

#         if src.startswith("http"):
#             return src
#     return None

# # =========================================================
# # QUALITY CHECK + SCORING
# # =========================================================

# def fetch_and_score(url):
#     try:
#         r = requests.get(url, timeout=6)
#         if r.status_code != 200:
#             return None

#         img = Image.open(BytesIO(r.content))
#         w, h = img.size
#         size = len(r.content)

#         if w < MIN_WIDTH or h < MIN_HEIGHT or size < MIN_SIZE:
#             return None

#         score = (w * h) + (size / 10)

#         return {
#             "url": url,
#             "bytes": r.content,
#             "width": w,
#             "height": h,
#             "size_kb": round(size / 1024, 1),
#             "score": int(score)
#         }
#     except:
#         return None

# # =========================================================
# # SEARCH ENGINES
# # =========================================================

# def collect_images(driver, query):
#     collected = []

#     engines = [
#         f"https://www.bing.com/images/search?q={query}",
#         f"https://duckduckgo.com/?q={query}&ia=images&iax=images",
#     ]

#     for url in engines:
#         driver.get(url)
#         time.sleep(3)

#         for img in driver.find_elements(By.TAG_NAME, "img"):
#             img_url = extract_image_url(img)
#             if img_url:
#                 data = fetch_and_score(img_url)
#                 if data:
#                     collected.append(data)

#     return collected

# # =========================================================
# # WIKIMEDIA (FINAL BOOST)
# # =========================================================

# def collect_wikimedia(query):
#     api = (
#         "https://commons.wikimedia.org/w/api.php"
#         "?action=query&format=json"
#         "&generator=search"
#         "&gsrlimit=20"
#         "&prop=imageinfo&iiprop=url"
#         "&gsrsearch=" + query.replace(" ", "%20")
#     )

#     images = []

#     try:
#         pages = requests.get(api, timeout=6).json().get("query", {}).get("pages", {})
#         for page in pages.values():
#             url = page["imageinfo"][0]["url"]
#             data = fetch_and_score(url)
#             if data:
#                 images.append(data)
#     except:
#         pass

#     return images

# # =========================================================
# # DEDUPLICATION
# # =========================================================

# def dedupe(images):
#     seen = set()
#     unique = []

#     for img in images:
#         h = hashlib.md5(img["bytes"]).hexdigest()
#         if h not in seen:
#             seen.add(h)
#             unique.append(img)

#     return unique

# # =========================================================
# # RUN
# # =========================================================

# if st.button("🚀 Start High-Quality Search", disabled=len(food_items) == 0):

#     options = Options()
#     if headless:
#         options.add_argument("--headless=new")

#     driver = webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=options
#     )

#     final_results = []
#     progress = st.progress(0)

#     for i, food in enumerate(food_items):
#         query = food 
#         if taste != "None":
#             query += " " + taste.lower()

#         images = collect_images(driver, query)
#         images += collect_wikimedia(query)

#         images = dedupe(images)
#         images = sorted(images, key=lambda x: x["score"], reverse=True)
#         images = images[:images_per_item]

#         for idx, img in enumerate(images, 1):
#             final_results.append({
#                 "Item_Name": food,
#                 "Image_No": idx,
#                 "Image_URL": img["url"],
#                 "Width": img["width"],
#                 "Height": img["height"],
#                 "Size_KB": img["size_kb"],
#                 "Score": img["score"],
#             })

#         progress.progress((i + 1) / len(food_items))

#     driver.quit()

#     df = pd.DataFrame(final_results)

#     # =====================================================
#     # OUTPUT
#     # =====================================================

#     st.subheader("📊 Results")
#     st.dataframe(df, use_container_width=True)

#     st.subheader("🖼️ Image Preview & Download")

#     for food in df["Item_Name"].unique():
#         st.markdown(f"### {food}")
#         cols = st.columns(images_per_item)
#         subset = df[df["Item_Name"] == food]

#         for i, row in enumerate(subset.itertuples()):
#             img_bytes = requests.get(row.Image_URL).content
#             with cols[i]:
#                 st.image(img_bytes)
#                 st.download_button(
#                     "⬇️ Download",
#                     img_bytes,
#                     file_name=f"{food.replace(' ', '_')}_{row.Image_No}.jpg",
#                     mime="image/jpeg"
#                 )

#     csv = df.to_csv(index=False).encode("utf-8")
#     st.download_button("⬇️ Download CSV", csv, "high_quality_images.csv")

#     st.success("✅ Completed with best quality images")
import streamlit as st
import pandas as pd
import time
import requests
from io import BytesIO
from PIL import Image
from urllib.parse import urlparse, parse_qs, unquote
import hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# =========================================================
# STREAMLIT CONFIG
# =========================================================

st.set_page_config(page_title="High Quality Image Scraper", layout="wide")

st.title("🖼️ High-Quality Image Scraper")
st.caption("Render-safe | Best quality | Multiple images per item")

# =========================================================
# SESSION STATE INIT
# =========================================================

if "results" not in st.session_state:
    st.session_state.results = None

# =========================================================
# DRIVER SETUP (RENDER / CLOUD SAFE)
# =========================================================

# def setup_driver():
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless")          # REQUIRED for Render
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
#     )

#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)
#     return driver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--window-size=1920,1080")

    # Explicit Chromium binary
    options.binary_location = "/usr/bin/chromium"

    # Explicit ChromeDriver (disable Selenium auto-discovery)
    service = ChromeService(executable_path="/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=options)
    return driver

# =========================================================
# SIDEBAR CONTROLS
# =========================================================

st.sidebar.header("🔍 Search Controls")

taste = st.sidebar.selectbox(
    "Food Type / Taste",
    ["None", "Hot", "Spicy", "Sweet", "Cool", "Dessert", "Indian"]
)

images_per_item = st.sidebar.slider("Images per item", 1, 10, 3)

MIN_WIDTH = st.sidebar.slider("Min Width (px)", 200, 800, 300)
MIN_HEIGHT = st.sidebar.slider("Min Height (px)", 200, 800, 300)
MIN_SIZE = st.sidebar.slider("Min File Size (KB)", 10, 200, 30) * 1024

# =========================================================
# INPUT
# =========================================================

mode = st.radio("Input Method", ["Upload CSV", "Manual Entry"])
food_items = []

if mode == "Upload CSV":
    file = st.file_uploader("Upload CSV (Item_Name)", type="csv")
    if file:
        df = pd.read_csv(file)
        if "Item_Name" not in df.columns:
            st.error("CSV must contain 'Item_Name'")
            st.stop()
        food_items = df["Item_Name"].dropna().astype(str).tolist()
else:
    text = st.text_area("Food names (one per line)")
    food_items = [x.strip() for x in text.split("\n") if x.strip()]

st.info(f"Food items loaded: {len(food_items)}")

# =========================================================
# SAFE ATTRIBUTE ACCESS
# =========================================================

def safe_get_attr(img, attr):
    try:
        return img.get_attribute(attr)
    except StaleElementReferenceException:
        return None

# =========================================================
# IMAGE URL EXTRACTION (UNIVERSAL)
# =========================================================

def extract_image_url(img):
    for attr in ["data-original", "data-src", "src"]:
        src = safe_get_attr(img, attr)
        if not src:
            continue

        if src.startswith("//"):
            src = "https:" + src

        if "duckduckgo.com/iu/" in src:
            parsed = urlparse(src)
            real = parse_qs(parsed.query).get("u")
            if real:
                return unquote(real[0])

        if src.startswith("http"):
            return src
    return None

# =========================================================
# FETCH + SCORE (QUALITY FIRST)
# =========================================================

def fetch_and_score(url):
    try:
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            return None

        img = Image.open(BytesIO(r.content))
        w, h = img.size
        size = len(r.content)

        if w < MIN_WIDTH or h < MIN_HEIGHT or size < MIN_SIZE:
            return None

        score = (w * h) + (size / 10)

        return {
            "url": url,
            "bytes": r.content,
            "width": w,
            "height": h,
            "size_kb": round(size / 1024, 1),
            "score": int(score),
        }
    except:
        return None

# =========================================================
# SCRAPING LOGIC
# =========================================================

def scrape_images(food):
    driver = setup_driver()

    query = food
    if taste != "None":
        query += " " + taste.lower()

    collected = []

    search_pages = [
        f"https://www.bing.com/images/search?q={query.replace(' ', '+')}",
        f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=images&iax=images",
    ]

    for page in search_pages:
        driver.get(page)
        time.sleep(3)

        imgs = list(driver.find_elements(By.TAG_NAME, "img"))  # freeze DOM

        for img in imgs:
            try:
                img_url = extract_image_url(img)
                if img_url:
                    data = fetch_and_score(img_url)
                    if data:
                        collected.append(data)
            except StaleElementReferenceException:
                continue

    driver.quit()

    # Deduplicate
    unique = {}
    for img in collected:
        h = hashlib.md5(img["bytes"]).hexdigest()
        unique[h] = img

    # Best quality first
    images = sorted(unique.values(), key=lambda x: x["score"], reverse=True)
    return images[:images_per_item]

# =========================================================
# RUN SEARCH
# =========================================================

if st.button("🚀 Start Search") and food_items:
    all_results = []

    for food in food_items:
        imgs = scrape_images(food)
        for i, img in enumerate(imgs, 1):
            all_results.append({
                "Item_Name": food,
                "Image_No": i,
                **img
            })

    st.session_state.results = all_results

# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)

    st.subheader("📊 Results")
    st.dataframe(df.drop(columns=["bytes"]), use_container_width=True)

    st.subheader("🖼️ Images & Downloads")

    for food in df["Item_Name"].unique():
        st.markdown(f"### {food}")
        subset = df[df["Item_Name"] == food]
        cols = st.columns(len(subset))

        for col, row in zip(cols, subset.itertuples()):
            with col:
                st.image(row.bytes)
                st.download_button(
                    "⬇️ Download",
                    row.bytes,
                    file_name=f"{food.replace(' ', '_')}_{row.Image_No}.jpg",
                    mime="image/jpeg",
                    key=f"{food}_{row.Image_No}"
                )

    csv = df.drop(columns=["bytes"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "images.csv")
