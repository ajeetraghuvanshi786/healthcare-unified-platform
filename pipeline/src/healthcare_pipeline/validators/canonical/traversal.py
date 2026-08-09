"""Compatibility facade for canonical traversal helpers.

Cross-cutting traversal belongs to the canonical boundary because validation,
terminology, identity, and future persistence services all need the same paths.
"""

from healthcare_pipeline.canonical.traversal import iter_codings, iter_identifiers

__all__ = ["iter_codings", "iter_identifiers"]
