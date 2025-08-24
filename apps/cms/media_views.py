import os
import mimetypes
from django.conf import settings
from django.http import Http404, HttpResponse, FileResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe
from django.utils.decorators import method_decorator
from django.views import View
from pathlib import Path


@method_decorator(require_safe, name='dispatch')
@method_decorator(cache_control(max_age=3600), name='dispatch')
class MediaFileView(View):
    """Custom view to serve media files in production"""
    
    def get(self, request, file_path):
        """Serve media file"""
        try:
            # Build the full file path
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            # Security check - ensure the path is within MEDIA_ROOT
            full_path = os.path.abspath(full_path)
            media_root = os.path.abspath(settings.MEDIA_ROOT)
            
            if not full_path.startswith(media_root):
                raise Http404("Invalid file path")
            
            # Check if file exists
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                raise Http404("File not found")
            
            # Get file info
            file_size = os.path.getsize(full_path)
            content_type, encoding = mimetypes.guess_type(full_path)
            
            # Default content type if not detected
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Use FileResponse for efficient file serving
            response = FileResponse(
                open(full_path, 'rb'),
                content_type=content_type
            )
            
            # Set filename for download
            filename = os.path.basename(full_path)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            response['Content-Length'] = str(file_size)
            
            return response
            
        except Exception as e:
            # Log the error in production
            if not settings.DEBUG:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Media file serving error: {str(e)} for path: {file_path}")
            raise Http404("File not found")


def serve_media_file(request, file_path):
    """Function-based view alternative"""
    try:
        # Build the full file path
        full_path = Path(settings.MEDIA_ROOT) / file_path
        
        # Security check - ensure the path is within MEDIA_ROOT
        if not str(full_path.resolve()).startswith(str(Path(settings.MEDIA_ROOT).resolve())):
            raise Http404("Invalid file path")
        
        # Check if file exists
        if not full_path.exists() or not full_path.is_file():
            raise Http404("File not found")
        
        # Get content type
        content_type, _ = mimetypes.guess_type(str(full_path))
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Return file response
        return FileResponse(
            open(full_path, 'rb'),
            content_type=content_type,
            filename=full_path.name
        )
        
    except Exception as e:
        if not settings.DEBUG:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Media file serving error: {str(e)} for path: {file_path}")
        raise Http404("File not found")