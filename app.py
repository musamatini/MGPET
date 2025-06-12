# app.py

from flask import (
    Flask, render_template, url_for, request, redirect, session, flash, Blueprint
)
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = "mg_pet_ultra_secret_key_v3_!@#$" # IMPORTANT: Change this!

# --- Configuration for Image Uploads ---
UPLOAD_FOLDER = os.path.join(app.static_folder, 'images', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

def ensure_upload_dirs():
    paths = [
        UPLOAD_FOLDER,
        os.path.join(UPLOAD_FOLDER, 'categories'),
        os.path.join(UPLOAD_FOLDER, 'subcategories'),
        os.path.join(UPLOAD_FOLDER, 'products')
    ]
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)
ensure_upload_dirs()

# --- Mock Company Info ---
COMPANY_NAME = "MG PET"
COMPANY_CONTACT_INFO = {
    "phone": "+1-234-567-8900",
    "email": "info@mgpet.com",
    "address": "123 Water Bottle Lane, Hydro City, HC 12345",
    "facebook_url": "https://facebook.com/mgpet",
    "instagram_url": "https://instagram.com/mgpet",
    "twitter_url": "https://twitter.com/mgpet"
}

# --- In-Memory Data Store ---
DATA_STORE = {
    "categories": {}, 
    "subcategories": {}, 
    "products": {}, 
    "admin_users": { "admin": "password123" }
}

# --- Helper Functions (generate_slug, allowed_file, save_image_file - same as before) ---
def generate_slug(name, existing_slugs_keys=None): # Renamed for clarity
    if not name:
        base_slug = str(uuid.uuid4())[:8] 
    else:
        base_slug = name.lower().strip().replace(' ', '-')
        base_slug = "".join(c for c in base_slug if c.isalnum() or c == '-')
    
    if existing_slugs_keys is None: # Should be provided
        return base_slug

    slug = base_slug
    counter = 1
    # Ensure generated slug is unique within the provided keys
    while slug in existing_slugs_keys:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_file(file, subfolder, current_image_path=None):
    if file and file.filename != '' and allowed_file(file.filename):
        if current_image_path:
            old_image_disk_path = os.path.join(app.static_folder, current_image_path)
            if os.path.exists(old_image_disk_path):
                try: os.remove(old_image_disk_path)
                except OSError as e: flash(f"Error deleting old image {current_image_path}: {e}", "danger")
        
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        target_subfolder_disk = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        if not os.path.exists(target_subfolder_disk): os.makedirs(target_subfolder_disk)
            
        disk_save_path = os.path.join(target_subfolder_disk, unique_filename)
        file.save(disk_save_path)
        return os.path.join('images/uploads', subfolder, unique_filename).replace("\\", "/")
    
    if current_image_path: return current_image_path
    return None

# --- Admin Blueprint ---
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates/admin')

