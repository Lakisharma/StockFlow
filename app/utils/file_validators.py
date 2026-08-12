import os
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.csv', '.xlsx', '.json'}
DISALLOWED_EXECUTABLE_EXTENSIONS = {'.exe', '.sh', '.bat', '.py', '.php', '.js', '.vbs', '.cmd', '.dll', '.so'}

def validate_file_upload(file_obj, allowed_extensions=None, max_size_mb=10.0):
    if not file_obj:
        return True

    # 1. Size Validation
    max_size_bytes = int(max_size_mb * 1024 * 1024)
    if file_obj.size > max_size_bytes:
        raise ValidationError(f"File size exceeds maximum permitted limit of {max_size_mb} MB.")

    # 2. Extension Validation
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext in DISALLOWED_EXECUTABLE_EXTENSIONS:
        raise ValidationError("Security violation: Executable scripts or binary files cannot be uploaded.")

    if allowed_extensions and ext not in allowed_extensions:
        allowed_str = ", ".join(allowed_extensions)
        raise ValidationError(f"Invalid file format '{ext}'. Allowed formats: {allowed_str}")

    return True
