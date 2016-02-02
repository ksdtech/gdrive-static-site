import logging

from pelican.contents import Content, Page

# logger for this file
logger = logging.getLogger(__name__)

class DocMeta(Content):
    """
    A custom content type for a YAML metadata file.  There are two types
    that we parse: _folder_.yml and _meta_xxxx.yml
    """

    # Properties that gdrive-static-site copy_folder.py inserts or updates
    mandatory_properties = ('author','basename','dirname','relative_url','source_id',
        'source_type','title','slug','date','modified')
    
    # No output, so don't care
    default_template = 'page'

class NavMenu(Content):
    """
    A custom content type for _navmenu_.yml metdata files.
    """
    
    # Properties that gdrive-static-site copy_folder.py inserts or updates
    mandatory_properties = ('author','basename','dirname','navmenu','source_id',
        'source_type','date','modified')

    # No output, so don't care
    default_template = 'page'
