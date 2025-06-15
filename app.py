# app.py

from flask import (
    Flask, render_template, url_for, request, redirect, session, flash, Blueprint, g, jsonify, send_file
)
from markupsafe import Markup 
import markdown 
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
import json
import zipfile
import io 

app = Flask(__name__)
app.secret_key = "mg_pet_multilingual_COMPLETE_secret_key_v1!@#$"

# --- Language Configuration ---
LANGUAGES = ['en', 'ar']
DEFAULT_LANGUAGE = 'en'
app.config['LANGUAGES'] = LANGUAGES
app.config['DEFAULT_LANGUAGE'] = DEFAULT_LANGUAGE

# --- Configuration & Basic Setup ---
UPLOAD_FOLDER = os.path.join(app.static_folder, 'images', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
def ensure_upload_dirs():
    paths = [UPLOAD_FOLDER, os.path.join(UPLOAD_FOLDER, 'categories'), os.path.join(UPLOAD_FOLDER, 'items'), os.path.join(UPLOAD_FOLDER, 'description_images')]
    for path in paths:
        if not os.path.exists(path): os.makedirs(path)
ensure_upload_dirs()

COMPANY_NAME = "MG PET" 
# Assuming COMPANY_LOCATIONS and COMPANY_GENERAL_CONTACT are already multilingual if needed, or we translate them in context_processor
COMPANY_LOCATIONS = [
    {
        "country": {"en": "Turkey", "ar": "تركيا"},
        "flag": "🇹🇷",
        "address_lines": {
            "en": ["Çelik mah. Megacenter sit no.12", "MERSIN/Turkiye"],
            "ar": ["تشيليك مح. ميغاسنتر سيت رقم 12", "مرسين/تركيا"]
        },
        "phone": "+90 545 336 64 80",
        "map_query": "Çelik mahallesi, Şevket Sümer, 156. Cd. No:12, 33020 Akdeniz/Mersin, Turkey"
    },
    {
        "country": {"en": "Syria", "ar": "سوريا"},
        "flag": "🇸🇾",
        "address_lines": {
            "en": ["Sheikh Najjar - Al-Naqarin Road", "Property No. 2784", "ALEPPO, SYRIA"],
            "ar": ["طريق الشيخ نجار - النقارين", "العقار رقم 2784", "حلب، سوريا"]
        },
        "phone": "+963 962 244 750",
        "map_query": "Sheikh Najjar, Aleppo, Syria"
    }
]
COMPANY_GENERAL_CONTACT = {
    "emails": [
        {"address": "info@mg-pet.com"},
        {"address": "sales@mg-pet.com"}
    ],
    "social_media": [
        {"name": "Facebook", "url": "https://www.facebook.com/share/1Dvi9DwJ3A/", "icon_class": "fab fa-facebook-f"},
        {"name": "Instagram", "url": "https://www.instagram.com/mgpet1?igsh=cHF3dGljaDFiNmho", "icon_class": "fab fa-instagram"}
    ]
}
def get_translated_text(text_dict, lang=None, fallback_key='en'):
    if not lang: lang = get_locale()
    if isinstance(text_dict, dict):
        # Prioritize current lang, then fallback_key, then first available lang, then empty string
        if lang in text_dict and text_dict[lang] is not None: return text_dict[lang]
        if fallback_key in text_dict and text_dict[fallback_key] is not None: return text_dict[fallback_key]
        for l_key in text_dict: # Check any key if specific ones are missing
            if text_dict[l_key] is not None: return text_dict[l_key]
        return "" # Ultimate fallback
    return str(text_dict) 

def get_translated_list(list_dict, lang=None, fallback_key='en'):
    if not lang: lang = get_locale()
    if isinstance(list_dict, dict):
        # Similar prioritization for lists
        if lang in list_dict and isinstance(list_dict[lang], list): return list_dict[lang]
        if fallback_key in list_dict and isinstance(list_dict[fallback_key], list): return list_dict[fallback_key]
        for l_key in list_dict:
            if isinstance(list_dict[l_key], list): return list_dict[l_key]
        return [] # Ultimate fallback
    return list_dict if isinstance(list_dict, list) else []

# --- Data Persistence ---
DATA_FILE = 'datastore.json'
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            data.setdefault("categories", {}); data.setdefault("items", {})
            data.setdefault("admin_users", {"admin": "password123"}) 
            return data
        except (json.JSONDecodeError, IOError) as e: print(f"Error loading data from {DATA_FILE}: {e}.")
    return { "categories": {}, "items": {}, "admin_users": { "admin": "password123" }}
def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(DATA_STORE, f, indent=4, ensure_ascii=False)
    except IOError as e: print(f"Error saving data to {DATA_FILE}: {e}")
DATA_STORE = load_data()

# --- Helper Functions ---
def generate_slug(name_dict, existing_slugs_keys=None, prefix="item", lang_priority=['en', 'ar']):
    base_name_for_slug = None
    for lang_code in lang_priority:
        if name_dict and isinstance(name_dict, dict) and name_dict.get(lang_code): # Check if name_dict is a dict
            base_name_for_slug = name_dict[lang_code]
            break
    if not base_name_for_slug and isinstance(name_dict, str): # Fallback if name_dict was a string
        base_name_for_slug = name_dict
    
    if not base_name_for_slug: base_slug = f"{prefix}-{uuid.uuid4().hex[:6]}" 
    else:
        base_slug = base_name_for_slug.lower().strip().replace(' ', '-'); base_slug = "".join(c for c in base_slug if c.isalnum() or c == '-')
    if not base_slug: base_slug = f"{prefix}-{uuid.uuid4().hex[:6]}"
    if existing_slugs_keys is None: return base_slug
    slug = base_slug; counter = 1
    while slug in existing_slugs_keys: slug = f"{base_slug}-{counter}"; counter += 1
    return slug
def allowed_file(filename): return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def save_image_file(file, item_type_folder, current_image_path=None):
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
        return os.path.join('images/uploads', item_type_folder, unique_filename).replace("\\", "/")
    if current_image_path: return current_image_path
    return None

# --- Language Selection & Helpers ---
@app.before_request
def before_request_language_handling():
    path_parts = request.path.split('/')
    lang_code_from_path = None
    if len(path_parts) > 1 and path_parts[1] in app.config['LANGUAGES']:
        lang_code_from_path = path_parts[1]

    if lang_code_from_path:
        g.lang_code = lang_code_from_path
        session['lang_code'] = lang_code_from_path
    elif 'lang_code' in session and session['lang_code'] in app.config['LANGUAGES']:
        g.lang_code = session['lang_code']
    else:
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES']) or app.config['DEFAULT_LANGUAGE']
        session['lang_code'] = g.lang_code
    
    # Redirect to language-prefixed URL if not already on one (for frontend routes)
    if not request.path.startswith(f"/{g.lang_code}/") and \
       request.endpoint and \
       request.endpoint not in ['static', 'admin.static'] and \
       not request.path.startswith('/admin'):
        # Only redirect if the current path doesn't already start with a valid lang code
        is_already_lang_prefixed = len(path_parts) > 1 and path_parts[1] in app.config['LANGUAGES']
        if not is_already_lang_prefixed and request.endpoint != 'root_redirect': # Avoid redirect loop from root
            view_args = request.view_args.copy() if request.view_args else {}
            view_args['lang_code'] = g.lang_code
            return redirect(url_for(request.endpoint, **view_args), code=302)

def get_locale(): 
    return g.get('lang_code', app.config['DEFAULT_LANGUAGE'])

def get_translated_text(text_dict, lang=None, fallback_key='en'):
    if not lang: lang = get_locale()
    if isinstance(text_dict, dict):
        # Prioritize current lang, then fallback_key, then first available lang, then empty string
        if lang in text_dict and text_dict[lang] is not None: return text_dict[lang]
        if fallback_key in text_dict and text_dict[fallback_key] is not None: return text_dict[fallback_key]
        for l_key in text_dict: # Check any key if specific ones are missing
            if text_dict[l_key] is not None: return text_dict[l_key]
        return "" # Ultimate fallback
    return str(text_dict) 

def get_translated_list(list_dict, lang=None, fallback_key='en'):
    if not lang: lang = get_locale()
    if isinstance(list_dict, dict):
        # Similar prioritization for lists
        if lang in list_dict and isinstance(list_dict[lang], list): return list_dict[lang]
        if fallback_key in list_dict and isinstance(list_dict[fallback_key], list): return list_dict[fallback_key]
        for l_key in list_dict:
            if isinstance(list_dict[l_key], list): return list_dict[l_key]
        return [] # Ultimate fallback
    return list_dict if isinstance(list_dict, list) else []


@app.context_processor
def inject_global_vars_and_lang():
    lang = get_locale() # Use the helper to get current language
    
    translated_nav_links = []
    raw_nav_links = [
        {"name": {"en": "Home", "ar": "الرئيسية"}, "endpoint": 'home_page', "anchor": "home"},
        {"name": {"en": "About Us", "ar": "من نحن"}, "endpoint": 'home_page', "anchor": "about"},
        {"name": {"en": "Products", "ar": "المنتجات"}, "endpoint": 'list_top_level_categories'},
        {"name": {"en": "Contact", "ar": "اتصل بنا"}, "endpoint": 'contact_page'}
    ]
    for link_data in raw_nav_links:
        url_args = {'lang_code': lang}
        if link_data.get("anchor"):
            url_args["_anchor"] = link_data["anchor"]
        
        translated_nav_links.append({
            "name": get_translated_text(link_data["name"], lang), # Use the helper
            "url": url_for(link_data["endpoint"], **url_args)
        })

    translated_frontend_categories_nav = []
    # Sort categories by translated name for the current language
    sorted_cats = sorted(
        DATA_STORE["categories"].items(), 
        key=lambda x: (get_translated_text(x[1].get("name"), lang) or x[0])
    )
    for slug, cat_data in sorted_cats:
        cat_name_translated = get_translated_text(cat_data.get("name"), lang)
        if cat_name_translated:
            translated_frontend_categories_nav.append({
                "slug": slug,
                "name": cat_name_translated,
                "url": url_for('view_category_children', lang_code=lang, category_slug=slug)
            })
            
    return dict(
        company_name=COMPANY_NAME, 
        company_locations=COMPANY_LOCATIONS, # These also need translation if their content is dicts
        company_general_contact=COMPANY_GENERAL_CONTACT, # And this
        nav_links=translated_nav_links,
        frontend_categories_nav=translated_frontend_categories_nav, 
        now=datetime.utcnow(),
        current_lang=lang, 
        languages=LANGUAGES, 
        get_translated_text=get_translated_text,   # <--- THIS LINE IS CRUCIAL
        get_translated_list=get_translated_list    # <--- AND THIS LINE
    )


# --- Admin Blueprint ---
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates/admin')
from functools import wraps
def login_required(f): # ... (same)
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning'); return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
@admin_bp.route('/')
@login_required
def admin_home_redirect(): return redirect(url_for('admin.manage_categories'))
@admin_bp.route('/login', methods=['GET', 'POST'])
def login(): # ... (same)
    if 'admin_logged_in' in session: return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        username = request.form.get('username'); password = request.form.get('password')
        if username in DATA_STORE['admin_users'] and DATA_STORE['admin_users'][username] == password:
            session['admin_logged_in'] = True; session['admin_username'] = username; flash('Login successful!', 'success')
            next_url = request.args.get('next'); return redirect(next_url or url_for('admin.manage_categories'))
        else: flash('Invalid username or password.', 'danger')
    return render_template('login.html', page_title="Admin Login")
@admin_bp.route('/logout')
def logout(): # ... (same)
    session.pop('admin_logged_in', None); session.pop('admin_username', None)
    flash('You have been logged out.', 'info'); return redirect(url_for('admin.login'))
@admin_bp.route('/download-backup') # Renamed route
@login_required
def download_backup():
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Add datastore.json
            if os.path.exists(DATA_FILE):
                zipf.write(DATA_FILE, arcname='datastore.json')
            else:
                app.logger.warning(f"'{DATA_FILE}' not found during backup creation. It will not be included in the zip.")
                # You could optionally add a placeholder text file in the zip
                # zipf.writestr('datastore_missing.txt', f"The file '{DATA_FILE}' was not found on the server at the time of backup.")


            # 2. Add UPLOAD_FOLDER contents
            upload_folder_path = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_folder_path) and os.path.isdir(upload_folder_path):
                # This will put files from UPLOAD_FOLDER into an 'uploads/' directory in the zip
                for root, _, files in os.walk(upload_folder_path):
                    for file in files:
                        file_path_on_disk = os.path.join(root, file)
                        # Create an archive name relative to the UPLOAD_FOLDER, then prepend 'uploads/'
                        relative_path_within_uploads_dir = os.path.relpath(file_path_on_disk, upload_folder_path)
                        arcname_in_zip = os.path.join('uploads', relative_path_within_uploads_dir)
                        zipf.write(file_path_on_disk, arcname=arcname_in_zip)
            else:
                app.logger.warning(f"Upload folder '{upload_folder_path}' not found or is not a directory. Images will not be included in the backup.")

        zip_buffer.seek(0) # Rewind buffer to the beginning before sending

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f'mg_pet_backup_{timestamp}.zip'

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/zip'
        )

    except FileNotFoundError as e: # Should be rare if DATA_FILE check is done above
        flash(f"Error creating backup: A required file was not found ({e}). Please check server logs.", "danger")
        app.logger.error(f"FileNotFoundError during backup creation: {e}")
        return redirect(url_for('admin.manage_categories')) # Or your preferred admin error page
    except Exception as e:
        flash(f"An unexpected error occurred while creating the backup: {str(e)}", "danger")
        app.logger.error(f"Exception during backup creation: {e}", exc_info=True) # Log full traceback
        return redirect(url_for('admin.manage_categories'))
