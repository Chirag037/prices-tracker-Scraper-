import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import json
import threading
import time
import re
from datetime import datetime
import os
import webbrowser

class PriceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Price Tracker Bot")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f0f0")
        
        # Data storage
        self.products = []
        self.data_file = "tracked_products.json"
        self.load_data()
        
        # Variables
        self.tracking_active = tk.BooleanVar(value=False)
        self.check_interval = tk.IntVar(value=30)  # minutes
        
        self.create_widgets()
        self.load_products_display()
        
        # Start tracking thread
        self.tracking_thread = None
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(main_frame, text="🛒 Price Tracker Bot", 
                              font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#2c3e50")
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Add product section
        add_frame = ttk.LabelFrame(main_frame, text="Add Product to Track", padding="10")
        add_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(add_frame, text="Product URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.url_entry = ttk.Entry(add_frame, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        ttk.Label(add_frame, text="Product Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(add_frame, width=30)
        self.name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        ttk.Label(add_frame, text="Target Price ($):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.target_price_entry = ttk.Entry(add_frame, width=15)
        self.target_price_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        add_btn = ttk.Button(add_frame, text="Add Product", command=self.add_product)
        add_btn.grid(row=2, column=2, padx=(10, 0), pady=2)
        
        # Tracking controls
        control_frame = ttk.LabelFrame(main_frame, text="Tracking Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Check Interval (minutes):").grid(row=0, column=0, sticky=tk.W)
        interval_spinbox = ttk.Spinbox(control_frame, from_=5, to=1440, width=10, textvariable=self.check_interval)
        interval_spinbox.grid(row=0, column=1, padx=(10, 0))
        
        self.start_btn = ttk.Button(control_frame, text="Start Tracking", command=self.toggle_tracking)
        self.start_btn.grid(row=0, column=2, padx=(20, 0))
        
        self.status_label = tk.Label(control_frame, text="Status: Stopped", fg="red")
        self.status_label.grid(row=0, column=3, padx=(20, 0))
        
        # Alert settings
        alert_frame = ttk.LabelFrame(main_frame, text="Alert Settings", padding="10")
        alert_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.sound_alerts = tk.BooleanVar(value=True)
        self.popup_alerts = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(alert_frame, text="Sound Alerts", variable=self.sound_alerts).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(alert_frame, text="Popup Alerts", variable=self.popup_alerts).grid(row=0, column=1, padx=(20, 0), sticky=tk.W)
        
        # Products display
        products_frame = ttk.LabelFrame(main_frame, text="Tracked Products", padding="10")
        products_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Treeview for products
        columns = ("Name", "Current Price", "Target Price", "Savings", "Status", "Last Checked")
        self.products_tree = ttk.Treeview(products_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.products_tree.heading(col, text=col)
            if col == "Name":
                self.products_tree.column(col, width=200)
            else:
                self.products_tree.column(col, width=100)
        
        scrollbar_v = ttk.Scrollbar(products_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar_v.set)
        
        self.products_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Double click to open URL
        self.products_tree.bind("<Double-1>", self.open_product_url)
        
        # Buttons for product management
        btn_frame = ttk.Frame(products_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_product).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Check Now", command=self.check_selected_product).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Check All", command=self.check_all_products).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Open URL", command=self.open_selected_url).pack(side=tk.LEFT)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        main_frame.rowconfigure(5, weight=1)
        products_frame.columnconfigure(0, weight=1)
        products_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def play_alert_sound(self):
        """Play system alert sound"""
        try:
            if self.sound_alerts.get():
                # Try to play system bell sound
                self.root.bell()
        except:
            pass
            
    def extract_price(self, soup, url):
        """Extract price from different e-commerce sites"""
        price_selectors = {
            'amazon': [
                '.a-price-whole',
                '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
                '.a-price-range .a-offscreen',
                'span.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
                '.a-price .a-offscreen',
                '#corePrice_feature_div .a-price .a-offscreen'
            ],
            'ebay': [
                '.u-flL.condenseFont',
                '.notranslate',
                '.p-price .notranslate',
                '[data-testid="x-price-primary"] .notranslate'
            ],
            'daraz': [
                '.pdp-product-price .pdp-price',
                '.price-box .price',
                '.current-price'
            ]
        }
        
        # Determine site
        site = 'generic'
        if 'amazon' in url.lower():
            site = 'amazon'
        elif 'ebay' in url.lower():
            site = 'ebay'
        elif 'daraz' in url.lower():
            site = 'daraz'
            
        # Try site-specific selectors first
        if site in price_selectors:
            for selector in price_selectors[site]:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text().strip()
                    # Extract numeric value
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', '').replace('$', ''))
                    if price_match:
                        try:
                            price = float(price_match.group())
                            if price > 0:
                                return price
                        except ValueError:
                            continue
        
        # Generic price extraction as fallback
        generic_selectors = [
            '[class*="price"]',
            '[id*="price"]',
            '.price',
            '.cost',
            '.amount',
            '[data-price]'
        ]
        
        for selector in generic_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Try data attribute first
                if element.get('data-price'):
                    try:
                        price = float(element.get('data-price'))
                        if price > 0:
                            return price
                    except ValueError:
                        pass
                        
                # Try text content
                text = element.get_text().strip()
                price_match = re.search(r'[\d,]+\.?\d*', text.replace(',', '').replace('$', ''))
                if price_match and len(price_match.group()) > 0:
                    try:
                        price = float(price_match.group())
                        if price > 0:
                            return price
                    except ValueError:
                        continue
        
        return None
        
    def get_product_price(self, url):
        """Fetch current price of product from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add delay to be respectful
            time.sleep(2)
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            price = self.extract_price(soup, url)
            
            return price
            
        except requests.exceptions.RequestException as e:
            self.log_message(f"Network error for {url}: {str(e)}")
            return None
        except Exception as e:
            self.log_message(f"Error parsing price from {url}: {str(e)}")
            return None
            
    def add_product(self):
        """Add new product to tracking list"""
        url = self.url_entry.get().strip()
        name = self.name_entry.get().strip()
        target_price_str = self.target_price_entry.get().strip()
        
        if not url or not name or not target_price_str:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            target_price = float(target_price_str)
        except ValueError:
            messagebox.showerror("Error", "Target price must be a number")
            return
            
        # Check if product already exists
        for product in self.products:
            if product['url'] == url:
                messagebox.showerror("Error", "This product is already being tracked")
                return
                
        # Try to get initial price
        self.log_message(f"Checking initial price for {name}...")
        current_price = self.get_product_price(url)
        
        product = {
            'name': name,
            'url': url,
            'target_price': target_price,
            'current_price': current_price,
            'last_checked': datetime.now().isoformat(),
            'alerts_sent': 0,
            'price_history': []
        }
        
        if current_price:
            product['price_history'].append({
                'price': current_price,
                'timestamp': datetime.now().isoformat()
            })
        
        self.products.append(product)
        self.save_data()
        self.load_products_display()
        
        # Clear entries
        self.url_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.target_price_entry.delete(0, tk.END)
        
        if current_price:
            self.log_message(f"✅ Added {name} - Current price: ${current_price:.2f}")
            if current_price <= target_price:
                self.log_message(f"🎉 Target price already reached for {name}!")
                self.show_price_alert(product)
        else:
            self.log_message(f"⚠️ Added {name} - Could not fetch initial price")
            
    def remove_product(self):
        """Remove selected product from tracking"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product to remove")
            return
            
        item = selection[0]
        product_name = self.products_tree.item(item)['values'][0]
        
        # Find and remove product
        self.products = [p for p in self.products if p['name'] != product_name]
        self.save_data()
        self.load_products_display()
        
        self.log_message(f"🗑️ Removed {product_name} from tracking")
        
    def check_selected_product(self):
        """Check price for selected product"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product to check")
            return
            
        item = selection[0]
        product_name = self.products_tree.item(item)['values'][0]
        
        # Find product and check price
        for product in self.products:
            if product['name'] == product_name:
                self.check_product_price(product)
                break
                
        self.save_data()
        self.load_products_display()
        
    def check_all_products(self):
        """Check prices for all products"""
        if not self.products:
            messagebox.showinfo("Info", "No products to check")
            return
            
        self.log_message("🔍 Checking all products...")
        
        for i, product in enumerate(self.products):
            self.log_message(f"Checking ({i+1}/{len(self.products)}): {product['name']}")
            self.check_product_price(product)
            
        self.save_data()
        self.load_products_display()
        self.log_message("✅ Finished checking all products")
        
    def check_product_price(self, product):
        """Check price for a single product and send alert if needed"""        
        current_price = self.get_product_price(product['url'])
        product['last_checked'] = datetime.now().isoformat()
        
        if current_price is None:
            self.log_message(f"❌ Failed to get price for {product['name']}")
            return
            
        old_price = product['current_price']
        product['current_price'] = current_price
        
        # Add to price history
        product['price_history'].append({
            'price': current_price,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 price points
        if len(product['price_history']) > 50:
            product['price_history'] = product['price_history'][-50:]
        
        # Check if price dropped below target
        if current_price <= product['target_price']:
            savings = product['target_price'] - current_price
            self.log_message(f"🎉 TARGET REACHED! {product['name']} is now ${current_price:.2f} (Save ${savings:.2f})")
            self.show_price_alert(product)
            
        elif old_price and current_price < old_price:
            savings = old_price - current_price
            self.log_message(f"📉 Price dropped for {product['name']}: ${old_price:.2f} → ${current_price:.2f} (Save ${savings:.2f})")
            
        elif old_price and current_price > old_price:
            increase = current_price - old_price
            self.log_message(f"📈 Price increased for {product['name']}: ${old_price:.2f} → ${current_price:.2f} (+${increase:.2f})")
            
        else:
            self.log_message(f"➡️ Price unchanged for {product['name']}: ${current_price:.2f}")
            
    def show_price_alert(self, product):
        """Show price alert to user"""
        self.play_alert_sound()
        
        if self.popup_alerts.get():
            savings = product['target_price'] - product['current_price']
            message = f"🎯 PRICE ALERT!\n\n"
            message += f"Product: {product['name']}\n"
            message += f"Current Price: ${product['current_price']:.2f}\n"
            message += f"Target Price: ${product['target_price']:.2f}\n"
            message += f"You Save: ${savings:.2f}\n\n"
            message += f"Would you like to open the product page?"
            
            result = messagebox.askyesno("Price Alert!", message)
            if result:
                webbrowser.open(product['url'])
                
        product['alerts_sent'] += 1
        
    def open_product_url(self, event):
        """Open product URL when double-clicked"""
        selection = self.products_tree.selection()
        if selection:
            item = selection[0]
            product_name = self.products_tree.item(item)['values'][0]
            
            for product in self.products:
                if product['name'] == product_name:
                    webbrowser.open(product['url'])
                    self.log_message(f"🌐 Opened {product['name']} in browser")
                    break
                    
    def open_selected_url(self):
        """Open selected product URL"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a product first")
            return
            
        item = selection[0]
        product_name = self.products_tree.item(item)['values'][0]
        
        for product in self.products:
            if product['name'] == product_name:
                webbrowser.open(product['url'])
                self.log_message(f"🌐 Opened {product['name']} in browser")
                break
            
    def toggle_tracking(self):
        """Start or stop price tracking"""
        if self.tracking_active.get():
            # Stop tracking
            self.tracking_active.set(False)
            self.start_btn.config(text="Start Tracking")
            self.status_label.config(text="Status: Stopped", fg="red")
            self.log_message("⏹️ Tracking stopped")
        else:
            # Start tracking
            if not self.products:
                messagebox.showwarning("Warning", "No products to track. Add some products first.")
                return
                
            self.tracking_active.set(True)
            self.start_btn.config(text="Stop Tracking")
            self.status_label.config(text="Status: Running", fg="green")
            self.log_message(f"▶️ Tracking started - checking every {self.check_interval.get()} minutes")
            
            # Start tracking thread
            self.tracking_thread = threading.Thread(target=self.tracking_loop, daemon=True)
            self.tracking_thread.start()
            
    def tracking_loop(self):
        """Main tracking loop"""
        while self.tracking_active.get():
            self.check_all_products()
            
            # Wait for specified interval
            for _ in range(self.check_interval.get() * 60):  # Convert minutes to seconds
                if not self.tracking_active.get():
                    break
                time.sleep(1)
                
    def load_products_display(self):
        """Update the products display"""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
            
        # Add products
        for product in self.products:
            current_price = f"${product['current_price']:.2f}" if product['current_price'] else "N/A"
            target_price = f"${product['target_price']:.2f}"
            
            # Calculate savings
            savings = "N/A"
            if product['current_price']:
                if product['current_price'] <= product['target_price']:
                    savings_amount = product['target_price'] - product['current_price']
                    savings = f"+${savings_amount:.2f}"
                else:
                    over_amount = product['current_price'] - product['target_price']
                    savings = f"-${over_amount:.2f}"
            
            # Status
            if product['current_price'] and product['current_price'] <= product['target_price']:
                status = "🎯 Target Reached!"
            elif product['current_price']:
                status = "📊 Tracking"
            else:
                status = "❌ Error"
                
            last_checked = "Never"
            if product.get('last_checked'):
                try:
                    dt = datetime.fromisoformat(product['last_checked'])
                    last_checked = dt.strftime("%m/%d %H:%M")
                except:
                    pass
                    
            # Truncate long names
            display_name = product['name'][:30] + "..." if len(product['name']) > 30 else product['name']
                    
            self.products_tree.insert("", tk.END, values=(
                display_name,
                current_price,
                target_price,
                savings,
                status,
                last_checked
            ))
            
    def save_data(self):
        """Save products data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.products, f, indent=2)
        except Exception as e:
            self.log_message(f"Error saving data: {str(e)}")
            
    def load_data(self):
        """Load products data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.products = json.load(f)
                    # Ensure all products have required fields
                    for product in self.products:
                        if 'price_history' not in product:
                            product['price_history'] = []
                        if 'alerts_sent' not in product:
                            product['alerts_sent'] = 0
            else:
                self.products = []
        except Exception as e:
            self.products = []
            self.log_message(f"Error loading data: {str(e)}")

def main():
    root = tk.Tk()
    app = PriceTracker(root)
    
    # Add some styling
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except:
        pass
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Add initial welcome message
    app.log_message("🚀 Price Tracker Bot started successfully!")
    app.log_message("💡 Tip: Double-click on any product to open its URL in browser")
    
    root.mainloop()

if __name__ == "__main__":
    main()