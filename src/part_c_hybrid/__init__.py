# Avoid eager import of the full graph so lightweight tests can import nodes only.
__all__ = ["build_hybrid_graph"]


def __getattr__(name: str):
    if name == "build_hybrid_graph":
        from .graph import build_hybrid_graph
        return build_hybrid_graph
    raise AttributeError(name)