# --- Category Management (Multilingual) ---
@admin_bp.route('/categories')
@login_required
def manage_categories():
    categories_display = []
    for slug, data in DATA_STORE["categories"].items():
        display_name = get_translated_text(data.get("name"), 'en') or slug
        categories_display.append({"slug": slug, "display_name": display_name, "children_count": len(data.get("children_item_slugs", [])), **data})
    categories_display.sort(key=lambda x: x["display_name"])
    return render_template('manage_categories.html', categories=categories_display, page_title="Manage Categories")

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name_dict = {lang: request.form.get(f'name_{lang}', '').strip() or None for lang in LANGUAGES}
        description_dict = {lang: [line.strip() for line in request.form.getlist(f'description_{lang}[]') if line.strip()] for lang in LANGUAGES}
        image_file = request.files.get('image')
        slug = generate_slug(name_dict, DATA_STORE["categories"].keys(), prefix="cat")
        image_path = save_image_file(image_file, 'categories') if image_file and image_file.filename else None
        DATA_STORE["categories"][slug] = {"name": name_dict, "description": description_dict, "image": image_path, "children_item_slugs": []}
        save_data(); display_name_for_flash = name_dict.get('en') or name_dict.get('ar') or slug
        flash(f"Category '{display_name_for_flash}' added successfully!", 'success')
        return redirect(url_for('admin.manage_categories'))
    return render_template('category_form.html', form_action="Add", page_title="Add New Category", category=None, languages=LANGUAGES)

