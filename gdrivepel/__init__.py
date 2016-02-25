from pelican import signals
from .readers import on_readers_init
from .generators import on_get_generators, on_all_generators_finalized
# from .search import on_content

# Pelican plugin interface

def register():
    """Plugin registration."""

    # Hook our readers logic in
    signals.readers_init.connect(on_readers_init)

    # Hook our generator logic in
    signals.get_generators.connect(on_get_generators)
    signals.all_generators_finalized.connect(on_all_generators_finalized)

    # Build search indexes
    # Would be nice if we had a custom signal to trigger when content was modified

    # Now hooked in from YamlGenerator, so don't register this connection
    # signals.content_object_init.connect(on_content)
