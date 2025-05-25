import streamlit as st
import requests
import re
import time
from urllib.parse import urlparse, parse_qs
import urllib3

# Disable SSL warnings for requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_short_url(url):
    """Check if the URL is a short URL that needs expansion"""
    short_url_patterns = [
        r'shope\.ee',
        r's\.shopee\.',
        r'\.shp\.ee',
        r'shopee\.link'
    ]
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in short_url_patterns)

def expand_short_url(short_url, max_retries=3):
    """Expand short URL to full URL using multiple methods"""
    if not is_short_url(short_url):
        return short_url
    
    methods = [
        expand_with_requests,
        expand_with_unshorten_api,
        expand_with_longurl_api,
        expand_with_allorigins_proxy
    ]
    
    for method in methods:
        try:
            expanded = method(short_url)
            if expanded and expanded != short_url:
                return expanded
        except Exception as e:
            st.write(f"Method {method.__name__} failed: {str(e)}")
            continue
    
    return short_url

def expand_with_requests(url):
    """Try to expand URL using direct requests with redirect following"""
    try:
        response = requests.head(
            url, 
            allow_redirects=True, 
            timeout=10,
            verify=False,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return response.url if response.url != url else None
    except:
        return None

def expand_with_unshorten_api(url):
    """Try to expand URL using unshorten.me API"""
    try:
        api_url = f"https://unshorten.me/json/{url}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('resolved_url')
    except:
        return None

def expand_with_longurl_api(url):
    """Try to expand URL using longurl.me API"""
    try:
        api_url = f"https://api.longurl.me/expand?url={url}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('long_url')
    except:
        return None

def expand_with_allorigins_proxy(url):
    """Try to expand URL using AllOrigins proxy"""
    try:
        proxy_url = f"https://api.allorigins.win/get?url={url}"
        response = requests.get(proxy_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            content = data.get('contents', '')
            
            # Look for canonical URL
            canonical_match = re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]*)"[^>]*>', content, re.IGNORECASE)
            if canonical_match:
                return canonical_match.group(1)
            
            # Look for og:url
            og_url_match = re.search(r'<meta[^>]*property="og:url"[^>]*content="([^"]*)"[^>]*>', content, re.IGNORECASE)
            if og_url_match:
                return og_url_match.group(1)
    except:
        return None

def extract_product_info(url):
    """Extract shop ID and item ID from Shopee URL"""
    patterns = [
        # Product URL format: /product/{shop_id}/{item_id}
        r'shopee\.co\.id/product/(\d+)/(\d+)',
        r'shopee\.com\.my/product/(\d+)/(\d+)',
        r'shopee\.sg/product/(\d+)/(\d+)',
        r'shopee\.ph/product/(\d+)/(\d+)',
        r'shopee\.co\.th/product/(\d+)/(\d+)',
        r'shopee\.vn/product/(\d+)/(\d+)',
        r'shopee\.com\.br/product/(\d+)/(\d+)',
        r'shopee\.tw/product/(\d+)/(\d+)',
        r'shopee\.com/product/(\d+)/(\d+)',
        
        # Legacy .i. format
        r'shopee\.co\.id/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.com\.my/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.sg/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.ph/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.co\.th/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.vn/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.com\.br/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.tw/.*?\.i\.(\d+)\.(\d+)',
        r'shopee\.com/.*?\.i\.(\d+)\.(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            domain_match = re.search(r'https?://([^/]+)', url)
            domain = domain_match.group(1) if domain_match else 'shopee.co.th'
            
            return {
                'shop_id': match.group(1),
                'item_id': match.group(2),
                'domain': domain,
                'is_product_format': 'product' in pattern
            }
    
    return None

def main():
    st.set_page_config(
        page_title="Pa's Shopee Affiliate Link",
        page_icon="🛍️",
        layout="centered"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #ee4d2d;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .url-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ee4d2d;
        margin: 1rem 0;
        word-break: break-all;
        font-family: monospace;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h2 class="main-header">🥹 Support Pa With a Cup of Tea 🍵</h2>', unsafe_allow_html=True)
    
    # Input fields
    with st.form("affiliate_form"):
        shopee_url = st.text_input(
            "Paste any Shopee URL (short or full):",
            placeholder="https://shopee.co.th/... or https://s.shopee.co.th/... or https://th.shp.ee/...",
            help="Enter any Shopee product URL. Short URLs will be automatically expanded."
        )
        
        affiliate_id = "an_15310390250"
        #affiliate_id = st.text_input(
        #    "Affiliate ID:",
        #    value="an_15310390250",
        #    help="This will be added as the affiliate parameter to the product URL.",
        #    disabled=True,
        #)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🔗 Generate Affiliate Link", use_container_width=True)
        with col2:
            pasted_generate = st.form_submit_button("📋 Paste & Generate Link", use_container_width=True)

    if pasted_generate:
        import pyperclip
        try:
            shopee_url = pyperclip.paste()
            st.info(f"📋 Pasted URL: {shopee_url}")
        except Exception as e:
            st.warning("⚠️ Could not read clipboard. Please paste manually.")
            return

    if submitted or pasted_generate:

        if not shopee_url.strip():
            st.error("❌ Please enter a Shopee URL")
            return
        
        if not affiliate_id.strip():
            st.error("❌ Please enter your affiliate ID")
            return
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: URL Expansion
            status_text.info("🔄 Expanding URL...")
            progress_bar.progress(25)
            time.sleep(0.5)  # Visual feedback
            
            expanded_url = expand_short_url(shopee_url.strip())
            
            # Step 2: Extract product info
            status_text.info("🔍 Extracting product information...")
            progress_bar.progress(50)
            time.sleep(0.5)
            
            product_info = extract_product_info(expanded_url)
            
            if not product_info:
                st.error("❌ Could not extract product information from the URL. Please check if it's a valid Shopee product URL.")
                return
            
            # Step 3: Generate URLs
            status_text.info("🔗 Generating affiliate link...")
            progress_bar.progress(75)
            time.sleep(0.5)
            
            base_product_url = f"https://{product_info['domain']}/product/{product_info['shop_id']}/{product_info['item_id']}"
            affiliate_link = f"{base_product_url}?utm_medium=affiliates&utm_source={affiliate_id.strip()}"
            
            # Step 4: Display results
            progress_bar.progress(100)
            status_text.success("✅ Affiliate link generated successfully!")
            time.sleep(1)

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            # Show only the open link button and thank you message
            #st.markdown("### 🎉 Your Affiliate Link is Ready!")

            st.markdown(f'''
            <div style="text-align:center; margin: 1rem 0;">
                <a href="{affiliate_link}" target="_blank">
                    <button style="background-color:#ee4d2d; color:white; padding: 12px 48px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer;">
                        🔗 Open Affiliate Link
                    </button>
                </a>
            </div>
            ''', unsafe_allow_html=True)

            st.success("🙏 Thank you for your support.")

            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.error("Please try again or check if the URL is valid.")

if __name__ == "__main__":
    main()