@admin_bp.route('/categories/edit/<category_slug>', methods=['GET', 'POST'])
@login_required
def edit_category(category_slug):
    category = DATA_STORE["categories"].get(category_slug)
    if not category: flash("Category not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        name_dict = {lang: request.form.get(f'name_{lang}', '').strip() or None for lang in LANGUAGES}
        description_dict = {lang: [line.strip() for line in request.form.getlist(f'description_{lang}[]') if line.strip()] for lang in LANGUAGES}
        image_file = request.files.get('image'); remove_image = request.form.get('remove_image') == 'on'
        current_image_path = category.get('image'); new_image_path = current_image_path
        if remove_image:
            if current_image_path:
                old_image_disk_path = os.path.join(app.static_folder, current_image_path)
                if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '': new_image_path = save_image_file(image_file, 'categories', current_image_path=current_image_path)
        category["name"] = name_dict; category["description"] = description_dict; category["image"] = new_image_path
        save_data(); display_name_for_flash = name_dict.get('en') or name_dict.get('ar') or category_slug
        flash(f"Category '{display_name_for_flash}' updated successfully!", 'success'); return redirect(url_for('admin.manage_categories'))
    return render_template('category_form.html', form_action="Edit", category=category, category_slug=category_slug, page_title=f"Edit Category", languages=LANGUAGES)

@admin_bp.route('/categories/delete/<category_slug>', methods=['POST'])
@login_required
def delete_category(category_slug): # ... (same, save_data() inside) ...
    category = DATA_STORE["categories"].get(category_slug)
    if category:
        if category.get("children_item_slugs"): flash(f"Cannot delete category: it has child items. Delete them first.", "danger"); return redirect(url_for('admin.manage_categories'))
        if category.get('image'):
            image_disk_path = os.path.join(app.static_folder, category['image'])
            if os.path.exists(image_disk_path): os.remove(image_disk_path)
        del DATA_STORE["categories"][category_slug]; save_data()
        flash(f"Category deleted successfully!", 'success')
    else: flash("Category not found.", "danger")
    return redirect(url_for('admin.manage_categories'))

# Admin views for children (view_category_children_admin, view_item_children_admin - use get_translated_text for display)
@admin_bp.route('/categories/<category_slug>/items')
@login_required
def view_category_children_admin(category_slug): # ... (Updated to use get_translated_text for display)
    category = DATA_STORE["categories"].get(category_slug)
    if not category: flash("Category not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    child_items_list = []
    for item_slug in category.get("children_item_slugs", []):
        item_data = DATA_STORE["items"].get(item_slug)
        if item_data: 
            display_name = get_translated_text(item_data.get("name"), 'en') or item_slug
            child_items_list.append({"slug": item_slug, "display_name": display_name, **item_data})
    child_items_list.sort(key=lambda x: (x.get("type", ""), x.get("display_name", x["slug"])))
    parent_display_name = get_translated_text(category.get("name"), 'en') or category_slug
    parent_context = {"type": "category", "slug": category_slug, "name": parent_display_name}
    breadcrumb_path = [{"name": parent_display_name, "url": None}]
    return render_template('manage_items_under_parent.html', items=child_items_list, parent_name_display=parent_display_name, parent_type_display="Category", parent_context=parent_context, parent_path=breadcrumb_path, page_title=f"Items in Category: {parent_display_name}")

@admin_bp.route('/items/<parent_item_slug>/children')
@login_required
def view_item_children_admin(parent_item_slug): # ... (Updated to use get_translated_text for display)
    parent_item = DATA_STORE["items"].get(parent_item_slug)
    if not parent_item or parent_item.get("type") != "subcategory":
        flash("Parent item not found or is not a subcategory.", "danger")
        # ... (graceful redirect) ...
        grandparent_type = parent_item.get("parent_type") if parent_item else None; grandparent_slug = parent_item.get("parent_slug") if parent_item else None
        if grandparent_type == 'category' and grandparent_slug: return redirect(url_for('admin.view_category_children_admin', category_slug=grandparent_slug))
        return redirect(url_for('admin.manage_categories'))

    child_items_list = []
    for item_slug in parent_item.get("children_item_slugs", []):
        item_data = DATA_STORE["items"].get(item_slug)
        if item_data: 
            display_name = get_translated_text(item_data.get("name"), 'en') or item_slug
            child_items_list.append({"slug": item_slug, "display_name": display_name, **item_data})
    child_items_list.sort(key=lambda x: (x.get("type", ""), x.get("display_name", x["slug"])))
    parent_display_name = get_translated_text(parent_item.get("name"), 'en') or parent_item_slug
    parent_context = {"type": "item", "slug": parent_item_slug, "name": parent_display_name}
    breadcrumb_path = []; current_trace_slug = parent_item_slug; current_trace_item = parent_item; temp_path_for_display = []
    while current_trace_item:
        is_current_parent = (current_trace_slug == parent_item_slug)
        current_item_display_name_for_bc = get_translated_text(current_trace_item.get("name"), 'en') or current_trace_slug
        url = None if is_current_parent else (url_for('admin.view_item_children_admin', parent_item_slug=current_trace_slug) if current_trace_item.get("type") == "subcategory" else None)
        temp_path_for_display.insert(0, { "name": current_item_display_name_for_bc, "url": url})
        pt = current_trace_item.get("parent_type"); ps = current_trace_item.get("parent_slug")
        if pt == "category":
            cat_data = DATA_STORE["categories"].get(ps,{})
            cat_display_name_for_bc = get_translated_text(cat_data.get("name"), 'en') or ps
            temp_path_for_display.insert(0, {"name": cat_display_name_for_bc, "url": url_for('admin.view_category_children_admin', category_slug=ps)})
            break
        elif pt == "item": current_trace_slug = ps; current_trace_item = DATA_STORE["items"].get(current_trace_slug)
        else: break
    breadcrumb_path = temp_path_for_display
    return render_template('manage_items_under_parent.html', items=child_items_list, parent_name_display=parent_display_name, parent_type_display="Subcategory", parent_context=parent_context, parent_path=breadcrumb_path, page_title=f"Items in Subcategory: {parent_display_name}")

def get_possible_parents_for_item(editing_item_slug=None): # ... (Updated to use get_translated_text for display names)
    parents = []
    for cat_slug, cat_data in DATA_STORE["categories"].items():
        parents.append({ "slug": cat_slug, "name": f"Category: {get_translated_text(cat_data.get('name'), 'en') or cat_slug}", "type": "category", "full_slug_id": f"category:{cat_slug}"})
    for item_slug, item_data in DATA_STORE["items"].items():
        if item_slug == editing_item_slug: continue
        if item_data.get('type') == 'subcategory':
            path_name_parts = []; current_parent_for_path_slug = item_slug; current_parent_for_path_data = item_data
            depth_count = 0; max_depth = 10 
            while current_parent_for_path_data and depth_count < max_depth:
                path_name_parts.insert(0, get_translated_text(current_parent_for_path_data.get('name'), 'en') or current_parent_for_path_slug)
                pt = current_parent_for_path_data.get('parent_type'); ps = current_parent_for_path_data.get('parent_slug')
                if pt == 'category':
                    top_cat_data = DATA_STORE["categories"].get(ps, {})
                    path_name_parts.insert(0, f"Category: {get_translated_text(top_cat_data.get('name'), 'en') or ps}")
                    break
                elif pt == 'item': current_parent_for_path_slug = ps; current_parent_for_path_data = DATA_STORE["items"].get(ps)
                else: break; depth_count += 1
            parents.append({ "slug": item_slug, "name": f"SubCat: {' > '.join(path_name_parts)}", "type": "item", "full_slug_id": f"item:{item_slug}"})
    parents.sort(key=lambda x: x["name"])
    return parents

# --- Item Add/Edit/Delete (Multilingual) ---
@admin_bp.route('/items/add/new', methods=['GET', 'POST'])
@login_required
def add_item():
    # ... (pre_selected logic - same) ...
    pre_selected_item_type = request.args.get('item_type'); parent_type_from_url = request.args.get('parent_type'); parent_slug_from_url = request.args.get('parent_slug')
    pre_selected_parent_full_slug = f"{parent_type_from_url}:{parent_slug_from_url}" if parent_type_from_url and parent_slug_from_url else None
    if request.method == 'POST':
        item_type = request.form.get('item_type', pre_selected_item_type)
        if not item_type: flash("Item type is missing.", "danger"); return redirect(request.url)
        
        name_dict = {lang: request.form.get(f'name_{lang}', '').strip() or None for lang in LANGUAGES}
        parent_full_slug_from_form = request.form.get('parent_full_slug')
        image_file = request.files.get('image')
        image_path = save_image_file(image_file, 'items') if image_file and image_file.filename else None

        if not parent_full_slug_from_form or ':' not in parent_full_slug_from_form: flash("Invalid parent selection.", "danger"); return redirect(request.url)
        parent_type, parent_slug = parent_full_slug_from_form.split(':', 1)
        # ... (parent validation & child type consistency check - same as before) ...
        parent_valid = False
        if parent_type == "category" and parent_slug in DATA_STORE["categories"]: parent_valid = True
        elif parent_type == "item" and parent_slug in DATA_STORE["items"] and DATA_STORE["items"][parent_slug].get('type') == 'subcategory': parent_valid = True
        if not parent_valid: flash("Selected parent is invalid or not found.", "danger"); return redirect(request.url)
        if parent_type == "item": 
            parent_item_data = DATA_STORE["items"][parent_slug]
            if parent_item_data.get("children_item_slugs"):
                first_child_slug = parent_item_data["children_item_slugs"][0]; first_child_type = DATA_STORE["items"].get(first_child_slug, {}).get("type")
                if first_child_type and first_child_type != item_type: flash(f"Parent subcategory already contains items of type '{first_child_type}'. Cannot add a '{item_type}'.", "danger"); return redirect(request.url)

        slug = generate_slug(name_dict, DATA_STORE["items"].keys(), prefix=item_type[:4])
        item_data = { "type": item_type, "name": name_dict, "parent_type": parent_type, "parent_slug": parent_slug, "image": image_path }

        if item_type == 'subcategory':
            item_data["description"] = {lang: [line.strip() for line in request.form.getlist(f'description_{lang}[]') if line.strip()] for lang in LANGUAGES}
            item_data["children_item_slugs"] = []
        elif item_type == 'product':
            item_data["short_description"] = {lang: [line.strip() for line in request.form.getlist(f'short_description_{lang}[]') if line.strip()] for lang in LANGUAGES}
            item_data["long_description_markdown"] = {lang: request.form.get(f'long_description_markdown_{lang}', '').strip() for lang in LANGUAGES}
            item_data["use_short_desc_for_long"] = request.form.get('use_short_desc_for_long') == 'on'
        
        DATA_STORE["items"][slug] = item_data
        if parent_type == "category": DATA_STORE["categories"][parent_slug]["children_item_slugs"].append(slug)
        elif parent_type == "item": DATA_STORE["items"][parent_slug]["children_item_slugs"].append(slug)
        save_data(); display_name_for_flash = name_dict.get('en') or name_dict.get('ar') or slug
        flash(f"{item_type.capitalize()} '{display_name_for_flash}' added successfully!", 'success')
        if parent_type == "category": return redirect(url_for('admin.view_category_children_admin', category_slug=parent_slug))
        elif parent_type == "item": return redirect(url_for('admin.view_item_children_admin', parent_item_slug=parent_slug))
        return redirect(url_for('admin.manage_categories'))
    parents_for_select = get_possible_parents_for_item()
    return render_template('item_form.html', form_action="Add", parents=parents_for_select, page_title=f"Add New {pre_selected_item_type.capitalize() if pre_selected_item_type else 'Item'}", item=None, pre_selected_item_type=pre_selected_item_type, pre_selected_parent_full_slug=pre_selected_parent_full_slug, languages=LANGUAGES)

@admin_bp.route('/items/edit/<item_slug>', methods=['GET', 'POST'])
@login_required
def edit_item(item_slug):
    item = DATA_STORE["items"].get(item_slug)
    if not item: flash("Item not found.", "danger"); return redirect(url_for('admin.manage_categories'))
    if request.method == 'POST':
        item_type = item.get('type')
        name_dict = {lang: request.form.get(f'name_{lang}', '').strip() or None for lang in LANGUAGES}
        item["name"] = name_dict
        # ... (parent change logic, image - same as before) ...
        old_parent_type = item.get('parent_type'); old_parent_slug = item.get('parent_slug')
        new_parent_full_slug = request.form.get('parent_full_slug'); image_file = request.files.get('image'); remove_image = request.form.get('remove_image') == 'on'
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
                    first_child_slug_of_new_parent = existing_children_of_new_parent[0]; first_child_type_of_new_parent = DATA_STORE["items"].get(first_child_slug_of_new_parent, {}).get("type")
                    if first_child_type_of_new_parent and first_child_type_of_new_parent != item_type: flash(f"New parent subcategory already contains items of type '{first_child_type_of_new_parent}'.", "danger"); return redirect(url_for('admin.edit_item', item_slug=item_slug))
        if remove_image:
            if current_image_path: old_image_disk_path = os.path.join(app.static_folder, current_image_path);
            if os.path.exists(old_image_disk_path): os.remove(old_image_disk_path)
            new_image_path = None
        elif image_file and image_file.filename != '': new_image_path = save_image_file(image_file, 'items', current_image_path=current_image_path)
        item["image"] = new_image_path
        if item_type == 'subcategory':
            item["description"] = {lang: [line.strip() for line in request.form.getlist(f'description_{lang}[]') if line.strip()] for lang in LANGUAGES}
        elif item_type == 'product':
            item["short_description"] = {lang: [line.strip() for line in request.form.getlist(f'short_description_{lang}[]') if line.strip()] for lang in LANGUAGES}
            item["long_description_markdown"] = {lang: request.form.get(f'long_description_markdown_{lang}', '').strip() for lang in LANGUAGES}
            item["use_short_desc_for_long"] = request.form.get('use_short_desc_for_long') == 'on'
        if old_parent_type != new_parent_type or old_parent_slug != new_parent_slug: # ... (parent update logic - same)
            if old_parent_type == "category" and old_parent_slug in DATA_STORE["categories"]:
                if item_slug in DATA_STORE["categories"][old_parent_slug]["children_item_slugs"]: DATA_STORE["categories"][old_parent_slug]["children_item_slugs"].remove(item_slug)
            elif old_parent_type == "item" and old_parent_slug in DATA_STORE["items"]:
                 if item_slug in DATA_STORE["items"][old_parent_slug].get("children_item_slugs", []): DATA_STORE["items"][old_parent_slug]["children_item_slugs"].remove(item_slug)
            if new_parent_type == "category": DATA_STORE["categories"][new_parent_slug]["children_item_slugs"].append(item_slug)
            elif new_parent_type == "item": DATA_STORE["items"][new_parent_slug]["children_item_slugs"].append(item_slug)
            item["parent_type"] = new_parent_type; item["parent_slug"] = new_parent_slug
        save_data(); display_name_for_flash = name_dict.get('en') or name_dict.get('ar') or item_slug
        flash(f"{item_type.capitalize()} '{display_name_for_flash}' updated successfully!", 'success')
        if item["parent_type"] == "category": return redirect(url_for('admin.view_category_children_admin', category_slug=item["parent_slug"]))
        elif item["parent_type"] == "item": return redirect(url_for('admin.view_item_children_admin', parent_item_slug=item["parent_slug"]))
        return redirect(url_for('admin.manage_categories'))
    parents_for_select = get_possible_parents_for_item(editing_item_slug=item_slug)
    current_parent_full_slug = f"{item.get('parent_type')}:{item.get('parent_slug')}"
    return render_template('item_form.html', form_action="Edit", item=item, item_slug=item_slug, parents=parents_for_select, current_parent_full_slug=current_parent_full_slug, page_title=f"Edit {item.get('type', 'Item').capitalize()}", languages=LANGUAGES)

@admin_bp.route('/items/delete/<item_slug>', methods=['POST'])
@login_required
def delete_item(item_slug): # ... (same logic, ensure save_data() is called)
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
        del DATA_STORE["items"][item_slug]; save_data()
        flash(f"{item_type.capitalize()} deleted successfully!", 'success')
    else: flash("Item not found.", "danger")
    return redirect(redirect_url)

@admin_bp.route('/upload-description-image', methods=['POST']) # ... (same)
@login_required
def upload_description_image():
    if 'description_image' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['description_image']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        image_path_web = save_image_file(file, 'description_images')
        if image_path_web:
            static_file_url = url_for('static', filename=image_path_web.replace('\\', '/'), _external=True)
            return jsonify({'imageUrl': static_file_url}), 200
        else: return jsonify({'error': 'File upload failed.'}), 500
    return jsonify({'error': 'File type not allowed.'}), 400

app.register_blueprint(admin_bp)

# --- Frontend Routes with Language Prefix ---
# Add language code to all frontend URL rules
@app.route('/<lang_code>/')
@app.route('/<lang_code>/#<anchor>')
def home_page(lang_code, anchor=None): # ... (ensure all frontend routes use lang_code and get_translated_text) ...
    if lang_code not in app.config['LANGUAGES']: return redirect(url_for('home_page', lang_code=app.config['DEFAULT_LANGUAGE']))
    session['lang_code'] = lang_code; g.lang_code = lang_code
    carousel_slides_data = [ {"image": "images/carousel/slide1.jpg", "alt": {"en": "High-quality PET Bottles", "ar": "قناني PET عالية الجودة"},  "caption_header": {"en": "MG PET for Premium PET Solutions", "ar": "MG PET لحلول PET المتميزة"},  "caption_text": {"en": "", "ar": ""}}, {"image": "images/carousel/slide2.jpg",  "alt": {"en": "Customizable Bottle Designs", "ar": "تصاميم قناني قابلة للتخصيص"},  "caption_header": {"en": "It starts with MG PET and ends with trust", "ar": "تبدأ الثقة مع MG PET"},  "caption_text": {"en": "", "ar": ""}}, {"image": "images/carousel/slide3.jpg",  "alt": {"en": "Eco-Friendly Options", "ar": "خيارات صديقة للبيئة"},  "caption_header": {"en": "MG PET is your partner for success and excellence", "ar": "MGPET شريكك للنجاح والتميز"},  "caption_text": {"en": "", "ar": ""}}]
    translated_carousel_slides = []
    for slide in carousel_slides_data:
        translated_carousel_slides.append({ "image": slide["image"], "alt": get_translated_text(slide["alt"]), "caption_header": get_translated_text(slide["caption_header"]), "caption_text": get_translated_text(slide["caption_text"])})
    return render_template('index.html', carousel_slides=translated_carousel_slides)

@app.route('/<lang_code>/contact', methods=['GET', 'POST'])
def contact_page(lang_code): # ... (ensure all frontend routes use lang_code and get_translated_text) ...
    if lang_code not in app.config['LANGUAGES']: return redirect(url_for('contact_page', lang_code=app.config['DEFAULT_LANGUAGE']))
    session['lang_code'] = lang_code; g.lang_code = lang_code
    if request.method == 'POST':
        flash(get_translated_text({"en": "Thank you for your message!", "ar": "شكراً لرسالتك!"}), "success")
        return redirect(url_for('contact_page', lang_code=lang_code))
    return render_template('contact.html', page_title=get_translated_text({"en": "Contact Us", "ar": "اتصل بنا"}))

@app.route('/<lang_code>/products') 
def list_top_level_categories(lang_code): # ... (ensure all frontend routes use lang_code and get_translated_text) ...
    if lang_code not in app.config['LANGUAGES']: return redirect(url_for('list_top_level_categories', lang_code=app.config['DEFAULT_LANGUAGE']))
    session['lang_code'] = lang_code; g.lang_code = lang_code
    categories_to_display = []
    sorted_categories = sorted(DATA_STORE["categories"].items(), key=lambda item: (get_translated_text(item[1].get("name"), lang_code) or item[0]))
    for slug, data in sorted_categories:
        name_translated = get_translated_text(data.get("name"), lang_code)
        if name_translated: categories_to_display.append({ "slug": slug, "name": name_translated, "image": data.get("image", "images/uploads/categories/default_cat.jpg"), "description_lines": get_translated_list(data.get("description"), lang_code)})
    return render_template('product_categories_list.html', items=categories_to_display, page_title=get_translated_text({"en": "Our Product Categories", "ar": "فئات منتجاتنا"}), breadcrumb=[{"name": get_translated_text({"en": "Products", "ar": "المنتجات"}), "url": None}])

@app.route('/<lang_code>/products/category/<category_slug>')
def view_category_children(lang_code, category_slug): # ... (ensure all frontend routes use lang_code and get_translated_text) ...
    if lang_code not in app.config['LANGUAGES']: return redirect(url_for('view_category_children', lang_code=app.config['DEFAULT_LANGUAGE'], category_slug=category_slug))
    session['lang_code'] = lang_code; g.lang_code = lang_code
    category = DATA_STORE["categories"].get(category_slug)
    if not category: flash("Category not found.", "warning"); return redirect(url_for('list_top_level_categories', lang_code=lang_code))
    category_name_translated = get_translated_text(category.get("name"), lang_code) or category_slug
    children_to_display = []
    sorted_child_slugs = sorted(category.get("children_item_slugs", []), key=lambda item_slug: (get_translated_text(DATA_STORE["items"].get(item_slug, {}).get("name"), lang_code) or item_slug))
    for item_slug in sorted_child_slugs:
        item_data = DATA_STORE["items"].get(item_slug)
        if item_data:
            child_name_translated = get_translated_text(item_data.get("name"), lang_code)
            if child_name_translated:
                desc_key = "description" if item_data.get("type") == "subcategory" else "short_description"
                children_to_display.append({ "slug": item_slug, "type": item_data.get("type"), "name": child_name_translated, "image": item_data.get("image", "images/uploads/items/default_item.jpg"), "description_lines": get_translated_list(item_data.get(desc_key), lang_code) })
    breadcrumb = [ {"name": get_translated_text({"en": "Products", "ar": "المنتجات"}), "url": url_for('list_top_level_categories', lang_code=lang_code)}, {"name": category_name_translated, "url": None}]
    return render_template('product_item_list.html', parent_name=category_name_translated, parent_type_display="Category", items=children_to_display, page_title=f"{get_translated_text({'en':'Items in','ar':'العناصر في'})} {category_name_translated}", breadcrumb=breadcrumb)

@app.route('/<lang_code>/products/item/<item_slug>')
def view_item_or_children(lang_code, item_slug): # ... (ensure all frontend routes use lang_code and get_translated_text) ...
    if lang_code not in app.config['LANGUAGES']: return redirect(url_for('view_item_or_children', lang_code=app.config['DEFAULT_LANGUAGE'], item_slug=item_slug))
    session['lang_code'] = lang_code; g.lang_code = lang_code
    item = DATA_STORE["items"].get(item_slug)
    if not item: flash("Item not found.", "warning"); return redirect(url_for('list_top_level_categories', lang_code=lang_code))
    item_name_translated = get_translated_text(item.get("name"), lang_code) or item_slug
    breadcrumb = [{"name": get_translated_text({"en": "Products", "ar": "المنتجات"}), "url": url_for('list_top_level_categories', lang_code=lang_code)}]
    path_to_current_item = []; current_parent_type = item.get("parent_type"); current_parent_slug = item.get("parent_slug")
    temp_path_segments = []
    while current_parent_slug:
        if current_parent_type == "category":
            category_data = DATA_STORE["categories"].get(current_parent_slug, {})
            temp_path_segments.insert(0, {"name": get_translated_text(category_data.get("name"), lang_code) or current_parent_slug, "url": url_for('view_category_children', lang_code=lang_code, category_slug=current_parent_slug)})
            break 
        elif current_parent_type == "item":
            parent_item_data = DATA_STORE["items"].get(current_parent_slug)
            if not parent_item_data: break
            temp_path_segments.insert(0, {"name": get_translated_text(parent_item_data.get("name"), lang_code) or current_parent_slug, "url": url_for('view_item_or_children', lang_code=lang_code, item_slug=current_parent_slug)})
            current_parent_type = parent_item_data.get("parent_type"); current_parent_slug = parent_item_data.get("parent_slug")
        else: break
    breadcrumb.extend(temp_path_segments)
    breadcrumb.append({"name": item_name_translated, "url": None})
    if item.get("type") == "subcategory":
        children_to_display = []
        sorted_child_slugs = sorted(item.get("children_item_slugs", []), key=lambda cs: (get_translated_text(DATA_STORE["items"].get(cs, {}).get("name"), lang_code) or cs))
        for child_slug in sorted_child_slugs:
            child_data = DATA_STORE["items"].get(child_slug)
            if child_data:
                child_name_translated = get_translated_text(child_data.get("name"), lang_code)
                if child_name_translated:
                    desc_key = "description" if child_data.get("type") == "subcategory" else "short_description"
                    children_to_display.append({ "slug": child_slug, "type": child_data.get("type"), "name": child_name_translated, "image": child_data.get("image", "images/uploads/items/default_item.jpg"), "description_lines": get_translated_list(child_data.get(desc_key), lang_code) })
        return render_template('product_item_list.html', parent_name=item_name_translated, parent_type_display="Subcategory", items=children_to_display, page_title=f"{get_translated_text({'en':'Items in','ar':'العناصر في'})} {item_name_translated}", breadcrumb=breadcrumb)
    elif item.get("type") == "product":
        long_desc_markdown_dict = item.get("long_description_markdown", {"en":"", "ar":""}) # Ensure dict
        long_desc_markdown_translated = get_translated_text(long_desc_markdown_dict, lang_code)
        if item.get("use_short_desc_for_long", False):
            short_desc_dict = item.get("short_description", {"en":[], "ar":[]}) # Ensure dict
            short_desc_list_translated = get_translated_list(short_desc_dict, lang_code)
            long_desc_markdown_translated = "\n\n".join(short_desc_list_translated)
        html_description = Markup(markdown.markdown(long_desc_markdown_translated, extensions=['attr_list', 'tables', 'fenced_code', 'nl2br']))
        return render_template('product_detail_page.html', product=item, product_name_display=item_name_translated, product_slug=item_slug, html_description=html_description, page_title=item_name_translated, breadcrumb=breadcrumb)
    else: flash("Unknown item type.", "danger"); return redirect(url_for('list_top_level_categories', lang_code=lang_code))

@app.route('/') # Root redirect
def root_redirect():
    preferred_lang = request.accept_languages.best_match(app.config['LANGUAGES']) or app.config['DEFAULT_LANGUAGE']
    return redirect(url_for('home_page', lang_code=preferred_lang))

@app.errorhandler(404)
def page_not_found(e): # ... (same)
    lang = session.get('lang_code', app.config['DEFAULT_LANGUAGE']); path_parts = request.path.split('/')
    if len(path_parts) > 1 and path_parts[1] in app.config['LANGUAGES']: lang = path_parts[1]
    if request.path.startswith('/admin/'): return render_template('404_admin.html', page_title="Page Not Found", current_lang=lang), 404
    return render_template('404.html', page_title="Page Not Found", current_lang=lang), 404

if __name__ == '__main__': # ... (Update sample data for multilingual) ...
    app.run(debug=True, host='0.0.0.0')