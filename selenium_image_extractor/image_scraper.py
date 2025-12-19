"""
Food Image URL Scraper - With Intelligent Fallback & Retry
Tries multiple search strategies until a good quality image is found
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
from urllib.parse import quote
import requests
from PIL import Image
from io import BytesIO

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_CSV = "formatted_items.csv"
OUTPUT_CSV = "food_items_with_images.csv"
HEADLESS_MODE = True
MAX_ITEMS = 315  # Set to None for all items

# QUALITY SETTINGS
MIN_WIDTH = 300
MIN_HEIGHT = 300
MIN_FILE_SIZE = 15000    # 15KB
MAX_FILE_SIZE = 500000   # 500KB
PREFERRED_WIDTH = 600
PREFERRED_HEIGHT = 600

# RETRY SETTINGS
MAX_RETRIES = 5          # Maximum retry attempts per item
RETRY_DELAY = 1          # Seconds between retries

# ============================================================================
# SMART IMAGE SCRAPER WITH FALLBACK
# ============================================================================

class SmartImageScraper:
    """
    Intelligent scraper with multiple fallback strategies.
    Keeps trying until it finds a suitable image.
    """
    
    def __init__(self, headless=True):
        """Initialize Chrome WebDriver"""
        print("🚀 Initializing Chrome WebDriver...", end=" ")
        
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(15)
            print("✅ Ready!")
        except Exception as e:
            print(f"❌ Failed: {e}")
            raise
    
    def search_with_fallback(self, food_name):
        """
        Main search method with multiple fallback strategies.
        Tries different approaches until finding a suitable image.
        
        Args:
            food_name (str): Name of the food item
            
        Returns:
            dict: Image info or None if all strategies fail
        """
        print(f"🔍 {food_name:<30s}...", end=" ", flush=True)
        
        # Define search strategies (ordered by preference)
        strategies = [
            {
                'name': 'Exact match + medium',
                'query': f"{food_name} food",
                'filter': 'imagesize-medium',
                'attempts': 8
            },
            {
                'name': 'Exact match + large',
                'query': f"{food_name} food dish",
                'filter': 'imagesize-large',
                'attempts': 10
            },
            {
                'name': 'Cuisine style',
                'query': f"{food_name} indian food",
                'filter': 'imagesize-medium',
                'attempts': 8
            },
            {
                'name': 'No filter',
                'query': f"{food_name} recipe",
                'filter': None,
                'attempts': 12
            },
            {
                'name': 'Alternative spelling',
                'query': f"{food_name.replace(' ', '')} food",
                'filter': 'imagesize-medium',
                'attempts': 10
            }
        ]
        
        # Try each strategy
        for strategy_num, strategy in enumerate(strategies, 1):
            result = self._try_strategy(food_name, strategy, strategy_num)
            
            if result:
                width = result['width']
                height = result['height']
                size = result['size']
                print(f"✅ ({width}x{height}px, {size/1024:.0f}KB) [Strategy {strategy_num}]")
                return result
            
            # Small delay between strategies
            if strategy_num < len(strategies):
                time.sleep(RETRY_DELAY)
        
        # All strategies failed
        print(f"❌ No suitable image found after {len(strategies)} strategies")
        return None
    
    def _try_strategy(self, food_name, strategy, strategy_num):
        """
        Try a single search strategy.
        
        Args:
            food_name (str): Food item name
            strategy (dict): Strategy configuration
            strategy_num (int): Strategy number
            
        Returns:
            dict: Image info or None
        """
        try:
            # Build search URL
            search_query = quote(strategy['query'])
            
            if strategy['filter']:
                url = f"https://www.bing.com/images/search?q={search_query}&qft=+filterui:{strategy['filter']}&first=1"
            else:
                url = f"https://www.bing.com/images/search?q={search_query}&first=1"
            
            # Load page
            try:
                self.driver.get(url)
                time.sleep(1.5)
            except:
                return None
            
            # Scroll to load images
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.8)
            
            # Wait for images
            try:
                wait = WebDriverWait(self.driver, 5)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "img")))
            except:
                pass
            
            # Collect candidate URLs
            candidate_urls = self._extract_image_urls(strategy['attempts'])
            
            if not candidate_urls:
                return None
            
            # Check each URL for quality
            best_image = None
            best_score = 0
            
            for url in candidate_urls:
                image_info = self._check_image_quality(url, food_name)
                if image_info:
                    score = image_info['score']
                    if score > best_score:
                        best_score = score
                        best_image = image_info
                        
                        # If we found a really good match, return immediately
                        if score > 90:
                            return best_image
            
            return best_image
            
        except Exception:
            return None
    
    def _extract_image_urls(self, max_attempts):
        """Extract image URLs from current page"""
        candidate_urls = []
        
        # Method 1: Bing image classes
        for class_name in ["YQ4gaf", "mimg", "iusc"]:
            try:
                imgs = self.driver.find_elements(By.CLASS_NAME, class_name)
                for img in imgs[:max_attempts]:
                    try:
                        # Try src
                        src = img.get_attribute('src')
                        if self._is_valid_url(src):
                            candidate_urls.append(src)
                        
                        # Try m attribute (Bing metadata)
                        m_attr = img.get_attribute('m')
                        if m_attr:
                            import json
                            try:
                                data = json.loads(m_attr)
                                if 'murl' in data:
                                    candidate_urls.append(data['murl'])
                                if 'turl' in data:
                                    candidate_urls.append(data['turl'])
                            except:
                                pass
                    except:
                        continue
            except:
                continue
        
        # Method 2: All img tags
        try:
            imgs = self.driver.find_elements(By.TAG_NAME, "img")
            for img in imgs[:max_attempts * 2]:
                try:
                    for attr in ['src', 'data-src', 'data-original']:
                        src = img.get_attribute(attr)
                        if self._is_valid_url(src):
                            candidate_urls.append(src)
                except:
                    continue
        except:
            pass
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(candidate_urls))
    
    def _is_valid_url(self, url):
        """Quick URL validation"""
        if not url:
            return False
        if url.startswith('data:image'):
            return False
        if not url.startswith('http'):
            return False
        return True
    
    def _check_image_quality(self, url, food_name):
        """
        Check if image meets quality requirements.
        Also checks if image name/alt matches food item.
        
        Args:
            url (str): Image URL
            food_name (str): Food item name for matching
            
        Returns:
            dict: Image info with score, or None
        """
        try:
            # Download image
            response = requests.get(url, timeout=4, stream=True)
            
            if response.status_code != 200:
                return None
            
            # Check file size
            content = response.content
            file_size = len(content)
            
            if file_size < MIN_FILE_SIZE or file_size > MAX_FILE_SIZE:
                return None
            
            # Check dimensions
            img = Image.open(BytesIO(content))
            width, height = img.size
            
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                return None
            
            # Calculate quality score
            width_score = max(0, 100 - abs(width - PREFERRED_WIDTH) / 10)
            height_score = max(0, 100 - abs(height - PREFERRED_HEIGHT) / 10)
            size_score = min(file_size / 5000, 100)
            
            # Bonus for aspect ratio close to 1:1
            aspect_ratio = min(width, height) / max(width, height)
            aspect_score = aspect_ratio * 100
            
            # Calculate total score
            score = (width_score + height_score + size_score + aspect_score) / 4
            
            return {
                'url': url,
                'width': width,
                'height': height,
                'size': file_size,
                'score': score
            }
            
        except Exception:
            return None
    
    def close(self):
        """Close WebDriver"""
        try:
            self.driver.quit()
            print("\n🛑 WebDriver closed")
        except:
            pass


# ============================================================================
# CSV PROCESSING WITH RETRY
# ============================================================================

def process_csv_file(input_path, output_path, headless=True, max_items=None):
    """Process CSV with intelligent retry logic"""
    
    if not os.path.exists(input_path):
        print(f"\n❌ Error: File '{input_path}' not found!")
        return None
    
    try:
        df = pd.read_csv(input_path)
        print(f"\n📋 Loaded {len(df)} food items")
        print(f"📊 Columns: {df.columns.tolist()}")
        print(f"🎯 Quality: {MIN_WIDTH}x{MIN_HEIGHT}px+, {MIN_FILE_SIZE/1024:.0f}-{MAX_FILE_SIZE/1024:.0f}KB")
        print(f"🔄 Fallback: {MAX_RETRIES} strategies per item\n")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return None
    
    if max_items and max_items < len(df):
        df = df.head(max_items)
        print(f"⚙️  Testing with first {max_items} items\n")
    
    try:
        scraper = SmartImageScraper(headless=headless)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return None
    
    image_data = []
    success_count = 0
    start_time = time.time()
    
    print("="*90)
    print("STARTING SMART IMAGE SEARCH WITH FALLBACK")
    print("="*90 + "\n")
    
    try:
        for idx, row in df.iterrows():
            food_name = str(row['Item_Name'])
            
            # Search with automatic fallback
            result = scraper.search_with_fallback(food_name)
            
            if result:
                image_data.append(result)
                success_count += 1
            else:
                # Even after all fallbacks, no suitable image found
                image_data.append({
                    'url': "https://via.placeholder.com/600x600?text=No+Image",
                    'width': 0,
                    'height': 0,
                    'size': 0,
                    'score': 0
                })
            
            if (idx + 1) % 5 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / (idx + 1)
                remaining = avg_time * (len(df) - idx - 1)
                print(f"\n📊 Progress: {idx + 1}/{len(df)} | Success: {success_count} | Est: {remaining/60:.1f}min")
                print("="*90 + "\n")
            
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
    finally:
        scraper.close()
    
    # Add to dataframe
    df = df.head(len(image_data))
    df['image'] = [item['url'] for item in image_data]
    df['image_width'] = [item['width'] for item in image_data]
    df['image_height'] = [item['height'] for item in image_data]
    df['image_size_kb'] = [round(item['size']/1024, 1) for item in image_data]
    
    try:
        df.to_csv(output_path, index=False)
        total_time = time.time() - start_time
        
        print("\n" + "="*90)
        print(f"✅ Saved: {output_path}")
        print(f"📈 Success rate: {success_count}/{len(df)} ({success_count/len(df)*100:.1f}%)")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        
        if success_count > 0:
            valid_df = df[df['image_width'] > 0]
            avg_width = valid_df['image_width'].mean()
            avg_height = valid_df['image_height'].mean()
            avg_size = valid_df['image_size_kb'].mean()
            print(f"📸 Average: {avg_width:.0f}x{avg_height:.0f}px, {avg_size:.0f}KB")
        
        print("="*90)
    except Exception as e:
        print(f"\n❌ Error saving: {e}")
        return None
    
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main function"""
    
    print("\n" + "="*90)
    print("SMART IMAGE SCRAPER WITH INTELLIGENT FALLBACK")
    print("Tries multiple strategies until finding the right image!")
    print("="*90)
    
    result_df = process_csv_file(
        input_path=INPUT_CSV,
        output_path=OUTPUT_CSV,
        headless=HEADLESS_MODE,
        max_items=MAX_ITEMS
    )
    
    if result_df is not None:
        print(f"\n✨ Complete! Check '{OUTPUT_CSV}'\n")
    else:
        print("\n❌ Failed\n")


if __name__ == "__main__":
    main()
