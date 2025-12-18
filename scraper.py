"""
SRS5G Photo Scraper
Scrape student photos from srs5g.ut.ac.id using Playwright with response interception.
"""
import base64
import os
import re
import sys
import time
from typing import Optional
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Response
from tqdm import tqdm

from config import (
    LOGIN_URL, STUDENT_INFO_URL, SELECTORS, DELAYS,
    HEADLESS, TIMEOUT, IMAGE_CONTENT_TYPES, NIM_CSV_FILE
)
from utils import (
    ensure_directories, load_nim_from_csv, load_progress, save_progress,
    add_completed, add_failed, save_photo, get_pending_nims, print_summary,
    photo_exists
)

# Load environment variables
load_dotenv()


class PhotoScraper:
    def __init__(self):
        self.username = os.getenv("SRS_USERNAME")
        self.password = os.getenv("SRS_PASSWORD")
        self.current_nim: Optional[str] = None
        self.photo_captured = False
        self.progress = {}
        
        if not self.username or not self.password:
            print("Error: SRS_USERNAME dan SRS_PASSWORD harus diset di file .env")
            print("Buat file .env dengan format:")
            print("  SRS_USERNAME=username_anda")
            print("  SRS_PASSWORD=password_anda")
            sys.exit(1)
    
    def handle_response(self, response: Response):
        """Handle intercepted responses to capture image data."""
        try:
            content_type = response.headers.get("content-type", "")
            
            # Check if this is an image response
            if any(img_type in content_type.lower() for img_type in IMAGE_CONTENT_TYPES):
                if self.current_nim and not self.photo_captured:
                    try:
                        image_bytes = response.body()
                        if image_bytes and len(image_bytes) > 1000:  # Minimal size check
                            if save_photo(self.current_nim, image_bytes):
                                self.photo_captured = True
                                add_completed(self.current_nim, self.progress)
                    except Exception as e:
                        pass  # Ignore errors in response handling
        except Exception:
            pass
    
    def solve_math_captcha(self, page: Page) -> Optional[str]:
        """
        Solve simple math CAPTCHA like "8 + 0 = "
        Returns the answer as string, or None if no captcha found.
        """
        try:
            # Try multiple methods to find the CAPTCHA text
            
            # Method 1: Get all text from the page
            page_text = page.inner_text("body")
            
            # Method 2: Try to get text from specific captcha container
            try:
                # Look for the captcha container and get its text
                captcha_containers = [
                    "div:has(input[placeholder*='Jawaban'])",
                    "div:has(input[name*='captcha'])",
                    ".captcha",
                    "[class*='captcha']",
                ]
                for selector in captcha_containers:
                    try:
                        element = page.locator(selector).first
                        if element:
                            container_text = element.inner_text()
                            if container_text:
                                page_text = container_text + " " + page_text
                    except:
                        pass
            except:
                pass
            
            # Method 3: Evaluate JavaScript to get text from all elements
            try:
                js_text = page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('*');
                        let texts = [];
                        elements.forEach(el => {
                            if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
                                const text = el.textContent.trim();
                                if (/\\d+\\s*[+\\-×÷xX*\\/]\\s*\\d+/.test(text)) {
                                    texts.push(text);
                                }
                            }
                        });
                        return texts.join(' ');
                    }
                """)
                if js_text:
                    page_text = js_text + " " + page_text
            except:
                pass
            
            print(f"Page text for CAPTCHA detection: {page_text[:200]}...")
            
            # Pattern to match math expressions like "8 + 0" or "5 - 3"
            patterns = [
                (r'(\d+)\s*\+\s*(\d+)', 'add'),      # Addition: 8 + 0
                (r'(\d+)\s*-\s*(\d+)', 'sub'),       # Subtraction: 5 - 3
                (r'(\d+)\s*[×xX\*]\s*(\d+)', 'mul'), # Multiplication: 2 × 4
                (r'(\d+)\s*[÷/]\s*(\d+)', 'div'),    # Division: 8 ÷ 2
            ]
            
            for pattern, op in patterns:
                match = re.search(pattern, page_text)
                if match:
                    a, b = int(match.group(1)), int(match.group(2))
                    if op == 'add':
                        result = a + b
                    elif op == 'sub':
                        result = a - b
                    elif op == 'mul':
                        result = a * b
                    elif op == 'div':
                        result = a // b if b != 0 else 0
                    
                    print(f"CAPTCHA detected: {match.group(0)} = {result}")
                    return str(result)
            
            print("No CAPTCHA math expression found in page text")
            return None
        except Exception as e:
            print(f"Error solving captcha: {e}")
            return None
    
    def login(self, page: Page, manual_mode: bool = False) -> bool:
        """Login to SRS5G with CAPTCHA handling."""
        try:
            print("Logging in to SRS5G...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=TIMEOUT)
            
            # Wait for page to fully load
            time.sleep(1)
            
            # Fill email - try by accessible name first
            try:
                email_input = page.get_by_role("textbox", name="EMAIL").first
                if email_input and email_input.is_visible():
                    email_input.fill(self.username)
                    print(f"Email filled: {self.username}")
                else:
                    raise Exception("Not found by role")
            except:
                # Fallback to selector
                email_input = page.locator(SELECTORS["email"]).first
                if email_input:
                    email_input.fill(self.username)
                    print(f"Email filled: {self.username}")
                else:
                    print("Error: Email input not found")
                    return False
            
            # Fill password - try by accessible name first
            try:
                password_input = page.get_by_role("textbox", name="KATA SANDI").first
                if password_input and password_input.is_visible():
                    password_input.fill(self.password)
                    print("Password filled")
                else:
                    raise Exception("Not found by role")
            except:
                # Fallback to selector
                password_input = page.locator(SELECTORS["password"]).first
                if password_input:
                    password_input.fill(self.password)
                    print("Password filled")
                else:
                    print("Error: Password input not found")
                    return False
            
            # Handle CAPTCHA
            if manual_mode:
                # Manual mode: wait for user to solve CAPTCHA and click login
                print("\n" + "="*60)
                print("MANUAL LOGIN MODE")
                print("="*60)
                print("Silahkan selesaikan CAPTCHA dan klik tombol 'Masuk' di browser.")
                print("Scraper akan melanjutkan setelah login berhasil...")
                print("="*60 + "\n")
                
                # Wait for user to complete login (max 120 seconds)
                try:
                    page.wait_for_url(
                        lambda url: "login" not in url.lower() and "auth" not in url.lower(),
                        timeout=120000
                    )
                except:
                    print("Timeout: Login tidak selesai dalam 2 menit.")
                    return False
            else:
                # Auto mode: try to solve CAPTCHA
                captcha_answer = self.solve_math_captcha(page)
                if captcha_answer:
                    # Try multiple selectors for captcha input
                    captcha_selectors = [
                        "input[placeholder*='Jawaban']",
                        "input[name*='captcha']", 
                        "input[name*='Captcha']",
                        "input[aria-label*='captcha']",
                        "input[aria-label*='Jawaban']",
                    ]
                    captcha_filled = False
                    for selector in captcha_selectors:
                        try:
                            captcha_input = page.locator(selector).first
                            if captcha_input and captcha_input.is_visible():
                                captcha_input.fill(captcha_answer)
                                print(f"CAPTCHA answer filled: {captcha_answer}")
                                captcha_filled = True
                                break
                        except:
                            pass
                    
                    if not captcha_filled:
                        # Try by accessible name
                        try:
                            captcha_input = page.get_by_role("textbox", name=re.compile("captcha|jawaban", re.I)).first
                            if captcha_input:
                                captcha_input.fill(captcha_answer)
                                print(f"CAPTCHA answer filled (by role): {captcha_answer}")
                                captcha_filled = True
                        except:
                            pass
                    
                    if not captcha_filled:
                        print("Warning: CAPTCHA input not found")
                else:
                    print("Warning: Could not auto-solve CAPTCHA. Try --manual mode.")
                
                # Click login button - try multiple methods
                try:
                    login_btn = page.get_by_role("button", name=re.compile("masuk|login|submit", re.I)).first
                    if login_btn and login_btn.is_visible():
                        login_btn.click()
                    else:
                        raise Exception("Not found by role")
                except:
                    login_btn = page.locator(SELECTORS["login_button"]).first
                    if login_btn:
                        login_btn.click()
                    else:
                        print("Error: Login button not found")
                        return False
                
                # Wait for login to complete
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                time.sleep(DELAYS["after_login"] / 1000)
            
            # Check if login successful (should redirect away from login page)
            if "login" in page.url.lower() or "auth" in page.url.lower():
                print("Error: Login gagal. Periksa email, password, atau CAPTCHA.")
                print("Coba gunakan mode --manual untuk login dengan CAPTCHA manual.")
                return False
            
            print("Login berhasil!")
            return True
        
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False
    
    def scrape_photo(self, page: Page, nim: str, debug: bool = False) -> bool:
        """Scrape photo for a single NIM."""
        self.current_nim = nim
        self.photo_captured = False
        
        try:
            # Navigate to student page
            url = f"{STUDENT_INFO_URL}?nim={nim}"
            page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
            time.sleep(DELAYS["after_navigate"] / 1000)
            
            if debug:
                print(f"\nDEBUG: Page URL: {page.url}")
                print(f"DEBUG: Page title: {page.title()}")
                # List all buttons on page
                buttons = page.locator("button, a.btn, [role='button']").all()
                print(f"DEBUG: Found {len(buttons)} buttons on page:")
                for i, btn in enumerate(buttons[:10]):  # Limit to first 10
                    try:
                        text = btn.inner_text()
                        print(f"  {i+1}. '{text}'")
                    except:
                        pass
            
            # Try multiple selectors for "Lihat" button (specifically for photo/pas foto)
            # We want the first "Lihat" which is usually for pas foto
            view_button_selectors = [
                "button:has-text('Lihat'):first-of-type",
                "text=Lihat >> nth=0",  # First "Lihat" button
                "button:has-text('Lihat')",
                "a:has-text('Lihat')",
                "[class*='btn']:has-text('Lihat')",
            ]
            
            button_clicked = False
            for selector in view_button_selectors:
                try:
                    button = page.locator(selector).first
                    if button and button.is_visible(timeout=1000):
                        button.click()
                        button_clicked = True
                        if debug:
                            print(f"DEBUG: Clicked button with selector: {selector}")
                        break
                except:
                    continue
            
            if not button_clicked:
                add_failed(nim, f"Button 'Lihat' tidak ditemukan pada halaman", self.progress)
                return False
            
            time.sleep(DELAYS["after_click"] / 1000)
            
            # Wait for modal/image to appear and extract blob data
            time.sleep(1)  # Wait for blob to load
            
            # Try to extract image from blob URL using JavaScript
            image_data = self.extract_blob_image(page, debug)
            
            if image_data:
                if save_photo(nim, image_data):
                    self.photo_captured = True
                    add_completed(nim, self.progress)
                    return True
            
            # Fallback: check if response interceptor caught it
            if self.photo_captured:
                return True
            
            add_failed(nim, "Foto tidak ditemukan (blob extraction failed)", self.progress)
            return False
        
        except Exception as e:
            add_failed(nim, f"Error: {str(e)}", self.progress)
            return False
    
    def extract_blob_image(self, page: Page, debug: bool = False) -> Optional[bytes]:
        """Extract image data from blob URL in the page."""
        try:
            # JavaScript to find blob image and convert to base64
            js_code = """
            async () => {
                // Find images with blob src
                const images = document.querySelectorAll('img[src^="blob:"]');
                if (images.length === 0) {
                    // Try to find in modal/dialog
                    const modalImages = document.querySelectorAll('.modal img, [role="dialog"] img, .swal2-image, .fancybox-image, img.img-fluid');
                    for (const img of modalImages) {
                        if (img.src && img.src.startsWith('blob:')) {
                            images = [img];
                            break;
                        }
                    }
                }
                
                if (images.length === 0) {
                    return null;
                }
                
                // Get the first blob image (usually the photo)
                const img = images[0];
                const blobUrl = img.src;
                
                try {
                    // Fetch the blob
                    const response = await fetch(blobUrl);
                    const blob = await response.blob();
                    
                    // Convert to base64
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            // Remove data URL prefix to get pure base64
                            const base64 = reader.result.split(',')[1];
                            resolve(base64);
                        };
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });
                } catch (e) {
                    console.error('Error fetching blob:', e);
                    return null;
                }
            }
            """
            
            # Execute JavaScript and get base64 data
            base64_data = page.evaluate(js_code)
            
            if base64_data:
                if debug:
                    print(f"DEBUG: Extracted blob image, base64 length: {len(base64_data)}")
                # Convert base64 to bytes
                image_bytes = base64.b64decode(base64_data)
                
                # Validate it's actually an image (check for JPEG/PNG magic bytes)
                if image_bytes[:2] == b'\xff\xd8':  # JPEG
                    if debug:
                        print("DEBUG: Valid JPEG image detected")
                    return image_bytes
                elif image_bytes[:4] == b'\x89PNG':  # PNG
                    if debug:
                        print("DEBUG: Valid PNG image detected")
                    return image_bytes
                elif len(image_bytes) > 5000:  # Assume valid if large enough
                    if debug:
                        print(f"DEBUG: Image size: {len(image_bytes)} bytes")
                    return image_bytes
                else:
                    if debug:
                        print(f"DEBUG: Invalid image data, size: {len(image_bytes)}")
            
            return None
        except Exception as e:
            if debug:
                print(f"DEBUG: Error extracting blob: {e}")
            return None
    
    def run(self, csv_path: str = None, manual_login: bool = False, headless: bool = True, debug: bool = False):
        """Main scraping loop."""
        self.debug = debug
        # Ensure directories exist
        ensure_directories()
        
        # Load NIM list
        csv_file = csv_path or str(NIM_CSV_FILE)
        if not os.path.exists(csv_file):
            print(f"Error: File CSV tidak ditemukan: {csv_file}")
            print("Buat file nim_list.csv dengan format:")
            print("  nim")
            print("  857264993")
            print("  857264994")
            print("  ...")
            sys.exit(1)
        
        print(f"Loading NIM list from {csv_file}...")
        all_nims = load_nim_from_csv(csv_file)
        print(f"Total NIM in CSV: {len(all_nims)}")
        
        # Load progress
        self.progress = load_progress()
        
        # Get pending NIMs (filter completed and existing)
        pending_nims = get_pending_nims(all_nims, self.progress)
        print(f"Already completed: {len(self.progress['completed'])}")
        print(f"Pending to process: {len(pending_nims)}")
        
        if not pending_nims:
            print("Semua NIM sudah selesai diproses!")
            print_summary(self.progress, len(all_nims))
            return
        
        # Manual login requires visible browser
        if manual_login:
            headless = False
            print("Manual login mode: Browser akan ditampilkan untuk login.")
        
        # Start browser
        with sync_playwright() as p:
            print("Starting browser...")
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            
            # Set up response interception
            page.on("response", self.handle_response)
            
            # Login
            if not self.login(page, manual_mode=manual_login):
                browser.close()
                sys.exit(1)
            
            # Process each NIM
            print(f"\nProcessing {len(pending_nims)} NIMs...")
            
            with tqdm(total=len(pending_nims), desc="Scraping photos") as pbar:
                for nim in pending_nims:
                    # Double check if photo exists (in case of parallel runs)
                    if photo_exists(nim):
                        add_completed(nim, self.progress)
                        pbar.update(1)
                        continue
                    
                    success = self.scrape_photo(page, nim, debug=self.debug)
                    
                    if success:
                        pbar.set_postfix({"last": nim, "status": "OK"})
                    else:
                        pbar.set_postfix({"last": nim, "status": "FAIL"})
                    
                    pbar.update(1)
                    
                    # Small delay between requests
                    time.sleep(DELAYS["between_requests"] / 1000)
            
            browser.close()
        
        # Print summary
        print_summary(self.progress, len(all_nims))


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape student photos from SRS5G")
    parser.add_argument(
        "--csv", 
        type=str, 
        default=None,
        help="Path to CSV file containing NIM list (default: nim_list.csv)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Run browser in visible mode (for debugging)"
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Manual login mode: User solves CAPTCHA manually, then scraper continues"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to see page details"
    )
    
    args = parser.parse_args()
    
    # Determine headless mode
    headless = HEADLESS
    if args.visible:
        headless = False
    if args.headless:
        headless = True
    if args.manual:
        headless = False  # Manual mode requires visible browser
    
    scraper = PhotoScraper()
    scraper.run(csv_path=args.csv, manual_login=args.manual, headless=headless, debug=args.debug)


if __name__ == "__main__":
    main()

