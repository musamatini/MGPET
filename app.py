# app.py

      
from flask import (
    Flask, render_template, url_for, request, redirect, session, flash, Blueprint
)
from markupsafe import Markup

from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
import json
import markdown # <-- IMPORT MARKDOWN

app = Flask(__name__)
app.secret_key = "mg_pet_ultra_secret_key_v7_markdown!@#$"

# --- Configuration & Existing Helper Functions (UPLOAD_FOLDER, etc. - keep them) ---
UPLOAD_FOLDER = os.path.join(app.static_folder, 'images', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
def ensure_upload_dirs():
    paths = [UPLOAD_FOLDER, 
             os.path.join(UPLOAD_FOLDER, 'categories'), 
             os.path.join(UPLOAD_FOLDER, 'items'),
             os.path.join(UPLOAD_FOLDER, 'description_images') # <-- NEW FOLDER FOR DESC IMAGES
            ]
    for path in paths:
        if not os.path.exists(path): os.makedirs(path)
ensure_upload_dirs()

COMPANY_NAME = "MG PET"
# ... (COMPANY_CONTACT_INFO, COMPANY_LOCATIONS, COMPANY_GENERAL_CONTACT - keep these from your current app.py) ...
COMPANY_CONTACT_INFO = { "phone": "+1-234-567-8900", "email": "info@mgpet.com", "address": "123 Water Bottle Lane, Hydro City, HC 12345", "facebook_url": "https://facebook.com/mgpet", "instagram_url": "https://instagram.com/mgpet", "twitter_url": "https://twitter.com/mgpet"}
COMPANY_LOCATIONS = [ { "country": "Turkey", "flag": "🇹🇷", "address_lines": [ "Çelik mah. Megacenter sit no.12", "MERSIN/Turkiye" ], "phone": "+90 545 336 64 80", "map_query": "Çelik mahallesi, Şevket Sümer, 156. Cd. No:12, 33020 Akdeniz/Mersin, Turkey" }, { "country": "Syria", "flag": "🇸🇾", "address_lines": [ "Sheikh Najjar - Al-Naqarin Road", "Property No. 2784", "ALEPPO, SYRIA" ], "phone": "+963 962 244 750", "map_query": "Sheikh Najjar, Aleppo, Syria" }]
COMPANY_GENERAL_CONTACT = { "emails": [{"address": "info@mg-pet.com", "label": "General Inquiries"}, {"address": "sales@mg-pet.com", "label": "Sales Department"}], "social_media": [{"name": "Facebook", "url": "https://www.facebook.com/share/1Dvi9DwJ3A/", "icon_class": "fab fa-facebook-f"}, {"name": "Instagram", "url": "https://www.instagram.com/mgpet1?igsh=cHF3dGljaDFiNmho", "icon_class": "fab fa-instagram"}]}


DATA_FILE = 'datastore.json'
def load_data(): # ... (keep your existing load_data, ensure it handles new product structure) ...
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: data = json.load(f)
            data.setdefault("categories", {}); data.setdefault("items", {})
            data.setdefault("admin_users", {"admin": "password123"}) 
            return data
        except (json.JSONDecodeError, IOError) as e: print(f"Error loading data from {DATA_FILE}: {e}.")
    return { "categories": {}, "items": {}, "admin_users": { "admin": "password123" }}
def save_data(): # ... (keep your existing save_data) ...
    try:
        with open(DATA_FILE, 'w') as f: json.dump(DATA_STORE, f, indent=4)
    except IOError as e: print(f"Error saving data to {DATA_FILE}: {e}")
DATA_STORE = load_data()

# Helper functions: generate_slug, allowed_file, save_image_file (keep these)
def generate_slug(name, existing_slugs_keys=None, prefix="item"): # ... (same) ...
    if not name: base_slug = f"{prefix}-{uuid.uuid4().hex[:6]}" 
    else:
        base_slug = name.lower().strip().replace(' ', '-'); base_slug = "".join(c for c in base_slug if c.isalnum() or c == '-')
    if not base_slug: base_slug = f"{prefix}-{uuid.uuid4().hex[:6]}"
    if existing_slugs_keys is None: return base_slug
    slug = base_slug; counter = 1
    while slug in existing_slugs_keys: slug = f"{base_slug}-{counter}"; counter += 1
    return slug
def allowed_file(filename): # ... (same) ...
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def save_image_file(file, item_type_folder, current_image_path=None): # ... (same) ...
    if file and file.filename != '' and allowed_file(file.filename):
        if current_image_path:
            old_image_disk_path = os.path.join(app.static_folder, current_image_path)
            if os.path.exists(old_image_disk_path):
                try: os.remove(old_image_disk_path)
                except OSError as e: flash(f"Error deleting old image {current_image_path}: {e}", "danger")
        filename = secure_filename(file.filename); name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        target_subfolder_disk = os.path.join(app.config['UPLOAD_FOLDER'], item_type_folder)
        if not os.path.exists(target_subfolder_disk): os.makedirs(target_subfolder_disk)
        disk_save_path = os.path.join(target_subfolder_disk, unique_filename); file.save(disk_save_path)
        return os.path.join('images/uploads', item_type_folder, unique_filename).replace("\\", "/") # Web path
    if current_image_path: return current_image_path
    return None


# --- Admin Blueprint ---
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates/admin')
from functools import wraps
def login_required(f): # ... (same) ...
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
# ... (admin_home_redirect, login, logout routes - keep these) ...
@admin_bp.route('/')
@login_required
def admin_home_redirect(): return redirect(url_for('admin.manage_categories'))
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_logged_in' in session: return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        username = request.form.get('username'); password = request.form.get('password')
        if username in DATA_STORE['admin_users'] and DATA_STORE['admin_users'][username] == password:
            session['admin_logged_in'] = True; session['admin_username'] = username
            flash('Login successful!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('admin.manage_categories'))
        else: flash('Invalid username or password.', 'danger')
    return render_template('login.html', page_title="Admin Login")
@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None); session.pop('admin_username', None)
    flash('You have been logged out.', 'info'); return redirect(url_for('admin.login'))

# --- Category Management Routes (keep these, they interact with DATA_STORE["categories"]) ---
# ... (manage_categories, add_category, edit_category, delete_category) ...
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
        slug = generate_slug(name, DATA_STORE["categories"].keys(), prefix="cat")
        image_path = save_image_file(image_file, 'categories') if image_file and image_file.filename else None
        DATA_STORE["categories"][slug] = { "name": name if name else None, "description": description_lines, "image": image_path, "children_item_slugs": []}
        save_data(); flash(f"Category '{name if name else slug}' added successfully!", 'success')
        return redirect(url_for('admin.manage_categories'))
    return render_template('category_form.html', form_action="Add", page_title="Add New Category", category=None)
@admin_bp.route('/categories/edit/<category_slug>', methods=['GET', 'POST'])
@login_required
def edit_category(category_slug):
    category = DATA_STORE["categories"].get(category_slug)
    if not category: flash("Category not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip(); description_lines = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
        image_file = request.files.get('image'); remove_image = request.form.get('remove_image') == 'on'
        current_image_path = category.get('image'); new_image_path = current_image_path
        if remove_image:
            if current_image_path:
                old_image_disk_path = os.path.join(app.static_folder, current_image_path)
                if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '': new_image_path = save_image_file(image_file, 'categories', current_image_path=current_image_path)
        category["name"] = new_name if new_name else None; category["description"] = description_lines; category["image"] = new_image_path
        save_data(); flash(f"Category updated successfully!", 'success'); return redirect(url_for('admin.manage_categories'))
    return render_template('category_form.html', form_action="Edit", category=category, category_slug=category_slug, page_title=f"Edit Category")
@admin_bp.route('/categories/delete/<category_slug>', methods=['POST'])
@login_required
def delete_category(category_slug):
    category = DATA_STORE["categories"].get(category_slug)
    if category:
        if category.get("children_item_slugs"):
            flash(f"Cannot delete category: it has child items. Delete them first.", "danger"); return redirect(url_for('admin.manage_categories'))
        if category.get('image'):
            image_disk_path = os.path.join(app.static_folder, category['image'])
            if os.path.exists(image_disk_path): os.remove(image_disk_path)
        del DATA_STORE["categories"][category_slug]
        save_data(); flash(f"Category deleted successfully!", 'success')
    else: flash("Category not found.", "danger")
    return redirect(url_for('admin.manage_categories'))

# Admin views for children of a category or subcategory (view_category_children_admin, view_item_children_admin - keep these)
@admin_bp.route('/categories/<category_slug>/items')
@login_required
def view_category_children_admin(category_slug): # ... (same)
    category = DATA_STORE["categories"].get(category_slug)
    if not category: flash("Category not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    child_items_list = []
    for item_slug in category.get("children_item_slugs", []):
        item_data = DATA_STORE["items"].get(item_slug)
        if item_data: child_items_list.append({"slug": item_slug, **item_data})
    child_items_list.sort(key=lambda x: (x.get("type", ""), x.get("name", x["slug"])))
    parent_context = {"type": "category", "slug": category_slug, "name": category.get("name", category_slug)}
    breadcrumb_path = [{"name": category.get("name", category_slug), "url": None}]
    return render_template('manage_items_under_parent.html', items=child_items_list, parent_name=category.get("name", category_slug), parent_type_display="Category", parent_context=parent_context, parent_path=breadcrumb_path, page_title=f"Items in Category: {category.get('name', category_slug)}")

@admin_bp.route('/items/<parent_item_slug>/children')
@login_required
def view_item_children_admin(parent_item_slug): # ... (same)
    parent_item = DATA_STORE["items"].get(parent_item_slug)
    if not parent_item or parent_item.get("type") != "subcategory":
        flash("Parent item not found or is not a subcategory.", "danger")
        grandparent_type = parent_item.get("parent_type") if parent_item else None; grandparent_slug = parent_item.get("parent_slug") if parent_item else None
        if grandparent_type == 'category' and grandparent_slug: return redirect(url_for('admin.view_category_children_admin', category_slug=grandparent_slug))
        return redirect(url_for('admin.manage_categories'))
    child_items_list = []
    for item_slug in parent_item.get("children_item_slugs", []):
        item_data = DATA_STORE["items"].get(item_slug)
        if item_data: child_items_list.append({"slug": item_slug, **item_data})
    child_items_list.sort(key=lambda x: (x.get("type", ""), x.get("name", x["slug"])))
    parent_context = {"type": "item", "slug": parent_item_slug, "name": parent_item.get("name", parent_item_slug)}
    breadcrumb_path = []; current_trace_slug = parent_item_slug; current_trace_item = parent_item; temp_path_for_display = []
    while current_trace_item:
        is_current_parent = (current_trace_slug == parent_item_slug)
        temp_path_for_display.insert(0, { "name": current_trace_item.get("name", current_trace_slug), "url": None if is_current_parent else (url_for('admin.view_item_children_admin', parent_item_slug=current_trace_slug) if current_trace_item.get("type") == "subcategory" else None)})
        pt = current_trace_item.get("parent_type"); ps = current_trace_item.get("parent_slug")
        if pt == "category":
            cat_data = DATA_STORE["categories"].get(ps,{})
            temp_path_for_display.insert(0, {"name": cat_data.get("name", ps), "url": url_for('admin.view_category_children_admin', category_slug=ps)})
            break
        elif pt == "item": current_trace_slug = ps; current_trace_item = DATA_STORE["items"].get(current_trace_slug)
        else: break
    breadcrumb_path = temp_path_for_display
    return render_template('manage_items_under_parent.html', items=child_items_list, parent_name=parent_item.get("name", parent_item_slug), parent_type_display="Subcategory", parent_context=parent_context, parent_path=breadcrumb_path, page_title=f"Items in Subcategory: {parent_item.get('name', parent_item_slug)}")

def get_possible_parents_for_item(editing_item_slug=None): # ... (same)
    parents = []
    for cat_slug, cat_data in DATA_STORE["categories"].items():
        parents.append({ "slug": cat_slug, "name": f"Category: {cat_data.get('name', cat_slug)}", "type": "category", "full_slug_id": f"category:{cat_slug}"})
    for item_slug, item_data in DATA_STORE["items"].items():
        if item_slug == editing_item_slug: continue
        if item_data.get('type') == 'subcategory':
            path_name_parts = []; current_parent_for_path_slug = item_slug; current_parent_for_path_data = item_data
            depth_count = 0; max_depth = 10 
            while current_parent_for_path_data and depth_count < max_depth:
                path_name_parts.insert(0, current_parent_for_path_data.get('name', current_parent_for_path_slug))
                pt = current_parent_for_path_data.get('parent_type'); ps = current_parent_for_path_data.get('parent_slug')
                if pt == 'category':
                    top_cat_data = DATA_STORE["categories"].get(ps, {})
                    path_name_parts.insert(0, f"Category: {top_cat_data.get('name', ps)}")
                    break
                elif pt == 'item': current_parent_for_path_slug = ps; current_parent_for_path_data = DATA_STORE["items"].get(ps)
                else: break
                depth_count += 1
            parents.append({ "slug": item_slug, "name": f"SubCat: {' > '.join(path_name_parts)}", "type": "item", "full_slug_id": f"item:{item_slug}"})
    parents.sort(key=lambda x: x["name"])
    return parents

# --- Item Add/Edit/Delete ---
@admin_bp.route('/items/add/new', methods=['GET', 'POST'])
@login_required
def add_item():
    pre_selected_item_type = request.args.get('item_type')
    parent_type_from_url = request.args.get('parent_type')
    parent_slug_from_url = request.args.get('parent_slug')
    pre_selected_parent_full_slug = f"{parent_type_from_url}:{parent_slug_from_url}" if parent_type_from_url and parent_slug_from_url else None

    if request.method == 'POST':
        item_type = request.form.get('item_type', pre_selected_item_type)
        if not item_type: flash("Item type is missing.", "danger"); return redirect(request.url)
        
        name = request.form.get('name', '').strip()
        parent_full_slug_from_form = request.form.get('parent_full_slug')
        image_file = request.files.get('image')
        image_path = save_image_file(image_file, 'items') if image_file and image_file.filename else None

        if not parent_full_slug_from_form or ':' not in parent_full_slug_from_form:
            flash("Invalid parent selection from form.", "danger"); return redirect(request.url)
        parent_type, parent_slug = parent_full_slug_from_form.split(':', 1)
        
        # ... (validation for parent and child type consistency - same as before) ...
        parent_valid = False
        if parent_type == "category" and parent_slug in DATA_STORE["categories"]: parent_valid = True
        elif parent_type == "item" and parent_slug in DATA_STORE["items"] and DATA_STORE["items"][parent_slug].get('type') == 'subcategory': parent_valid = True
        if not parent_valid: flash("Selected parent is invalid or not found.", "danger"); return redirect(request.url)
        if parent_type == "item": 
            parent_item_data = DATA_STORE["items"][parent_slug]
            if parent_item_data.get("children_item_slugs"):
                first_child_slug = parent_item_data["children_item_slugs"][0]
                first_child_type = DATA_STORE["items"].get(first_child_slug, {}).get("type")
                if first_child_type and first_child_type != item_type: flash(f"Parent subcategory already contains items of type '{first_child_type}'. Cannot add a '{item_type}'.", "danger"); return redirect(request.url)

        slug = generate_slug(name, DATA_STORE["items"].keys(), prefix=item_type[:4])
        item_data = { "type": item_type, "name": name if name else None, "parent_type": parent_type, "parent_slug": parent_slug, "image": image_path }

        if item_type == 'subcategory':
            item_data["description"] = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
            item_data["children_item_slugs"] = []
        elif item_type == 'product':
            item_data["short_description"] = [line.strip() for line in request.form.getlist('short_description[]') if line.strip()]
            # For long_description, now it's a single Markdown string
            item_data["long_description_markdown"] = request.form.get('long_description_markdown', '').strip() # <-- NEW
            item_data["use_short_desc_for_long"] = request.form.get('use_short_desc_for_long') == 'on'
        
        DATA_STORE["items"][slug] = item_data
        if parent_type == "category": DATA_STORE["categories"][parent_slug]["children_item_slugs"].append(slug)
        elif parent_type == "item": DATA_STORE["items"][parent_slug]["children_item_slugs"].append(slug)
        
        save_data()
        flash(f"{item_type.capitalize()} '{name if name else slug}' added successfully!", 'success')
        if parent_type == "category": return redirect(url_for('admin.view_category_children_admin', category_slug=parent_slug))
        elif parent_type == "item": return redirect(url_for('admin.view_item_children_admin', parent_item_slug=parent_slug))
        return redirect(url_for('admin.manage_categories'))
    
    parents_for_select = get_possible_parents_for_item()
    return render_template('item_form.html', form_action="Add", parents=parents_for_select, 
                           page_title=f"Add New {pre_selected_item_type.capitalize() if pre_selected_item_type else 'Item'}", 
                           item=None, pre_selected_item_type=pre_selected_item_type,
                           pre_selected_parent_full_slug=pre_selected_parent_full_slug)

@admin_bp.route('/items/edit/<item_slug>', methods=['GET', 'POST'])
@login_required
def edit_item(item_slug):
    item = DATA_STORE["items"].get(item_slug)
    if not item: flash("Item not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    
    if request.method == 'POST':
        item_type = item.get('type') # Type cannot be changed on edit
        # ... (logic for name, parent, image - same as before) ...
        old_parent_type = item.get('parent_type'); old_parent_slug = item.get('parent_slug')
        new_parent_full_slug = request.form.get('parent_full_slug'); new_name = request.form.get('name', '').strip()
        image_file = request.files.get('image'); remove_image = request.form.get('remove_image') == 'on'
        current_image_path = item.get('image'); new_image_path = current_image_path
        if not new_parent_full_slug or ':' not in new_parent_full_slug: flash("Invalid parent selection.", "danger"); return redirect(url_for('admin.edit_item', item_slug=item_slug))
        new_parent_type, new_parent_slug = new_parent_full_slug.split(':', 1); parent_valid = False
        if new_parent_type == "category" and new_parent_slug in DATA_STORE["categories"]: parent_valid = True
        elif new_parent_type == "item" and new_parent_slug in DATA_STORE["items"] and DATA_STORE["items"][new_parent_slug].get('type') == 'subcategory': parent_valid = True
        if not parent_valid: flash("Selected parent is invalid or not found.", "danger"); return redirect(url_for('admin.edit_item', item_slug=item_slug))
        if new_parent_slug == item_slug and new_parent_type == 'item': flash("An item cannot be its own parent.", "danger"); return redirect(url_for('admin.edit_item', item_slug=item_slug))
        if new_parent_type == "item" and (new_parent_type != old_parent_type or new_parent_slug != old_parent_slug):
            parent_item_data = DATA_STORE["items"][new_parent_slug]
            if parent_item_data.get("children_item_slugs"):
                existing_children_of_new_parent = [s for s in parent_item_data.get("children_item_slugs", []) if s != item_slug]
                if existing_children_of_new_parent:
                    first_child_slug_of_new_parent = existing_children_of_new_parent[0]
                    first_child_type_of_new_parent = DATA_STORE["items"].get(first_child_slug_of_new_parent, {}).get("type")
                    if first_child_type_of_new_parent and first_child_type_of_new_parent != item_type: flash(f"New parent subcategory already contains items of type '{first_child_type_of_new_parent}'.", "danger"); return redirect(url_for('admin.edit_item', item_slug=item_slug))
        if remove_image:
            if current_image_path:
                old_image_disk_path = os.path.join(app.static_folder, current_image_path)
                if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '': new_image_path = save_image_file(image_file, 'items', current_image_path=current_image_path)
        
        item["name"] = new_name if new_name else None
        item["image"] = new_image_path

        if item_type == 'subcategory':
            item["description"] = [line.strip() for line in request.form.getlist('description[]') if line.strip()]
        elif item_type == 'product':
            item["short_description"] = [line.strip() for line in request.form.getlist('short_description[]') if line.strip()]
            item["long_description_markdown"] = request.form.get('long_description_markdown', '').strip() # <-- NEW
            item["use_short_desc_for_long"] = request.form.get('use_short_desc_for_long') == 'on'
        
        # ... (parent change logic - same as before) ...
        if old_parent_type != new_parent_type or old_parent_slug != new_parent_slug:
            if old_parent_type == "category" and old_parent_slug in DATA_STORE["categories"]:
                if item_slug in DATA_STORE["categories"][old_parent_slug]["children_item_slugs"]: DATA_STORE["categories"][old_parent_slug]["children_item_slugs"].remove(item_slug)
            elif old_parent_type == "item" and old_parent_slug in DATA_STORE["items"]:
                 if item_slug in DATA_STORE["items"][old_parent_slug].get("children_item_slugs", []): DATA_STORE["items"][old_parent_slug]["children_item_slugs"].remove(item_slug)
            if new_parent_type == "category": DATA_STORE["categories"][new_parent_slug]["children_item_slugs"].append(item_slug)
            elif new_parent_type == "item": DATA_STORE["items"][new_parent_slug]["children_item_slugs"].append(item_slug)
            item["parent_type"] = new_parent_type; item["parent_slug"] = new_parent_slug
        
        save_data()
        flash(f"{item_type.capitalize()} updated successfully!", 'success')
        # ... (redirect logic - same as before) ...
        if item["parent_type"] == "category": return redirect(url_for('admin.view_category_children_admin', category_slug=item["parent_slug"]))
        elif item["parent_type"] == "item": return redirect(url_for('admin.view_item_children_admin', parent_item_slug=item["parent_slug"]))
        return redirect(url_for('admin.manage_categories'))

    parents_for_select = get_possible_parents_for_item(editing_item_slug=item_slug)
    current_parent_full_slug = f"{item.get('parent_type')}:{item.get('parent_slug')}"
    return render_template('item_form.html', form_action="Edit", item=item, item_slug=item_slug, 
                           parents=parents_for_select, current_parent_full_slug=current_parent_full_slug,
                           page_title=f"Edit {item.get('type', 'Item').capitalize()}")

@admin_bp.route('/items/delete/<item_slug>', methods=['POST'])
@login_required
def delete_item(item_slug): # ... (same logic, ensure save_data() is called) ...
    item = DATA_STORE["items"].get(item_slug)
    redirect_url = url_for('admin.manage_categories')
    if item:
        item_type = item.get("type"); parent_type = item.get("parent_type"); parent_slug = item.get("parent_slug")
        if parent_type == "category" and parent_slug: redirect_url = url_for('admin.view_category_children_admin', category_slug=parent_slug)
        elif parent_type == "item" and parent_slug: redirect_url = url_for('admin.view_item_children_admin', parent_item_slug=parent_slug)
        if item_type == 'subcategory' and item.get("children_item_slugs"): flash(f"Cannot delete subcategory: it has child items. Delete them first.", "danger"); return redirect(redirect_url)
        if parent_type == "category" and parent_slug in DATA_STORE["categories"]:
            if item_slug in DATA_STORE["categories"][parent_slug]["children_item_slugs"]: DATA_STORE["categories"][parent_slug]["children_item_slugs"].remove(item_slug)
        elif parent_type == "item" and parent_slug in DATA_STORE["items"]:
            if item_slug in DATA_STORE["items"][parent_slug].get("children_item_slugs", []): DATA_STORE["items"][parent_slug]["children_item_slugs"].remove(item_slug)
        if item.get('image'):
            image_disk_path = os.path.join(app.static_folder, item['image'])
            if os.path.exists(image_disk_path): os.remove(image_disk_path)
        del DATA_STORE["items"][item_slug]
        save_data(); flash(f"{item_type.capitalize()} deleted successfully!", 'success')
    else: flash("Item not found.", "danger")
    return redirect(redirect_url)

# Admin route for uploading images to be used in descriptions
@admin_bp.route('/upload-description-image', methods=['POST'])
@login_required
def upload_description_image():
    if 'description_image' not in request.files:
        return json.dumps({'error': 'No file part'}), 400, {'ContentType':'application/json'}
    file = request.files['description_image']
    if file.filename == '':
        return json.dumps({'error': 'No selected file'}), 400, {'ContentType':'application/json'}
    if file and allowed_file(file.filename):
        image_path_web = save_image_file(file, 'description_images')
        if image_path_web:
            full_url = url_for('static', filename=image_path_web, _external=True)
            return json.dumps({'imageUrl': full_url}), 200, {'ContentType':'application/json'}
        else:
            return json.dumps({'error': 'File upload failed'}), 500, {'ContentType':'application/json'}
    return json.dumps({'error': 'File type not allowed'}), 400, {'ContentType':'application/json'}

app.register_blueprint(admin_bp)

# --- Global Context Processor & Frontend Routes ---
@app.context_processor
def inject_global_vars(): # ... (same, ensure COMPANY_LOCATIONS, COMPANY_GENERAL_CONTACT are passed) ...
    frontend_categories_list = []
    sorted_cats = sorted(DATA_STORE["categories"].items(), key=lambda x: x[1].get("name", x[0]))
    for slug, cat_data in sorted_cats:
        if cat_data.get("name"): frontend_categories_list.append({ "slug": slug, "name": cat_data.get("name") })
    return dict(company_name=COMPANY_NAME, company_locations=COMPANY_LOCATIONS, company_general_contact=COMPANY_GENERAL_CONTACT,
        nav_links=[ {"name": "Home", "url": url_for('home_page', _anchor='home')}, {"name": "About Us", "url": url_for('home_page', _anchor='about')}, {"name": "Products", "url": url_for('list_top_level_categories')}, {"name": "Contact", "url": url_for('contact_page')}],
        frontend_categories_nav=frontend_categories_list, now=datetime.utcnow())

# ... (home_page, contact_page, list_top_level_categories, view_category_children - keep these) ...
@app.route('/#<anchor>')
@app.route('/')
def home_page(anchor=None):
    carousel_slides = [ {"image": "images/carousel/slide1.jpg", "alt": "High-quality PET Bottles", "caption_header": "MGPET for Premium PET Solutions", "caption_text": ""}, {"image": "images/carousel/slide2.jpg", "alt": "Customizable Bottle Designs", "caption_header": "It starts with MG PET and ends with trust", "caption_text": ""}, {"image": "images/carousel/slide3.jpg", "alt": "Eco-Friendly Options", "caption_header": "MG PET is your partner for success and excellence", "caption_text": ""}]
    return render_template('index.html', carousel_slides=carousel_slides)
@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        name = request.form.get('name'); email = request.form.get('email'); phone = request.form.get('phone'); message = request.form.get('message')
        # print(f"Contact Form: Name: {name}, Email: {email}, Phone: {phone}, Message: {message}") # DEBUG
        flash("Thank you for your message! We will get back to you soon.", "success"); return redirect(url_for('contact_page'))
    return render_template('contact.html', page_title="Contact Us")

# app.py

@app.route('/products') 
def list_top_level_categories():
    # print("--- DEBUG: list_top_level_categories ---") # DEBUG
    categories_to_display = []
    # Sort categories by name for display
    sorted_categories = sorted(DATA_STORE["categories"].items(), key=lambda item: item[1].get("name", item[0]))

    for slug, data in sorted_categories:
        categories_to_display.append({ 
            "slug": slug, 
            "name": data.get("name"), 
            "image": data.get("image", "images/uploads/categories/default_cat.jpg"), # Default if no image
            "description_lines": data.get("description", []) 
        })
    
    breadcrumb = [
        {"name": "Products", "url": None} # Current page is active
    ]
    # print(f"Categories to display: {json.dumps(categories_to_display, indent=2)}") # DEBUG
    
    return render_template('product_categories_list.html', 
                           items=categories_to_display, 
                           page_title="Our Product Categories",
                           breadcrumb=breadcrumb)

@app.route('/products/category/<category_slug>')
def view_category_children(category_slug):
    # print(f"--- DEBUG: view_category_children for {category_slug} ---") # DEBUG
    category = DATA_STORE["categories"].get(category_slug)
    if not category: 
        flash("Category not found.", "warning")
        return redirect(url_for('list_top_level_categories'))
    
    # print(f"Category data: {json.dumps(category, indent=2)}") # DEBUG
    children_to_display = []
    # Sort children by name
    sorted_child_slugs = sorted(category.get("children_item_slugs", []), 
                                key=lambda item_slug: DATA_STORE["items"].get(item_slug, {}).get("name", item_slug))
    # print(f"Child slugs for category {category_slug}: {sorted_child_slugs}") # DEBUG
    
    for item_slug in sorted_child_slugs:
        item_data = DATA_STORE["items"].get(item_slug)
        if item_data: 
            # print(f"  Processing child item {item_slug}: {json.dumps(item_data, indent=2)}") # DEBUG
            desc_lines_for_child = []
            if item_data.get("type") == "subcategory":
                desc_lines_for_child = item_data.get("description", [])
            elif item_data.get("type") == "product":
                desc_lines_for_child = item_data.get("short_description", [])
            
            children_to_display.append({ 
                "slug": item_slug, 
                "type": item_data.get("type"), 
                "name": item_data.get("name"), 
                "image": item_data.get("image", "images/uploads/items/default_item.jpg"), 
                "description_lines": desc_lines_for_child
            })
        else:
            print(f"  WARNING: Child slug '{child_slug}' not found in DATA_STORE['items'] for parent category '{category_slug}'") # DEBUG
    
    # print(f"Children to display for category {category_slug}: {json.dumps(children_to_display, indent=2)}") # DEBUG
    
    # Breadcrumb: Products > Category Name (active)
    breadcrumb = [
        {"name": "Products", "url": url_for('list_top_level_categories')},
        {"name": category.get("name", category_slug), "url": None} # Current page active
    ]
    # print(f"Breadcrumb for {category_slug} children: {json.dumps(breadcrumb, indent=2)}") # DEBUG
    
    return render_template('product_item_list.html', 
                           parent_name=category.get("name", category_slug),
                           parent_type_display="Category", 
                           items=children_to_display, 
                           page_title=f"Items in {category.get('name', category_slug)}",
                           breadcrumb=breadcrumb)

# app.py
# Ensure you have: from markupsafe import Markup
# Ensure you have: import markdown

@app.route('/products/item/<item_slug>')
def view_item_or_children(item_slug):
    # print(f"--- DEBUG: view_item_or_children for item_slug: {item_slug} ---") # DEBUG
    item = DATA_STORE["items"].get(item_slug)
    if not item: 
        flash("Item not found.", "warning")
        # print(f"Item '{item_slug}' not found in DATA_STORE['items'].") # DEBUG
        return redirect(url_for('list_top_level_categories'))
    
    # print(f"Item data for {item_slug}: {json.dumps(item, indent=2)}") # DEBUG
    
    # --- Construct Dynamic Breadcrumb ---
    # Starts with "Products" linking to the top-level category list
    breadcrumb = [{"name": "Products", "url": url_for('list_top_level_categories')}]
    
    path_from_category = [] # This will store items from the top-level category down to the current item's direct parent
    
    # Temporarily store the current item's details to add at the very end if it's the active page
    current_item_breadcrumb_segment = {"name": item.get("name", item_slug), "url": None}

    # Trace parents upwards from the current item
    parent_type = item.get("parent_type")
    parent_slug = item.get("parent_slug")
    
    # Iteratively build the path from the current item upwards to its top-level category
    # This loop collects the parent segments for the breadcrumb path
    temp_path_segments = [] # Store segments in reverse order while tracing up
    
    # Start with the current item if it's a subcategory that will list children
    # If current item is a product, its name will be the last (active) segment.
    # If current item is a subcategory whose children are being viewed, its name is the last active segment.
    
    # Let's simplify: trace all parents up to the category
    # The current item (item_slug) will be the last "active" element in the breadcrumb
    
    temp_parent_type = parent_type
    temp_parent_slug = parent_slug
    
    while temp_parent_slug: # Loop as long as there's a parent slug
        if temp_parent_type == "category":
            category_data = DATA_STORE["categories"].get(temp_parent_slug, {})
            path_from_category.insert(0, {
                "name": category_data.get("name", temp_parent_slug),
                "url": url_for('view_category_children', category_slug=temp_parent_slug)
            })
            break # Reached the top-level category
        elif temp_parent_type == "item": # Parent is another subcategory
            parent_item_data = DATA_STORE["items"].get(temp_parent_slug)
            if not parent_item_data: break # Should not happen with consistent data
            path_from_category.insert(0, {
                "name": parent_item_data.get("name", temp_parent_slug),
                # This item in the breadcrumb (a parent subcategory) should link to its own children view
                "url": url_for('view_item_or_children', item_slug=temp_parent_slug) 
            })
            # Move to the next parent up
            temp_parent_type = parent_item_data.get("parent_type")
            temp_parent_slug = parent_item_data.get("parent_slug")
        else: # Should not happen
            break
            
    breadcrumb.extend(path_from_category) # Add the traced path
    breadcrumb.append(current_item_breadcrumb_segment) # Add the current item as active

    # print(f"Breadcrumb for {item_slug}: {json.dumps(breadcrumb, indent=2)}") # DEBUG

    if item.get("type") == "subcategory":
        # print(f"Item '{item_slug}' is a SUBCATEGORY. Looking for its children.") # DEBUG
        children_to_display = []
        sorted_child_slugs = sorted(item.get("children_item_slugs", []), 
                                    key=lambda child_slug: DATA_STORE["items"].get(child_slug, {}).get("name", child_slug))
        # print(f"Child slugs for subcategory '{item_slug}': {sorted_child_slugs}") # DEBUG
        
        for child_slug in sorted_child_slugs:
            child_data = DATA_STORE["items"].get(child_slug)
            if child_data: 
                # print(f"  Processing child item '{child_slug}' of subcategory: {json.dumps(child_data, indent=2)}") # DEBUG
                desc_lines_for_child = []
                if child_data.get("type") == "subcategory":
                    desc_lines_for_child = child_data.get("description", [])
                elif child_data.get("type") == "product":
                    desc_lines_for_child = child_data.get("short_description", [])
                
                children_to_display.append({ 
                    "slug": child_slug, "type": child_data.get("type"), "name": child_data.get("name"), 
                    "image": child_data.get("image", "images/uploads/items/default_item.jpg"), 
                    "description_lines": desc_lines_for_child
                })
            else:
                print(f"  WARNING: Child slug '{child_slug}' not found in DATA_STORE['items'] for parent '{item_slug}'") # DEBUG
        
        # print(f"Children to display for subcategory '{item_slug}': {json.dumps(children_to_display, indent=2)}") # DEBUG
        return render_template('product_item_list.html', 
                               parent_name=item.get("name", item_slug),
                               parent_type_display="Subcategory", 
                               items=children_to_display, 
                               page_title=f"Items in {item.get('name', item_slug)}",
                               breadcrumb=breadcrumb)
    
    elif item.get("type") == "product":
        # print(f"Item '{item_slug}' is a PRODUCT. Displaying product detail.") # DEBUG
        long_desc_markdown = item.get("long_description_markdown", "")
        if item.get("use_short_desc_for_long", False) and item.get("short_description"):
            long_desc_markdown = "\n\n".join(item.get("short_description", []))
        
        # Ensure markdown library is imported: import markdown
        # Ensure Markup is imported: from markupsafe import Markup
        html_description = Markup(markdown.markdown(long_desc_markdown, extensions=['attr_list', 'tables', 'fenced_code', 'nl2br']))
        
        return render_template('product_detail_page.html', 
                               product=item, 
                               product_slug=item_slug, 
                               html_description=html_description,
                               page_title=item.get("name", "Product Details"),
                               breadcrumb=breadcrumb)
    else: 
        flash("Unknown item type.", "danger")
        # print(f"Unknown item type for '{item_slug}': {item.get('type')}") # DEBUG
        return redirect(url_for('list_top_level_categories'))

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/admin/'): return render_template('404_admin.html', page_title="Page Not Found"), 404
    return render_template('404.html', page_title="Page Not Found"), 404

if __name__ == '__main__':
    # Sample data is removed, app will load from datastore.json or start empty
    print("--- Initial DATA_STORE (Loaded or Default) ---")
    print("Categories:", json.dumps(DATA_STORE["categories"], indent=2))
    print("Items:", json.dumps(DATA_STORE["items"], indent=2))
    print("----------------------------------------------")
    app.run(debug=True)