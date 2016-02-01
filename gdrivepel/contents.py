import logging

from pelican.contents import Content, Page

# logger for this file
logger = logging.getLogger(__name__)

class Section(Page):
    """A custom content type for a section page, that is a Page that 
    contains a table of contents (secondary navigation), listing documents 
    and subtopics within the page's folder."""

    def __init__(self, *args, **kwargs):
        super(Section, self).__init__(*args, **kwargs)
        self._output_location_referenced = False

    @property
    def url(self):
        # Note when url has been referenced, so we can avoid overriding it.
        self._output_location_referenced = True
        return super(Section, self).url

    @property
    def save_as(self):
        # Note when save_as has been referenced, so we can avoid overriding it.
        self._output_location_referenced = True
        return super(Section, self).save_as

    def attach_to(self, content):
        """Override our output directory with that of the given content object.
        """
        # Determine our file's new output path relative to the linking document.
        # If it currently lives beneath the linking document's source directory,
        # preserve that relationship on output. Otherwise, make it a sibling.
        linking_source_dir = os.path.dirname(content.source_path)
        tail_path = os.path.relpath(self.source_path, linking_source_dir)
        if tail_path.startswith(os.pardir + os.sep):
            tail_path = os.path.basename(tail_path)
        new_save_as = os.path.join(
            os.path.dirname(content.save_as), tail_path)

        # We do not build our new url by joining tail_path with the linking
        # document's url, because we cannot know just by looking at the latter
        # whether it points to the document itself or to its parent directory.
        # (An url like 'some/content' might mean a directory named 'some'
        # with a file named 'content', or it might mean a directory named
        # 'some/content' with a file named 'index.html'.) Rather than trying
        # to figure it out by comparing the linking document's url and save_as
        # path, we simply build our new url from our new save_as path.
        new_url = path_to_url(new_save_as)

        def _log_reason(reason):
            logger.warning("The {attach} link in %s cannot relocate %s "
                "because %s. Falling back to {filename} link behavior instead.",
                content.get_relative_source_path(),
                self.get_relative_source_path(), reason,
                extra={'limit_msg': "More {attach} warnings silenced."})

        # We never override an override, because we don't want to interfere
        # with user-defined overrides that might be in EXTRA_PATH_METADATA.
        if hasattr(self, 'override_save_as') or hasattr(self, 'override_url'):
            if new_save_as != self.save_as or new_url != self.url:
                _log_reason("its output location was already overridden")
            return

        # We never change an output path that has already been referenced,
        # because we don't want to break links that depend on that path.
        if self._output_location_referenced:
            if new_save_as != self.save_as or new_url != self.url:
                _log_reason("another link already referenced its location")
            return

        self.override_save_as = new_save_as
        self.override_url = new_url


class DocMeta(Content):
    """A custom content type for a YAML metadata file.  There are two types
    that we parse: _folder_.yml and _meta_xxxx.yml"""

    # Properties that gdrive-static-site copy_folder.py inserts or updates
    mandatory_properties = ('author','basename','dirname','relative_url','source_id',
        'source_type','title','slug','date','modified')
    # No output, so don't care
    default_template = 'page'

    # __init__(self, content, metadata, settings source_path, context)
    def __init__(self, *args, **kwargs):
        super(DocMeta, self).__init__(*args, **kwargs)
        logger.debug('DocMeta, source_path = %s' % self.source_path)
        logger.debug('      dirname = %s' % self.dirname)
        logger.debug('     basename = %s' % self.basename)
        logger.debug(' relative_url = %s' % self.relative_url)
        logger.debug('         slug = %s' % self.relative_url)


class NavMenu(Content):
    """A custom content type for _navmenu_.yml metdata files."""

    # Properties that gdrive-static-site copy_folder.py inserts or updates
    mandatory_properties = ('author','basename','dirname','navmenu','source_id',
        'source_type','date','modified')

    # No output, so don't care
    default_template = 'page'

    # __init__(self, content, metadata, settings source_path, context)
    def __init__(self, *args, **kwargs):
        super(NavMenu, self).__init__(*args, **kwargs)
        logger.debug('NavMenu, source_path = %s' % self.source_path)
        logger.debug('      dirname = %s' % self.dirname)
        logger.debug('     basename = %s' % self.basename)
        logger.debug(' relative_url = %s' % self.relative_url)
        logger.debug('         slug = %s' % self.relative_url)