from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
def admin_home_redirect():
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ... (same as before) ...
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in DATA_STORE['admin_users'] and DATA_STORE['admin_users'][username] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('admin.manage_categories'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', page_title="Admin Login")


@admin_bp.route('/logout')
def logout():
    # ... (same as before) ...
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

# --- Category Management (same as before) ---
@admin_bp.route('/categories')
@login_required
def manage_categories():
    categories = [{"slug": slug, **data} for slug, data in DATA_STORE["categories"].items()]
    categories.sort(key=lambda x: x.get("name", x["slug"]))
    return render_template('manage_categories.html', categories=categories, page_title="Manage Categories")

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description_lines = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
        image_file = request.files.get('image')
        slug = generate_slug(name if name else "category", DATA_STORE["categories"].keys())
        image_path = save_image_file(image_file, 'categories') if image_file and image_file.filename else None
        
        DATA_STORE["categories"][slug] = {
            "name": name if name else None, "description": description_lines,
            "image": image_path, "subcategories": []
        }
        flash(f"Category '{name if name else slug}' added successfully!", 'success')
        return redirect(url_for('admin.manage_categories'))
    return render_template('category_form.html', form_action="Add", page_title="Add New Category", category=None)

@admin_bp.route('/categories/edit/<category_slug>', methods=['GET', 'POST'])
@login_required
def edit_category(category_slug):
    category = DATA_STORE["categories"].get(category_slug)
    if not category:
        flash("Category not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        description_lines = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
        image_file = request.files.get('image')
        remove_image = request.form.get('remove_image') == 'on'
        current_image_path = category.get('image')
        new_image_path = current_image_path
        if remove_image:
            if current_image_path:
                old_image_disk_path = os.path.join(app.static_folder, current_image_path)
                if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '':
            new_image_path = save_image_file(image_file, 'categories', current_image_path=current_image_path)
        
        category["name"] = new_name if new_name else None
        category["description"] = description_lines
        category["image"] = new_image_path
        flash(f"Category updated successfully!", 'success')
        return redirect(url_for('admin.manage_categories'))
    return render_template('category_form.html', form_action="Edit", category=category, category_slug=category_slug, page_title=f"Edit Category")

@admin_bp.route('/categories/delete/<category_slug>', methods=['POST'])
@login_required
def delete_category(category_slug):
    # ... (same as before) ...
    category = DATA_STORE["categories"].get(category_slug)
    if category:
        if category.get("subcategories"):
            flash(f"Cannot delete category: it has subcategories. Delete them first.", "danger")
            return redirect(url_for('admin.manage_categories'))
        if category.get('image'):
            image_disk_path = os.path.join(app.static_folder, category['image'])
            if os.path.exists(image_disk_path): os.remove(image_disk_path)
        del DATA_STORE["categories"][category_slug]
        flash(f"Category deleted successfully!", 'success')
    else:
        flash("Category not found.", "danger")
    return redirect(url_for('admin.manage_categories'))

# --- Subcategory Management (same as before) ---
@admin_bp.route('/subcategories')
@login_required
def manage_subcategories():
    subcategories_list = []
    for slug, data in DATA_STORE["subcategories"].items():
        parent_cat_slug = data.get("parent_category")
        parent_cat_name = DATA_STORE["categories"].get(parent_cat_slug, {}).get("name", "N/A")
        subcategories_list.append({
            "slug": slug, "parent_category_name": parent_cat_name, **data
        })
    subcategories_list.sort(key=lambda x: (x.get("parent_category_name", ""), x.get("name", x["slug"])))
    return render_template('manage_subcategories.html', subcategories=subcategories_list, page_title="Manage Subcategories")

@admin_bp.route('/subcategories/add', methods=['GET', 'POST'])
@login_required
def add_subcategory():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        parent_category_slug = request.form.get('parent_category')
        description_lines = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
        image_file = request.files.get('image')
        if not parent_category_slug or parent_category_slug not in DATA_STORE["categories"]:
            flash("Invalid parent category selected.", "danger"); return redirect(url_for('admin.add_subcategory')) 
        slug = generate_slug(name if name else "subcategory", DATA_STORE["subcategories"].keys())
        image_path = save_image_file(image_file, 'subcategories') if image_file and image_file.filename else None
        DATA_STORE["subcategories"][slug] = {
            "name": name if name else None, "parent_category": parent_category_slug,
            "description": description_lines, "image": image_path, "products": []
        }
        DATA_STORE["categories"][parent_category_slug]["subcategories"].append(slug)
        flash(f"Subcategory added successfully!", 'success')
        return redirect(url_for('admin.manage_subcategories'))
    categories_for_select = [{"slug": slug, "name": data.get("name", slug)} for slug, data in DATA_STORE["categories"].items()]
    categories_for_select.sort(key=lambda x: x["name"])
    return render_template('subcategory_form.html', form_action="Add", categories=categories_for_select, page_title="Add New Subcategory", subcategory=None)

@admin_bp.route('/subcategories/edit/<subcategory_slug>', methods=['GET', 'POST'])
@login_required
def edit_subcategory(subcategory_slug):
    subcategory = DATA_STORE["subcategories"].get(subcategory_slug)
    if not subcategory:
        flash("Subcategory not found.", "danger"); return redirect(url_for('admin.manage_subcategories'))
    if request.method == 'POST':
        old_parent_slug = subcategory.get('parent_category')
        new_parent_slug = request.form.get('parent_category')
        new_name = request.form.get('name', '').strip()
        description_lines = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
        image_file = request.files.get('image')
        remove_image = request.form.get('remove_image') == 'on'
        current_image_path = subcategory.get('image')
        new_image_path = current_image_path
        if not new_parent_slug or new_parent_slug not in DATA_STORE["categories"]:
            flash("Invalid parent category selected.", "danger"); return redirect(url_for('admin.edit_subcategory', subcategory_slug=subcategory_slug))
        if remove_image:
            if current_image_path:
                old_image_disk_path = os.path.join(app.static_folder, current_image_path)
                if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '':
            new_image_path = save_image_file(image_file, 'subcategories', current_image_path=current_image_path)
        subcategory["name"] = new_name if new_name else None
        subcategory["description"] = description_lines
        subcategory["image"] = new_image_path
        if old_parent_slug != new_parent_slug:
            if old_parent_slug and old_parent_slug in DATA_STORE["categories"] and subcategory_slug in DATA_STORE["categories"][old_parent_slug]["subcategories"]:
                DATA_STORE["categories"][old_parent_slug]["subcategories"].remove(subcategory_slug)
            DATA_STORE["categories"][new_parent_slug]["subcategories"].append(subcategory_slug)
            subcategory["parent_category"] = new_parent_slug
        flash(f"Subcategory updated successfully!", 'success')
        return redirect(url_for('admin.manage_subcategories'))
    categories_for_select = [{"slug": slug, "name": data.get("name", slug)} for slug, data in DATA_STORE["categories"].items()]
    categories_for_select.sort(key=lambda x: x["name"])
    return render_template('subcategory_form.html', form_action="Edit", subcategory=subcategory, 
                           subcategory_slug=subcategory_slug, categories=categories_for_select,
                           page_title=f"Edit Subcategory")

@admin_bp.route('/subcategories/delete/<subcategory_slug>', methods=['POST'])
@login_required
def delete_subcategory(subcategory_slug):
    # ... (same as before) ...
    subcategory = DATA_STORE["subcategories"].get(subcategory_slug)
    if subcategory:
        if subcategory.get("products"):
            flash(f"Cannot delete subcategory: it has products. Delete them first.", "danger")
            return redirect(url_for('admin.manage_subcategories'))
        parent_cat_slug = subcategory.get("parent_category")
        if parent_cat_slug and parent_cat_slug in DATA_STORE["categories"]:
            if subcategory_slug in DATA_STORE["categories"][parent_cat_slug]["subcategories"]:
                DATA_STORE["categories"][parent_cat_slug]["subcategories"].remove(subcategory_slug)
        if subcategory.get('image'):
            image_disk_path = os.path.join(app.static_folder, subcategory['image'])
            if os.path.exists(image_disk_path): os.remove(image_disk_path)
        del DATA_STORE["subcategories"][subcategory_slug]
        flash(f"Subcategory deleted successfully!", 'success')
    else:
        flash("Subcategory not found.", "danger")
    return redirect(url_for('admin.manage_subcategories'))

# --- Product Management ---
@admin_bp.route('/products')
@login_required
def manage_products():
    products_list = []
    for slug, data in DATA_STORE["products"].items():
        parent_subcat_slug = data.get("parent_subcategory")
        parent_subcat_data = DATA_STORE["subcategories"].get(parent_subcat_slug, {})
        parent_subcat_name = parent_subcat_data.get("name", "N/A")
        parent_cat_slug = parent_subcat_data.get("parent_category")
        parent_cat_name = DATA_STORE["categories"].get(parent_cat_slug, {}).get("name", "N/A")
        products_list.append({
            "slug": slug, "parent_category_name": parent_cat_name,
            "parent_subcategory_name": parent_subcat_name, **data
        })
    products_list.sort(key=lambda x: (x.get("parent_category_name", ""), x.get("parent_subcategory_name", ""), x.get("name", x["slug"])))
    return render_template('manage_products.html', products=products_list, page_title="Manage Products")

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        parent_subcategory_slug = request.form.get('parent_subcategory')
        short_desc_lines = [line.strip() for line in request.form.getlist('short_description[]') if line.strip()]
        long_desc_lines = [line.strip() for line in request.form.getlist('long_description[]') if line.strip()]
        use_short_for_long = request.form.get('use_short_desc_for_long') == 'on'
        image_file = request.files.get('image')

        if not parent_subcategory_slug or parent_subcategory_slug not in DATA_STORE["subcategories"]:
            flash("Invalid parent subcategory selected.", "danger")
            # Consider passing subcategories back to the form for repopulation
            return redirect(url_for('admin.add_product')) 

        slug = generate_slug(name if name else "product", DATA_STORE["products"].keys())
        image_path = save_image_file(image_file, 'products') if image_file and image_file.filename else None

        DATA_STORE["products"][slug] = {
            "name": name if name else None,
            "parent_subcategory": parent_subcategory_slug,
            "short_description": short_desc_lines,
            "long_description": long_desc_lines,
            "use_short_desc_for_long": use_short_for_long,
            "image": image_path
        }
        # Add this product to its parent subcategory's list
        DATA_STORE["subcategories"][parent_subcategory_slug]["products"].append(slug)
        
        flash(f"Product '{name if name else slug}' added successfully!", 'success')
        return redirect(url_for('admin.manage_products'))
    
    subcategories_for_select = []
    for sc_slug, sc_data in DATA_STORE["subcategories"].items():
        parent_cat_slug = sc_data.get("parent_category")
        parent_cat_name = DATA_STORE["categories"].get(parent_cat_slug, {}).get("name", parent_cat_slug)
        subcategories_for_select.append({
            "slug": sc_slug, 
            "name": f"{parent_cat_name} > {sc_data.get('name', sc_slug)}"
        })
    subcategories_for_select.sort(key=lambda x: x["name"])
    return render_template('product_form.html', form_action="Add", subcategories=subcategories_for_select, page_title="Add New Product", product=None)

@admin_bp.route('/products/edit/<product_slug>', methods=['GET', 'POST'])
@login_required
def edit_product(product_slug):
    product = DATA_STORE["products"].get(product_slug)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('admin.manage_products'))

    if request.method == 'POST':
        old_parent_subcat_slug = product.get('parent_subcategory')
        new_parent_subcat_slug = request.form.get('parent_subcategory')
        new_name = request.form.get('name', '').strip()
        short_desc_lines = [line.strip() for line in request.form.getlist('short_description[]') if line.strip()]
        long_desc_lines = [line.strip() for line in request.form.getlist('long_description[]') if line.strip()]
        use_short_for_long = request.form.get('use_short_desc_for_long') == 'on'
        image_file = request.files.get('image')
        remove_image = request.form.get('remove_image') == 'on'
        current_image_path = product.get('image')
        new_image_path = current_image_path

        if not new_parent_subcat_slug or new_parent_subcat_slug not in DATA_STORE["subcategories"]:
            flash("Invalid parent subcategory selected.", "danger")
            return redirect(url_for('admin.edit_product', product_slug=product_slug))

        if remove_image:
            if current_image_path:
                old_image_disk_path = os.path.join(app.static_folder, current_image_path)
                if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '':
            new_image_path = save_image_file(image_file, 'products', current_image_path=current_image_path)
        
        product["name"] = new_name if new_name else None
        product["short_description"] = short_desc_lines
        product["long_description"] = long_desc_lines
        product["use_short_desc_for_long"] = use_short_for_long
        product["image"] = new_image_path
        
        # If parent subcategory changed, update references
        if old_parent_subcat_slug != new_parent_subcat_slug:
            if old_parent_subcat_slug and old_parent_subcat_slug in DATA_STORE["subcategories"] and product_slug in DATA_STORE["subcategories"][old_parent_subcat_slug]["products"]:
                DATA_STORE["subcategories"][old_parent_subcat_slug]["products"].remove(product_slug)
            DATA_STORE["subcategories"][new_parent_subcat_slug]["products"].append(product_slug)
            product["parent_subcategory"] = new_parent_subcat_slug
        
        flash(f"Product '{new_name if new_name else product_slug}' updated successfully!", 'success')
        return redirect(url_for('admin.manage_products'))

    subcategories_for_select = []
    for sc_slug, sc_data in DATA_STORE["subcategories"].items():
        parent_cat_slug = sc_data.get("parent_category")
        parent_cat_name = DATA_STORE["categories"].get(parent_cat_slug, {}).get("name", parent_cat_slug)
        subcategories_for_select.append({
            "slug": sc_slug, 
            "name": f"{parent_cat_name} > {sc_data.get('name', sc_slug)}"
        })
    subcategories_for_select.sort(key=lambda x: x["name"])
    return render_template('product_form.html', form_action="Edit", product=product, 
                           product_slug=product_slug, subcategories=subcategories_for_select,
                           page_title=f"Edit Product")

@admin_bp.route('/products/delete/<product_slug>', methods=['POST'])
@login_required
def delete_product(product_slug):
    product = DATA_STORE["products"].get(product_slug)
    if product:
        parent_subcat_slug = product.get("parent_subcategory")
        if parent_subcat_slug and parent_subcat_slug in DATA_STORE["subcategories"]:
            if product_slug in DATA_STORE["subcategories"][parent_subcat_slug]["products"]:
                DATA_STORE["subcategories"][parent_subcat_slug]["products"].remove(product_slug)

        if product.get('image'):
            image_disk_path = os.path.join(app.static_folder, product['image'])
            if os.path.exists(image_disk_path): os.remove(image_disk_path)
        
        del DATA_STORE["products"][product_slug]
        flash(f"Product deleted successfully!", 'success')
    else:
        flash("Product not found.", "danger")
    return redirect(url_for('admin.manage_products'))

app.register_blueprint(admin_bp)

# --- Global Context Processor (Frontend) ---
@app.context_processor
def inject_global_vars():
    # ... (same as before) ...
    frontend_categories_list = []
    for slug, cat_data in DATA_STORE["categories"].items():
        if cat_data.get("name"):
            frontend_categories_list.append({
                "slug": slug,
                "name": cat_data.get("name"),
            })
    frontend_categories_list.sort(key=lambda x: x["name"])
    return dict(
        company_name=COMPANY_NAME,
        contact_info=COMPANY_CONTACT_INFO,
        nav_links=[
            {"name": "Home", "url": url_for('home_page', _anchor='home')},
            {"name": "About Us", "url": url_for('home_page', _anchor='about')},
            {"name": "Products", "url": url_for('list_categories')},
            {"name": "Contact", "url": url_for('contact_page')} # MODIFIED for new contact page
        ],
        frontend_categories_nav=frontend_categories_list,
        now=datetime.utcnow()
    )

# --- Frontend Routes ---
@app.route('/#<anchor>')
@app.route('/')
def home_page(anchor=None):
    # ... (same as before) ...
    carousel_slides = [
        {"image": "images/carousel/slide1.jpg", "alt": "High-quality PET Bottles", "caption_header": "Premium PET Solutions", "caption_text": "Discover our range of durable and versatile PET bottles."},
        {"image": "images/carousel/slide2.jpg", "alt": "Customizable Bottle Designs", "caption_header": "Your Brand, Your Bottle", "caption_text": "Custom designs to make your product stand out."},
        {"image": "images/carousel/slide3.jpg", "alt": "Eco-Friendly Options", "caption_header": "Sustainable Choices", "caption_text": "Explore our eco-friendly PET bottles made from recycled materials."}
    ]
    return render_template('index.html', carousel_slides=carousel_slides)


@app.route('/contact', methods=['GET', 'POST']) # NEW Contact Page
def contact_page():
    if request.method == 'POST':
        # Process form data (e.g., send email)
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        # Here you would typically send an email or save to a database
        print(f"Contact Form Submission: Name: {name}, Email: {email}, Phone: {phone}, Message: {message}")
        flash("Thank you for your message! We will get back to you soon.", "success")
        return redirect(url_for('contact_page')) # Redirect to clear form
        
    return render_template('contact.html', page_title="Contact Us")


@app.route('/products')
def list_categories():
    # ... (same as before) ...
    categories_to_display = []
    sorted_categories = sorted(DATA_STORE["categories"].items(), key=lambda item: item[1].get("name", item[0]))
    for slug, data in sorted_categories:
        categories_to_display.append({
            "slug": slug, "name": data.get("name"), 
            "image": data.get("image", "images/products/filler_product_1.jpg"),
            "description_lines": data.get("description", [])
        })
    return render_template('product_categories.html', categories=categories_to_display, page_title="Our Product Categories")

@app.route('/products/<category_slug>')
def list_subcategories(category_slug):
    # ... (same as before, ensure parent_category is checked when getting name) ...
    category = DATA_STORE["categories"].get(category_slug)
    if not category:
        flash("Category not found.", "warning"); return redirect(url_for('list_categories'))
    subcategories_to_display = []
    sorted_subcat_slugs = sorted(category.get("subcategories", []), key=lambda sc_slug: DATA_STORE["subcategories"].get(sc_slug, {}).get("name", sc_slug))
    for subcat_slug in sorted_subcat_slugs:
        subcat_data = DATA_STORE["subcategories"].get(subcat_slug)
        if subcat_data:
            subcategories_to_display.append({
                "slug": subcat_slug, "name": subcat_data.get("name"),
                "image": subcat_data.get("image", "images/products/filler_product_2.jpg"),
                "description_lines": subcat_data.get("description", [])
            })
    return render_template('product_subcategories.html',
                           category_name=category.get("name", category_slug),
                           category_slug=category_slug,
                           subcategories=subcategories_to_display,
                           page_title=f"Subcategories for {category.get('name', category_slug)}")


@app.route('/products/<category_slug>/<subcategory_slug>')
def list_products_in_subcategory(category_slug, subcategory_slug):
    # ... (same as before, ensure parent checks) ...
    subcategory = DATA_STORE["subcategories"].get(subcategory_slug)
    category = DATA_STORE["categories"].get(category_slug)
    if not subcategory or not category or subcategory.get("parent_category") != category_slug:
        flash("Subcategory or Category not found.", "warning"); return redirect(url_for('list_categories'))
    products_to_display = []
    sorted_prod_slugs = sorted(subcategory.get("products", []), key=lambda p_slug: DATA_STORE["products"].get(p_slug, {}).get("name", p_slug))
    for prod_slug in sorted_prod_slugs:
        prod_data = DATA_STORE["products"].get(prod_slug)
        if prod_data:
            products_to_display.append({
                "slug": prod_slug, "name": prod_data.get("name"),
                "image": prod_data.get("image", "images/products/filler_product_3.jpg"),
                "description_lines": prod_data.get("short_description", [])
            })
    return render_template('products_in_subcategory.html',
                           category_name=category.get("name", category_slug),
                           category_slug=category_slug,
                           subcategory_name=subcategory.get("name", subcategory_slug),
                           subcategory_slug=subcategory_slug,
                           products=products_to_display,
                           page_title=f"Products in {subcategory.get('name', subcategory_slug)}")

@app.route('/product/<product_slug>')
def view_product(product_slug):
    # Using the refined breadcrumb logic from previous fix
    product = DATA_STORE["products"].get(product_slug)
    if not product:
        flash("Product not found.", "warning"); return redirect(url_for('list_categories'))
    description_to_use = product.get("long_description", [])
    if product.get("use_short_desc_for_long", False) and product.get("short_description"):
        description_to_use = product.get("short_description")
    parent_subcategory_slug = product.get("parent_subcategory")
    parent_subcategory_data = None; parent_category_slug = None; parent_category_data = None
    if parent_subcategory_slug:
        parent_subcategory_data = DATA_STORE["subcategories"].get(parent_subcategory_slug)
        if parent_subcategory_data:
            parent_category_slug = parent_subcategory_data.get("parent_category")
            if parent_category_slug:
                parent_category_data = DATA_STORE["categories"].get(parent_category_slug)
    category_breadcrumb_part = None
    if parent_category_data and parent_category_slug:
        category_breadcrumb_part = {"name": parent_category_data.get("name"), "slug": parent_category_slug}
    subcategory_breadcrumb_part = None
    if parent_subcategory_data and parent_subcategory_slug:
        subcategory_breadcrumb_part = {"name": parent_subcategory_data.get("name"), "slug": parent_subcategory_slug}
    breadcrumb_data = {"category": category_breadcrumb_part, "subcategory": subcategory_breadcrumb_part}
    return render_template('product_detail.html', product=product, description_to_use=description_to_use,
                           breadcrumb_data=breadcrumb_data, page_title=product.get("name", "Product Details"))

# --- Error Handler ---
@app.errorhandler(404)
def page_not_found(e):
    # ... (same as before) ...
    if request.path.startswith('/admin/'):
        return render_template('404_admin.html', page_title="Page Not Found"), 404
    return render_template('404.html', page_title="Page Not Found"), 404

if __name__ == '__main__':
    app.run(debug=True)