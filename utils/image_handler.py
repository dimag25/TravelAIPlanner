import os
from PIL import Image
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_SIZE = (800, 800)  # Maximum dimensions for uploaded images

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """
    Save and process the uploaded image.
    Returns the path where the image was saved (relative to static folder).
    """
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    filename = secure_filename(file.filename)
    base_name, extension = os.path.splitext(filename)
    unique_filename = f"{base_name}_{os.urandom(8).hex()}{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Open and process the image
    img = Image.open(file)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize if larger than MAX_SIZE while maintaining aspect ratio
    if img.size[0] > MAX_SIZE[0] or img.size[1] > MAX_SIZE[1]:
        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
    
    # Save the processed image
    img.save(file_path, optimize=True, quality=85)
    
    # Return the path relative to static folder
    return os.path.relpath(file_path, 'static')
